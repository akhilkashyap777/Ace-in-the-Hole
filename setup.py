from cx_Freeze import setup, Executable
import sys

# Dependencies that might need explicit inclusion
build_options = {
    'packages': [
        'kivymd', 'kivymd.uix', 'plyer', 'plyer.platforms',
        'cryptography', 'bcrypt', 'pygame', 'qrcode', 
        'requests', 'PIL', 'json', 'os', 'sys'
    ],
    'excludes': ['tkinter'],  # Exclude unnecessary modules
    'include_files': []  # Add any data files here if needed
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Hide console on Windows

executables = [
    Executable('main.py', base=base, target_name='AceVault')
]

setup(
    name='AceVault',
    version='1.0',
    description='Ace Vault Application',
    options={'build_exe': build_options},
    executables=executables
)
