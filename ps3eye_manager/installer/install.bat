@echo off
echo === PS3 Eye Manager - Installation ===
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Downloading and installing Python...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
)

:: Run the installation script
python install_dependencies.py

echo.
echo Press a key to exit...
pause >nul