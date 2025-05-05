"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useDocumentStore } from "@/hooks/useDocumentStore";
import { uploadFiles } from "@/services/api";
import { toast } from "react-hot-toast";

interface DemoFileUploaderProps {
  projectId: string | null;
}

export default function DemoFileUploader({ projectId }: DemoFileUploaderProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const { addDocuments, updateDocumentStatus } = useDocumentStore();
  
  // Create sample files for demo purposes
  const createSampleFiles = () => {
    // Create a sample markdown file
    const markdownContent = "# Sample Markdown\n\nThis is a sample markdown file.";
    const markdownFile = new File([markdownContent], "sample.md", { type: "text/markdown" });
    
    // Create a sample text file
    const textContent = "This is a sample text file.";
    const textFile = new File([textContent], "sample.txt", { type: "text/plain" });
    
    // Create a sample JSON file
    const jsonContent = JSON.stringify({ name: "Sample JSON", type: "JSON File" }, null, 2);
    const jsonFile = new File([jsonContent], "sample.json", { type: "application/json" });
    
    return [markdownFile, textFile, jsonFile];
  };
  
  const handleDemoUpload = async () => {
    if (!projectId) {
      toast.error("No project selected");
      return;
    }
    
    const sampleFiles = createSampleFiles();
    setIsUploading(true);
    setUploadProgress(0);
    
    try {
      // Generate a timestamp to ensure unique IDs
      const timestamp = Date.now();
      
      // Generate document IDs first
      const docIds = sampleFiles.map((file, index) => 
        `${timestamp}-${index}-${Math.random().toString(36).substring(2, 9)}`
      );
      
      // Add files to document store with specific IDs
      sampleFiles.forEach((file, index) => {
        const newDocument: any = {
          id: docIds[index],
          name: file.name,
          size: file.size,
          type: file.type,
          projectId,
          uploadedAt: new Date(),
          status: 'pending' as const,
          progress: 0,
          file,
        };
        
        // Add to store manually
        useDocumentStore.setState(state => ({
          documents: [...state.documents, newDocument]
        }));
        
        // Set initial status
        updateDocumentStatus(docIds[index], 'pending', 0);
      });
      
      // Log the current documents for debugging
      console.log('Documents in store:', useDocumentStore.getState().documents);
      
      // Simulate file upload with progress
      const result = await uploadFiles(
        projectId,
        sampleFiles,
        (file, progress) => {
          // Update progress in UI
          setUploadProgress(progress);
          
          // Find the document ID for this file
          const index = sampleFiles.findIndex(f => f.name === file.name);
          if (index !== -1) {
            // Update document status
            updateDocumentStatus(docIds[index], progress < 100 ? 'uploading' : 'success', progress);
          }
        }
      );
      
      if (result.success) {
        toast.success(result.message);
      } else if (result.failedFiles && result.failedFiles.length > 0) {
        toast.error(`Failed to upload ${result.failedFiles.length} files`);
      }
    } catch (error) {
      toast.error("Error uploading files");
      console.error("Upload error:", error);
    } finally {
      setIsUploading(false);
      // Reset progress after a delay
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };
  
  return (
    <div className="space-y-4 mt-4 p-4 border border-dashed rounded-md">
      <h3 className="text-sm font-medium">Demo File Upload</h3>
      <p className="text-sm text-muted-foreground">
        Click the button below to simulate uploading sample files.
      </p>
      
      <div className="flex items-center justify-between">
        <div className="flex-1 mr-4">
          {isUploading && (
            <div className="space-y-1">
              <Progress value={uploadProgress} className="h-2" />
              <p className="text-xs text-muted-foreground">
                Uploading... {uploadProgress.toFixed(0)}%
              </p>
            </div>
          )}
        </div>
        <Button 
          onClick={handleDemoUpload} 
          disabled={isUploading}
          className="min-w-32"
        >
          {isUploading ? "Uploading..." : "Upload Sample Files"}
        </Button>
      </div>
    </div>
  );
}
