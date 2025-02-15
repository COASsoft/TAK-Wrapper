import React from 'react';
import { Loader2 } from 'lucide-react';
import { BackgroundWrapper } from './BackgroundWrapper';

interface LoadingStateProps {
  statusMessage: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ statusMessage }) => (
  <BackgroundWrapper>
    <div className="absolute inset-0 flex items-center justify-center">
      <div className="relative top-[260px] text-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
        <p className="text-muted-foreground">{statusMessage}</p>
      </div>
    </div>
  </BackgroundWrapper>
); 