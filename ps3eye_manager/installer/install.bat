@echo off
echo === PS3 Eye Manager - Installazione ===
echo.

:: Verifica se Python e' installato
python --version >nul 2>&1
if errorlevel 1 (
    echo Python non trovato. Scarico e installo Python...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
)

:: Esegui lo script di installazione
python install_dependencies.py

echo.
echo Premi un tasto per uscire...
pause >nul
