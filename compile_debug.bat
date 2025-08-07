@echo off
echo Compiling Python scripts to executable...

:: Check if pyinstaller is installed
pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

:: Prepare icon
set ICON=icon.ico
copy /Y "assets\favicon.ico" %ICON%

:: Define the main script
set MAIN_SCRIPT=launcher.py

:: Compile with PyInstaller
"C:\Users\shoup\AppData\Roaming\Python\Python313\Scripts\pyinstaller.exe" ^
    --onefile ^
    --icon %ICON% ^
    --add-data "assets;assets" ^
    --hidden-import flet_video ^
    --hidden-import flet_runtime ^
    %MAIN_SCRIPT%

echo Compilation complete. Executable is in the dist folder.
pause
