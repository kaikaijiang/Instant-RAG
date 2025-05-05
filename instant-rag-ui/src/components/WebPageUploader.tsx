"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import toast from "react-hot-toast";
import { uploadWebPage } from "@/services/api";

interface WebPageUploaderProps {
  projectId: string;
}

export default function WebPageUploader({ projectId }: WebPageUploaderProps) {
  const [url, setUrl] = useState<string>("");
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [previewError, setPreviewError] = useState<boolean>(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Handle URL input change
  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
    setPreviewError(false);
  };

  // Handle iframe load error
  const handleIframeError = () => {
    setPreviewError(true);
  };

  // Handle web page upload
  const handleUpload = async () => {
    if (!url) {
      toast.error("Please enter a URL");
      return;
    }

    // Validate URL format
    try {
      new URL(url);
    } catch (error) {
      toast.error("Please enter a valid URL");
      return;
    }

    setIsUploading(true);
    const toastId = toast.loading("Uploading web page...");

    try {
      const result = await uploadWebPage(projectId, url, false);
      
      if (result.status === "success") {
        toast.success(`Upload complete: ${result.chunks_created} chunks created`, { id: toastId });
        setUrl("");
        setPreviewError(false);
      } else {
        toast.error("Upload failed", { id: toastId });
      }
    } catch (error) {
      console.error("Error uploading web page:", error);
      toast.error(`Upload failed: ${error instanceof Error ? error.message : "Unknown error"}`, { id: toastId });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col space-y-2">
        <Label htmlFor="url-input">Web Page URL</Label>
        <div className="flex space-x-2">
          <Input
            id="url-input"
            placeholder="https://example.com"
            value={url}
            onChange={handleUrlChange}
            disabled={isUploading}
          />
          <Button 
            onClick={handleUpload} 
            disabled={!url || isUploading}
            className="whitespace-nowrap"
          >
            {isUploading ? "Uploading..." : "Upload"}
          </Button>
        </div>
      </div>

      {url && (
        <Card className="mt-4 overflow-hidden">
          <CardContent className="p-0">
            {previewError ? (
              <div className="h-[300px] flex items-center justify-center bg-muted">
                <p className="text-muted-foreground">Cannot preview this page</p>
              </div>
            ) : (
              <div className="relative h-[300px] w-full">
                <iframe
                  ref={iframeRef}
                  src={url}
                  className="w-full h-full border-0"
                  onError={handleIframeError}
                  sandbox="allow-same-origin"
                  title="Web page preview"
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
