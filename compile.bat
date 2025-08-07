@echo off
echo Compiling Flet app to executable...

:: Check if flet is installed
pip show flet >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Flet not found. Installing...
    pip install flet
)

:: Run flet pack with asset folder
flet pack launcher.py --add-data "assets;assets" --icon "assets/favicon.ico" --name "ProjectVangaurd"

echo Compilation complete. Executable is in the dist folder.
pause
