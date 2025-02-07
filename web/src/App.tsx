import React, { useState, useEffect } from 'react';
import { ConfigScreen } from './components/ConfigScreen';
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './ui/card';
import { Alert, AlertTitle, AlertDescription } from './ui/alert';
import { Loader2 } from 'lucide-react';
import { api } from './lib/api';

declare global {
  interface Window {
    pywebview: {
      api: {
        check_docker_installed: () => Promise<boolean>;
        check_docker_running: () => Promise<boolean>;
        get_docker_install_url: () => Promise<string>;
        save_config: (installDir: string, port: string) => Promise<{ success: boolean, error?: string }>;
        start_container: () => Promise<{ success: boolean, error?: string }>;
        stop_container: () => Promise<{ success: boolean, error?: string }>;
        get_config: () => Promise<{ TAK_SERVER_INSTALL_DIR: string, BACKEND_PORT: string }>;
        select_directory: () => Promise<{ path: string }>;
        open_external_url: (url: string) => Promise<{ success: boolean }>;
        navigate: (url: string) => void;
      };
    };
  }
}

const BackgroundWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="relative min-h-screen bg-svg-background overflow-hidden">
    <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
      <img 
        src="/tak.svg" 
        alt="" 
        className="w-full h-full max-w-[90vh] max-h-[90vh] object-contain opacity-50 blur-[2px]"
      />
    </div>
    <div className="relative z-10 min-h-screen">
      {children}
    </div>
  </div>
);

export const App: React.FC = () => {
  const [isDockerInstalled, setIsDockerInstalled] = useState<boolean | null>(null);
  const [isDockerRunning, setIsDockerRunning] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isContainerStarting, setIsContainerStarting] = useState(false);
  const [isApiReady, setIsApiReady] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [statusMessage, setStatusMessage] = useState<string>('Initializing...');

  // Wait for pywebview API to be ready
  useEffect(() => {
    const checkApi = () => {
      if (window.pywebview && window.pywebview.api) {
        setIsApiReady(true);
      } else {
        setTimeout(checkApi, 100);
      }
    };
    checkApi();
  }, []);

  const checkDocker = async () => {
    if (!isApiReady) return;
    
    try {
      setError(null);
      setStatusMessage('Checking Docker installation...');
      const installed = await api.checkDockerInstalled();
      setIsDockerInstalled(installed);
      
      if (installed) {
        setStatusMessage('Checking if Docker is running...');
        const running = await api.checkDockerRunning();
        setIsDockerRunning(running);

        if (running) {
          setStatusMessage('Checking configuration...');
          // Check if we have config and start container if we do
          const config = await api.getConfig();
          if (config.TAK_SERVER_INSTALL_DIR && config.BACKEND_PORT) {
            setIsInitialLoad(false);
            setIsContainerStarting(true);
            setStatusMessage('Starting TAK Manager container...');
            const result = await api.startContainer();
            if (!result.success) {
              setError(result.error || 'Failed to start container');
            } else if (result.port) {
              setStatusMessage('Opening TAK Manager...');
              console.log('Opening TAK Manager on port:', result.port);
              window.pywebview.api.navigate(`http://localhost:${result.port}`);
            }
          }
        } else {
          setStatusMessage('Waiting for Docker to start...');
        }
      }
    } catch (error) {
      setError('Failed to check Docker status');
      console.error('Failed to check Docker:', error);
    } finally {
      setIsLoading(false);
      setIsContainerStarting(false);
    }
  };

  useEffect(() => {
    if (isApiReady) {
      checkDocker();
    }
  }, [isApiReady]);

  useEffect(() => {
    return () => {
      // Cleanup: stop container when component unmounts
      api.stopContainer().catch(console.error);
    };
  }, []);

  const handleInstallDocker = async () => {
    if (!isApiReady) return;
    
    try {
      await api.openExternalUrl('https://www.docker.com/products/docker-desktop/');
    } catch (error) {
      console.error('Failed to open Docker installation page:', error);
      setError('Failed to open Docker installation page');
    }
  };

  const handleSaveConfig = async (installDir: string, port: string) => {
    if (!isApiReady) return;
    
    setIsLoading(true);
    setStatusMessage('Saving configuration...');
    try {
      const result = await api.saveConfig(installDir, port);
      if (result.success) {
        setIsInitialLoad(false);
        setIsContainerStarting(true);
        setStatusMessage('Starting TAK Manager container...');
        const containerResult = await api.startContainer();
        if (!containerResult.success) {
          setError(containerResult.error || 'Failed to start container');
        } else if (containerResult.port) {
          setStatusMessage('Opening TAK Manager...');
          console.log('Opening TAK Manager on port:', containerResult.port);
          window.pywebview.api.navigate(`http://localhost:${containerResult.port}`);
        }
      } else {
        setError(result.error || 'Failed to save configuration');
      }
    } catch (error) {
      setError('Failed to save configuration');
      console.error('Failed to save configuration:', error);
    } finally {
      setIsLoading(false);
      setIsContainerStarting(false);
    }
  };

  if (isLoading) {
    return (
      <BackgroundWrapper>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <p className="text-muted-foreground">{statusMessage}</p>
          </div>
        </div>
      </BackgroundWrapper>
    );
  }

  if (isContainerStarting) {
    return (
      <BackgroundWrapper>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <p className="text-muted-foreground">{statusMessage}</p>
          </div>
        </div>
      </BackgroundWrapper>
    );
  }

  if (error) {
    return (
      <BackgroundWrapper>
        <div className="container mx-auto px-4 flex items-center justify-center min-h-screen">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="text-destructive">Error</CardTitle>
              <CardDescription>{error}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                onClick={checkDocker}
                className="w-full"
                variant="default"
              >
                Try Again
              </Button>
            </CardContent>
          </Card>
        </div>
      </BackgroundWrapper>
    );
  }

  if (isDockerInstalled === false) {
    return (
      <BackgroundWrapper>
        <div className="container mx-auto px-4 flex items-center justify-center min-h-screen">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Docker Not Installed</CardTitle>
              <CardDescription>
                Docker is required to run TAK Manager
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <AlertTitle>Installation Required</AlertTitle>
                <AlertDescription>
                  Please install Docker Desktop to continue using TAK Manager.
                </AlertDescription>
              </Alert>
              <div className="flex flex-col space-y-2">
                <Button 
                  onClick={handleInstallDocker}
                  className="w-full"
                  variant="default"
                >
                  Install Docker
                </Button>
                <Button 
                  onClick={checkDocker}
                  className="w-full"
                  variant="outline"
                >
                  Check Again
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </BackgroundWrapper>
    );
  }

  if (isDockerRunning === false) {
    return (
      <BackgroundWrapper>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <p className="text-muted-foreground">{statusMessage}</p>
          </div>
        </div>
      </BackgroundWrapper>
    );
  }

  return isInitialLoad ? (
    <BackgroundWrapper>
      <ConfigScreen onSaveConfig={handleSaveConfig} />
    </BackgroundWrapper>
  ) : (
    <BackgroundWrapper>
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">{statusMessage}</p>
        </div>
      </div>
    </BackgroundWrapper>
  );
}; 