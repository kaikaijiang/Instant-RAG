"use client";

import { useState, useCallback, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, File, X, AlertCircle, CheckCircle } from "lucide-react";
import { toast } from "react-hot-toast";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useDocumentStore } from "@/hooks/useDocumentStore";
import { uploadFiles } from "@/services/api";

interface DocumentUploaderProps {
  projectId: string | null;
}

export default function DocumentUploader({ projectId }: DocumentUploaderProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  const { addDocuments, updateDocumentStatus } = useDocumentStore();
  
  // Reset selected files when project changes
  useEffect(() => {
    setSelectedFiles([]);
    setIsUploading(false);
    setUploadProgress(0);
  }, [projectId]);
  
  const onDrop = useCallback((acceptedFiles: File[]) => {
    setSelectedFiles(prev => [...prev, ...acceptedFiles]);
  }, []);
  
  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/markdown': ['.md'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB max file size
  });
  
  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };
  
  const handleUpload = async () => {
    if (!projectId) {
      toast.error("No project selected");
      return;
    }
    
    if (selectedFiles.length === 0) {
      toast.error("No files selected");
      return;
    }
    
    setIsUploading(true);
    setUploadProgress(0);
    
    try {
      // Add files to document store
      addDocuments(projectId, selectedFiles);
      
      // Upload files to server
      const result = await uploadFiles(
        projectId,
        selectedFiles,
        (file, progress) => {
          // Update progress in UI
          setUploadProgress(progress);
        }
      );
      
      if (result.success) {
        toast.success(result.message);
        setSelectedFiles([]);
      } else if (result.failedFiles && result.failedFiles.length > 0) {
        toast.error(`Failed to upload ${result.failedFiles.length} files`);
        // Keep failed files in the list
        setSelectedFiles(prev => 
          prev.filter(file => result.failedFiles?.includes(file.name))
        );
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
  
  // Show file rejection errors
  useEffect(() => {
    if (fileRejections.length > 0) {
      fileRejections.forEach(({ file, errors }) => {
        errors.forEach(error => {
          if (error.code === 'file-too-large') {
            toast.error(`${file.name} is too large (max 10MB)`);
          } else if (error.code === 'file-invalid-type') {
            toast.error(`${file.name} has an invalid file type`);
          } else {
            toast.error(`${file.name}: ${error.message}`);
          }
        });
      });
    }
  }, [fileRejections]);
  
  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          isDragActive 
            ? "border-primary bg-primary/5" 
            : "border-border hover:border-primary/50 hover:bg-accent"
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
        <p className="text-sm text-muted-foreground mb-1">
          Drag & drop files here, or click to select files
        </p>
        <p className="text-xs text-muted-foreground">
          Supports PDF, Markdown, TXT, DOCX, PNG, and JPG (max 10MB)
        </p>
      </div>
      
      {selectedFiles.length > 0 && (
        <div className="space-y-4">
          <div className="bg-background border rounded-md p-3">
            <h4 className="text-sm font-medium mb-2">Selected Files ({selectedFiles.length})</h4>
            <ul className="space-y-2 max-h-48 overflow-y-auto">
              {selectedFiles.map((file, index) => (
                <li key={index} className="flex items-center justify-between text-sm p-2 rounded-md bg-accent/50">
                  <div className="flex items-center space-x-2 overflow-hidden">
                    <File className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                    <span className="truncate">{file.name}</span>
                    <span className="text-xs text-muted-foreground">
                      ({(file.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => removeFile(index)}
                    disabled={isUploading}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </li>
              ))}
            </ul>
          </div>
          
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
              onClick={handleUpload} 
              disabled={isUploading || selectedFiles.length === 0}
              className="min-w-24"
            >
              {isUploading ? "Uploading..." : "Upload Files"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
