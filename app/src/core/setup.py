"""
Module for setting up a modlist.

Useful functions:
- setup_modlist(modlist_name: str) -> bool: Set up the modlist by asking the user for the download path and the .wabbajack file. Returns True if the modlist was set up successfully, False otherwise.

Useful classes:
- ModData: A dictionary representing the data of a mod.

Imports: logger, state.
"""

import json
import logging
from pathlib import Path
import re
from tkinter import filedialog, messagebox
from typing import Any, TypedDict
import zipfile

import requests

from . import state
from .logger import MainLogger

_logger: logging.Logger = MainLogger.get().getChild(__name__)

class ModData(TypedDict):
    """
    A dictionary representing the data of a mod.
    """
    FileName: str
    Size: int
    Hash: str
    GameID: int
    FileID: int

def _read_modlist_from_wabbajack_file(wabbajack_file: Path) -> list[dict[Any, Any]]:
    """
    Reads the modlist from a Wabbajack file and returns it as a list of dictionaries.

    Args:
    - wabbajack_file (Path): The path to the .wabbajack file.
    """
    assert isinstance(wabbajack_file, Path), f"wabbajack_file must be a Path, given {type(wabbajack_file)} instead"
    assert wabbajack_file != Path(), "wabbajack_file must have a name"
    assert wabbajack_file.is_file(), f"{wabbajack_file} does not exist"
    
    _logger.debug(f"Reading modlist from {wabbajack_file}")
    with zipfile.ZipFile(wabbajack_file, 'r') as wabbajack_zip:
        with wabbajack_zip.open('modlist') as file:
            modlist: bytes = file.read()
    modlist_json_dict: dict[Any, Any] = json.loads(modlist)
    modlist_data: list[dict[Any, Any]] = modlist_json_dict['Archives']
    _logger.debug("Modlist read successfully")
    return modlist_data
    
def _create_list(wabbajack_file: Path, modlist_name: str) -> None:
    """
    Creates a modlist from a Wabbajack file and saves it as a .csv file.

    Args:
    - wabbajack_file (Path): The path to the .wabbajack file.
    - modlist_name (str): The name of the modlist to be created.
    """
    assert isinstance(wabbajack_file, Path), f"wabbajack_file must be a Path, given {type(wabbajack_file)} instead"
    assert wabbajack_file != Path(), "wabbajack_file must have a name"
    assert isinstance(modlist_name, str), f"modlist_name must be a string, given {type(modlist_name)} instead"
    assert modlist_name != '', "modlist_name cannot be empty"
    assert wabbajack_file.is_file(), f"{wabbajack_file} does not exist"

    _logger.debug(f"Creating list for {modlist_name}")
    modlist_data: list[dict[Any, Any]] = _read_modlist_from_wabbajack_file(wabbajack_file)
    refactored_modlist_data: list[ModData] = []
    game_id_dict: dict[str, int] = {}
    errors: int = 0
    for mod_data in modlist_data:
        if mod_data['State']['$type'] != 'NexusDownloader, Wabbajack.Lib':
            continue
        game_name: str = mod_data['State']['GameName']
        if game_name not in game_id_dict:
            response: requests.Response = requests.get(f'https://www.nexusmods.com/{game_name.lower()}')
            match: re.Match[str] | None = re.search(r'window.current_game_id = (\d+);', response.text)
            if not match:
                errors += 1
                continue
            game_id: int = int(match.group(1))
            if game_id == 0:
                errors += 1
                continue
            game_id_dict[game_name] = game_id
        useful_data: ModData = {
            'FileName': mod_data['Name'],
            'Size': mod_data['Size'],
            'Hash': mod_data['Hash'],
            'GameID': game_id_dict[game_name],
            'FileID': mod_data['State']['FileID']
        }
        refactored_modlist_data.append(useful_data)
    with state.DownloadInfo().get_modlist_file(modlist_name).open('w') as json_file:
        json.dump(refactored_modlist_data, json_file, indent=4)
    mods_found: int = len(refactored_modlist_data)
    _logger.info(f"List created successfully. Found {mods_found} mods. {errors} {"error" if errors == 1 else "errors"} occurred.")

def setup_modlist(modlist_name: str) -> bool:
    """
    Set up the modlist by asking the user for the download path and the .wabbajack file.
    Returns True if the modlist was set up successfully, False otherwise.

    Args:
    - modlist_name (str): The name of the modlist to be set up.
    """
    assert isinstance(modlist_name, str), f"modlist_name must be a string, given {type(modlist_name)} instead"
    assert modlist_name != '', "modlist_name cannot be empty"

    _logger.info(f"Setting up modlist {modlist_name}")
    wabbajack_file: Path = Path(filedialog.askopenfilename(
        title="Select the .wabbajack file",
        filetypes=[("Wabbajack files", "*.wabbajack")]
    ))
    if wabbajack_file == Path():
        messagebox.showerror("Error", "You must select a .wabbajack file.")
        _logger.info("No .wabbajack file selected")
        return False
    download_dir: Path = Path(filedialog.askdirectory(title="Select the download folder"))
    if download_dir == Path():
        messagebox.showerror("Error", "You must select a download folder.")
        _logger.info("No download folder selected")
        return False
    download_path: Path = download_dir.resolve()
    _create_list(wabbajack_file, modlist_name)
    state.DownloadInfo().set_path(modlist_name, download_path)
    _logger.info(f"Modlist {modlist_name} set up successfully")
    return True
