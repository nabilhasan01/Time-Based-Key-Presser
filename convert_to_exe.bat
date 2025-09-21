@echo off
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo This script requires administrative privileges. Requesting elevation...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %CD% && %0 %1' -Verb RunAs"
    exit /b
)

echo Building TimeSyncedKeyPresser executable with admin privileges...

set "EXE_NAME=TimeSyncedKeyPresser"
set "SCRIPT_NAME=TimeSyncedKeyPresser.py"


set "ICON_FILE=resource\icon.ico"
if exist "%ICON_FILE%" (
    set "ICON_OPTION=--icon=%ICON_FILE%"
) else (
    echo Warning: %ICON_FILE% not found. Building without an icon, which may affect --uac-admin reliability.
    set "ICON_OPTION="
)

pyinstaller --onefile --windowed ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=pydirectinput ^
    --hidden-import=ntplib ^
    --add-data "resource\icon.ico;resource" ^
    --uac-admin ^
    %ICON_OPTION% ^
    --name "%EXE_NAME%" ^
    %SCRIPT_NAME%

if %ERRORLEVEL% neq 0 (
    echo Error: PyInstaller build failed.
    pause
    exit /b 1
)

echo Cleaning up build artifacts...
if exist "build" (
    rmdir /s /q "build"
    echo Build folder deleted.
)
if exist "%EXE_NAME%.spec" (
    del "%EXE_NAME%.spec"
    echo Spec file deleted.
)

echo Build completed successfully. Executable: dist\%EXE_NAME%.exe
pause