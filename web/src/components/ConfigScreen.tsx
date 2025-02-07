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

declare module 'react' {
  interface InputHTMLAttributes<T> extends HTMLAttributes<T> {
    webkitdirectory?: string;
    directory?: string;
  }
}

const formSchema = z.object({
  installDir: z.string().min(1, {
    message: "Install directory is required.",
  }),
  port: z.string().min(1, {
    message: "Port is required.",
  }).regex(/^\d+$/, {
    message: "Please enter a valid port number.",
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
  })

  function onSubmit(values: z.infer<typeof formSchema>) {
    onSaveConfig(values.installDir, values.port);
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
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-md mx-auto mt-8 mb-4">
          <Card className="border-border bg-card">
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
                        <FormLabel className="text-foreground">TAK Server Install Directory</FormLabel>
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
                        <FormLabel className="text-foreground">Backend Port</FormLabel>
                        <FormControl>
                          <Input 
                            placeholder="8989" 
                            className="bg-background border-input text-foreground placeholder:text-muted-foreground" 
                            {...field} 
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
      </div>
    </div>
  );
}; 