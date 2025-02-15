declare global {
  interface Window {
    pywebview: {
      api: {
        check_docker_installed: () => Promise<boolean>;
        check_docker_running: () => Promise<boolean>;
        get_docker_install_url: () => Promise<string>;
        save_config: (installDir: string, port: string) => Promise<{ success: boolean, error?: string }>;
        start_container: () => Promise<{ success: boolean, error?: string, port?: string }>;
        stop_container: () => Promise<{ success: boolean, error?: string }>;
        get_config: () => Promise<{ TAK_SERVER_INSTALL_DIR: string, BACKEND_PORT: string }>;
        select_directory: () => Promise<{ path: string }>;
        open_external_url: (url: string) => Promise<{ success: boolean }>;
        navigate: (url: string) => void;
        check_port: (port: number) => Promise<{ available: boolean, message: string }>;
      };
    };
  }
}

export {}; 