from cx_Freeze import setup, Executable
import sys
import os

# Set environment variables for Kivy
os.environ['KIVY_WINDOW'] = 'sdl2'
os.environ['KIVY_GL_BACKEND'] = 'mock'
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# Build options
build_exe_options = {
    "packages": ["kivymd", "kivy", "pygame", "PIL", "requests", "qrcode", "bcrypt", "cryptography", "plyer"],
    "include_files": [],
    "excludes": []
}

setup(
    name="AceVault-Linux",
    version="1.0",
    description="Ace Vault Application",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", target_name="AceVault-Linux")]
)
