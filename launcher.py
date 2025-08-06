import flet as ft
import os
import shutil
import requests
import zipfile
import asyncio
import io
import sys
from concurrent.futures import ThreadPoolExecutor

# Constants
VERSION = '1_11_2931_2'
VERSION_PTR = '1_11_2931_10'
RELEASE_URI = 'https://github.com/DirectalArrowYT/ProjectVangaurd/releases/download/ThingNoWorky/ProjectVangaurd.zip'
OG_FILES_URL = 'https://github.com/CutesyThrower12/HW2-Original-Files/releases/download/1.0/hw2ogfiles.zip'
HW2_HOGAN_PATH = "Packages\\Microsoft.HoganThreshold_8wekyb3d8bbwe\\LocalState"
UPDATER_RELEASE_URL = "https://github.com/TheDoctor200/NuphillionLauncher/releases/latest/download/NuphillionLauncher.exe"

appData = os.environ.get('LOCALAPPDATA')
if not appData:
    raise RuntimeError("Unable to find LOCALAPPDATA.")

class ModManager:
    def __init__(self, appData):
        self.localStateDir = os.path.join(appData, HW2_HOGAN_PATH)
        self.version = VERSION
        if os.path.isdir(self.localPkgDir(VERSION_PTR)):
            self.version = VERSION_PTR
        self._executor = ThreadPoolExecutor(max_workers=1)

    def localPkgDir(self, version=None):
        return os.path.join(self.localStateDir, f"GTS\\{version or self.version}_active")

    def localPkgPath(self):
        return os.path.join(self.localPkgDir(), 'ProjectVangaurd.pkg')

    def localManifestPath(self):
        return os.path.join(self.localPkgDir(), f"{self.version}_file_manifest.xml")

    def local_mod_exists(self):
        return os.path.isfile(self.localPkgPath()) and os.path.isfile(self.localManifestPath())

    def ensure_directories(self):
        """Ensure all required directories exist"""
        os.makedirs(self.localStateDir, exist_ok=True)
        gts_path = os.path.join(self.localStateDir, "GTS")
        os.makedirs(gts_path, exist_ok=True)
        os.makedirs(self.localPkgDir(), exist_ok=True)

    def mod_cleanup(self):
        """Clean up and prepare directories for mod installation"""
        try:
            self.ensure_directories()
            target_dir = self.localPkgDir()
            if os.path.isdir(target_dir):
                shutil.rmtree(target_dir)
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            print(f"Directory creation error: {e}")
            raise

    async def _download_file(self, url):
        try:
            response = await asyncio.get_running_loop().run_in_executor(
                self._executor,
                lambda: requests.get(url, timeout=10, stream=True)
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Download error: {e}")
            return None

    async def install_mod(self, progress_callback):
        try:
            self.ensure_directories()
            progress_callback(0)
            content = await self._download_file(RELEASE_URI)
            if not content:
                return "Failed to download mod."

            progress_callback(20)
            
            self.mod_cleanup()
            with zipfile.ZipFile(io.BytesIO(content)) as mod_zip:
                files_to_extract = [f for f in mod_zip.namelist() 
                                  if f.endswith('.pkg') or f.endswith('.xml')]
                
                if not files_to_extract:
                    return "Invalid mod package: No valid files found"

                total_files = len(files_to_extract)
                for i, name in enumerate(files_to_extract):
                    if name.endswith('.pkg'):
                        target_path = self.localPkgPath()
                    else:
                        target_path = self.localManifestPath()

                    with mod_zip.open(name) as source, open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    
                    progress = 20 + int((i + 1) / total_files * 80)
                    progress_callback(progress)

            if not self.local_mod_exists():
                return "Installation failed: Files not properly installed"

            return "Mod installation complete!"
        except Exception as e:
            print(f"Installation error: {e}")
            return f"Installation failed: {str(e)}"

    async def restore_original_files(self, progress_callback):
        try:
            progress_callback(0)
            content = await self._download_file(OG_FILES_URL)
            if not content:
                return "Failed to download original files."

            progress_callback(20)
            
            self.mod_cleanup()
            with zipfile.ZipFile(io.BytesIO(content)) as og_zip:
                total_files = len(og_zip.namelist())
                for i, member in enumerate(og_zip.infolist()):
                    if member.is_dir():
                        continue
                    target_path = os.path.join(self.localPkgDir(), os.path.basename(member.filename))
                    with og_zip.open(member) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
                    progress = 20 + int((i + 1) / total_files * 80)
                    progress_callback(progress)

            return "Original files restored successfully!"
        except Exception as e:
            print(f"Restore error: {e}")
            return f"Restore failed: {str(e)}"

mod_manager = ModManager(appData)

from win_utils import get_aumid, launch_app
from update_utils import check_for_update
from launch_game_utils import launch_game_click

def main(page: ft.Page):
    page.title = "Project Vangaurd Mod Manager"
    page.window_title = "Project Vangaurd Mod Manager"
    page.window_resizable = True
    page.window_center = True
    page.window_maximizable = True
    page.window_always_on_top = False
    page.bgcolor = "#006064"
    page.padding = 0

    if hasattr(sys, "_MEIPASS"):
        BASE_DIR = sys._MEIPASS
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    bg_path = os.path.join(ASSETS_DIR, "new_bg.png")  # 1920x1080 background
    splash_logo_path = os.path.join(ASSETS_DIR, "splash_logo.png")  # 1100x600 logo
    gif_path = os.path.join(ASSETS_DIR, "HaloWars2Preview.gif")
    favicon_path = os.path.join(ASSETS_DIR, "favicon.ico")

    if os.path.exists(favicon_path):
        page.window_icon = favicon_path
        page.icon = favicon_path
        try:
            page.tray_icon = favicon_path
        except Exception:
            pass

    # Set initial window size to 1920x1080
    page.window_width = 1920
    page.window_height = 1080

    class DynamicBg(ft.Stack):
        def __init__(self):
            super().__init__()
            self.bg_img = ft.Image(
                src=bg_path,
                fit=ft.ImageFit.COVER,
                width=page.window_width,
                height=page.window_height,
                opacity=1.0
            )
            self.controls = [self.bg_img]

        def resize(self, width, height):
            self.bg_img.width = width
            self.bg_img.height = height
            self.update()

    status_label = ft.Text("Status:", color="white", size=18, weight="bold")
    progress_bar = ft.ProgressBar(width=page.width * 0.26, value=0, color="#97E9E6")  # 26% of window width
    status_text = ft.Text("", color="white", size=16)

    install_task = {"task": None, "cancel_event": None}

    def quick_update():
        status_text.update()
        progress_bar.update()

    async def install_mod_click(e):
        if install_task["task"] and not install_task["task"].done():
            install_task["cancel_event"].set()
            await install_task["task"]

        cancel_event = asyncio.Event()
        install_task["cancel_event"] = cancel_event

        status_text.value = "Installing mod..."
        progress_bar.value = 0
        quick_update()

        def progress_callback(value):
            progress_bar.value = value / 100
            quick_update()

        async def do_install():
            result = await mod_manager.install_mod(progress_callback)
            if cancel_event.is_set():
                status_text.value = "Installation cancelled."
            else:
                status_text.value = result
            quick_update()

        install_task["task"] = asyncio.create_task(do_install())
        await install_task["task"]

    async def uninstall_mod_click(e):
        if install_task["task"] and not install_task["task"].done():
            install_task["cancel_event"].set()
            await install_task["task"]

        status_text.value = "Restoring original files..."
        progress_bar.value = 0
        quick_update()
        def progress_callback(value):
            progress_bar.value = value / 100
            quick_update()
        result = await mod_manager.restore_original_files(progress_callback)
        status_text.value = result
        quick_update()

    async def update_app_click(e):
        await check_for_update(page, status_text, progress_bar, quick_update)

    async def check_status_click(e):
        if mod_manager.local_mod_exists():
            status_text.value = "Mod is installed and up-to-date!" if mod_manager.version == VERSION else "Mod is outdated. Update available."
            progress_bar.value = 1.0
        else:
            status_text.value = "Mod is not installed."
            progress_bar.value = 0.0
        quick_update()

    async def launch_game_click_handler(e):
        await launch_game_click(
            e,
            status_text=status_text,
            progress_bar=progress_bar,
            quick_update=quick_update,
            page=page
        )

    def create_button(text, on_click, color, icon=None):
        return ft.ElevatedButton(
            text,
            on_click=on_click,
            bgcolor=color,
            color="white",
            width=page.width * 0.13,  # 13% of window width
            height=50,
            icon=icon,
            icon_color="white" if icon else None
        )

    # Splash logo (scales with window, max 1100x600)
    splash_logo = ft.Image(
        src=splash_logo_path,
        width=page.width * 0.57 if page.width * 0.57 <= 1100 else 1100,  # Max 1100px
        height=page.height * 0.55 if page.height * 0.55 <= 600 else 600,  # Max 600px
        fit=ft.ImageFit.CONTAIN
    ) if os.path.exists(splash_logo_path) else None

    # Buttons row (horizontal layout)
    buttons = ft.Row([
        create_button("Install Mod", install_mod_click, "#38D3FB", ft.Icons.DOWNLOAD),
        create_button("Uninstall Mod", uninstall_mod_click, "#38D3FB", ft.Icons.DELETE_FOREVER),
        create_button("Check Status", check_status_click, "#38D3FB", ft.Icons.INFO),
        create_button("Update Launcher", update_app_click, "#38D3FB", ft.Icons.UPGRADE),
        create_button("Launch Game", launch_game_click_handler, "#38D3FB", ft.Icons.PLAY_ARROW),
    ], spacing=page.width * 0.01, alignment=ft.MainAxisAlignment.CENTER)  # 1% of window width spacing

    # GIF at the bottom (scales with window)
    gif_container = ft.Container(
        content=ft.Image(
            src=gif_path,
            width=page.width * 0.09 if page.width * 0.09 <= 180 else 180,  # Max 180px
            height=page.height * 0.11 if page.height * 0.11 <= 120 else 120,  # Max 120px
            fit=ft.ImageFit.CONTAIN,
            border_radius=18,
        ),
        padding=ft.padding.only(top=page.height * 0.01, bottom=page.height * 0.02),  # 1% top, 2% bottom
        alignment=ft.alignment.center,
    ) if os.path.exists(gif_path) else ft.Text("GIF not found", color="white")

    # Main content layout
    content = ft.Column([
        ft.Container(splash_logo, alignment=ft.alignment.center) if splash_logo else ft.Text("Splash logo not found", color="white"),
        ft.Container(buttons, padding=ft.padding.only(top=page.height * 0.02, left=page.width * 0.03, right=page.width * 0.03)),  # 2% top, 3% side
        ft.Container(status_label, padding=ft.padding.only(top=page.height * 0.02)),
        status_text,
        progress_bar,
        gif_container,
        ft.Text("Mod Manager Credits: | TheDoctor | CutesyThrower12 | Directal |", size=12, color="white"),
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

    stack_children = []
    if os.path.exists(bg_path):
        dynamic_bg = DynamicBg()
        stack_children.append(dynamic_bg)
        def on_resize(e):
            dynamic_bg.resize(page.window_width, page.window_height)
            # Update control sizes on resize
            splash_logo.width = page.width * 0.57 if page.width * 0.57 <= 1100 else 1100
            splash_logo.height = page.height * 0.55 if page.height * 0.55 <= 600 else 600
            for btn in buttons.controls:
                btn.width = page.width * 0.13
            progress_bar.width = page.width * 0.26
            buttons.spacing = page.width * 0.01
            gif_container.content.width = page.width * 0.09 if page.width * 0.09 <= 180 else 180
            gif_container.content.height = page.height * 0.11 if page.height * 0.11 <= 120 else 120
            gif_container.padding = ft.padding.only(top=page.height * 0.01, bottom=page.height * 0.02)
            content.controls[1].padding = ft.padding.only(top=page.height * 0.02, left=page.width * 0.03, right=page.width * 0.03)
            content.controls[2].padding = ft.padding.only(top=page.height * 0.02)
            page.update()
        page.on_resize = on_resize

    stack_children.append(content)

    page.add(
        ft.Stack([
            *stack_children,
        ], expand=True)
    )

ft.app(target=main)