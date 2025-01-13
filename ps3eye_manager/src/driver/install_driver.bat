@echo off
echo Installazione driver PS3 Eye Virtual Camera...

REM Richiedi privilegi di amministratore
NET FILE 1>NUL 2>NUL
if '%errorlevel%' == '0' ( goto :ADMIN ) else ( goto :UAC )

:UAC
echo Richiesta privilegi di amministratore...
powershell -Command "Start-Process -Verb RunAs -FilePath '%0' -ArgumentList 'ADMIN'"
exit /b

:ADMIN
cd /d "%~dp0"

REM Verifica l'esistenza di CMake
if not exist "C:\Program Files\CMake\bin\cmake.exe" (
    echo CMake non trovato. Installare CMake da https://cmake.org/download/
    pause
    exit /b 1
)

REM Verifica l'esistenza di Visual Studio
if not exist "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.com" (
    if not exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.com" (
        echo Visual Studio 2022 non trovato. Installare Visual Studio 2022 con il supporto C++
        pause
        exit /b 1
    )
)

REM Compila il driver
echo Compilazione driver...
rmdir /s /q build 2>nul
mkdir build
cd build

echo Configurazione CMake...
"C:\Program Files\CMake\bin\cmake.exe" .. -G "Visual Studio 17 2022" -A x64 ^
    -DCMAKE_BUILD_TYPE=Release

if %errorlevel% neq 0 (
    echo Errore nella configurazione CMake
    pause
    exit /b 1
)

echo Compilazione...
"C:\Program Files\CMake\bin\cmake.exe" --build . --config Release

if %errorlevel% neq 0 (
    echo Errore nella compilazione
    pause
    exit /b 1
)

REM Installa il driver
echo Installazione driver...
if exist "Release\ps3eye_virtual_camera.dll" (
    "C:\Windows\System32\regsvr32.exe" /s "Release\ps3eye_virtual_camera.dll"
    if %errorlevel% neq 0 (
        echo Errore nell'installazione del driver
        pause
        exit /b 1
    )
) else (
    echo DLL non trovata
    pause
    exit /b 1
)

echo Installazione completata con successo!
pause
