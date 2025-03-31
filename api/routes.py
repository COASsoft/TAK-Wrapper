from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import webbrowser
from api.handlers.path_handler import select_directory, save_config as save_config_file, load_config
from api.handlers.docker_handler import (
    check_docker_installed,
    check_docker_running,
    start_docker_desktop,
    start_container,
    stop_container
)
from api.handlers.port_checker import check_port_availability
import requests
from packaging import version
import os
import json
import socket
import subprocess
import platform
from pathlib import Path

router = APIRouter()
compose_file = "docker-compose.prod.yml"

class ConfigData(BaseModel):
    install_dir: str
    port: str

class UrlData(BaseModel):
    url: str

@router.post("/open-external-url")
async def open_external_url(data: UrlData):
    """Open URL in the host system's default browser"""
    try:
        webbrowser.open(data.url)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-docker-installed")
async def check_docker_installed_route():
    """Check if Docker is installed"""
    return {"installed": check_docker_installed()}

@router.get("/check-docker-running")
async def check_docker_running_route():
    """Check if Docker daemon is running and try to start it if not"""
    if check_docker_running():
        return {"running": True}
    
    # Try to start Docker Desktop
    start_docker_desktop()
    return {"running": check_docker_running()}

@router.post("/start-container")
async def start_container_route():
    """Start the TAK Manager container"""
    result = start_container(compose_file)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Get port from environment
    config = load_config()
    port = config.get("BACKEND_PORT")
    if not port:
        raise HTTPException(status_code=500, detail="No backend port specified")
    
    return {"success": True, "port": port}

@router.post("/stop-container")
async def stop_container_route():
    """Stop the TAK Manager container"""
    result = stop_container(compose_file)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.get("/config")
async def get_config():
    """Get current configuration"""
    return load_config()

@router.post("/config")
async def save_config(config: ConfigData):
    """Save configuration and create .env file"""
    if not save_config_file(config.install_dir, config.port):
        raise HTTPException(status_code=500, detail="Failed to save configuration")
    return {"success": True}

@router.get("/select-directory")
async def select_directory_route():
    """Select directory using native file picker"""
    try:
        path = select_directory()
        return {"path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-port/{port}")
async def check_port(port: int):
    """Check if a port is available for use."""
    is_available, message = check_port_availability(port)
    return {"available": is_available, "message": message}

def get_current_version():
    """Get current version from version.txt"""
    try:
        version_file = Path(__file__).parent.parent / 'version.txt'
        if version_file.exists():
            version = version_file.read_text().strip()
            if version.startswith('v'):
                version = version[1:]
            return version
    except Exception as e:
        print(f"Error reading version file: {e}")
    return '1.0.0'  # Fallback version

@router.get("/check-update")
async def check_update():
    """Check for updates from GitHub repository"""
    try:
        # Get current version from version.txt
        current_version = get_current_version()

        try:
            # Fetch latest release from GitHub API
            response = requests.get(
                'https://api.github.com/repos/JShadowNull/TAK-Manager/releases/latest',
                timeout=10
            )
            response.raise_for_status()
            
            latest_release = response.json()
            latest_version = latest_release.get('tag_name', '')
            release_notes = latest_release.get('body', 'No release notes available.')
            
            if not latest_version:
                return {
                    "has_update": False,
                    "error": "No version information found in latest release",
                    "current_version": current_version,
                    "latest_version": current_version,
                    "release_notes": ""
                }

            if latest_version.startswith('v'):
                latest_version = latest_version[1:]
            
            # Compare versions
            has_update = version.parse(latest_version) > version.parse(current_version)
            
            return {
                "has_update": has_update,
                "current_version": current_version,
                "latest_version": latest_version,
                "release_notes": release_notes
            }
        except requests.RequestException as e:
            # Handle network-related errors specifically
            return {
                "has_update": False,
                "error": f"Network error checking for updates: {str(e)}",
                "current_version": current_version,
                "latest_version": current_version,
                "release_notes": ""
            }
        except json.JSONDecodeError:
            # Handle invalid JSON response
            return {
                "has_update": False,
                "error": "Invalid response from update server",
                "current_version": current_version,
                "latest_version": current_version,
                "release_notes": ""
            }
    except Exception as e:
        # Handle any other unexpected errors
        return {
            "has_update": False,
            "error": f"Error checking for updates: {str(e)}",
            "current_version": "1.0.0",
            "latest_version": "1.0.0",
            "release_notes": ""
        }

def check_network_connectivity():
    """Check if we can reach the GitHub server"""
    host = "github.com"
    try:
        # Try DNS resolution first
        socket.gethostbyname(host)
        
        # Use platform-specific ping command
        system = platform.system().lower()
        if system == "windows":
            ping_cmd = ["ping", "-n", "1", "-w", "1000", host]
        else:  # macOS or Linux
            ping_cmd = ["ping", "-c", "1", "-W", "1", host]
            
        result = subprocess.run(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except:
        return False

@router.get("/check-network")
async def check_network():
    """Check if network connection to update server is available"""
    is_connected = check_network_connectivity()
    return {"connected": is_connected} 