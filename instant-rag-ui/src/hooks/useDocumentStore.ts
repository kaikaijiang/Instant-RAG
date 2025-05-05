import { create } from 'zustand';

export interface DocumentFile {
  id: string;
  name: string;
  size: number;
  type: string;
  projectId: string;
  uploadedAt: Date;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  file: File;
}

interface DocumentState {
  documents: DocumentFile[];
  isUploading: boolean;
  uploadProgress: number;
  
  // Actions
  addDocument: (projectId: string, file: File) => void;
  addDocuments: (projectId: string, files: File[]) => void;
  removeDocument: (id: string) => void;
  clearDocuments: (projectId: string) => void;
  updateDocumentStatus: (id: string, status: DocumentFile['status'], progress?: number) => void;
  setUploading: (isUploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  getProjectDocuments: (projectId: string) => DocumentFile[];
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  isUploading: false,
  uploadProgress: 0,
  
  addDocument: (projectId, file) => {
    const newDocument: DocumentFile = {
      id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      name: file.name,
      size: file.size,
      type: file.type,
      projectId,
      uploadedAt: new Date(),
      status: 'pending' as const,
      progress: 0,
      file,
    };
    
    set(state => ({
      documents: [...state.documents, newDocument]
    }));
    
    return newDocument.id;
  },
  
  addDocuments: (projectId, files) => {
    const newDocuments: DocumentFile[] = files.map(file => ({
      id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      name: file.name,
      size: file.size,
      type: file.type,
      projectId,
      uploadedAt: new Date(),
      status: 'pending' as const,
      progress: 0,
      file,
    }));
    
    set(state => ({
      documents: [...state.documents, ...newDocuments]
    }));
  },
  
  removeDocument: (id) => {
    set(state => ({
      documents: state.documents.filter(doc => doc.id !== id)
    }));
  },
  
  clearDocuments: (projectId) => {
    set(state => ({
      documents: state.documents.filter(doc => doc.projectId !== projectId)
    }));
  },
  
  updateDocumentStatus: (id, status, progress = 0) => {
    set(state => ({
      documents: state.documents.map(doc => 
        doc.id === id 
          ? { ...doc, status, progress: progress || doc.progress } 
          : doc
      )
    }));
  },
  
  setUploading: (isUploading) => {
    set({ isUploading });
  },
  
  setUploadProgress: (progress) => {
    set({ uploadProgress: progress });
  },
  
  getProjectDocuments: (projectId) => {
    return get().documents.filter(doc => doc.projectId === projectId);
  },
}));
