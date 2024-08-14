"""
Module to handle the login process to Nexus Mods.

Classes:
- Login: Class to handle the login process to Nexus Mods.

Functions:
- is_logged: Returns True if the user is logged in, False otherwise.
- logout: Logs out the user.

Imports: logger, paths.
"""

import json
import logging
import socket
import threading
from typing import Any, Callable

from flask import Flask
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from werkzeug import serving

from . import paths
from .logger import MainLogger

_logger: logging.Logger = MainLogger.get().getChild(__name__)

class Login:
    """
    Class to handle the login process to Nexus Mods.

    Useful methods:
    - start: Start the login process in a new thread.
    - done: Set the event to notify the login process that the user has finished.
    - close: Closes the login process even if not finished.
    - login_page_ready: Returns True if the login page is ready to be used.
    """
    def __init__(self) -> None:
        self._closing: bool = False
        self._thread: threading.Thread|None = None
        self._server:  serving.BaseWSGIServer|None = None
        self._wait_user_event: threading.Event = threading.Event()
        self._login_ready: bool = False
    
    def start(self, click_done: Callable, callback: Callable|None = None) -> None:
        """
        Start the login process in a new thread.

        Args:
        - click_done: Function to call when the user finishes the login process.
        - callback: Function to call after the login process is finished.
        """
        assert isinstance(callback, Callable) or callback is None, f"The callback argument must be a callable object or None, given {type(callback)} instead."
        assert not is_logged(), "User already logged in."
        assert self._thread is None or not self._thread.is_alive(), "Login process already started."
        
        self._click_done: Callable = click_done
        self._thread = threading.Thread(target=self._login, daemon=True, args=(callback,))
        self._thread.start()
    
    def done(self) -> None:
        """
        Set the event to notify the login process that the user has finished.
        """
        self._wait_user_event.set()
        if self._server is not None:
            self._stop_server()
        _logger.debug("'Wait for user' event set.")
        
    def close(self) -> None:
        """
        Closes the login process even if not finished.
        """
        self._closing = True
        self.done()
        _logger.info("Closing login process.")
    
    def login_page_ready(self) -> bool:
        """
        Returns True if the login page is ready to be used.
        """
        return self._login_ready

    def _login(self, callback: Callable|None = None) -> None:
        """
        Login to Nexus Mods and save the cookies to a file.

        Args:
        - callback: Function to call after the login process is finished.
        """
        assert isinstance(callback, Callable) or callback is None, f"The callback argument must be a callable object or None, given {type(callback)} instead."
        assert not is_logged(), "User already logged in."

        _logger.info("Starting login process.")
        self._start_server()
        options: webdriver.ChromeOptions = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-automation'])   # Better looking browser
        options.add_argument('--disable-blink-features=AutomationControlled')   # Necessary to avoid detection
        options.add_argument("--disable-search-engine-choice-screen")   # Skip engine choice
        options.add_argument(f'--load-extension={paths.CHROME_EXTENSION_FOLDER.absolute()}')   # Used to communicate with the Flask server
        with webdriver.Chrome(options=options) as driver:
            driver.get("https://www.nexusmods.com/")
            if self._closing:
                return
            try:
                login_button: WebElement = driver.find_element(By.ID, 'login')
                login_link: str | None = login_button.get_attribute('href')
                if login_link is None:
                    _logger.error("Login link not found.")
                    return
                driver.execute_script(f'window.open("{login_link}");')
                self._login_ready = True
                _logger.debug("Login page ready.")
            except:
                _logger.error("Login button not found.")
                return
            self._wait_user_event.wait()
            if self._closing:
                return
            _logger.debug("User finished login process.")
            driver.switch_to.window(driver.window_handles[0])
            driver.minimize_window()
            driver.get("https://users.nexusmods.com/account/profile")
            if self._closing or driver.current_url != 'https://users.nexusmods.com/account/profile':
                if driver.current_url != 'https://users.nexusmods.com/account/profile':
                    _logger.warning("Login failed.")
                return
            cookies: dict[str, Any] = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
        with paths.COOKIES_FILE.open('w') as file:
            json.dump(cookies, file)
        if callback:
            callback()
        _logger.info("Cookies saved successfully.")

    def _start_server(self) -> None:
        """
        Initialize the Flask server to automatically close the browser when the user logs in.
        """
        app = Flask(__name__)
        CORS(app)

        @app.route('/login', methods=['POST'])
        def handle_login() -> tuple[str, int]:
            if self._click_done:
                self._click_done()
            return 'OK', 200
        
        self._port: int = 8000
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', self._port)) != 0:  # If the port is free
                    self._server = serving.make_server('localhost', self._port, app)
                    threading.Thread(target=self._server.serve_forever, daemon=True).start() # There is a little chance that the port is taken between the check and the start, but it's not handled
                    with open (paths.PORT_FILE, 'w') as file:
                        file.write(f'{self._port}')
                    return
                self._port += 1

    def _stop_server(self) -> None:
        """
        Stop the Flask server.
        """
        if self._server:
            threading.Thread(target=self._server.shutdown, daemon=True).start()
        _logger.debug("Stopping server.")

def is_logged() -> bool:
    """
    Returns True if the user is logged in, False otherwise.
    """
    return paths.COOKIES_FILE.is_file()

def logout() -> None:
    """
    Logs out the user.
    """
    if is_logged():
        paths.COOKIES_FILE.unlink()
        _logger.info("User logged out.")
    else:
        _logger.warning("User not logged in.")
