"""
Module that handles the global state of the application.

Variables:
- close_event: Event to notify the close of the application.

Classes:
- DownloadInfo: Singleton class that manages the downloads information, thread-safe.
- ButtonState: Singleton class that manages the state of the buttons, thread-safe.

Functions:
- save_all: Saves the current state of the application to file.

Imports: paths.
"""

import json
from pathlib import Path
import threading
from typing import Any, Self, Type

from . import paths

close_event = threading.Event()

class DownloadInfo:
    """
    Singleton class that manages the downloads information, thread-safe.
    
    Useful methods:
    - get_lock: returns the lock used to synchronize access to the infos
    - get_selected: returns the name of the selected download
    - set_selected: sets the selected download to be the one with the given name
    - get_selected_path: returns the path of the selected download
    - get_downloads: returns a copy of the downloads dictionary with the format {name: path}
    - get_path: returns the path of the download with the given name
    - set_path: sets the path of the download with the given name
    - remove_download: removes the download from the downloads dictionary if it exists
    - get_modlist_file: returns the file path for the modlist of the given download
    - save: saves the current state to file
    """
    _instance: Self|None = None
    _initialized: bool = False

    _selected_key: str = 'SELECTED'
    _downloads_key: str = 'DOWNLOADS'

    def __new__(cls: Type[Self]) -> Self:
        if not cls._instance:
            cls._instance = super().__new__(cls)
        
        assert isinstance(cls._instance, cls), f"The instance must be an instance of the class, given {type(cls._instance)} instead"

        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        
        self._lock = threading.RLock()
        self._file: Path = paths.DOWNLOAD_STATE_FILE
        self._selected: str = ''
        self._download_info: dict[str, Path] = {}

        if self._file.is_file():
            with self._file.open('r') as download_info_json:
                info_dict: dict[str, Any] = json.load(download_info_json)
            self._selected = info_dict[self._selected_key]
            self._download_info = {download : Path(path) for download, path in info_dict[self._downloads_key].items()}

    def get_selected(self) -> str:
        """
        Returns the name of the selected download. If no download is selected, returns an empty string.
        """
        with self._lock:
            return self._selected
    
    def set_selected(self, download: str) -> None:
        """
        Sets the selected download to be the one with the given name.
        """
        assert isinstance(download, str), f"The download name must be a string, given {type(download)} instead"
        assert download in self._download_info or download == '', f"The download with the name {download} does not exist"

        with self._lock:
            self._selected = download

    def get_selected_path(self) -> Path|None:
        """
        Returns the path of the selected download. If no download is selected, returns None.
        """
        return self.get_path(self.get_selected())

    def get_downloads(self) -> dict[str, Path]:
        """
        Returns a copy of the downloads dictionary with the format {download_name: path}.
        """
        with self._lock:
            return self._download_info.copy()
    
    def get_path(self, download: str) -> Path|None:
        """
        Returns the path of the download with the given name. If the download does not exist, returns None.
        """
        assert isinstance(download, str), f"The download name must be a string, given {type(download)} instead"

        with self._lock:
            return self._download_info.get(download, None)
        
    def set_path(self, download: str, path: Path) -> None:
        """
        Sets the path of the download with the given name.
        """
        assert isinstance(download, str), f"The download must be a string, given {type(download)} instead"
        assert download != '', "The download name must not be an empty string"
        assert isinstance(path, Path), f"The path must be a Path, given {type(path)} instead"
        assert path.is_dir(), f"The path must be an existing directory, given {path} instead"

        with self._lock:
            self._download_info[download] = path

    def remove_download(self, name: str) -> None:
        """
        Removes the download from the downloads dictionary if it exists. If the selected download is the one being removed, the selected download is set to an empty string.
        """
        assert isinstance(name, str), f"The name must be a string, given {type(name)} instead"

        with self._lock:
            self._download_info.pop(name, None)
            if self.get_selected() == name:
                self.set_selected('')

    def get_modlist_file(self, download: str|None = None) -> Path:
        """
        Returns the file path for the modlist of the given download. Defaults to the download that is currently selected.
        WARNING: No checks are made to verify if the download exists.
        """
        assert download is None or isinstance(download, str), f"The download argument must be a string or None, given {type(download)} instead"

        if download is None:
            download = self.get_selected()
        return (paths.MODLIST_INFO_FOLDER / download).with_suffix('.json')
    
    def save(self) -> None:
        """
        Saves the current state to file.
        """
        with self._lock:
            info_dict: dict[str, Any] = {
                self._selected_key: self._selected,
                self._downloads_key: {download : str(path) for download, path in self._download_info.items()}
            }
        with self._file.open('w') as download_info_json:
            json.dump(info_dict, download_info_json, indent=4)
    
    def get_lock(self) -> threading.RLock:
        """
        Returns the lock used to synchronize access to the infos.
        """
        return self._lock

class ButtonState:
    """
    Singleton class that manages the state of the buttons, thread-safe.
    
    Useful methods:
    - get_lock: returns the lock used to synchronize access to the buttons' state
    - get_buttons: returns a copy of the buttons dictionary with the format {button_name: value}
    - get_button: returns the value of the button with the given name
    - set_button: sets the value of the button with the given name
    - remove_button: removes the button with the given name
    - save: saves the current state to file
    """
    _instance: Self|None = None
    _initialized: bool = False

    def __new__(cls: Type[Self]) -> Self:
        if not cls._instance:
            cls._instance = super().__new__(cls)
        
        assert isinstance(cls._instance, cls), f"The instance must be an instance of the class, given {type(cls._instance)} instead"

        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self._lock = threading.RLock()
        self._file: Path = paths.BUTTON_STATE_FILE
        self._button_state: dict[str, bool] = {}

        if self._file.is_file():
            with self._file.open('r') as button_state_json:
                self._button_state = json.load(button_state_json)

        self._initialized = True
        
    def get_buttons(self) -> dict[str, bool]:
        """
        Returns a copy of the buttons dictionary with the format {button_name: value}.
        """
        with self._lock:
            return self._button_state.copy()
        
    def get_button(self, button: str, default: bool|None = None) -> bool|None:
        """
        Returns the value of the button with the given name. If the button does not exist, returns the default value.
        """
        assert isinstance(button, str), f"The button must be a string, given {type(button)} instead"
        assert default is None or isinstance(default, bool), f"The default value must be a boolean or None, given {type(default)} instead"

        with self._lock:
            return self._button_state.get(button, default)
        
    def set_button(self, button: str, value: bool) -> None:
        """
        Sets the value of the button with the given name.
        """
        assert isinstance(button, str), f"The button must be a string, given {type(button)} instead"
        assert isinstance(value, bool), f"The value must be a boolean, given {type(value)} instead"

        with self._lock:
            self._button_state[button] = value
    
    def remove_button(self, button: str) -> None:
        """
        Removes the button with the given name if it exists.
        """
        assert isinstance(button, str), f"The button must be a string, given {type(button)} instead"

        with self._lock:
            self._button_state.pop(button, None)
    
    def save(self) -> None:
        """
        Saves the current state to file.
        """
        with self._lock:
            with self._file.open('w') as button_state_json:
                json.dump(self._button_state, button_state_json, indent=4)
    
    def get_lock(self) -> threading.RLock:
        """
        Returns the lock used to synchronize access to the buttons' state.
        """
        return self._lock

def save_all() -> None:
    """
    Saves the current state of the application to file.
    """
    DownloadInfo().save()
    ButtonState().save()
