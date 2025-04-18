# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
import glob
import os

block_cipher = None

# Get the root directory and version from environment
root_dir = Path('.').resolve()
version = os.environ.get('VERSION') 

# Define output directories
dist_dir = root_dir / 'dist'
work_dir = root_dir / 'build'
os.makedirs(dist_dir, exist_ok=True)
os.makedirs(work_dir, exist_ok=True)

# Define platform-specific settings
if sys.platform == 'darwin':  # macOS
    icon = root_dir / 'resources' / 'icon.icns'
    name = 'TAK Manager'
    bundle_id = 'com.takmanager.app'
elif sys.platform == 'win32':  # Windows
    icon = root_dir / 'resources' / 'icon.ico'
    name = 'takmanager'  # Simplified name without caps
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
    ('../docker-compose.yml', '.'),  # Docker compose file
    ('version.txt', '.'),  # Version file
    ('../Dockerfile', '.'),  # Docker file
    ('../.env', '.'),  # Environment file
]

# Add platform-specific resources
if icon.exists():
    datas.append((str(icon), '.'))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
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
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(icon)] if icon.exists() else None,
    runtime_tmpdir=None,  # Changed from 'tak-manager' to None
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
            'CFBundleShortVersionString': version,
            'CFBundleVersion': version,
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