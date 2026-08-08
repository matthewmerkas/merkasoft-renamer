# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_all

# 1. Compute project root directory (2 levels up from build/pyinstaller)
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
PROJECT_ROOT = os.path.abspath(os.path.join(SPEC_DIR, "../.."))

# 2. Collect dependencies for pillow_heif
heif_datas, heif_binaries, heif_hiddenimports = collect_all('pillow_heif')

# 3. Assemble data files relative to PROJECT_ROOT
datas = []

for item in ['Renamer', 'assets']:
    item_path = os.path.join(PROJECT_ROOT, item)
    if os.path.exists(item_path):
        datas.append((item_path, item))

theme_path = os.path.join(PROJECT_ROOT, 'Theme.qml')
if os.path.exists(theme_path):
    datas.append((theme_path, '.'))

datas += heif_datas

binaries = [] + heif_binaries

# 4. Include all required hidden imports
hiddenimports = [
    'models',
    'models.file',
    'services',
    'services.base_processor',
    'services.regex_processor',
    'dateutil',
    'exifread',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQuickControls2',
] + heif_hiddenimports

# 5. OS and Icon Detection
is_win = sys.platform.startswith('win')
is_mac = sys.platform == 'darwin'

win_icon = os.path.join(PROJECT_ROOT, 'assets', 'icon.ico')
mac_icon = os.path.join(PROJECT_ROOT, 'assets', 'icon.icns')

# 6. Analysis
a = Analysis(
    [os.path.join(PROJECT_ROOT, 'main.py')],
    pathex=[PROJECT_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pytest'],
    noarchive=False,
)

pyz = PYZ(a.pure)

# 7. Executable Configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Merkasoft Renamer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=win_icon if (is_win and os.path.exists(win_icon)) else None,
)

# 8. Directory Collection
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='Merkasoft Renamer',
)

# 9. macOS App Bundle Configuration
if is_mac:
    app = BUNDLE(
        coll,
        name='Merkasoft Renamer.app',
        icon=mac_icon if os.path.exists(mac_icon) else None,
        bundle_identifier='com.merkasoft.renamer',
    )
