import os
import sys
import uvicorn
import webview
import subprocess
import signal
import atexit
import time
import requests
import psutil
from pathlib import Path
from docker_handler import stop_container, get_resource_path
from api import create_app
from webview.util import escape_string

class Api:
    def __init__(self, app):
        self.window = None
        self.app = app  # Store reference to main app for cleanup
        self.is_tak_manager = False  # Flag to identify TAK Manager window

    def navigate(self, url):
        """Open TAK Manager in a new window"""
        print(f"Opening new window for: {url}")
        
        # Wait for service to be ready
        print("Waiting for service to be ready...")
        for _ in range(10):  # Try for 10 seconds
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(1)
        
        # Store old window reference
        old_window = self.window
        
        # Create new window with close event handler
        self.window = webview.create_window(
            'TAK Manager',
            url,
            width=1200,
            height=800,
            js_api=self
        )
        
        # Mark this as TAK Manager window
        self.is_tak_manager = True
        
        # Add close event handler for TAK Manager window
        self.window.events.closed += self.app.full_cleanup
        
        # Destroy old window after small delay to ensure new window is ready
        if old_window:
            def destroy_old():
                time.sleep(0.5)  # Small delay
                old_window.destroy()
            
            import threading
            threading.Thread(target=destroy_old).start()

class TakManagerApp:
    def __init__(self, dev_mode=False, api_port=8000):
        self.compose_file = str(Path(get_resource_path("docker-compose.prod.yml")))
        self.window = None
        self.web_dir = Path(get_resource_path("web"))
        self.dev_mode = dev_mode
        self.api_port = api_port
        self.processes = []
        self._is_cleaning_up = False
        self.js_api = Api(self)  # Pass self reference
        
        # Register cleanup handlers
        atexit.register(self.full_cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def kill_process_tree(self, pid):
        """Kill a process and all its children"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Kill children
            for child in children:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Kill parent
            try:
                parent.kill()
            except psutil.NoSuchProcess:
                pass
            
            psutil.wait_procs(children + [parent], timeout=5)
        except psutil.NoSuchProcess:
            pass

    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print("\nReceived signal to terminate...")
        self.full_cleanup()
        sys.exit(0)

    def cleanup_setup(self):
        """Clean up only setup-related resources"""
        if self._is_cleaning_up:
            return
        self._is_cleaning_up = True
        
        print("Cleaning up setup resources...")
        
        # Only close the setup window
        if self.window and not self.js_api.is_tak_manager:
            try:
                self.window.destroy()
                print("Setup window closed")
            except Exception as e:
                print(f"Error closing setup window: {e}")

        # Only kill setup-specific processes (dev server if in dev mode)
        if self.dev_mode:
            for process in self.processes:
                if "vite" in str(process.args):
                    try:
                        self.kill_process_tree(process.pid)
                        print(f"Dev server process tree {process.pid} terminated")
                    except Exception as e:
                        print(f"Error terminating dev server process tree {process.pid}: {e}")

        self._is_cleaning_up = False

    def full_cleanup(self):
        """Clean up all resources before exit"""
        if self._is_cleaning_up:
            return
        self._is_cleaning_up = True
        
        print("Cleaning up all resources...")
        
        # Stop any running containers first
        try:
            stop_container(self.compose_file)
            print("Docker containers stopped")
        except Exception as e:
            print(f"Error stopping Docker containers: {e}")

        # Close all webview windows
        try:
            for window in webview.windows:
                try:
                    window.destroy()
                except:
                    pass
            print("All webview windows closed")
        except Exception as e:
            print(f"Error closing windows: {e}")

        # Kill all child processes and their descendants
        for process in self.processes:
            try:
                self.kill_process_tree(process.pid)
                print(f"Process tree {process.pid} terminated")
            except Exception as e:
                print(f"Error terminating process tree {process.pid}: {e}")

        # Force exit to ensure all resources are cleaned up
        os._exit(0)

    def wait_for_server(self, url: str, timeout: int = 30) -> bool:
        """Wait for a server to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            time.sleep(1)
            print(f"Waiting for {url} to be ready...")
        return False

    def start_api_server(self):
        """Start the FastAPI server"""
        try:
            app = create_app(dev_mode=self.dev_mode)
            
            if self.dev_mode:
                uvicorn.run(
                    "app:create_dev_app",
                    host="127.0.0.1",
                    port=self.api_port,
                    reload=True,
                    factory=True
                )
            else:
                uvicorn.run(
                    app,
                    host="127.0.0.1",
                    port=self.api_port
                )
        except Exception as e:
            print(f"Server failed to start: {e}")
            raise

    def run(self):
        """Run the application"""
        try:
            # Start the appropriate servers based on mode
            if self.dev_mode:
                # Start Vite dev server
                try:
                    npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'
                    vite_process = subprocess.Popen(
                        [npm_cmd, 'run', 'dev'],
                        cwd=str(self.web_dir),
                        start_new_session=True
                    )
                    self.processes.append(vite_process)
                except subprocess.CalledProcessError:
                    print("Failed to start Vite dev server")
                    sys.exit(1)

                # Start FastAPI development server
                api_process = subprocess.Popen(
                    [sys.executable, str(Path(__file__)), '--dev', '--port', str(self.api_port)],
                    start_new_session=True
                )
                self.processes.append(api_process)

                # Wait for both servers to be ready
                frontend_url = "http://localhost:3000"
                backend_url = f"http://localhost:{self.api_port}/health"
                
                print("Waiting for servers to start...")
                if not self.wait_for_server(frontend_url):
                    raise Exception("Frontend server failed to start")
                if not self.wait_for_server(backend_url):
                    raise Exception("Backend server failed to start")
                print("Servers are ready!")

            else:
                # Build frontend for production
                dist_dir = self.web_dir / "dist"
                if not dist_dir.exists():
                    print("Building frontend...")
                    npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'
                    subprocess.run([npm_cmd, 'run', 'build'], cwd=str(self.web_dir), check=True)
                
                # Start FastAPI production server
                api_process = subprocess.Popen(
                    [sys.executable, str(Path(__file__)), '--port', str(self.api_port)],
                    start_new_session=True
                )
                self.processes.append(api_process)

                # Wait for backend server to be ready
                backend_url = f"http://localhost:{self.api_port}/health"
                print("Waiting for server to start...")
                if not self.wait_for_server(backend_url):
                    raise Exception("Backend server failed to start")
                print("Server is ready!")

            # Create initial configuration window
            frontend_url = "http://localhost:3000" if self.dev_mode else f"http://localhost:{self.api_port}"
            self.window = webview.create_window(
                'TAK Manager Setup',
                url=frontend_url,
                width=1200,
                height=800,
                js_api=self.js_api
            )
            
            # Add close event handler for setup window
            self.window.events.closed += self.cleanup_setup
            
            # Update the API's window reference
            self.js_api.window = self.window

            # Start the webview
            webview.start(debug=True)

        except Exception as e:
            print(f"Error running application: {e}")
            self.full_cleanup()
            sys.exit(1)

def create_dev_app():
    """Factory function for development server with auto-reload."""
    return create_app(dev_mode=True)

def main():
    import argparse
    import sys
    
    # Filter out the PyInstaller runtime path argument
    filtered_args = [arg for arg in sys.argv if not arg.endswith('Frameworks/app.py')]
    
    parser = argparse.ArgumentParser(description='TAK Manager')
    parser.add_argument('--dev', action='store_true', help='Run in development mode')
    parser.add_argument('--port', type=int, default=8000, help='API port (default: 8000)')
    
    # Use the filtered arguments for parsing
    args = parser.parse_args(filtered_args[1:])  # Skip the first argument (script name)

    # If no additional arguments are provided or only --dev, run the full application
    if len(filtered_args) == 1 or (len(filtered_args) == 2 and filtered_args[1] == '--dev'):
        app = TakManagerApp(dev_mode=args.dev, api_port=args.port)
        try:
            app.run()
        except KeyboardInterrupt:
            print("\nReceived keyboard interrupt...")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            app.full_cleanup()
            sys.exit(0)
    else:
        # If arguments are provided, assume we're starting just the API server
        app = TakManagerApp(dev_mode=args.dev, api_port=args.port)
        app.start_api_server()

if __name__ == '__main__':
    main() 