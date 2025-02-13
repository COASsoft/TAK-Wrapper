import React, { HTMLAttributes } from 'react';
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "../ui/form"
import { Input } from "../ui/input"
import { Button } from "../ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../ui/card"
import { api } from "../lib/api"
import { BackgroundWrapper } from "./BackgroundWrapper"
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "../ui/tooltip"
import { CircleHelp } from "lucide-react"
declare module 'react' {
  interface InputHTMLAttributes<T> extends HTMLAttributes<T> {
    webkitdirectory?: string;
    directory?: string;
  }
}

const RESERVED_PORTS = [5432, 8443, 8446, 8089, 8444];

const formSchema = z.object({
  installDir: z.string().min(1, {
    message: "Install directory is required.",
  }),
  port: z.string().min(1, {
    message: "Port must be a number greater than or equal to 1024.",
  }).refine(value => {
    const portNumber = parseInt(value, 10);
    return portNumber >= 1024 && portNumber <= 49151;
  }, {
    message: "Port must be a number between 1024 and 49151.",
  }).refine(value => {
    const portNumber = parseInt(value, 10);
    return !RESERVED_PORTS.includes(portNumber);
  }, {
    message: `The following ports are reserved: ${RESERVED_PORTS.join(', ')}`,
  }),
})

interface ConfigScreenProps {
  onSaveConfig: (installDir: string, port: string) => void;
}

export const ConfigScreen: React.FC<ConfigScreenProps> = ({ onSaveConfig }) => {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      installDir: "",
      port: "",
    },
    mode: "onSubmit"
  })

  const [portAvailability, setPortAvailability] = React.useState<{ available: boolean; message: string } | null>(null);

  const checkPortAvailability = async (port: string) => {
    try {
      const portNumber = parseInt(port, 10);
      if (isNaN(portNumber)) return;
      
      const result = await api.checkPortAvailability(portNumber);
      setPortAvailability(result);
    } catch (error) {
      console.error('Error checking port availability:', error);
      setPortAvailability({ available: false, message: 'Error checking port availability' });
    }
  };

  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      // Check port availability before submitting
      const portNumber = parseInt(values.port, 10);
      const portCheck = portAvailability || await api.checkPortAvailability(portNumber);
      
      if (!portCheck.available) {
        form.setError('port', { message: portCheck.message });
        return;
      }
      
      onSaveConfig(values.installDir, values.port);
    } catch (error) {
      console.error('Error during form submission:', error);
      form.setError('port', { message: 'Error checking port availability' });
    }
  }

  const openDirectoryPicker = async () => {
    try {
      const result = await api.selectDirectory();
      if (result.path) {
        form.setValue('installDir', result.path);
      }
    } catch (error) {
      console.error('Failed to open directory picker:', error);
    }
  };

  return (
    <TooltipProvider>
      <BackgroundWrapper>
        <div className="container mx-auto px-4 flex items-center justify-center min-h-screen">
          <Card className="w-full max-w-xl border-border bg-card">
            <CardHeader>
              <CardTitle className="text-card-foreground">TAK Manager Configuration</CardTitle>
              <CardDescription className="text-muted-foreground">
                Please configure your TAK Server installation settings.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                  <FormField
                    control={form.control}
                    name="installDir"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-foreground flex items-center">
                          TAK Server Install Directory
                          <div className="ml-2">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <CircleHelp className="h-4 w-4 text-muted-foreground hover:text-foreground cursor-help" />
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>This is the directory where your TAK server will live. All config files and certificates will be stored here.</p>
                              </TooltipContent>
                            </Tooltip>
                          </div>
                        </FormLabel>
                        <div className="flex gap-2">
                          <FormControl>
                            <Input 
                              placeholder="/Users/john/Documents" 
                              className="bg-background border-input text-foreground placeholder:text-muted-foreground" 
                              {...field} 
                            />
                          </FormControl>
                          <Button 
                            type="button"
                            variant="outline"
                            className="shrink-0 border-input bg-background hover:bg-accent hover:text-accent-foreground"
                            onClick={openDirectoryPicker}
                          >
                            Browse...
                          </Button>
                        </div>
                        <FormMessage className="text-destructive" />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="port"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-foreground flex items-center">
                          Backend Port
                          <div className="ml-2">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <CircleHelp className="h-4 w-4 text-muted-foreground hover:text-foreground cursor-help" />
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>The port number that TAK Manager will use for its backend service. Must be between 1024 and 49151. Using the default port 8989 is recommended.</p>
                              </TooltipContent>
                            </Tooltip>
                          </div>
                        </FormLabel>
                        <FormControl>
                          <Input 
                            placeholder="8989" 
                            className="bg-background border-input text-foreground placeholder:text-muted-foreground" 
                            {...field}
                            onChange={(e) => {
                              field.onChange(e);
                              checkPortAvailability(e.target.value);
                            }}
                          />
                        </FormControl>
                        <FormMessage className="text-destructive" />
                      </FormItem>
                    )}
                  />

                  <Button 
                    type="submit" 
                    className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
                  >
                    Save Configuration
                  </Button>
                </form>
              </Form>
            </CardContent>
          </Card>
        </div>
      </BackgroundWrapper>
    </TooltipProvider>
  );
}; 