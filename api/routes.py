from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import webbrowser
from path_handler import select_directory, save_config as save_config_file, load_config
from docker_handler import (
    check_docker_installed,
    check_docker_running,
    start_docker_desktop,
    start_container,
    stop_container
)
from port_checker import check_port_availability

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