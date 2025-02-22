import socket
import platform
import subprocess
from typing import Tuple

# Define reserved ports that shouldn't be used
RESERVED_PORTS = {5432, 8443, 8446, 8089, 8444}  # Set for O(1) lookup

def is_port_in_use_socket(port: int) -> bool:
    """Check if a port is in use using socket connection."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except socket.error:
            return True

def is_port_in_use_command(port: int) -> bool:
    """Check if a port is in use using system commands with multiple methods."""
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Improved Windows check with multiple netstat patterns
            cmd = (
                f'netstat -ano | '
                f'findstr "LISTENING" | '
                f'findstr /R ":{port} 0.0.0.0:{port} \[::\]:{port}"'
            )
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        else:
            # Improved macOS/Linux check using lsof with state filtering
            cmd = f'lsof -nP -i :{port} -s TCP:LISTEN >/dev/null 2>&1'
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0
    except subprocess.SubprocessError:
        # If command fails, fallback to socket check
        return is_port_in_use_socket(port)

def check_port_availability(port: int) -> Tuple[bool, str]:
    """
    Check if a port is available for use.
    Returns a tuple of (is_available: bool, message: str)
    """
    try:
        # Validate port range
        if not 1024 <= port <= 49151:
            return False, "Port must be between 1024 and 49151"
        
        # Check if port is in reserved list
        if port in RESERVED_PORTS:
            return False, f"Port {port} is reserved for other services"
        
        # Check using both methods but require consistent negative for availability
        socket_available = not is_port_in_use_socket(port)
        command_available = not is_port_in_use_command(port)
        
        if not (socket_available and command_available):
            return False, f"Port {port} is already in use"
            
        return True, "Port is available"
        
    except Exception as e:
        return False, f"Error checking port availability: {str(e)}" 