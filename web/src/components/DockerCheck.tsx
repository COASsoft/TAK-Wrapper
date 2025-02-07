import React, { useEffect, useState } from 'react';
import { Button } from '../ui/button';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Loader2 } from 'lucide-react';

const DOCKER_CHECK_INTERVAL = 5000; // Check every 5 seconds

export const DockerCheck: React.FC = () => {
    const [isInstalled, setIsInstalled] = useState<boolean | null>(null);
    const [isChecking, setIsChecking] = useState(true);

    const checkDocker = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/check-docker');
            const data = await response.json();
            setIsInstalled(data.installed);
        } catch (error) {
            console.error('Failed to check Docker:', error);
        } finally {
            setIsChecking(false);
        }
    };

    useEffect(() => {
        checkDocker();
        const interval = setInterval(checkDocker, DOCKER_CHECK_INTERVAL);
        return () => clearInterval(interval);
    }, []);

    const handleInstallDocker = () => {
        let installUrl = '';
        const platform = window.navigator.platform.toLowerCase();
        
        if (platform.includes('mac')) {
            installUrl = 'https://docs.docker.com/desktop/install/mac-install/';
        } else if (platform.includes('win')) {
            installUrl = 'https://docs.docker.com/desktop/install/windows-install/';
        } else {
            installUrl = 'https://docs.docker.com/engine/install/';
        }
        
        window.open(installUrl, '_blank');
    };

    if (isChecking) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (!isInstalled) {
        return (
            <div className="flex flex-col items-center justify-center h-screen p-4">
                <Alert className="max-w-lg mb-4">
                    <AlertTitle>Docker Not Detected</AlertTitle>
                    <AlertDescription>
                        Docker and Docker Compose are required to run TAK Manager. 
                        Please install Docker and restart the application.
                    </AlertDescription>
                </Alert>
                <Button onClick={handleInstallDocker}>
                    Install Docker
                </Button>
            </div>
        );
    }

    return null; // Docker is installed, don't show anything
}; 