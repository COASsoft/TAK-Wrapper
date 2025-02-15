import os
import subprocess
import platform
from pathlib import Path

def select_directory():
    """Open the native file explorer and return selected path"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        script = '''
        tell application "System Events"
            activate
            set folderPath to choose folder with prompt "Select TAK Server Installation Directory"
            return POSIX path of folderPath
        end tell
        '''
        try:
            result = subprocess.run(['osascript', '-e', script], 
                                 capture_output=True, 
                                 text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            print(f"Error selecting directory: {e}")
            
    elif system == "windows":  # Windows
        powershell_script = '''
        Add-Type -AssemblyName System.Windows.Forms
        $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
        $folderBrowser.Description = "Select TAK Server Installation Directory"
        $folderBrowser.ShowNewFolderButton = $true
        if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            $folderBrowser.SelectedPath
        }
        '''
        try:
            result = subprocess.run(
                ['powershell', '-Command', powershell_script],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception as e:
            print(f"Error selecting directory: {e}")
            
    else:  # Linux
        # Try zenity first (common on GNOME)
        try:
            result = subprocess.run(
                ['zenity', '--file-selection', '--directory', 
                 '--title=Select TAK Server Installation Directory'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            # If zenity not found, try kdialog (KDE)
            try:
                result = subprocess.run(
                    ['kdialog', '--getexistingdirectory', 
                     'Select TAK Server Installation Directory'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except FileNotFoundError:
                # If neither found, try yad (another common option)
                try:
                    result = subprocess.run(
                        ['yad', '--file', '--directory',
                         '--title=Select TAK Server Installation Directory'],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        return result.stdout.strip()
                except FileNotFoundError:
                    print("No supported file dialog found. Please install zenity, kdialog, or yad.")
                except Exception as e:
                    print(f"Error selecting directory: {e}")
    
    return ""

def get_app_config_dir() -> Path:
    """Get the appropriate config directory for the current OS"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "TAK-Manager"
    elif system == "windows":  # Windows
        return Path(os.getenv('APPDATA', str(Path.home() / 'AppData' / 'Roaming'))) / "TAK-Manager"
    else:  # Linux
        return Path.home() / ".config" / "tak-manager"

def load_config() -> dict:
    """Load configuration from .env files
    
    Checks in the following order:
    1. Packaged .env file in the same directory as this script
    2. Local system .env file in the OS-specific app config directory
    """
    config = {"TAK_SERVER_INSTALL_DIR": "", "BACKEND_PORT": ""}
    
    try:
        # First check packaged env file
        packaged_env_path = Path(__file__).parent / '.env'
        if packaged_env_path.exists():
            with open(packaged_env_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key in ['TAK_SERVER_INSTALL_DIR', 'BACKEND_PORT']:
                            config[key] = value
        
        # If packaged env is empty, check local system env file
        if not any(config.values()):
            local_env_path = get_app_config_dir() / '.env'
            if local_env_path.exists():
                with open(local_env_path, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            if key in ['TAK_SERVER_INSTALL_DIR', 'BACKEND_PORT']:
                                config[key] = value

        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {"TAK_SERVER_INSTALL_DIR": "", "BACKEND_PORT": ""}

def save_config(install_dir: str, port: str) -> bool:
    """Update both the packaged and local system .env files with new configuration"""
    try:
        # Save to packaged env file
        packaged_env_path = Path(__file__).parent / '.env'
        if packaged_env_path.exists():
            with open(packaged_env_path, 'r') as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                if line.startswith('BACKEND_PORT='):
                    new_lines.append(f'BACKEND_PORT={port}\n')
                elif line.startswith('TAK_SERVER_INSTALL_DIR='):
                    new_lines.append(f'TAK_SERVER_INSTALL_DIR={install_dir}\n')
                else:
                    new_lines.append(line)

            with open(packaged_env_path, 'w') as f:
                f.writelines(new_lines)

        # Save to local system env file
        config_dir = get_app_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        local_env_path = config_dir / '.env'
        
        # Create or update local env file
        if not local_env_path.exists():
            env_content = f"""BACKEND_PORT={port}
TAK_SERVER_INSTALL_DIR={install_dir}
"""
            with open(local_env_path, 'w') as f:
                f.write(env_content)
        else:
            with open(local_env_path, 'r') as f:
                lines = f.readlines()

            new_lines = []
            found_port = False
            found_install_dir = False
            for line in lines:
                if line.startswith('BACKEND_PORT='):
                    new_lines.append(f'BACKEND_PORT={port}\n')
                    found_port = True
                elif line.startswith('TAK_SERVER_INSTALL_DIR='):
                    new_lines.append(f'TAK_SERVER_INSTALL_DIR={install_dir}\n')
                    found_install_dir = True
                else:
                    new_lines.append(line)
            
            if not found_port:
                new_lines.append(f'BACKEND_PORT={port}\n')
            if not found_install_dir:
                new_lines.append(f'TAK_SERVER_INSTALL_DIR={install_dir}\n')

            with open(local_env_path, 'w') as f:
                f.writelines(new_lines)

        # Update environment variables
        os.environ['BACKEND_PORT'] = port
        os.environ['TAK_SERVER_INSTALL_DIR'] = install_dir

        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False 