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

def load_config() -> dict:
    """Load configuration from .env file located in the same directory as this script"""
    try:
        env_path = Path(__file__).parent / '.env'  # The .env file is loaded from the current script's directory
        if not env_path.exists():
            return {"TAK_SERVER_INSTALL_DIR": "", "BACKEND_PORT": ""}

        config = {}
        with open(env_path, 'r') as f:
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
    """Update the .env file located in the same directory as this script with new configuration"""
    try:
        env_path = Path(__file__).parent / '.env'  # The .env file is saved in the current script's directory
        if not env_path.exists():
            return False

        # Read existing .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()

        # Update only the BACKEND_PORT and TAK_SERVER_INSTALL_DIR lines
        new_lines = []
        for line in lines:
            if line.startswith('BACKEND_PORT='):
                new_lines.append(f'BACKEND_PORT={port}\n')
            elif line.startswith('TAK_SERVER_INSTALL_DIR='):
                new_lines.append(f'TAK_SERVER_INSTALL_DIR={install_dir}\n')
            else:
                new_lines.append(line)

        # Write back to .env file
        with open(env_path, 'w') as f:
            f.writelines(new_lines)

        # Update environment variables
        os.environ['BACKEND_PORT'] = port
        os.environ['TAK_SERVER_INSTALL_DIR'] = install_dir

        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False 