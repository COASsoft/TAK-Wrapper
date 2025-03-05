import React from 'react';
import { Button } from '../ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { BackgroundWrapper } from './BackgroundWrapper';
import { ScrollArea } from '../ui/scroll-area';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface UpdatePromptProps {
  currentVersion: string;
  latestVersion: string;
  releaseNotes: string;
  onUpdate: () => void;
  onSkip: () => void;
}

interface CodeProps extends React.HTMLProps<HTMLElement> {
  inline?: boolean;
}

export const UpdatePrompt: React.FC<UpdatePromptProps> = ({ 
  currentVersion, 
  latestVersion,
  releaseNotes,
  onUpdate, 
  onSkip 
}) => (
  <BackgroundWrapper>
    <div className="container mx-auto px-4 flex items-center justify-center min-h-screen">
      <Card className="w-full max-w-xl">
        <CardHeader className="space-y-4">
          <div>
            <CardTitle>Update Available</CardTitle>
            <CardDescription>
              Version {latestVersion} is now available. You are currently running version {currentVersion}.
            </CardDescription>
          </div>
          {releaseNotes && (
            <div>
              <h4 className="text-sm font-medium mb-2">Release Notes:</h4>
              <ScrollArea className="h-[200px] w-full rounded-md border p-4 bg-muted/20">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      // Override heading styles to be smaller
                      h1: ({node, ...props}) => <h3 className="text-lg font-bold mt-4 mb-2" {...props} />,
                      h2: ({node, ...props}) => <h4 className="text-base font-semibold mt-3 mb-2" {...props} />,
                      h3: ({node, ...props}) => <h5 className="text-sm font-semibold mt-2 mb-1" {...props} />,
                      // Style links
                      a: ({node, ...props}) => <a className="text-primary hover:underline" {...props} />,
                      // Style lists
                      ul: ({node, ...props}) => <ul className="list-disc list-inside my-2" {...props} />,
                      ol: ({node, ...props}) => <ol className="list-decimal list-inside my-2" {...props} />,
                      // Style code blocks
                      code: ({inline, ...props}: CodeProps) => 
                        inline ? 
                          <code className="bg-secondary/20 rounded px-1" {...props} /> :
                          <code className="block bg-secondary/20 rounded p-2 my-2" {...props} />,
                    }}
                  >
                    {releaseNotes}
                  </ReactMarkdown>
                </div>
              </ScrollArea>
            </div>
          )}
        </CardHeader>
        <CardContent className="space-y-2">
          <Button 
            onClick={onUpdate}
            className="w-full"
            variant="primary"
          >
            Update Now
          </Button>
          <Button 
            onClick={onSkip}
            className="w-full"
            variant="outline"
          >
            Skip Update
          </Button>
        </CardContent>
      </Card>
    </div>
  </BackgroundWrapper>
); 