```bat
@echo off
echo === PS3 Eye Manager ===

rem Close any previous instances
taskkill /F /IM python.exe /FI "WINDOWTITLE eq PS3 Eye Manager*" >nul 2>&1
timeout /t 2 /nobreak >nul

echo Starting the application...

rem Set the path for 32-bit Python
set PYTHON_PATH="C:\Program Files (x86)\Python311-32\python.exe"

rem Check if 32-bit Python exists
if not exist %PYTHON_PATH% (
    echo ERROR: 32-bit Python not found at %PYTHON_PATH%
    echo Please install Python 3.11 32-bit
    pause
    exit /b 1
)

rem Launch the application
cd /d "%~dp0"
%PYTHON_PATH% ps3eye_manager/src/main_v3.py

rem If there is an error, show the message and wait
if errorlevel 1 (
    echo.
    echo ERROR: The application closed with an error
    pause
)
```