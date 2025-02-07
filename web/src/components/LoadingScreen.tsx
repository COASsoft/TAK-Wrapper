import React from 'react';

interface LoadingScreenProps {
  message?: string;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({ 
  message = 'Starting TAK Manager...' 
}) => {
  return (
    <div className="container">
      <div className="min-h-screen flex flex-col items-center justify-center space-y-6">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        <h2 className="text-xl text-muted-foreground">
          {message}
        </h2>
      </div>
    </div>
  );
}; 