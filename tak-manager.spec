# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
import glob

block_cipher = None

# Get the root directory
root_dir = Path('.')

# Define platform-specific settings
if sys.platform == 'darwin':  # macOS
    icon = root_dir / 'resources' / 'icon.icns'
    name = 'TAK Manager'
    bundle_id = 'com.takmanager.app'
elif sys.platform == 'win32':  # Windows
    icon = root_dir / 'resources' / 'icon.ico'
    name = 'TAK Manager'
else:  # Linux
    icon = root_dir / 'resources' / 'icon.png'
    name = 'tak-manager'

# Find Docker image files that actually exist
docker_files = []
for ext in ['*.tar', '*.tar.gz']:
    pattern = str(root_dir / 'docker' / ext)
    found_files = glob.glob(pattern)
    if found_files:
        docker_files.append((pattern, 'docker'))

# Define data files to include
datas = [
    *docker_files,  # Add any Docker images that were found
    ('web/dist', 'web/dist'),  # Built web frontend
    ('.env', '.'),  # Environment template
    ('docker-compose.prod.yml', '.'),  # Docker compose file
]

# Add platform-specific resources
if icon.exists():
    datas.append((str(icon), '.'))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'webview.platforms.cocoa',
        'webview.platforms.win32',
        'webview.platforms.gtk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=name,
    debug=False,  # Disable debug
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Enable console for proper process handling
    disable_windowed_traceback=False,
    argv_emulation=False,  # Disable argv emulation to fix argument parsing
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon if icon.exists() else None,
)

# Platform specific bundle configurations
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name=f'{name}.app',
        icon=icon if icon.exists() else None,
        bundle_identifier=bundle_id,
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'LSMinimumSystemVersion': '10.13.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'NSAppleEventsUsageDescription': 'Required for automation',
            'NSCameraUsageDescription': 'Required for webview',
            'NSMicrophoneUsageDescription': 'Required for webview',
        },
    )
else:
    # For Windows and Linux, create a directory with all files
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=name,
    ) 