"use client";

import { useState, useEffect } from "react";
import { File, Trash2, AlertCircle, CheckCircle, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDocumentStore, DocumentFile } from "@/hooks/useDocumentStore";
import { Progress } from "@/components/ui/progress";

interface DocumentListProps {
  projectId: string | null;
}

export default function DocumentList({ projectId }: DocumentListProps) {
  const { documents, removeDocument } = useDocumentStore();
  const [projectDocuments, setProjectDocuments] = useState<DocumentFile[]>([]);
  
  useEffect(() => {
    if (projectId) {
      const docs = documents.filter(doc => doc.projectId === projectId);
      setProjectDocuments(docs);
      console.log('Project documents:', docs);
    } else {
      setProjectDocuments([]);
    }
  }, [projectId, documents]);
  
  if (projectDocuments.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No documents uploaded yet.</p>
        <p className="text-sm">Upload documents to start using your RAG system.</p>
      </div>
    );
  }
  
  const getStatusIcon = (status: DocumentFile['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-muted-foreground" />;
      case 'uploading':
        return <Clock className="h-4 w-4 text-primary animate-pulse" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-destructive" />;
      default:
        return null;
    }
  };
  
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium">Uploaded Documents ({projectDocuments.length})</h3>
      <ul className="space-y-2 max-h-[400px] overflow-y-auto">
        {projectDocuments.map((doc) => (
          <li 
            key={doc.id} 
            className="flex items-center justify-between p-3 rounded-md bg-accent/50 group"
          >
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="flex-shrink-0">
                {getStatusIcon(doc.status)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{doc.name}</p>
                <p className="text-xs text-muted-foreground">
                  {new Date(doc.uploadedAt).toLocaleString()} • {(doc.size / 1024).toFixed(1)} KB
                </p>
                {doc.status === 'uploading' && (
                  <Progress value={doc.progress} className="h-1 mt-1" />
                )}
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={() => removeDocument(doc.id)}
            >
              <Trash2 className="h-4 w-4 text-muted-foreground" />
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}
