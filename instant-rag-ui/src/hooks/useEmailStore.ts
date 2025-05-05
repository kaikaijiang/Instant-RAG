import { create } from 'zustand';
import { connectToEmailServer, summarizeEmails } from '@/services/api';
import { useProjectStore } from './useProjectStore';

export interface EmailSettings {
  imapServer: string;
  emailAddress: string;
  password: string;
  senderFilter: string;
  subjectKeywords: string;
  startDate: string | null;
  endDate: string | null;
}

export interface ProcessingStatus {
  uploadingDocuments: boolean;
  embeddingDocuments: boolean;
  fetchingEmails: boolean;
  summarizingEmails: boolean;
}

export interface EmailSummary {
  id: string;
  summary: string;
  timestamp: Date;
}

export interface FetchedEmail {
  subject: string;
  timestamp: Date;
}

interface EmailState {
  emailSettings: EmailSettings;
  isConnecting: boolean;
  connectionError: string | null;
  processingStatus: ProcessingStatus;
  emailSummaries: EmailSummary[];
  fetchedEmails: FetchedEmail[];
  updateEmailSettings: (settings: Partial<EmailSettings>) => void;
  setIsConnecting: (isConnecting: boolean) => void;
  setConnectionError: (error: string | null) => void;
  setProcessingStatus: (status: Partial<ProcessingStatus>) => void;
  addEmailSummary: (summary: EmailSummary) => void;
  setFetchedEmails: (emails: FetchedEmail[]) => void;
  summarizeEmails: () => Promise<EmailSummary>;
}

const initialEmailSettings: EmailSettings = {
  imapServer: '',
  emailAddress: '',
  password: '',
  senderFilter: '',
  subjectKeywords: '',
  startDate: null,
  endDate: null,
};

const initialProcessingStatus: ProcessingStatus = {
  uploadingDocuments: false,
  embeddingDocuments: false,
  fetchingEmails: false,
  summarizingEmails: false,
};

export const useEmailStore = create<EmailState>((set, get) => ({
  emailSettings: initialEmailSettings,
  isConnecting: false,
  connectionError: null,
  processingStatus: initialProcessingStatus,
  emailSummaries: [],
  fetchedEmails: [],
  
  updateEmailSettings: (settings) => set((state) => ({
    emailSettings: {
      ...state.emailSettings,
      ...settings,
    },
  })),
  
  setIsConnecting: (isConnecting) => set({
    isConnecting,
  }),
  
  setConnectionError: (error) => set({
    connectionError: error,
  }),
  
  setProcessingStatus: (status) => set((state) => ({
    processingStatus: {
      ...state.processingStatus,
      ...status,
    },
  })),
  
  addEmailSummary: (summary) => set((state) => ({
    emailSummaries: [...state.emailSummaries, summary],
  })),
  
  setFetchedEmails: (emails) => set({
    fetchedEmails: emails,
  }),
  
  summarizeEmails: async () => {
    // Set summarizing status to true
    get().setProcessingStatus({ summarizingEmails: true });
    
    try {
      // Get the selected project ID from the project store
      const { selectedProjectId } = useProjectStore.getState();
      
      // If no project is selected, show an error message
      if (!selectedProjectId) {
        throw new Error('No project selected. Please select a project first.');
      }
      
      // Call the real API function with the selected project ID
      const result = await summarizeEmails(selectedProjectId);
      
      // Process each summary in the response
      if (result.summaries && result.summaries.length > 0) {
        // Take the first summary for now (we can enhance this to handle multiple summaries later)
        const firstSummary = result.summaries[0];
        
        // Create an EmailSummary object
        const emailSummary: EmailSummary = {
          id: firstSummary.id,
          summary: firstSummary.summary,
          timestamp: new Date()
        };
        
        // Add the summary to the store
        get().addEmailSummary(emailSummary);
        
        // Set summarizing status to false
        get().setProcessingStatus({ summarizingEmails: false });
        
        return emailSummary;
      } else {
        // No summaries returned
        const emptySummary: EmailSummary = {
          id: Math.random().toString(36).substring(2, 15),
          summary: "No email summaries were generated.",
          timestamp: new Date()
        };
        
        // Set summarizing status to false
        get().setProcessingStatus({ summarizingEmails: false });
        
        return emptySummary;
      }
    } catch (error) {
      console.error("Error summarizing emails:", error);
      // Set summarizing status to false
      get().setProcessingStatus({ summarizingEmails: false });
      throw error;
    }
  },
}));
