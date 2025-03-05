import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Alert, AlertTitle, AlertDescription } from '../ui/alert';
import { BackgroundWrapper } from './BackgroundWrapper';

interface DockerInstallPromptProps {
  onInstall: () => void;
  onCheckAgain: () => void;
}

export const DockerInstallPrompt: React.FC<DockerInstallPromptProps> = ({ onInstall, onCheckAgain }) => {
  const [loadingCheckAgain, setLoadingCheckAgain] = useState(false);

  const handleCheckAgain = async () => {
    setLoadingCheckAgain(true);
    await onCheckAgain();
    setLoadingCheckAgain(false);
  };

  return (
    <BackgroundWrapper>
      <div className="container mx-auto px-4 flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-xl">
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
                Please install Docker Desktop to continue using TAK Manager. the link below will direct you to the Docker website. Download docker and complete setup steps then return to the application once completed.
              </AlertDescription>
            </Alert>
            <div className="flex flex-col space-y-2">
              <Button 
                onClick={onInstall}
                className="w-full"
                variant="primary"
              >
                Install Docker
              </Button>
              <Button 
                onClick={handleCheckAgain}
                className="w-full"
                variant="outline"
                loading={loadingCheckAgain}
                loadingText="Checking..."
              >
                Check Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </BackgroundWrapper>
  );
}; 