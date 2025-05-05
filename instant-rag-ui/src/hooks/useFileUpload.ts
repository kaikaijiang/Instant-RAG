import { useState, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import { uploadFile } from '@/services/api';

interface UseFileUploadOptions {
  onSuccess?: (file: File) => void;
  onError?: (error: Error, file: File) => void;
}

export function useFileUpload(projectId: string | null, options: UseFileUploadOptions = {}) {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const uploadFiles = useCallback(async (files: File[]) => {
    if (!projectId) {
      toast.error('No project selected. Please select or create a project first.');
      return;
    }
    
    setIsUploading(true);
    setProgress(0);
    
    const totalFiles = files.length;
    let completedFiles = 0;
    
    try {
      for (const file of files) {
        try {
          // Simulate progress updates
          const progressInterval = setInterval(() => {
            setProgress(prev => {
              const newProgress = prev + Math.random() * 10;
              return newProgress > 95 ? 95 : newProgress;
            });
          }, 200);
          
          // Upload the file
          const result = await uploadFile(projectId, file);
          
          clearInterval(progressInterval);
          
          if (result.success) {
            completedFiles++;
            setProgress((completedFiles / totalFiles) * 100);
            options.onSuccess?.(file);
          } else {
            throw new Error(result.message);
          }
        } catch (error) {
          options.onError?.(error as Error, file);
          toast.error(`Failed to upload ${file.name}`);
        }
      }
      
      setProgress(100);
      if (completedFiles === totalFiles) {
        toast.success(`Successfully uploaded ${completedFiles} file(s)`);
      } else {
        toast.success(`Uploaded ${completedFiles} of ${totalFiles} file(s)`);
      }
    } finally {
      setIsUploading(false);
      // Reset progress after a delay
      setTimeout(() => setProgress(0), 2000);
    }
  }, [projectId, options]);
  
  return {
    isUploading,
    progress,
    uploadFiles,
  };
}
