import subprocess
import platform
import docker
import time
from pathlib import Path
import os
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # Check if we're running in a packaged app
        if getattr(sys, 'frozen', False):
            # We're in a packaged app
            if platform.system().lower() == "darwin":
                # On macOS, resources are in Contents/Resources
                base_path = os.path.abspath(os.path.join(
                    os.path.dirname(sys.executable),
                    '../Resources'
                ))
            else:
                # On other platforms, use _MEIPASS
                base_path = sys._MEIPASS
        else:
            # Development mode - go up 2 levels from handlers directory
            base_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__),
                '../..'  # Go from handlers -> api -> project root
            ))
        
        full_path = os.path.join(base_path, relative_path)
        # Use print only in development mode or log to file instead of console
        if not getattr(sys, 'frozen', False):
            print(f"Resource path for {relative_path}: {full_path}")
        return full_path
    except Exception as e:
        # Log to file instead of console in production
        if not getattr(sys, 'frozen', False):
            print(f"Error in get_resource_path: {e}")
        raise

def start_docker_desktop():
    """Start Docker Desktop application or service"""
    system = platform.system().lower()
    try:
        if system == "darwin":  # macOS
            subprocess.Popen(["open", "-a", "Docker"])
        elif system == "windows":  # Windows
            # Properly launch Docker Desktop on Windows
            # Use START command with correct syntax and hide the console window
            startupinfo = None
            if hasattr(subprocess, 'STARTUPINFO'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
            
            # Find Docker Desktop path
            program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
            docker_path = os.path.join(program_files, 'Docker', 'Docker', 'Docker Desktop.exe')
            
            if os.path.exists(docker_path):
                subprocess.Popen([docker_path], startupinfo=startupinfo)
            else:
                # Try alternative location
                program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
                docker_path_alt = os.path.join(program_files_x86, 'Docker', 'Docker', 'Docker Desktop.exe')
                if os.path.exists(docker_path_alt):
                    subprocess.Popen([docker_path_alt], startupinfo=startupinfo)
                else:
                    # Fallback to shell command but hide window
                    subprocess.Popen('cmd /c start "" "Docker Desktop"', shell=True, 
                                    startupinfo=startupinfo)
        elif system == "linux":  # Linux
            # Try systemd service first
            try:
                subprocess.run(['systemctl', '--user', 'start', 'docker'], check=True)
            except subprocess.CalledProcessError:
                try:
                    # Try system-wide service
                    subprocess.run(['sudo', 'systemctl', 'start', 'docker'], check=True)
                except subprocess.CalledProcessError:
                    if not getattr(sys, 'frozen', False):
                        print("Could not start Docker service. Please ensure Docker is installed and the service is enabled.")
                    return False
        # Give Docker some time to start
        time.sleep(5)
        return True
    except Exception as e:
        if not getattr(sys, 'frozen', False):
            print(f"Failed to start Docker Desktop/Service: {e}")
        return False

# Helper function to create proper startupinfo for Windows to hide console windows
def get_startupinfo():
    """Get startupinfo object to hide console windows on Windows"""
    startupinfo = None
    if platform.system().lower() == "windows" and hasattr(subprocess, 'STARTUPINFO'):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        # Also use CREATE_NO_WINDOW flag
        startupinfo.dwFlags |= subprocess.CREATE_NO_WINDOW
    return startupinfo

def get_docker_binary():
    """Get the absolute path to the docker binary"""
    system = platform.system().lower()
    
    if system == "windows":
        # Common Windows Docker paths
        docker_paths = [
            r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
            r"C:\Program Files\Docker\Docker\resources\docker.exe",
            r"C:\ProgramData\DockerDesktop\version-bin\docker.exe"
        ]
        
        # First check if docker is in PATH
        if os.environ.get('PATH'):
            for path in os.environ['PATH'].split(os.pathsep):
                docker_path = os.path.join(path, 'docker.exe')
                if os.path.isfile(docker_path) and os.access(docker_path, os.X_OK):
                    return docker_path
        
        # Then check common locations
        for path in docker_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        
        return 'docker'  # Fallback to just 'docker' if not found
    else:
        # Unix-like systems (macOS, Linux)
        docker_paths = [
            '/usr/local/bin/docker',  # Homebrew installation
            '/opt/homebrew/bin/docker',  # Apple Silicon Homebrew
            '/usr/bin/docker',  # System installation
        ]
        
        # First check if docker is in PATH
        if os.environ.get('PATH'):
            for path in os.environ['PATH'].split(os.pathsep):
                docker_path = os.path.join(path, 'docker')
                if os.path.isfile(docker_path) and os.access(docker_path, os.X_OK):
                    return docker_path
        
        # Then check common locations
        for path in docker_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        
        return 'docker'  # Fallback to just 'docker' if not found

def setup_environment():
    """Setup the environment with necessary paths"""
    if platform.system().lower() == "darwin":
        # Add common binary paths to PATH if not already present
        paths_to_add = [
            '/usr/local/bin',  # Homebrew
            '/opt/homebrew/bin',  # Apple Silicon Homebrew
            '/usr/bin',
            '/bin',
            '/usr/sbin',
            '/sbin'
        ]
        
        current_path = os.environ.get('PATH', '')
        new_paths = [p for p in paths_to_add if p not in current_path.split(os.pathsep)]
        if new_paths:
            os.environ['PATH'] = os.pathsep.join([*new_paths, current_path])

def check_docker_installed() -> bool:
    """Check if Docker is installed and accessible"""
    try:
        setup_environment()
        docker_bin = get_docker_binary()
        startupinfo = get_startupinfo()
        subprocess.run([docker_bin, '--version'], capture_output=True, text=True, check=True, startupinfo=startupinfo)
        subprocess.run([docker_bin, 'compose', 'version'], capture_output=True, text=True, check=True, startupinfo=startupinfo)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_docker_running() -> bool:
    """Check if Docker daemon is running"""
    try:
        client = docker.from_env()
        client.ping()
        return True
    except docker.errors.DockerException:
        return False

def find_and_load_docker_image():
    """Find and load the TAK Manager Docker image"""
    try:
        # Find the image tar file using the resource path
        image_dir = Path(get_resource_path("docker"))
        
        # Look for both .tar and .tar.gz extensions
        tar_files = []
        for ext in [".tar", ".tar.gz"]:
            tar_files.extend(list(image_dir.glob(f"tak-manager-*{ext}")))
        
        if not tar_files:
            raise Exception("No TAK Manager image found in docker directory")
        
        # Use the latest version if multiple files exist
        # Sort by version number, not by extension
        def get_version(file_path):
            # Extract version from filename (tak-manager-1.0.0.tar.gz or tak-manager-1.0.0.tar -> 1.0.0)
            version = file_path.stem.split('-')[-1]
            if version.endswith('.tar'):  # Handle .tar extension in stem
                version = version[:-4]
            return version
            
        image_tar = sorted(tar_files, key=get_version)[-1]
        
        # Extract version, handling both .tar and .tar.gz cases
        version = get_version(image_tar)
        image_name = f"tak-manager:{version}"
        
        # Check if image already exists
        client = docker.from_env()
        try:
            client.images.get(image_name)
            if not getattr(sys, 'frozen', False):
                print(f"Docker image {image_name} already loaded")
            return True
        except docker.errors.ImageNotFound:
            # Load Docker image from tar
            if not getattr(sys, 'frozen', False):
                print(f"Loading TAK Server Docker image {image_name} from {image_tar}...")
            setup_environment()
            docker_bin = get_docker_binary()
            startupinfo = get_startupinfo()
            load_result = subprocess.run(
                [docker_bin, 'load', '-i', str(image_tar)],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            if load_result.returncode != 0:
                raise Exception(f"Failed to load Docker image: {load_result.stderr}")
            if not getattr(sys, 'frozen', False):
                print("Docker image loaded successfully")
            return True
            
    except Exception as e:
        if not getattr(sys, 'frozen', False):
            print(f"Error loading Docker image: {e}")
        return False

def start_container(compose_file: str) -> dict:
    """Start the TAK Manager container"""
    try:
        setup_environment()
        docker_bin = get_docker_binary()
        
        # First ensure the Docker image is loaded
        if not find_and_load_docker_image():
            return {"success": False, "error": "Failed to load Docker image. Ensure Docker is installed and running."}

        # Get the correct compose file path using get_resource_path
        compose_file = get_resource_path(compose_file)
        if not getattr(sys, 'frozen', False):
            print(f"Using compose file: {compose_file}")
        
        # Get data directory and ensure it exists with proper permissions
        data_dir = get_app_data_dir()
        config_dir = os.path.join(data_dir, 'config')
        logs_dir = os.path.join(data_dir, 'logs')
        
        # Ensure all required directories exist
        for directory in [data_dir, config_dir, logs_dir]:
            os.makedirs(directory, exist_ok=True)
            # Ensure directory has proper permissions (read/write for user)
            os.chmod(directory, 0o755)

        # Copy .env file to data directory if it doesn't exist
        env_src = get_resource_path(".env")
        env_dest = os.path.join(data_dir, ".env")
        if not os.path.exists(env_dest):
            import shutil
            shutil.copy2(env_src, env_dest)
            # Ensure env file has proper permissions
            os.chmod(env_dest, 0o644)
        
        # Load environment variables from the persistent env file
        with open(env_dest, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

        # Prepare environment with absolute paths
        env_vars = {
            **os.environ,
            'TAK_MANAGER_DATA_DIR': data_dir,
            'TAK_MANAGER_CONFIG_DIR': config_dir,
            'TAK_MANAGER_LOGS_DIR': logs_dir
        }

        # Start container using docker compose
        if not getattr(sys, 'frozen', False):
            print(f"Starting TAK Server container with data dir: {data_dir}")
        
        startupinfo = get_startupinfo()
        result = subprocess.run(
            [docker_bin, 'compose', '-f', compose_file, 'up', '-d'],
            capture_output=True,
            text=True,
            env=env_vars,
            startupinfo=startupinfo
        )
        if result.returncode != 0:
            if not getattr(sys, 'frozen', False):
                print(f"Docker compose error: {result.stderr}")
            return {"success": False, "error": result.stderr}

        port = os.environ.get("BACKEND_PORT", "")
        if not port:
            return {"success": False, "error": "No backend port specified"}

        return {"success": True, "port": port}
    except Exception as e:
        if not getattr(sys, 'frozen', False):
            print(f"Error in start_container: {str(e)}")
        return {"success": False, "error": str(e)}

def stop_container(compose_file: str) -> dict:
    """Stop the TAK Manager container"""
    try:
        setup_environment()
        docker_bin = get_docker_binary()
        
        # Convert compose_file path to use correct path separators for the OS
        compose_file = str(Path(compose_file))
        
        startupinfo = get_startupinfo()
        result = subprocess.run(
            [docker_bin, 'compose', '-f', compose_file, 'down'],
            capture_output=True,
            text=True,
            startupinfo=startupinfo
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_app_data_dir():
    """Get the application data directory"""
    system = platform.system().lower()
    if system == "darwin":  # macOS
        data_dir = os.path.expanduser("~/Library/Application Support/TAK-Manager")
    elif system == "windows":  # Windows
        data_dir = os.path.join(os.getenv("APPDATA"), "TAK-Manager")
    else:  # Linux
        data_dir = os.path.expanduser("~/.tak-manager")
    
    os.makedirs(data_dir, exist_ok=True)
    return data_dir 