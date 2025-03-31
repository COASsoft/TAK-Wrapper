import React, { useState, useEffect } from 'react';
import { ConfigScreen } from './components/ConfigScreen';
import { LoadingState } from './components/LoadingState';
import { ErrorState } from './components/ErrorState';
import { DockerInstallPrompt } from './components/DockerInstallPrompt';
import { UpdatePrompt } from './components/UpdatePrompt';
import { BackgroundWrapper } from './components/BackgroundWrapper';
import { api } from './lib/api';
import type {} from './types/global';

// Define constants for URLs
const GITHUB_RELEASES_URL = 'https://github.com/JShadowNull/TAK-Manager/releases/latest';
const DOCKER_DESKTOP_URL = 'https://www.docker.com/products/docker-desktop/';

export const App: React.FC = () => {
  const [isDockerInstalled, setIsDockerInstalled] = useState<boolean | null>(null);
  const [isDockerRunning, setIsDockerRunning] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isContainerStarting, setIsContainerStarting] = useState(false);
  const [isApiReady, setIsApiReady] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [statusMessage, setStatusMessage] = useState<string>('Initializing...');
  const [updateInfo, setUpdateInfo] = useState<{
    hasUpdate: boolean;
    currentVersion: string;
    latestVersion: string;
    releaseNotes: string;
    checkComplete: boolean;
  } | null>({ 
    hasUpdate: false, 
    currentVersion: '', 
    latestVersion: '', 
    releaseNotes: '',
    checkComplete: false 
  });

  // Add retry count state
  const [updateCheckRetries, setUpdateCheckRetries] = useState(0);
  const MAX_RETRIES = 3;

  // Add docker check attempts state
  const [dockerCheckAttempts, setDockerCheckAttempts] = useState(0);
  const MAX_DOCKER_CHECK_ATTEMPTS = 10;  // Maximum number of attempts to check Docker status

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

  const checkForUpdates = async () => {
    try {
      // Check network connectivity first
      setStatusMessage('Checking network connectivity...');
      const isConnected = await api.checkNetwork();
      
      if (!isConnected) {
        console.log('No network connectivity, skipping update check');
        setUpdateInfo({
          hasUpdate: false,
          currentVersion: 'Unknown',
          latestVersion: 'Unknown',
          releaseNotes: '',
          checkComplete: true
        });
        return;
      }

      setStatusMessage(`Checking for updates${updateCheckRetries > 0 ? ` (Attempt ${updateCheckRetries + 1}/${MAX_RETRIES})` : ''}...`);
      const updateData = await api.checkForUpdate();
      
      if (!updateData.error) {
        setUpdateInfo({
          hasUpdate: updateData.hasUpdate,
          currentVersion: updateData.currentVersion,
          latestVersion: updateData.latestVersion,
          releaseNotes: updateData.releaseNotes,
          checkComplete: true
        });
      } else {
        throw new Error(updateData.error);
      }
    } catch (error) {
      console.error('Failed to check for updates:', error);
      
      if (updateCheckRetries < MAX_RETRIES - 1) {
        // Only retry if we have network connectivity
        const isConnected = await api.checkNetwork();
        if (isConnected) {
          // Increment retry count and try again after a delay
          setUpdateCheckRetries(prev => prev + 1);
          setTimeout(checkForUpdates, 2000); // Wait 2 seconds before retrying
        } else {
          // No network connectivity, skip update check
          console.log('No network connectivity, skipping update check');
          setUpdateInfo({
            hasUpdate: false,
            currentVersion: 'Unknown',
            latestVersion: 'Unknown',
            releaseNotes: '',
            checkComplete: true
          });
        }
      } else {
        // Max retries reached, continue with application
        console.log('Max retries reached for update check, continuing with application');
        setUpdateInfo(prev => prev ? {
          ...prev,
          hasUpdate: false,
          checkComplete: true,
        } : null);
      }
    }
  };

  const handleUpdate = () => {
    // Open the release page in the default browser
    if (window.pywebview && window.pywebview.api) {
      api.openExternalUrl(GITHUB_RELEASES_URL);
    }
  };

  const handleSkipUpdate = () => {
    setUpdateInfo(prev => prev ? { ...prev, hasUpdate: false } : null);
  };

  const checkDocker = async () => {
    if (!isApiReady || !updateInfo?.checkComplete) return;
    
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
          setDockerCheckAttempts(0);  // Reset attempts when Docker is running
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
        } else if (dockerCheckAttempts < MAX_DOCKER_CHECK_ATTEMPTS) {
          // If Docker is not running and we haven't exceeded max attempts, retry after delay
          setStatusMessage(`Waiting for Docker to start`);
          setDockerCheckAttempts(prev => prev + 1);
          setTimeout(checkDocker, 3000);  // Retry after 3 seconds
        } else {
          // If we've exceeded max attempts, show error
          setError('Docker is not running after multiple attempts. Please ensure Docker Desktop is started and try again.');
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
      if (isDockerRunning) {  // Only set loading to false if Docker is running
        setIsLoading(false);
        setIsContainerStarting(false);
      }
    }
  };

  // First effect: Check for updates when API is ready
  useEffect(() => {
    if (isApiReady) {
      setUpdateCheckRetries(0); // Reset retry count
      checkForUpdates();
    }
  }, [isApiReady]);

  // Second effect: Only proceed with Docker check after update check is complete
  useEffect(() => {
    if (updateInfo?.checkComplete && !updateInfo.hasUpdate) {
      checkDocker();
    }
  }, [isApiReady, updateInfo?.checkComplete, updateInfo?.hasUpdate]);

  useEffect(() => {
    return () => {
      // Cleanup: stop container when component unmounts
      api.stopContainer().catch(console.error);
    };
  }, []);

  const handleInstallDocker = async () => {
    if (!isApiReady) return;
    
    try {
      const result = await api.openExternalUrl(DOCKER_DESKTOP_URL);
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

  // Show loading state while checking for updates
  if (!updateInfo?.checkComplete) {
    return <LoadingState statusMessage={statusMessage} />;
  }

  if (error) {
    return <ErrorState error={error} onRetry={checkDocker} />;
  }

  if (updateInfo?.hasUpdate && updateInfo?.checkComplete) {
    return (
      <UpdatePrompt
        currentVersion={updateInfo.currentVersion}
        latestVersion={updateInfo.latestVersion}
        releaseNotes={updateInfo.releaseNotes}
        onUpdate={handleUpdate}
        onSkip={handleSkipUpdate}
      />
    );
  }

  // Show loading state while checking Docker installation
  if (isDockerInstalled === null) {
    return <LoadingState statusMessage={statusMessage} />;
  }

  if (isDockerInstalled === false) {
    return <DockerInstallPrompt onInstall={handleInstallDocker} onCheckAgain={checkDocker} />;
  }

  // Show loading state while checking if Docker is running
  if (isDockerRunning === null) {
    return <LoadingState statusMessage={statusMessage} />;
  }

  if (isDockerRunning === false) {
    return <LoadingState statusMessage={statusMessage} />;
  }

  // Only show ConfigScreen when all previous checks are complete and it's initial load
  return isInitialLoad ? (
    <BackgroundWrapper>
      <ConfigScreen onSaveConfig={handleSaveConfig} />
    </BackgroundWrapper>
  ) : (
    <LoadingState statusMessage={statusMessage} />
  );
}; 