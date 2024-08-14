"""
Starting point of the program.

Imports: logger, main_ui, paths, state.
"""

import logging
import sys
from tkinter import messagebox

import filelock

from app.src.core import main_ui, paths, state
from app.src.core.logger import MainLogger

_logger: logging.Logger = MainLogger.get().getChild(__name__)

def main() -> None:
    """
    Entry point of the program.
    
    Acquires a lock to ensure only one instance of the program is running.
    If the lock is already acquired, displays an error message and exits.
    """
    try:
        with filelock.FileLock(paths.LOCK_FILE, timeout=0):
            _logger.info("Starting the program")
            main_ui.MainUI().start()
    except filelock.Timeout:
        messagebox.showerror("Error", "Another instance of the program is running.")
        sys.exit(1)
    except Exception as e:
        _logger.critical(f"An error occurred: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")
        state.save_all()
        raise e
    state.save_all()
    _logger.info("Exiting the program")

if __name__ == "__main__":
    main()
