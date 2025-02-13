import React, { useState, useEffect } from 'react';
import { ConfigScreen } from './components/ConfigScreen';
import { LoadingState } from './components/LoadingState';
import { ErrorState } from './components/ErrorState';
import { DockerInstallPrompt } from './components/DockerInstallPrompt';
import { BackgroundWrapper } from './components/BackgroundWrapper';
import { api } from './lib/api';
import type {} from './types/global';

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
          const config = await api.getConfig();
          if (config.TAK_SERVER_INSTALL_DIR && config.BACKEND_PORT) {
            setIsInitialLoad(false);
            setIsContainerStarting(true);
            setStatusMessage('Starting TAK Manager container...');
            const result = await api.startContainer();
            if (!result.success) {
              setError(result.error ?? 'Unknown error occurred while starting container');
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
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('An unexpected error occurred while checking Docker status');
      }
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
      const result = await api.openExternalUrl('https://www.docker.com/products/docker-desktop/');
      if (!result.success) {
        setError('Failed to open Docker installation page');
      }
    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('Failed to open Docker installation page');
      }
      console.error('Failed to open Docker installation page:', error);
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
          setError(containerResult.error ?? 'Unknown error occurred while starting container');
        } else if (containerResult.port) {
          setStatusMessage('Opening TAK Manager...');
          console.log('Opening TAK Manager on port:', containerResult.port);
          window.pywebview.api.navigate(`http://localhost:${containerResult.port}`);
        }
      } else {
        setError(result.error ?? 'Unknown error occurred while saving configuration');
      }
    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('An unexpected error occurred while saving configuration');
      }
      console.error('Failed to save configuration:', error);
    } finally {
      setIsLoading(false);
      setIsContainerStarting(false);
    }
  };

  if (isLoading || isContainerStarting) {
    return <LoadingState statusMessage={statusMessage} />;
  }

  if (error) {
    return <ErrorState error={error} onRetry={checkDocker} />;
  }

  if (isDockerInstalled === false) {
    return <DockerInstallPrompt onInstall={handleInstallDocker} onCheckAgain={checkDocker} />;
  }

  if (isDockerRunning === false) {
    return <LoadingState statusMessage={statusMessage} />;
  }

  return isInitialLoad ? (
    <BackgroundWrapper>
      <ConfigScreen onSaveConfig={handleSaveConfig} />
    </BackgroundWrapper>
  ) : (
    <LoadingState statusMessage={statusMessage} />
  );
}; 