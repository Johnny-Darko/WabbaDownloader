#!/bin/bash

# Functions

# Pause function
pause() {
    read -n 1 -p "Press any key to exit..."
    echo
}

# Error function
error() {
    echo There was an error during the process.
    pause
    exit $1
}

deleteFile() {
    rm -f "$1"
    if [ -f "$1" ]; then
        sleep 1
        rm -f "$1"
        local exit_status=$?
        if [ -f "$1" ]; then
            echo "Error: Unable to delete the file $1."
            error $exit_status
        fi
    fi
}

deleteDir() {
    rm -rf "$1"
    if [ -d "$1" ]; then
        sleep 1
        rm -rf "$1"
        local exit_status=$?
        if [ -d "$1" ]; then
            echo "Error: Unable to delete the directory $1."
            error $exit_status
        fi
    fi
}

# Main

# Create a virtual environment to avoid conflicts and unnecessary libraries
python3 -m venv "venv"
exit_status=$?
[ $exit_status -ne 0 ] && error $exit_status
source "./venv/bin/activate"
exit_status=$?
[ $exit_status -ne 0 ] && error $exit_status
python3 -m pip install --upgrade pip
exit_status=$?
if [ $exit_status -ne 0 ]; then
    deactivate
    error $exit_status
fi
python3 -m pip install -r "requirements.txt"
exit_status=$?
if [ $exit_status -ne 0 ]; then
    deactivate
    error $exit_status
fi
python3 -m pip install pyinstaller
exit_status=$?
if [ $exit_status -ne 0 ]; then
    deactivate
    error $exit_status
fi

pyinstaller "main.py" -w --optimize=2 -n "WabbaDownloader"
exit_status=$?
if [ $exit_status -ne 0 ]; then
    deactivate
    error $exit_status
fi

deactivate

# Copy the executable to the current folder
cp -r "./dist/WabbaDownloader/." "."
exit_status=$?
[ $exit_status -ne 0 ] && error $exit_status

echo "Executable created successfully."

# Cleanup
echo "Cleaning up..."

deleteFile "WabbaDownloader.spec"
deleteDir "build"
deleteDir "dist"
deleteDir "venv"

# Ask the user if they want to remove the source files, only accept Y or N
while true; do
    read -n 1 -p "Do you want to remove the source files (you don't need them) [Y/N]? "
    echo
    if [[ $REPLY =~ ^[YyNn]$ ]]; then
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            deleteFile ".gitignore"
            deleteFile "main.py"
            deleteFile "requirements.txt"
            deleteFile "windows-installer.cmd"
            deleteFile "app/data/icons/icon.ico"
            deleteDir "app/src/core"

            # Schedule this script to delete itself
            trap 'rm -- "$0"' EXIT
        fi
        break
    fi
done

echo "Cleanup completed."
pause
