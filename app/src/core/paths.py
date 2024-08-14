"""
Module that contains the paths used throughout the application.

Useful paths:
- CHROME_EXTENSION_FOLDER: Folder where the chrome extension is located.
- MODLIST_INFO_FOLDER: Folder where the informations about the modlists (and each of their mods) are stored.
- BUTTON_STATE_FILE: File where the state of the buttons is stored.
- COOKIES_FILE: File where the cookies are stored.
- DOWNLOAD_STATE_FILE: File where the informations about downloads are stored.
- ICON_FILE: File where the icon is stored.
- LOCK_FILE: File where the application lock is stored.
- LOG_FILE: File where the logs are stored.
- PORT_FILE: File where the port used by the chrome extension is stored.
"""

from pathlib import Path

# Folders
APP_FOLDER: Path = Path('app')

APP_DATA_FOLDER: Path = APP_FOLDER / 'data'
SOURCE_FOLDER: Path = APP_FOLDER / 'src'

ICON_FOLDER: Path = APP_DATA_FOLDER / 'icons'
LOG_FOLDER: Path = APP_DATA_FOLDER / 'logs'
STATE_FOLDER: Path = APP_DATA_FOLDER / 'state'

CHROME_EXTENSION_FOLDER: Path = SOURCE_FOLDER / 'chrome_extension'

LOCK_FOLDER: Path = STATE_FOLDER / 'locks'  
MODLIST_INFO_FOLDER: Path = STATE_FOLDER / 'modlist_info'

CHROME_EXTENSION_STATE_FOLDER: Path = CHROME_EXTENSION_FOLDER / 'state'


# Files
ICON_FILE: Path = ICON_FOLDER / 'icon.png'

LOG_FILE: Path = LOG_FOLDER / 'log.log'

BUTTON_STATE_FILE: Path = STATE_FOLDER / 'button_state.json'
COOKIES_FILE: Path = STATE_FOLDER / 'cookies.json'
DOWNLOAD_STATE_FILE: Path = STATE_FOLDER / 'download_state.json'

LOCK_FILE: Path = LOCK_FOLDER / 'app.lock'

PORT_FILE: Path = CHROME_EXTENSION_STATE_FOLDER / 'port.txt'


# Create the necessary directories if they don't exist.
LOG_FOLDER.mkdir(parents=True, exist_ok=True)
STATE_FOLDER.mkdir(parents=True, exist_ok=True)
LOCK_FOLDER.mkdir(parents=True, exist_ok=True)
MODLIST_INFO_FOLDER.mkdir(parents=True, exist_ok=True)
CHROME_EXTENSION_STATE_FOLDER.mkdir(parents=True, exist_ok=True)
