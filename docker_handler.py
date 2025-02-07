import subprocess
import platform
import docker
import time
from pathlib import Path
import os

def start_docker_desktop():
    """Start Docker Desktop application"""
    system = platform.system().lower()
    try:
        if system == "darwin":  # macOS
            subprocess.Popen(["open", "-a", "Docker"])
        elif system == "windows":  # Windows
            subprocess.Popen(["start", "Docker Desktop"], shell=True)
        # Give Docker some time to start
        time.sleep(5)
        return True
    except Exception as e:
        print(f"Failed to start Docker Desktop: {e}")
        return False

def check_docker_installed() -> bool:
    """Check if Docker is installed and accessible"""
    try:
        subprocess.run(['docker', '--version'], capture_output=True, text=True, check=True)
        subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True, check=True)
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
        # Find the image tar file
        image_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "docker"
        tar_files = list(image_dir.glob("tak-manager-*.tar.gz"))
        
        if not tar_files:
            raise Exception("No TAK Manager image found in docker directory")
        
        # Use the latest version if multiple files exist
        image_tar = sorted(tar_files)[-1]
        
        # Extract version from filename (tak-manager-1.0.0.tar.gz -> 1.0.0)
        version = image_tar.stem.split('-')[-1].replace('.tar', '')
        image_name = f"tak-manager:{version}"
        
        # Check if image already exists
        client = docker.from_env()
        try:
            client.images.get(image_name)
            print(f"Docker image {image_name} already loaded")
            return True
        except docker.errors.ImageNotFound:
            # Load Docker image from tar
            print(f"Loading TAK Server Docker image {image_name}...")
            load_result = subprocess.run(
                ['docker', 'load', '-i', str(image_tar)],
                capture_output=True,
                text=True
            )
            if load_result.returncode != 0:
                raise Exception(f"Failed to load Docker image: {load_result.stderr}")
            print("Docker image loaded successfully")
            return True
            
    except Exception as e:
        print(f"Error loading Docker image: {e}")
        return False

def start_container(compose_file: str) -> dict:
    """Start the TAK Manager container"""
    try:
        # First ensure the Docker image is loaded
        if not find_and_load_docker_image():
            return {"success": False, "error": "Failed to load Docker image"}

        # Start container using docker-compose
        print("Starting TAK Server container...")
        result = subprocess.run(
            ['docker', 'compose', '-f', compose_file, 'up', '-d'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}

        port = os.environ.get("BACKEND_PORT", "")
        if not port:
            return {"success": False, "error": "No backend port specified"}

        return {"success": True, "port": port}
    except Exception as e:
        return {"success": False, "error": str(e)}

def stop_container(compose_file: str) -> dict:
    """Stop the TAK Manager container"""
    try:
        result = subprocess.run(
            ['docker', 'compose', '-f', compose_file, 'down'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)} 