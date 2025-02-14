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
import threading

# Add Windows-specific imports at the top
if sys.platform == 'win32':
    import ctypes

def hide_console():
    """Hide the console window on Windows"""
    if sys.platform == 'win32':
        try:
            # Get console window handle
            console_window = ctypes.windll.kernel32.GetConsoleWindow()
            # Hide the console window
            if console_window:
                ctypes.windll.user32.ShowWindow(console_window, 0)
        except Exception as e:
            print(f"Error hiding console: {e}")

class Api:
    def __init__(self, app):
        self.window = None
        self.app = app
        self.is_tak_manager = False

    def navigate(self, url):
        """Open TAK Manager in a new window"""
        for _ in range(10):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(1)
        
        old_window = self.window
        self.window = webview.create_window(
            'TAK Manager',
            url,
            width=1200,
            height=800,
            js_api=self,
            text_select=True
        )
        
        self.is_tak_manager = True
        self.window.events.closed += self.app.full_cleanup
        
        if old_window:
            def destroy_old():
                time.sleep(0.5)
                old_window.destroy()
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
        
        if self.window and not self.js_api.is_tak_manager:
            try:
                self.window.destroy()
            except Exception:
                pass

        if self.dev_mode:
            for process in self.processes:
                if "vite" in str(process.args):
                    try:
                        self.kill_process_tree(process.pid)
                    except Exception:
                        pass

        self._is_cleaning_up = False

    def full_cleanup(self):
        """Clean up all resources before exit"""
        if self._is_cleaning_up:
            return
        self._is_cleaning_up = True
        
        try:
            stop_container(self.compose_file)
        except Exception:
            pass

        try:
            for window in webview.windows:
                try:
                    window.destroy()
                except:
                    pass
        except Exception:
            pass

        for process in self.processes:
            try:
                self.kill_process_tree(process.pid)
            except Exception:
                pass

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
                    port=self.api_port,
                    log_level="error"
                )
        except Exception:
            raise

    def run(self):
        """Run the application"""
        try:
            if self.dev_mode:
                try:
                    npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'
                    vite_process = subprocess.Popen(
                        [npm_cmd, 'run', 'dev'],
                        cwd=str(self.web_dir),
                        start_new_session=True
                    )
                    self.processes.append(vite_process)
                except subprocess.CalledProcessError:
                    sys.exit(1)

                api_process = subprocess.Popen(
                    [sys.executable, str(Path(__file__)), '--dev', '--port', str(self.api_port)],
                    start_new_session=True
                )
                self.processes.append(api_process)

                frontend_url = "http://localhost:3000"
                backend_url = f"http://localhost:{self.api_port}/health"
                
                if not self.wait_for_server(frontend_url):
                    raise Exception("Frontend server failed to start")
                if not self.wait_for_server(backend_url):
                    raise Exception("Backend server failed to start")

            else:
                dist_dir = self.web_dir / "dist"
                if not dist_dir.exists():
                    npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'
                    subprocess.run([npm_cmd, 'run', 'build'], cwd=str(self.web_dir), check=True)
                
                import threading
                api_thread = threading.Thread(
                    target=self.start_api_server,
                    name="api_server",
                    daemon=True
                )
                api_thread.start()

                backend_url = f"http://localhost:{self.api_port}/health"
                if not self.wait_for_server(backend_url):
                    raise Exception("Backend server failed to start")

            frontend_url = "http://localhost:3000" if self.dev_mode else f"http://localhost:{self.api_port}"
            self.window = webview.create_window(
                'TAK Manager Setup',
                url=frontend_url,
                width=1200,
                height=800,
                js_api=self.js_api,
                text_select=True
            )

            self.window.events.closed += self.cleanup_setup
            self.js_api.window = self.window
            webview.start(
                http_server=True,
                http_port=13377,
                private_mode=False
            )

        except Exception as e:
            self.full_cleanup()
            sys.exit(1)

def create_dev_app():
    """Factory function for development server with auto-reload."""
    return create_app(dev_mode=True)

def main():
    import argparse
    import sys
    
    # Check if we're running as a packaged executable
    is_packaged = getattr(sys, 'frozen', False)
    
    if is_packaged:
        # When packaged, always run in production mode with default port
        # Hide console window at startup in production mode
        hide_console()
        app = TakManagerApp(dev_mode=False, api_port=8000)
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
        # Development mode - handle arguments
        parser = argparse.ArgumentParser(description='TAK Manager')
        parser.add_argument('--dev', action='store_true', help='Run in development mode')
        parser.add_argument('--port', type=int, default=8000, help='API port (default: 8000)')
        
        # Filter out any PyInstaller-related arguments
        filtered_args = [arg for arg in sys.argv[1:] if not any(x in arg for x in ['_internal', 'Frameworks'])]
        args = parser.parse_args(filtered_args)

        # If no additional arguments are provided or only --dev, run the full application
        app = TakManagerApp(dev_mode=args.dev, api_port=args.port)
        if not filtered_args or (len(filtered_args) == 1 and filtered_args[0] == '--dev'):
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
            app.start_api_server()

if __name__ == '__main__':
    main() 