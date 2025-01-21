@echo off
echo Installing PS3 Eye Virtual Camera driver...

REM Request admin privileges
NET FILE 1>NUL 2>NUL
if '%errorlevel%' == '0' ( goto :ADMIN ) else ( goto :UAC )

:UAC
echo Requesting admin privileges...
powershell -Command "Start-Process -Verb RunAs -FilePath '%0' -ArgumentList 'ADMIN'"
exit /b

:ADMIN
cd /d "%~dp0"

REM Check for CMake
if not exist "C:\Program Files\CMake\bin\cmake.exe" (
    echo CMake not found. Install CMake from https://cmake.org/download/
    pause
    exit /b 1
)

REM Check for Visual Studio
if not exist "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.com" (
    if not exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.com" (
        echo Visual Studio 2022 not found. Install Visual Studio 2022 with C++ support
        pause
        exit /b 1
    )
)

REM Compile the driver
echo Compiling driver...
rmdir /s /q build 2>nul
mkdir build
cd build

echo Configuring CMake...
"C:\Program Files\CMake\bin\cmake.exe" .. -G "Visual Studio 17 2022" -A x64 ^
    -DCMAKE_BUILD_TYPE=Release

if %errorlevel% neq 0 (
    echo Error configuring CMake
    pause
    exit /b 1
)

echo Compiling...
"C:\Program Files\CMake\bin\cmake.exe" --build . --config Release

if %errorlevel% neq 0 (
    echo Error compiling
    pause
    exit /b 1
)

REM Install the driver
echo Installing driver...
if exist "Release\ps3eye_virtual_camera.dll" (
    "C:\Windows\System32\regsvr32.exe" /s "Release\ps3eye_virtual_camera.dll"
    if %errorlevel% neq 0 (
        echo Error installing driver
        pause
        exit /b 1
    )
) else (
    echo DLL not found
    pause
    exit /b 1
)

echo Installation completed successfully!
pause
