# WabbaDownloader

## Index

1. [What is WabbaDownloader](#what-is-wabbadownloader)
2. [Disclaimer](#disclaimer)
3. [How to Use It](#how-to-use-it)
   - [Requirements](#requirements)
   - [Important Informations](#important-informations)
   - [Create the Executable](#create-the-executable)
     - [On Windows](#on-windows)
     - [On Unix/Linux](#on-unixlinux)
4. [Where Can I Find the .wabbajack File?](#where-can-i-find-the-wabbajack-file)
5. [How to Install Tkinter on Windows?](#how-to-install-tkinter-on-windows)
6. [How Does WabbaDownloader Work](#how-does-wabbadownloader-work)
7. [Run with Python](#run-with-python)
    - [On Windows](#on-windows-1)
    - [On Unix/Linux](#on-unixlinux-1)
8. [Why Do I Need to Log in to Nexus Mods?](#why-do-i-need-to-log-in-to-nexus-mods)

## What is WabbaDownloader

WabbaDownloader is a software designed to easily download modlists from Nexus Mods, operating completely in the background without requiring user interaction or displaying annoying pop-ups. If a download is interrupted, it can be resumed without losing any information.

<div align="center">
    <img src="app/data/icons/icon.png" alt="WabbaDownloader icon" title="WabbaDownloader icon" style="height: 15vh">
</div>

## Disclaimer

WabbaDownloader is for demonstration purposes only.

Using it to download from Nexus Mods violates their Terms of Service (TOS):

> Attempting to download files or otherwise record data offered through our services (including but not limited to the Nexus Mods website and the Nexus Mods API) in a fashion that drastically exceeds the expected average, through the use of software automation or otherwise, is prohibited without express permission. Users found in violation of this policy will have their account suspended.

## How to Use It

### Requirements

- Python 3
- Chrome

### Important Informations

WabbaDownloader should be placed in a folder that does **not** require special permissions (so avoid `Program Files` and such), just like the destination folder for each download. This ensures that the application can read from and write to these folders without encountering permission issues.

Using the same folder as the destination for multiple downloads can lead to conflicts if the modlists share a mod but with different versions. It is generally recommended using a different folder for each modlist.

### Create the Executable

By following this section, you will create an executable file. Simply click it, and the program will start. Once the creation is complete, Python is no longer needed.

If you want to run it with Python, instead, you can skip this section and go to [Run with Python](#run-with-python)

(Note: The installer will create and delete a virtual environment named `venv` within the project directory. If you plan to create your own virtual environment, please use a different name to avoid conflicts. For development purposes, we use the name `env` for our virtual environment.)

#### On Windows

On Windows, simply run `windows-installer.cmd` and the executable will be created.

#### On Unix/Linux

On Unix systems, a few steps are required:
- Install `tkinter`. For example, on Ubuntu/Debian, open a terminal and run:
    ```bash
    sudo apt install python3-tk
    ```
- Install `venv`.
    ```bash
    sudo apt install python3-venv
    ```
- Run `unix-installer.sh`.


## Where Can I Find the .wabbajack File?

The .wabbajack file can be found in the folder `path/to/your/wabbajack/folder/xx/downloaded_mod_lists`, where `path/to/your/wabbajack/folder` is the path to the folder containing the Wabbajack executable, and `xx` is its actual version number.

Some .wabbajack files may also be available for direct download from the modlist site.

## How to Install Tkinter on Windows?

On Windows, the default Python installation typically includes `tkinter`. However, if it's not included, you can add it through the Python installer by selecting `tcl/tk and IDLE` in the optional features menu.

## How Does WabbaDownloader Work

Here is a brief explanation of how WabbaDownloader works:

- The program extracts informations from the .wabbajack file and saves them. These informations are used to locate the files, check their size (and thus determine wich downloads are completed), and verify their integrity after the download.
- When you log in to Nexus Mods, it saves the cookies. These will be used to make your account the one requesting the download (you must be logged in to download anything).
- Using the informations from the .wabbajack file, it requests the direct download link of each mod from Nexus Mods.
- Finally, it downloads the file. If it is corrupted, it is deleted, and the download is attempted again.

## Run with Python

If you already have created the executable (recommended) you don't need to read this section.

To run the program with Python, follow these steps:

### On Windows

- Install the requirements. Open a terminal in the WabbaDownloader folder and run:
    ```cmd
    pip install -r requirements.txt
    ```
- Run the program:
    ```cmd
    python main.py
    ```

### On Unix/Linux

- Install `tkinter`. For example, on Ubuntu/Debian, open a terminal and run:
    ```bash
    sudo apt install python3-tk
    ```
- Install the requirements. The easiest way is probably by creating a virtual environment.
    - Install `venv`.
        ```bash
        sudo apt install python3-venv
        ```
    - Create the environment:
        ```bash
        python3 -m venv venv
        ```
    - Activate the environment:
        ```bash
        source venv/bin/activate
        ```
    - Install the requirements:
        ```bash
        python3 -m pip install -r requirements.txt
        ```
- Run the program:
    ```bash
    python3 main.py
    ```
    Each time you do this, you must have the environment active. You can deactivate it with:
    ```bash
    deactivate
    ```

## Why Do I Need to Log in to Nexus Mods?

Logging in to Nexus Mods is necessary because each download must be associated with a user account. You cannot download anything without an account.