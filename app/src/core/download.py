"""
Module to start the download process for the mods in the download list.
Use this module to import the Download class.

Imports: hash, logger, main_ui, paths, setup, state.
"""

import json
import logging
from pathlib import Path
import threading
import time
from typing import Any

import requests
import xxhash

from . import hash, main_ui, paths, setup, state
from .logger import MainLogger

_logger: logging.Logger = MainLogger.get().getChild(__name__)

class Download:
    """
    Start the download process for the mods in the download list.
    """
    def __init__(self) -> None:
        _download_path: Path|None = state.DownloadInfo().get_selected_path()
        assert _download_path, "No download path selected"
        
        _logger.info(f"Preparing to download mods to {_download_path}")
        self.download_path: Path = _download_path
        self._download_thread: threading.Thread|None = None
        try:
            self._load_mod_list()
            with requests.Session() as self._session:
                self._load_cookies()
                _logger.debug("Cookies loaded successfully")
                _logger.info("Starting download process")
                self._handle_list()
                if state.close_event.is_set():
                    _logger.info("Download process interrupted")
                else:
                    if self._download_thread:
                        self._download_thread.join()
                    main_ui.MainUI().write("\n")
                    _logger.info("Download process completed")
                    main_ui.MainUI().write("\nYou can now close the application")
        except Exception as e:
            _logger.error(f"An error occurred: {e}")
            state.close_event.set()
            raise e

    def _get_paths(self, file_name: str) -> tuple[Path, Path]:
        """
        Get the paths for the file and the part file.

        Args:
        - file_name (str): the name of the file.
        """
        assert isinstance(file_name, str), f"file_name must be a string, given {type(file_name)} instead"
        assert file_name != '', "file_name cannot be empty"
        
        file_path: Path = self.download_path / file_name
        part_path: Path = Path(f'{file_path}.part')
        return file_path, part_path

    def _load_mod_list(self) -> None:
        """
        Load the mod list from the mod data file.
        """
        with state.DownloadInfo().get_modlist_file().open('r') as json_file:
            full_mod_list: list[setup.ModData] = json.load(json_file)

        def is_already_downloaded(mod_data: setup.ModData) -> bool:
            """
            Check if the file is already downloaded.
            Delete unnecessary or corrupted files. No hash check for fully downloaded files.

            Args:
            - mod_data (ModData) : the mod data to check.
            """
            assert isinstance(mod_data, dict), f"mod_data must be a dictionary (ModData) object, given {type(mod_data)} instead"

            file_name: str = mod_data['FileName']
            total_size: int = mod_data['Size']
            hash_code: str = mod_data['Hash']
            file_path: Path
            part_path: Path
            file_path, part_path = self._get_paths(file_name)
            if file_path.is_file():
                part_path.unlink(missing_ok=True)
                return True
            if part_path.is_file():
                size: int = part_path.stat().st_size
                if size == total_size:
                    if hash.compare_hash_from_path(part_path, hash_code):
                        part_path.rename(file_path)
                        return True
                    else:
                        part_path.unlink()
                elif size > total_size:
                    part_path.unlink()
            return False
        
        self.mod_list: list[setup.ModData] = [mod_data for mod_data in full_mod_list if not is_already_downloaded(mod_data)]
        self.total_mods: int = len(self.mod_list)
        _logger.info(f"Found {self.total_mods} mods to download, {len(full_mod_list)-self.total_mods} mods already downloaded")

    def _load_cookies(self) -> None:
        """
        Load cookies from the cookies file.
        """
        with paths.COOKIES_FILE.open('r') as cookies_file:
            cookies: dict[str, Any] = json.load(cookies_file)
        self._session.cookies.update(cookies)
    
    def _direct_download(self, direct_url: str, file_name: str, total_size: int, hash_code: str) -> None:
        """
        Download a mod from the direct download link.
        """
        assert isinstance(direct_url, str), f"direct_url must be a string, given {type(direct_url)} instead"
        assert direct_url != '', "direct_url cannot be empty"
        assert isinstance(file_name, str), f"file_name must be a string, given {type(file_name)} instead"
        assert file_name != '', "file_name cannot be empty"
        assert isinstance(total_size, int), f"total_size must be an integer, given {type(total_size)} instead"
        assert total_size > 0, "total_size must be greater than 0"
        assert isinstance(hash_code, str), f"hash_code must be a string, given {type(hash_code)} instead"
        assert hash_code != '', "hash_code cannot be empty"

        try:
            _logger.info(f"Downloading {file_name}")
            file_path: Path
            part_path: Path
            file_path, part_path = self._get_paths(file_name)
            headers: dict[str, str] = {}
            already_downloaded_bytes: int = part_path.stat().st_size if part_path.is_file() else 0
            if already_downloaded_bytes:
                headers['Range'] = f'bytes={already_downloaded_bytes}-'
            downloaded: bool = False
            attempts: int = 0
            max_attempts: int = 2
            while not downloaded:
                with self._session.get(direct_url, headers=headers, stream=True) as r:
                    r.raise_for_status()
                    if total_size - already_downloaded_bytes != int(r.headers.get('Content-Length', 0)):
                        _logger.error(f"Error while downloading {file_name}. Size mismatch.")
                        _logger.debug(f"Expected size: {total_size-already_downloaded_bytes}, received size: {r.headers.get('Content-Length', 0)}")
                        return
                    main_ui.MainUI().set_download(file_name, total_size, already_downloaded_bytes)
                    file_hasher: xxhash.xxh64 = hash.get_hasher(part_path)
                    chunk_size: int = 256 * 1024    # I don't know what the best chunk size is
                    with part_path.open('ab') as file:
                        start_time: float = time.perf_counter()
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            file.write(chunk)
                            if state.close_event.is_set():
                                return
                            file_hasher.update(chunk)
                            bytes_downloaded: int = len(chunk)
                            already_downloaded_bytes += bytes_downloaded
                            end_time: float = time.perf_counter()
                            download_speed: float = bytes_downloaded / (end_time - start_time)
                            start_time = end_time
                            main_ui.MainUI().update_download_progression(already_downloaded_bytes, download_speed)
                if not hash.compare_hash(file_hasher, hash_code):
                    _logger.debug(f"Error while downloading {file_name}. Hash mismatch.")
                    part_path.unlink(missing_ok=True)
                    already_downloaded_bytes = 0
                    headers = {}
                    attempts += 1
                    if attempts == max_attempts:
                        _logger.error(f"Failed to download {file_name} after {max_attempts} attempts")
                        return
                    _logger.debug(f"Retrying download for {file_name}")
                    continue
                downloaded = True
            part_path.rename(file_path)
            _logger.info(f"{file_name} downloaded successfully")
        except Exception as e:
            _logger.error(f"Error while downloading {file_name}. Details: {e}")
            state.close_event.set()
            raise e

    def _handle_list(self) -> None:
        """
        Handle the download list.
        """
        if self.total_mods == 0:
            _logger.info("No mods to download")
            return
        main_ui.MainUI().set_total_downloads(self.total_mods)
        for _ in range(self.total_mods):
            mod_data: setup.ModData = self.mod_list.pop()
            file_name: str = mod_data['FileName']
            file_id: int = mod_data['FileID']
            game_id: int = mod_data['GameID']
            total_size: int = mod_data['Size']
            hash_code: str = mod_data['Hash']

            def get_direct_url() -> str:
                """
                Get the direct download link for a mod.
                """
                post_url: str = 'https://www.nexusmods.com/Core/Libs/Common/Managers/Downloads?GenerateDownloadUrl'
                data: dict[str, int] = {
                    'fid': file_id,
                    'game_id': game_id
                }
                post_response: requests.Response = self._session.post(post_url, data=data)
                if post_response.status_code == 200:
                    direct_url: str = post_response.json().get('url', '')
                    if direct_url and self._session.head(direct_url).status_code == 200:
                        _logger.debug(f"Direct download link for {file_name} obtained")
                        return direct_url
                    
                _logger.error(f"Error while getting direct download link for {file_name}")
                return ''
            
            direct_url: str = get_direct_url()
            if not direct_url or state.close_event.is_set():
                state.close_event.set()
                return
            if self._download_thread:
                self._download_thread.join()
            self._download_thread = threading.Thread(target=self._direct_download, daemon=True, args=(direct_url, file_name, total_size, hash_code))
            if state.close_event.is_set():
                return
            self._download_thread.start()
