"""
Module for the main UI of the application.
Use this module to import the MainUI class.

Imports: download, logger, login, paths, setup, state, utils.
"""

import logging
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, ttk
from typing import Any, Callable, Iterable, Self, Type

from . import download, login, paths, setup, state, utils
from .logger import MainLogger

_logger: logging.Logger = MainLogger.get().getChild(__name__)

class MainUI:
    """
    The main UI of the application.
    It is a singleton class.
    Call the start method to start the main window.

    Useful methods:
    - start: starts the main window.
    - write: writes a message to the log text widget. Thread-safe.
    - set_total_downloads: sets the total number of downloads.
    - set_download: sets the download to be displayed.
    - update_download_progression: updates the download progression.
    - schedule: schedules a function to be called in the main thread.
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
        self._initialized = True    # If done at the end of the method, __init__ would be called again by inner functions.
        self._scheduling_queue: queue.Queue[tuple[Callable[..., Any], Iterable[Any]]] = queue.Queue()
        self._scheduled: str = ''
        self._create_window()
        self._update()
        _logger.debug("MainUI initialized.")
        self.write("Welcome to WabbaDownloader!\n\n")

    def _create_window(self) -> None:
        """
        Creates the main window of the application.
        """
        self.main_window: tk.Tk = tk.Tk()
        self.main_window.withdraw()
        self._set_window_geometry()
        self.main_window.title("WabbaDownloader")
        self.main_window.protocol('WM_DELETE_WINDOW', self.close_window)
        
        self.main_window.iconphoto(True, tk.PhotoImage(file=paths.ICON_FILE))

        self._create_top_frame()
        self._create_checkbuttons_frame()
        self._create_log_frame()
        self._create_download_combobox_frame()
        self._create_start_button()

        self.main_window.deiconify()
    
    def _set_window_geometry(self) -> None:
        """
        Sets the geometry of the main window.
        """
        screen_width: int = self.main_window.winfo_screenwidth()
        screen_height: int = self.main_window.winfo_screenheight()
        window_width: int = screen_width // 3
        window_height: int = screen_height // 2
        window_x: int = (screen_width - window_width) // 2
        window_y: int = (screen_height - window_height) // 2
        self.main_window.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")

    def _create_top_frame(self) -> None:
        """
        Creates the top frame of the main window.
        """
        self.top_frame: tk.Frame = tk.Frame(self.main_window)

        self.login_button: tk.Button = tk.Button(self.top_frame, font=('', 10, 'bold'), command=self._login_logout)
        self.update_login_button()
        self.login_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.top_frame.pack(fill=tk.X, padx=20, pady=5)
    
    def update_login_button(self) -> None:
        """
        Updates the login button based on the user's login status.
        """
        if login.is_logged():
            self.login_button.config(text="Logout", bg='red', fg='white')
        else:
            self.login_button.config(text="Login", bg='blue', fg='white')
    
    def _login_logout(self) -> None:
        """
        Logs the user in or out based on the current login status.
        """
        if login.is_logged():
            if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
                login.logout()
                self.update_login_button()
        else:
            self._LoginWindow(self.main_window, self.update_login_button)
    
    class _LoginWindow:
        """
        A window to log the user in to their Nexus Mods account.
        """
        def __init__(self, parent_window: tk.Misc | None = None, callback: Callable|None = None) -> None:
            """
            Creates a window to log the user in to their Nexus Mods account.

            Args:
            - parent_window (Misc | None): the parent window of the login window.
            - callback (Callable | None): a function to be called after the login window is closed.
            """
            assert parent_window is None or isinstance(parent_window, tk.Misc), f"The parent_window argument must be a Misc object or None, given {type(parent_window)} instead."
            assert callback is None or callable(callback), f"The callback argument must be a callable object or None, given {type(callback)} instead."

            self._callback: Callable|None = callback
            self._answer: tk.BooleanVar = tk.BooleanVar()
            self._scheduled: str = ''
            self._create_window(parent_window)
            self._wait_for_user()
            if not self._answer.get():
                self._clean_up()
                return
            self._login_handler: login.Login = login.Login()
            self._update_window()
            self._login_handler.start(self.done, self._callback)

        def _create_window(self, parent_window: tk.Misc | None = None) -> None:
            """
            Creates the window for the login process.

            Args:
            - parent_window (Misc | None): the parent window of the login window.
            """
            assert parent_window is None or isinstance(parent_window, tk.Misc), f"The parent_window argument must be a Misc object or None, given {type(parent_window)} instead."

            self.window: tk.Toplevel = tk.Toplevel(parent_window)
            self.window.withdraw()
            self.window.grab_set()

            self.window.title("Login")
            self.text: tk.Label = tk.Label(self.window, text="Please login to your Nexus Mods account.\nYou will be redirected to the login page.\n\nPress Done when you have logged in.", font=('', 10))
            self.text.pack(pady=5)

            self._center_window(parent_window)

            self.window.resizable(False, False)
            self.window.deiconify()

        def _center_window(self, parent_window: tk.Misc | None = None) -> None:
            """
            Centers the window on the screen or with respect to the parent window.

            Args:
            - parent_window (Misc | None): the parent window of the window to be centered.
            """
            self.window.update_idletasks()
            x: int
            y: int
            if parent_window:
                parent_window.update_idletasks()
                x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (self.window.winfo_width() // 2)
                y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (self.window.winfo_height() // 2)
            else:
                x = self.window.winfo_screenwidth() // 2 - self.window.winfo_width() // 2
                y = self.window.winfo_screenheight() // 2 - self.window.winfo_height() // 2
            self.window.geometry(f'+{x}+{y}')
        
        def _wait_for_user(self) -> None:
            """
            Waits for the user to read the message
            """
            self.ok_button: tk.Button = tk.Button(self.window, text="OK", command=lambda: self._answer.set(True))
            self.ok_button.pack(pady=5)
            self.window.bind('<Return>', lambda event: self.ok_button.invoke())
            self.window.protocol('WM_DELETE_WINDOW', lambda: self._answer.set(False))
            self.window.wait_variable(self._answer)

        def _update_window(self) -> None:
            """
            Updates the window after the user has read the message.
            """
            self.ok_button.destroy()
            self.done_button: tk.Button = tk.Button(self.window, text="Done", command=self.done, state=tk.DISABLED)
            self.done_button.pack(pady=5)
            self.cancel_button: tk.Button = tk.Button(self.window, text="Cancel", command=self.cancel)
            self.cancel_button.pack(pady=5)
            self.window.bind('<Return>', lambda event: self.done_button.invoke())
            self.window.protocol('WM_DELETE_WINDOW', self.cancel_button.invoke)
            self._wait_for_login_page()

        def _wait_for_login_page(self) -> None:
            """
            Waits for the login page to be ready and enables the done button.
            """
            if self._login_handler.login_page_ready():
                self.done_button.config(state=tk.NORMAL)
            else:
                self._scheduled = self.window.after(100, self._wait_for_login_page)

        def done(self) -> None:
            """
            Closes the login window after the user has logged in.
            """
            self._login_handler.done()
            self._clean_up()
        
        def cancel(self) -> None:
            """
            Cancels the login process and closes the login window.
            """
            self._login_handler.close()
            self._clean_up()
        
        def _clean_up(self) -> None:
            """
            Destroys the login window and cancels the scheduled function.
            """
            if self._scheduled:
                self.window.after_cancel(self._scheduled)
            self.window.destroy()

    class _CheckbuttonInfo:
        """
        A class to store the default value and the variable of a checkbutton.
        """
        def __init__(self, default: bool, var: tk.BooleanVar) -> None:
            """
            Creates a new checkbutton info object.

            Args:
            - default (bool): the default value of the checkbutton.
            - var (BooleanVar): the variable of the checkbutton.
            """
            assert isinstance(default, bool), f"The default argument must be a boolean, given {type(default)} instead."
            assert isinstance(var, tk.BooleanVar), f"The var argument must be a BooleanVar, given {type(var)} instead."

            self.default: bool = default
            self.var: tk.BooleanVar = var

    def _create_checkbuttons_frame(self) -> None:
        """
        Creates the frame for the checkbuttons.
        """
        self.checkbutton_frame: tk.Frame = tk.Frame(self.main_window)

        self.checkbuttons: dict[str, MainUI._CheckbuttonInfo] = {}

        self.reset_button = tk.Button(self.checkbutton_frame, text="Restore Defaults", command=self.reset_checkbuttons)
        self.reset_button.pack(side=tk.RIGHT, padx=5)

        self.checkbutton_frame.pack(pady=5)

    def create_checkbutton(self, text: str, default: bool, var: tk.BooleanVar|None = None) -> None:
        """
        Creates a checkbutton.

        Args:
        - text (str): the text to be displayed on the checkbutton.
        - default (bool): the default value of the checkbutton.
        - var (BooleanVar | None): the variable of the checkbutton. If None, a new variable is created.
        """
        assert isinstance(text, str), f"The text argument must be a string, given {type(text)} instead."
        assert isinstance(default, bool), f"The default argument must be a boolean, given {type(default)} instead."
        assert var is None or isinstance(var, tk.BooleanVar), f"The var argument must be a BooleanVar (or None), given {type(var)} instead."

        if not var:
            var = tk.BooleanVar()
        value: bool|None = state.ButtonState().get_button(text, default) # last value of the checkbutton

        assert isinstance(value, bool), f"The value must be a boolean, given {type(value)} instead."

        def on_checkbutton_change() -> None:
            """
            Saves the state of the checkbutton.
            """
            state.ButtonState().set_button(text, var.get())

        var.trace_add('write', lambda name, index, mode, sv=var: on_checkbutton_change())  # save checkbutton state
        var.set(value)
        check: tk.Checkbutton = tk.Checkbutton(self.checkbutton_frame, text=text, variable=var)
        check.pack(side=tk.LEFT, padx=5)
        self.checkbuttons[text] = MainUI._CheckbuttonInfo(default, var)
    
    def reset_checkbuttons(self) -> None:
        """
        Resets the checkbuttons to their default values.
        """
        for checkbutton in self.checkbuttons:
            var: tk.BooleanVar = self.checkbuttons[checkbutton].var
            old_value: bool = var.get()
            new_value: bool = self.checkbuttons[checkbutton].default
            if old_value != new_value:
                var.set(new_value)

    def _create_log_frame(self) -> None:
        """
        Creates the log frame.
        """
        class _LogTextHandler(logging.Handler):
            """
            A class to display the logs in the text widget.
            """            
            def emit(self, record: logging.LogRecord) -> None:
                """
                Logs the record to the text widget.
                """
                MainUI().write(f'{self.format(record)}\n', record.levelname)
        
        self.log_frame: tk.Frame = tk.Frame(self.main_window, bd=3, relief=tk.SUNKEN)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        self.log_text: scrolledtext.ScrolledText = scrolledtext.ScrolledText(self.log_frame, state=tk.DISABLED, width=0, height=0, wrap=tk.WORD)
        self.log_text.tag_configure(logging.getLevelName(logging.DEBUG), foreground='gray')
        self.log_text.tag_configure(logging.getLevelName(logging.INFO), foreground='black')
        self.log_text.tag_configure(logging.getLevelName(logging.WARNING), foreground='orange')
        self.log_text.tag_configure(logging.getLevelName(logging.ERROR), foreground='red')
        self.log_text.tag_configure(logging.getLevelName(logging.CRITICAL), foreground='red', underline=True)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self._log_handler: _LogTextHandler = _LogTextHandler(level=logging.INFO)
        self._log_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        MainLogger.get().addHandler(self._log_handler)

        
        verbose_var: tk.BooleanVar = tk.BooleanVar()

        def on_verbose_change(_, __, ___) -> None:
            """
            Changes the log level based on the verbose checkbutton.
            """
            if verbose_var.get():
                self._log_handler.setLevel(logging.DEBUG)
                _logger.debug("Verbose enabled.")
            else:
                self._log_handler.setLevel(logging.INFO)
                _logger.debug("Verbose disabled.")

        verbose_var.trace_add('write', on_verbose_change)
        self.create_checkbutton("Verbose", False, var=verbose_var)
    
    def _write(self, chars: str, *args: str | list[str] | tuple[str, ...]) -> None:
        """
        Writes the given text to the log text widget.

        Args:
        - chars (str): the text to be written.
        - args (str | list[str] | tuple[str, ...]): the tags to be applied to the text.
        """
        assert isinstance(chars, str), f"The chars argument must be a string, given {type(chars)} instead."
        assert isinstance(args, (str, list, tuple)), f"The args argument must be a string, list or tuple, given {type(args)} instead."

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, chars, *args)
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def write(self, chars: str, *args: str | list[str] | tuple[str, ...]) -> None:
        """
        Writes the given text to the log text widget, thread-safe.

        Args:
        - chars (str): the text to be written.
        - args (str | list[str] | tuple[str, ...]): the tags to be applied to the text.
        """
        assert isinstance(chars, str), f"The chars argument must be a string, given {type(chars)} instead."
        assert isinstance(args, (str, list, tuple)), f"The args argument must be a string, list or tuple, given {type(args)} instead."
        
        self.schedule(self._write, (chars, *args))
    
    def _create_download_combobox_frame(self) -> None:
        """
        Creates the download combobox frame.
        """
        self.download_combobox_frame: tk.Frame = tk.Frame(self.main_window)
        self.download_combobox_label: tk.Label = tk.Label(self.download_combobox_frame, text="Select Download:")
        self.download_combobox_label.pack(side=tk.LEFT, padx=5)

        self.download_value: tk.StringVar = tk.StringVar()
        self.download_combobox: ttk.Combobox = ttk.Combobox(self.download_combobox_frame, state='readonly', textvariable=self.download_value)
        with state.DownloadInfo().get_lock():
            self.download_combobox.configure(values=tuple(state.DownloadInfo().get_downloads()))
            last_download: str = state.DownloadInfo().get_selected()
        self.download_combobox.set(last_download)
        self.download_combobox.pack(side=tk.LEFT, padx=5)

        self.context_menu: tk.Menu = tk.Menu(self.download_combobox, tearoff=0)
        self.context_menu.add_command(label="New", command=self._add_modlist)
        self.context_menu.add_command(label="Rename", command=self._rename_modlist)
        self.context_menu.add_command(label="Delete", command=self._delete_modlist)
        self.download_combobox.bind('<Button-3>', self._show_context_menu)
        
        tk.Button(self.download_combobox_frame, text="+", command=self._add_modlist, width=2, bd=3).pack(side=tk.LEFT, padx=5)
        self.download_combobox_frame.pack(pady=5)

        self._create_info_frame()

        def on_download_change() -> None:
            """
            Saves the selected download and updates the info frame.
            """
            state.DownloadInfo().set_selected(self.download_combobox.get())
            self.update_info_frame()

        self.download_value.trace_add("write", lambda name, index, mode, sv=self.download_value: on_download_change())
    
    def _create_info_frame(self) -> None:
        """
        Creates the frame to display the infos about the selected download.
        """
        self.info_frame: tk.Frame = tk.Frame(self.main_window)
        self.destinations_label: tk.Label = tk.Label(self.info_frame)
        self.destinations_label.pack(side=tk.BOTTOM, padx=5, pady=5)
        self.update_info_frame()
        self.info_frame.pack(pady=5)
    
    def update_info_frame(self) -> None:
            """
            Updates the info frame with the selected download's info.
            """
            download_path: Path|None = state.DownloadInfo().get_selected_path()
            if download_path is None:
                download_path = Path('')
            self.destinations_label.config(text=f"Download path: {download_path}")

    def _show_context_menu(self, event: tk.Event) -> None:
        """
        Shows the context menu for the download combobox.

        Args:
        - event (tkinter.Event): the event that triggered the context menu.
        """
        assert isinstance(event, tk.Event), f"The event argument must be a tkinter.Event object, given {type(event)} instead."
        
        if self.download_combobox.get() == '':
            self.context_menu.entryconfig("Rename", state='disabled')
            self.context_menu.entryconfig("Delete", state='disabled')
        else:
            self.context_menu.entryconfig("Rename", state='normal')
            self.context_menu.entryconfig("Delete", state='normal')

        self.context_menu.post(event.x_root, event.y_root)

    def _rename_modlist(self) -> None:
        """
        Renames the selected download.
        """
        name: str = self.download_combobox.get()
        new_name: str|None = simpledialog.askstring("Rename Modlist", "Enter the new name of the download:")
        if not new_name:
            return
        new_name = new_name.strip()
        if new_name == name:
            return
        if new_name == '':
            messagebox.showerror("Error", "The name cannot be empty.")
            return
        with state.DownloadInfo().get_lock():
            if new_name in state.DownloadInfo().get_downloads():
                messagebox.showerror("Error", "That modlist already exists.")
                return
            path: Path|None = state.DownloadInfo().get_path(name)
            assert path is not None, f"The download {name} has no path."

            modlist_file: Path = state.DownloadInfo().get_modlist_file(name)
            modlist_file.rename(state.DownloadInfo().get_modlist_file(new_name))
            state.DownloadInfo().set_path(new_name, path)
            self.delete_download(name, suppress_log=True)
        self.download_combobox.set(new_name)
        _logger.info(f"Modlist {name} renamed to {new_name}.")
    
    def _delete_modlist(self) -> None:
        """
        Deletes the selected download.
        """
        name: str = self.download_combobox.get()
        if messagebox.askyesno("Delete Modlist", f"Are you sure you want to delete {name}?\nThis will not delete the files in the download folder."):
            self.delete_download(name)
    
    def delete_download(self, download: str, suppress_log: bool = False) -> None:
        """
        Deletes the specified download.

        Args:
        - download (str): the name of the download to be deleted.
        """
        assert isinstance(download, str), f"The download argument must be a string, given {type(download)} instead."
        assert download != '', "The download argument cannot be empty."

        with state.DownloadInfo().get_lock():
            state.DownloadInfo().remove_download(download)
            self.download_combobox.configure(values=tuple(state.DownloadInfo().get_downloads()))
        if not self.download_combobox.cget('values'):
            self.download_combobox.set('')
        else:
            self.download_combobox.set(self.download_combobox.cget('values')[0])
        modlist_file: Path = state.DownloadInfo().get_modlist_file(download)
        if modlist_file.is_file():
            modlist_file.unlink()
            if not suppress_log:
                _logger.info(f"Modlist {download} deleted.")
        elif not suppress_log:
            _logger.warning(f"Modlist {download} not found.")


    def _add_modlist(self) -> None:
        """
        Adds a new download.
        """
        name: str|None = simpledialog.askstring("New Modlist", "Enter a name for the new modlist:")
        if name is None:
            return
        name = name.strip()
        if name == '':
            messagebox.showerror("Error", "The name cannot be empty.")
            return
        with state.DownloadInfo().get_lock():
            if name in state.DownloadInfo().get_downloads():
                messagebox.showerror("Error", "That modlist already exists.")
                return
            setted: bool = setup.setup_modlist(name)
            if setted:
                self.download_combobox.configure(values=tuple(state.DownloadInfo().get_downloads()))
                self.download_combobox.set(name)
                _logger.info(f"Modlist {name} created.")
            else:
                messagebox.showerror("Error", "The modlist could not be created.")
    
    def _create_start_button(self) -> None:
        """
        Creates the start button.
        """
        self.start_button: tk.Button = tk.Button(self.main_window, text="Start", width=8, height=2, bd=3, font=('', 12, 'bold'), bg='green', fg='white', command=self.start_download)
        self.start_button.pack(pady=20)
    
    def start_download(self) -> None:
        """
        Runs the main functionality of the program after checking everything is fine.
        """
        with state.DownloadInfo().get_lock():
            download: str = state.DownloadInfo().get_selected()
            if not download:
                messagebox.showerror("Error", "You must select a download.")
                return
            path: Path|None = state.DownloadInfo().get_path(download)
            assert path is not None, f"The download {download} has no path."

            if not path.is_dir():
                self.delete_download(download)
                messagebox.showerror("Error", "The download folder is missing.")
                return
            if not state.DownloadInfo().get_modlist_file(download).is_file():
                self.delete_download(download)
                messagebox.showerror("Error", "The modlist file is missing.")
                return
        if not login.is_logged():
            messagebox.showerror("Error", "You must be logged in.")
            return
        self._destroy_ui_elements()
        self.download_combobox_frame.destroy()
        self._create_download_status_frame()
        self._download_status = MainUI._DownloadStatus()
        self._start_download_thread()

    def _create_download_status_frame(self) -> None:
        """
        Creates the download status frame and the items in it.
        """
        self.download_status_frame: tk.Frame = tk.Frame(self.main_window)
        self.download_status_frame.pack(fill=tk.X, padx=20, pady=10)

        self.download_status_frame.grid_rowconfigure(0, weight=1)
        self.download_status_frame.grid_rowconfigure(1, weight=1)
        self.download_status_frame.grid_columnconfigure(0, weight=0)
        self.download_status_frame.grid_columnconfigure(1, weight=1)
        self.download_status_frame.grid_columnconfigure(2, weight=0)

        self.download_number_label: tk.Label = tk.Label(self.download_status_frame, font=('', 10, 'bold'))
        self.download_number_label.grid(row=0, column=0, padx=5)

        self.download_message_label: tk.Label = tk.Label(self.download_status_frame, anchor=tk.W, width=1)   # width=1 to prevent the label from resizing when the text changes
        self.download_message_label.grid(row=0, column=1, sticky=tk.EW, padx=5)

        self.download_progression_label: tk.Label = tk.Label(self.download_status_frame)
        self.download_progression_label.grid(row=0, column=2, padx=5)

        self.progress_bar: ttk.Progressbar = ttk.Progressbar(self.download_status_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=tk.EW, columnspan=3)
    
    class _DownloadStatus:
        """
        A class to store the download status.

        Useful methods:
        - set_total_downloads: sets the total number of downloads.
        - set_download: sets the download to be displayed.
        - update_download_progression: updates the download progression.
        """
        def __init__(self) -> None:
            """
            Creates a new download status object.
            """
            self._file_name: str = ""
            self._downloaded_bytes: int = 0
            self._total_size: int = 0
            self._num_download: int = 0
            self._total_downloads: int = 0
            self._speed: float = 0

            self._update_in_queue: bool = False
            self._lock: threading.Lock = threading.Lock()

        def set_total_downloads(self, total_downloads: int) -> None:
            """
            Sets the total number of downloads.
            """
            assert isinstance(total_downloads, int), f"The total_downloads argument must be an integer, given {type(total_downloads)} instead."
            assert total_downloads > 0, f"The total_downloads must be greater than 0."

            with self._lock:
                self._total_downloads = total_downloads
        
        def set_download(self, file_name: str, total_size: int, already_downloaded_bytes: int = 0) -> None:
            """
            Sets the download to be displayed.
            """
            assert isinstance(file_name, str), f"The file_name argument must be a string, given {type(file_name)} instead."
            assert isinstance(total_size, int), f"The total_size argument must be an integer, given {type(total_size)} instead."
            assert total_size > 0, f"The total_size must be greater than 0."
            assert isinstance(already_downloaded_bytes, int), f"The already_downloaded_bytes argument must be an integer, given {type(already_downloaded_bytes)} instead."
            assert already_downloaded_bytes >= 0, f"The already_downloaded_bytes must be greater than or equal to 0."
            assert already_downloaded_bytes <= total_size, f"The already_downloaded_bytes must be less than or equal to the total_size."

            with self._lock:
                self._file_name = file_name
                self._total_size = total_size
                self._downloaded_bytes = already_downloaded_bytes
                self._speed = 0
                self._num_download += 1
            self._update()
        
        def update_download_progression(self, value: int, speed: float|None = None) -> None:
            """
            Updates the download progression. If speed is None, the speed is not updated.
            """
            assert isinstance(value, int), f"The value argument must be an integer, given {type(value)} instead."
            assert value >= 0, f"The value must be greater than or equal to 0."
            assert value <= self._total_size, f"The value must be less than or equal to the total_size."
            assert speed is None or isinstance(speed, float), f"The speed argument must be a float or None, given {type(speed)} instead."
            assert speed is None or speed >= 0, f"The speed must be greater than or equal to 0."

            with self._lock:
                self._downloaded_bytes = value
                if speed is not None:
                    self._speed = speed
            self._update()
        
        def _update(self) -> None:
            """
            Updates the download status.
            """
            with self._lock:
                if not self._update_in_queue:
                    self._update_in_queue = True
                    MainUI().schedule(self._display_update)
        
        def _display_update(self) -> None:
            """
            Displays the update in the UI.
            Sets update_in_queue to False so that the next update can be scheduled.
            """
            with self._lock:
                MainUI().progress_bar.config(value=self._downloaded_bytes, maximum=self._total_size)
                time_now: float = time.perf_counter()
                MainUI().download_number_label.config(text=f"({self._num_download}/{self._total_downloads})")
                MainUI().download_message_label.config(text=f"Downloading {Path(self._file_name).stem}")
                MainUI().download_progression_label.config(text=f"({utils.convert_byte_size(self._downloaded_bytes)}/{utils.convert_byte_size(self._total_size)} at {utils.convert_byte_size(self._speed)}/s)")
                self._update_in_queue = False
        
    def set_total_downloads(self, total_downloads: int) -> None:
        """
        Sets the total number of downloads.
        """
        assert isinstance(total_downloads, int), f"The total_downloads argument must be an integer, given {type(total_downloads)} instead."

        self._download_status.set_total_downloads(total_downloads)
    
    def set_download(self, file_name: str, total_size: int, already_downloaded_bytes: int = 0) -> None:
        """
        Sets the download to be displayed.
        """
        assert isinstance(file_name, str), f"The file_name argument must be a string, given {type(file_name)} instead."
        assert isinstance(total_size, int), f"The total_size argument must be an integer, given {type(total_size)} instead."
        assert isinstance(already_downloaded_bytes, int), f"The already_downloaded_bytes argument must be an integer, given {type(already_downloaded_bytes)} instead."

        self._download_status.set_download(file_name, total_size, already_downloaded_bytes)
    
    def update_download_progression(self, value: int, speed: float|None = None) -> None:
        """
        Updates the download progression. If speed is None, the speed is not updated.
        """
        assert isinstance(value, int), f"The value argument must be an integer, given {type(value)} instead."
        assert speed is None or isinstance(speed, float), f"The speed argument must be a float or None, given {type(speed)} instead."

        self._download_status.update_download_progression(value, speed)
    
    def _update(self) -> None:
        """
        Updates the main window with the scheduled functions.
        """
        while not self._scheduling_queue.empty():
            target: Callable[..., Any]
            args: Iterable[Any]
            target, args = self._scheduling_queue.get()
            target(*args)
        time_for_update: int = 250
        self._scheduled = self.main_window.after(time_for_update, self._update)
    
    def schedule(self, target: Callable[..., Any], args: Iterable[Any] = ()) -> None:
        """
        Schedules a function to be called in the main thread.
        Use this method to call non-thread-safe functions that interact with Tkinter widgets.

        Args:
        - target (Callable[..., Any]): the function to be called.
        - args (Iterable[Any]): the arguments to be passed to the function.
        """
        self._scheduling_queue.put((target, args))
        
    def _destroy_ui_elements(self) -> None:
        """
        Destroys the UI elements that are not required after the start button is pressed.
        """
        self.top_frame.destroy()
        self.start_button.destroy()

    def _start_download_thread(self) -> None:
        """
        Starts the main thread.
        """
        download_thread = threading.Thread(target=download.Download, daemon=True)
        download_thread.start()

    def close_window(self) -> None:
        """
        Closes the window and performs necessary cleanup actions after the user confirms.
        """
        if len(threading.enumerate()) > 1:  # if there are threads other than the main thread
            if not messagebox.askyesno("Exit", "The script is still running. Do you want to exit?"):
                return
        _logger.info("Closing the program.")
        state.close_event.set()
        start_time: float = time.time()
        while time.time() - start_time < 10:
            all_threads: list[threading.Thread] = threading.enumerate()
            all_threads.remove(threading.main_thread()) # ignore the main thread
            if not all_threads:
                break
            for thread in all_threads:
                thread.join(timeout=1)
            self.main_window.update()
        else:
            _logger.warning("The script has been forced to exit.")
        if self._scheduled:
            self.main_window.after_cancel(self._scheduled)
        self.main_window.destroy()

    def start(self) -> None:
        """
        Starts the main window.
        """
        self.main_window.mainloop()
