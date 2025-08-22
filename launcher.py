import flet as ft
import flet_video as ftv
import os
import shutil
import requests
import zipfile
import asyncio
import io
import sys
import logging
from concurrent.futures import ThreadPoolExecutor
# Set up logging to a file
# logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
VERSION = '1_11_2931_2'
VERSION_PTR = '1_11_2931_10'
RELEASE_URI = 'https://github.com/DirectalArrowYT/ProjectVangaurd/releases/download/ThingNoWorky/ProjectVangaurd.zip'
OG_FILES_URL = 'https://github.com/CutesyThrower12/HW2-Original-Files/releases/download/1.0/hw2ogfiles.zip'
HW2_HOGAN_PATH = "Packages\\Microsoft.HoganThreshold_8wekyb3d8bbwe\\LocalState"
UPDATER_RELEASE_URL = "https://github.com/DirectalArrowYT/VangaurdModManager/releases/latest/download/ProjectVangaurd.exe"
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
            logging.error(f"Directory creation error: {e}")
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
            logging.error(f"Download error: {e}")
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
            logging.error(f"Installation error: {e}")
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
            logging.error(f"Restore error: {e}")
            return f"Restore failed: {str(e)}"

mod_manager = ModManager(appData)
from win_utils import get_aumid, launch_app
from update_utils import check_for_update
from launch_game_utils import launch_game_click

def main(page: ft.Page):
    page.title = "Project Vangaurd Mod Manager"
    page.window_title = "Project Vangaurd Mod Manager"
    page.window_resizable = False  # Lock window size
    page.window_center = True
    page.window_maximizable = False  # Prevent maximizing
    page.window_fullscreen = False  # Disable fullscreen
    page.bgcolor = "#006064"
    page.padding = 0
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    music_path = os.path.join(ASSETS_DIR, "menu.mp3")
    bg_path = os.path.join(ASSETS_DIR, "new_bg.png")  # 1920x1080 background
    splash_logo_path = os.path.join(ASSETS_DIR, "splash_logo.png")  # 1100x600 logo
    mp4_path = os.path.join(ASSETS_DIR, "HaloWars2Preview.mp4")
    favicon_path = os.path.join(ASSETS_DIR, "favicon.ico")
    logging.debug(f"Attempting to load favicon from: {favicon_path}")
    
    bg_music = ft.Audio(
        src=music_path,
        autoplay=True,
    )
    
    for attempt in range(3):  # Retry up to 3 times
        if os.path.exists(favicon_path):
            logging.debug(f"Favicon found on attempt {attempt + 1}, setting icon")
            try:
                page.window_icon = favicon_path
                page.icon = favicon_path
                page.tray_icon = favicon_path
                logging.debug("Icon set successfully")
                break
            except Exception as e:
                logging.error(f"Error setting icon on attempt {attempt + 1}: {e}")
        else:
            logging.warning(f"Favicon not found at: {favicon_path} on attempt {attempt + 1}")
        if attempt < 2:  # Wait before retrying
            import time
            time.sleep(0.5)
    else:
        logging.error("Failed to set favicon after 3 attempts")
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

    class DynamicVideo(ft.Stack):
        def __init__(self):
            super().__init__()
            self.video = ftv.Video(
                playlist=[ftv.VideoMedia(mp4_path)],
                playlist_mode=ftv.PlaylistMode.LOOP,
                autoplay=True,
                muted=True,
                fit=ft.ImageFit.COVER,
                width=page.window_width,
                height=page.window_height,
                opacity=0.25,
                show_controls=False,
                on_loaded=lambda e: logging.debug("Video loaded successfully!"),
                on_error=lambda e: logging.error(f"Video error: {e.data}")
            )
            # Center the video in a container
            self.video_container = ft.Container(
                content=self.video,
                alignment=ft.alignment.center,
                expand=True
            )
            # Overlay to block interaction with video controls
            self.overlay = ft.GestureDetector(
                on_tap=lambda e: None,
                on_pan_start=lambda e: None,
                on_pan_update=lambda e: None,
                on_pan_end=lambda e: None,
                content=ft.Container(width=page.window_width, height=page.window_height, bgcolor=ft.Colors.TRANSPARENT)
            )
            self.controls = [self.video_container, self.overlay]
        
        def resize(self, width, height):
            self.video.width = width
            self.video.height = height
            self.video_container.width = width
            self.video_container.height = height
            self.overlay.content.width = width
            self.overlay.content.height = height
            self.update()

    status_label = ft.Text("Status:", color="white", size=18, weight="bold")
    progress_bar = ft.ProgressBar(width=page.width * 0.26, value=0, color="#38D3FB")  # 26% of window width
    status_text = ft.Text("", color="white", size=16)
    install_task = {"task": None, "cancel_event": None}

    def quick_update():
        status_text.update()
        progress_bar.update()
    
    def on_window_event(e: ft.ControlEvent):
        if e.data == "focused":   # Window gains focus
            bg_music.resume()
        elif e.data == "unfocused":  # Window loses focus
            bg_music.pause()

    page.on_window_event = on_window_event
    page.overlay.append(bg_music)

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
        if install_task["task"] and not install_task["task"].done:
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

    # Main content layout
    content = ft.Column([
        ft.Container(splash_logo, alignment=ft.alignment.center) if splash_logo else ft.Text("Splash logo not found", color="white"),
        ft.Container(buttons, padding=ft.padding.only(top=page.height * 0.02, left=page.width * 0.03, right=page.width * 0.03)),  # 2% top, 3% side
        ft.Container(status_label, padding=ft.padding.only(top=page.height * 0.02)),
        status_text,
        progress_bar,
        ft.Text("Mod Manager Credits: | TheDoctor | CutesyThrower12 || VANGAURD CREDITS: Directal", size=12, color="white"),
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

    dynamic_bg = None
    dynamic_video = None
    stack_children = []
    if os.path.exists(bg_path):
        dynamic_bg = DynamicBg()
        stack_children.append(dynamic_bg)
    if os.path.exists(mp4_path):
        dynamic_video = DynamicVideo()
        stack_children.append(dynamic_video)
    stack_children.append(content)

    def on_resize(e):
        if dynamic_bg:
            dynamic_bg.resize(page.window_width, page.window_height)
        if dynamic_video:
            dynamic_video.resize(page.window_width, page.window_height)
        # Update control sizes on resize
        if splash_logo:
            splash_logo.width = page.width * 0.57 if page.width * 0.57 <= 1100 else 1100
            splash_logo.height = page.height * 0.55 if page.height * 0.55 <= 600 else 600
            splash_logo.update()
        for btn in buttons.controls:
            btn.width = page.width * 0.13
            btn.update()
        progress_bar.width = page.width * 0.26
        progress_bar.update()
        buttons.spacing = page.width * 0.01
        buttons.update()
        content.controls[1].padding = ft.padding.only(top=page.height * 0.02, left=page.width * 0.03, right=page.width * 0.03)
        content.controls[2].padding = ft.padding.only(top=page.height * 0.02)
        page.update()

    page.on_resize = on_resize
    page.add(
        ft.Stack([
            *stack_children,
        ], expand=True)
    )

ft.app(target=main)