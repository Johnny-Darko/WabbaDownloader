@echo off

REM Main

REM Create a virtual environment to avoid conflicts and unnecessary libraries
python -m venv "venv"
if errorlevel 1 (
    call :error
    exit /b %ERRORLEVEL%
)
call ".\venv\Scripts\activate"
if errorlevel 1 (
    set "lastError=%ERRORLEVEL%"
    call :error
    exit /b %lastError%
)
python -m pip install --upgrade pip
if errorlevel 1 (
    set "lastError=%ERRORLEVEL%"
    call ".\venv\Scripts\deactivate.bat"
    call :error
    exit /b %lastError%
)
python -m pip install -r "requirements.txt"
if errorlevel 1 (
    set "lastError=%ERRORLEVEL%"
    call ".\venv\Scripts\deactivate.bat"
    call :error
    exit /b %lastError%
)
python -m pip install pyinstaller
if errorlevel 1 (
    set "lastError=%ERRORLEVEL%"
    call ".\venv\Scripts\deactivate.bat"
    call :error
    exit /b %lastError%
)

pyinstaller "main.py" -w --optimize=2 -n "WabbaDownloader" -i "app\data\icons\icon.ico"
if errorlevel 1 (
    set "lastError=%ERRORLEVEL%"
    call ".\venv\Scripts\deactivate.bat"
    call :error
    exit /b %lastError%
)

call ".\venv\Scripts\deactivate.bat"

REM Copy the executable to the current folder
xcopy ".\dist\WabbaDownloader\*" "." /e
if errorlevel 1 (
    set "lastError=%ERRORLEVEL%"
    call :error
    exit /b %lastError%
)

echo Executable created successfully.

REM Cleanup
echo Cleaning up...

call :deleteFile "WabbaDownloader.spec"
if errorlevel 1 exit /b %ERRORLEVEL%
call :deleteDir "build"
if errorlevel 1 exit /b %ERRORLEVEL%
call :deleteDir "dist"
if errorlevel 1 exit /b %ERRORLEVEL%
call :deleteDir "venv"
if errorlevel 1 exit /b %ERRORLEVEL%

REM Ask the user if they want to remove the source files
choice /C YN /M "Do you want to remove the source files (you don't need them)"
if errorlevel 2 goto endif

    call :deleteFile ".gitignore"
    if errorlevel 1 exit /b %ERRORLEVEL%
    call :deleteFile "main.py"
    if errorlevel 1 exit /b %ERRORLEVEL%
    call :deleteFile "requirements.txt"
    if errorlevel 1 exit /b %ERRORLEVEL%
    call :deleteFile "unix-installer.sh"
    if errorlevel 1 exit /b %ERRORLEVEL%
    call :deleteFile "app\data\icons\icon.ico"
    if errorlevel 1 exit /b %ERRORLEVEL%
    call :deleteDir "app\src\core"
    if errorlevel 1 exit /b %ERRORLEVEL%

    REM Schedule this script to delete itself
    start /b "" cmd /c del "%~f0"
    if errorlevel 1 (
        set "lastError=%ERRORLEVEL%"
        call :error
        exit /b %lastError%
    )

:endif
    echo Cleanup completed.
    pause
    exit /b 0


REM Functions

REM Error function
:error
    echo There was an error during the process.
    pause
    exit /b 0

REM Delete functions
:deleteFile
    del "%~1"
    if exist "%~1" (
        timeout /t 1 /nobreak >nul
        del "%~1"
        set "lastError=%ERRORLEVEL%"
        if exist "%~1" (
            call :error
            exit /b %lastError%
        )
    )
    exit /b 0

:deleteDir
    rmdir "%~1" /s /q
    if exist "%~1" (
        timeout /t 1 /nobreak >nul
        rmdir "%~1" /s /q
        set "lastError=%ERRORLEVEL%"
        if exist "%~1" (
            call :error
            exit /b %lastError%
        )
    )
    exit /b 0
