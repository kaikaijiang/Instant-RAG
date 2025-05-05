"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useProjectStore } from "@/hooks/useProjectStore";
import { useEmailStore } from "@/hooks/useEmailStore";
import DocumentUploader from "@/components/DocumentUploader";
import DocumentList from "@/components/DocumentList";
import WebPageUploader from "@/components/WebPageUploader";
import EmailSetup from "@/components/EmailSetup";
import ProcessingStatus from "@/components/ProcessingStatus";
import EmailSummarization from "@/components/EmailSummarization";
import Chat from "@/components/Chat";

interface ProjectWorkspaceProps {
  projectId: string | null;
}

export default function ProjectWorkspace({ projectId }: ProjectWorkspaceProps) {
  const { projects } = useProjectStore();
  const { processingStatus } = useEmailStore();
  
  // Track completed steps
  const [completedSteps, setCompletedSteps] = useState({
    uploadingDocuments: false,
    embeddingDocuments: false,
    fetchingEmails: false,
    summarizingEmails: false,
  });
  
  // Find the current project by ID
  const currentProject = projectId 
    ? projects.find(project => project.id === projectId) 
    : null;
    
  // Update completed steps when processing status changes
  useEffect(() => {
    if (!processingStatus.uploadingDocuments && completedSteps.uploadingDocuments === false) {
      setCompletedSteps(prev => ({ ...prev, uploadingDocuments: true }));
    }
    
    if (!processingStatus.embeddingDocuments && completedSteps.embeddingDocuments === false) {
      setCompletedSteps(prev => ({ ...prev, embeddingDocuments: true }));
    }
    
    if (!processingStatus.fetchingEmails && completedSteps.fetchingEmails === false) {
      setCompletedSteps(prev => ({ ...prev, fetchingEmails: true }));
    }
    
    if (!processingStatus.summarizingEmails && completedSteps.summarizingEmails === false) {
      setCompletedSteps(prev => ({ ...prev, summarizingEmails: true }));
    }
  }, [processingStatus, completedSteps]);

  if (!projectId) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Welcome to Instant-RAG</CardTitle>
            <CardDescription>
              Create a project to get started with your AI-powered RAG system.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Select or create a project from the sidebar to begin uploading documents and setting up your RAG system.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-full p-6 overflow-auto" style={{ maxHeight: "100vh" }}>
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">
          {currentProject?.name || "Project Workspace"}
        </h1>
        <p className="text-muted-foreground">
          Upload documents, configure settings, and chat with your AI assistant.
        </p>
      </div>

      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Email Setup</h2>
        <EmailSetup projectId={projectId} />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Processing Feedback</CardTitle>
            <CardDescription>
              Track the status of your document and email processing.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ProcessingStatus 
              status={processingStatus} 
              completedSteps={completedSteps} 
            />
          </CardContent>
        </Card>
        
        <EmailSummarization projectId={projectId} />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle>Documents</CardTitle>
            <CardDescription>
              Add PDF, Markdown, or image files to your RAG system.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 flex-1">
            <DocumentUploader projectId={projectId} />
            
            <div className="border-t pt-4 mt-4">
              <h3 className="text-sm font-medium mb-2">Web Page Upload</h3>
              <WebPageUploader projectId={projectId} />
            </div>
            
            <div className="border-t pt-4 mt-4">
              <h3 className="text-sm font-medium mb-2">Uploaded Documents</h3>
              <DocumentList projectId={projectId} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Project Settings</CardTitle>
            <CardDescription>
              Configure your RAG system settings.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Configure embedding models, vector stores, and other settings for your project.
            </p>
            <Button variant="outline" className="w-full">
              Configure Settings
            </Button>
          </CardContent>
        </Card>
      </div>


      <Card className="flex flex-col" style={{ minHeight: "500px" }}>
        <CardHeader>
          <CardTitle>Chat</CardTitle>
          <CardDescription>
            Interact with your AI assistant using your uploaded documents.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-1 p-0">
          <Chat projectId={projectId} />
        </CardContent>
      </Card>
    </div>
  );
}
