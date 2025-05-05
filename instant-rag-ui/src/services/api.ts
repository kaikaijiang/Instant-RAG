/**
 * This file contains API service functions for the Instant-RAG application.
 * It supports both real API calls to a backend server and mock implementations.
 */

import { Project } from "@/hooks/useProjectStore";
import { getSession, signOut } from "next-auth/react";
import { json } from "stream/consumers";
import { toast } from "@/hooks/use-toast";

// API Configuration
export const API_CONFIG = {
  // Base URL for the API - defaults to localhost:8000 if not set in environment
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // Set to true to use mock implementations instead of real API calls
  useMocks: process.env.NEXT_PUBLIC_USE_MOCK_API === 'true' || false,
  
  // Artificial delay for mock responses (in ms)
  mockDelay: 800
};

/**
 * Helper function to create a FormData object from files
 */
function createFormData(files: File[], projectId: string): FormData {
  const formData = new FormData();
  formData.append('project_id', projectId);
  
  files.forEach(file => {
    formData.append('files', file);
  });
  
  return formData;
}

/**
 * Function to upload a single file to the server
 */
export async function uploadFile(projectId: string, file: File): Promise<{ success: boolean; message: string }> {
  if (API_CONFIG.useMocks) {
    // Mock implementation
    await new Promise(resolve => setTimeout(resolve, API_CONFIG.mockDelay));
    
    return {
      success: true,
      message: `File ${file.name} uploaded successfully to project ${projectId}`,
    };
  } else {
    // Real API implementation
    try {
      const formData = createFormData([file], projectId);
      const session = await getSession();
      
      // Add authorization header if we have a token
      const headers: HeadersInit = {};
      if (session?.token) {
        headers['Authorization'] = `Bearer ${session.token}`;
      }
      
      const response = await fetch(`${API_CONFIG.baseUrl}/project/upload_docs`, {
        method: 'POST',
        headers,
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed with status: ${response.status}`);
      }
      
      const result = await response.json();
      return {
        success: true,
        message: result.message || `File ${file.name} uploaded successfully`,
      };
    } catch (error) {
      console.error('Error uploading file:', error);
      return {
        success: false,
        message: `Failed to upload ${file.name}: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
    }
  }
}

/**
 * Function to upload multiple files to the server
 */
export async function uploadFiles(
  projectId: string, 
  files: File[], 
  onProgress?: (file: File, progress: number) => void
): Promise<{ success: boolean; message: string; failedFiles?: string[] }> {
  if (API_CONFIG.useMocks) {
    // Mock implementation
    const failedFiles: string[] = [];
    
    // Process each file
    for (const file of files) {
      // Simulate progress updates
      for (let progress = 0; progress <= 100; progress += 10) {
        onProgress?.(file, progress);
        // Small delay to simulate network activity
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      // Randomly fail some uploads (10% chance)
      if (Math.random() < 0.1) {
        failedFiles.push(file.name);
      }
    }
    
    // Return result
    if (failedFiles.length === 0) {
      return {
        success: true,
        message: `All ${files.length} files uploaded successfully to project ${projectId}`,
      };
    } else {
      return {
        success: failedFiles.length < files.length,
        message: `${files.length - failedFiles.length} of ${files.length} files uploaded successfully to project ${projectId}`,
        failedFiles,
      };
    }
  } else {
    // Real API implementation
    try {
      const formData = createFormData(files, projectId);
      const session = await getSession();
      
      // Add authorization header if we have a token
      const headers: HeadersInit = {};
      if (session?.token) {
        headers['Authorization'] = `Bearer ${session.token}`;
      }
      
      // For real implementation, we'd use a proper upload library with progress
      // For simplicity, we'll just simulate progress here
      if (onProgress) {
        for (const file of files) {
          onProgress(file, 50); // Start at 50%
        }
      }
      
      const response = await fetch(`${API_CONFIG.baseUrl}/project/upload_docs`, {
        method: 'POST',
        headers,
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed with status: ${response.status}`);
      }
      
      // Update progress to 100% for all files
      if (onProgress) {
        for (const file of files) {
          onProgress(file, 100);
        }
      }
      
      const result = await response.json();
      return {
        success: true,
        message: result.message || `All files uploaded successfully`,
      };
    } catch (error) {
      console.error('Error uploading files:', error);
      return {
        success: false,
        message: `Failed to upload files: ${error instanceof Error ? error.message : 'Unknown error'}`,
        failedFiles: files.map(f => f.name),
      };
    }
  }
}

/**
 * Function to process a document
 */
export async function processDocument(projectId: string, documentId: string): Promise<{ success: boolean; message: string }> {
  if (API_CONFIG.useMocks) {
    // Mock implementation
    await new Promise(resolve => setTimeout(resolve, API_CONFIG.mockDelay * 2));
    
    return {
      success: true,
      message: `Document ${documentId} processed successfully for project ${projectId}`,
    };
  } else {
    // Real API implementation
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${API_CONFIG.baseUrl}/project/process_document`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          project_id: projectId,
          document_id: documentId,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Processing failed with status: ${response.status}`);
      }
      
      const result = await response.json();
      return {
        success: true,
        message: result.message || 'Document processed successfully',
      };
    } catch (error) {
      console.error('Error processing document:', error);
      return {
        success: false,
        message: `Failed to process document: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
    }
  }
}

/**
 * Helper function to get auth headers with token
 */
export async function getAuthHeaders(): Promise<HeadersInit> {
  const session = await getSession();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  if (session?.token) {
    headers['Authorization'] = `Bearer ${session.token}`;
  } else {
    console.error('No token found in session:', session);
  }
  
  return headers;
}

/**
 * Function to fetch projects from the server
 */
export async function fetchProjects(): Promise<Project[]> {
  if (API_CONFIG.useMocks) {
    // Mock implementation
    await new Promise(resolve => setTimeout(resolve, API_CONFIG.mockDelay));
    
    return [
      {
        id: '1',
        name: 'Sample Project 1',
        createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
      },
      {
        id: '2',
        name: 'Sample Project 2',
        createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
      },
    ];
  } else {
    // Real API implementation
    try {
      // Get auth headers with token
      const headers = await getAuthHeaders();
      
      // Log the request attempt
      const hasAuthHeader = 'Authorization' in headers;
      console.log('Fetching projects with auth header:', hasAuthHeader ? 'Yes' : 'No');
      
      const response = await fetch(`${API_CONFIG.baseUrl}/project/list`, {
        headers,
        // Add credentials to include cookies in the request
        credentials: 'include'
      });
      
      // Log the response status
      console.log('Projects fetch response status:', response.status);
      
      if (!response.ok) {
        // If we get a 401 Unauthorized error, it might be an authentication issue
        if (response.status === 401) {
          console.error('Authentication error when fetching projects. Token might be invalid or expired.');
          
          // Show a toast notification
          toast({
            variant: "destructive",
            title: "Authentication Error",
            description: "Your session has expired. Please log in again."
          });
          
          // Redirect to login page directly
          console.log("Redirecting to login page due to 401 error in fetchProjects");
          signOut({ callbackUrl: "/login", redirect: true });
          
          // Still throw the error for proper error handling in the calling code
          throw new Error(`Authentication failed when fetching projects: ${response.status}`);
        }
        
        throw new Error(`Failed to fetch projects with status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Projects data received:', data);
      
      // Handle different response formats
      // Some APIs return { projects: [...] } and others return the array directly
      const projectsArray = Array.isArray(data) ? data : data.projects || [];
      
      if (!Array.isArray(projectsArray)) {
        console.error('Unexpected API response format:', data);
        return [];
      }
      
      // Convert string dates to Date objects
      return projectsArray.map((project: any) => ({
        ...project,
        id: project.id || project._id || String(Date.now()), // Ensure we have an id
        name: project.name || 'Unnamed Project',
        createdAt: new Date(project.created_at || project.createdAt || Date.now()),
      }));
    } catch (error) {
      console.error('Error fetching projects:', error);
      // Rethrow the error so it can be handled by the caller
      throw error;
    }
  }
}

/**
 * Function to send a chat message to the AI
 */
export async function sendChatMessage(projectId: string, message: string, topK: number = 5): Promise<{ 
  id: string; 
  content: string; 
  timestamp: Date;
  isAi: boolean;
}> {
  if (API_CONFIG.useMocks) {
    // Mock implementation
    await new Promise(resolve => setTimeout(resolve, API_CONFIG.mockDelay * 2));
    
    return {
      id: Math.random().toString(36).substring(2, 15),
      content: `This is a mock AI response to: "${message}"`,
      timestamp: new Date(),
      isAi: true,
    };
  } else {
    // Real API implementation
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${API_CONFIG.baseUrl}/chat/query`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          project_id: projectId,
          question: message,
          top_k: topK, // Use the provided topK parameter
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Chat query failed with status: ${response.status}`);
      }
      
      const result = await response.json();
      
      return {
        id: Math.random().toString(36).substring(2, 15), // Generate a random ID
        content: result.answer,
        timestamp: new Date(),
        isAi: true,
      };
    } catch (error) {
      console.error('Error sending chat message:', error);
      return {
        id: Math.random().toString(36).substring(2, 15),
        content: `Error: ${error instanceof Error ? error.message : 'Failed to get response from server'}`,
        timestamp: new Date(),
        isAi: true,
      };
    }
  }
}

/**
 * Function to connect to an email server and fetch emails
 */
export async function connectToEmailServer(
  projectId: string,
  settings: {
    imapServer: string;
    emailAddress: string;
    password: string;
    senderFilter?: string;
    subjectKeywords?: string;
    startDate?: string;
    endDate?: string;
  }
): Promise<{ success: boolean; message: string; emails?: { count: number; subjects: string[] } }> {
  if (API_CONFIG.useMocks) {
    // Mock implementation
    await new Promise(resolve => setTimeout(resolve, API_CONFIG.mockDelay * 2));
    
    return {
      success: true,
      message: `Connected to ${settings.imapServer} and fetched emails for ${settings.emailAddress}`,
      emails: {
        count: 5,
        subjects: [
          "Mock Email Subject 1",
          "Mock Email Subject 2",
          "Mock Email Subject 3",
          "Mock Email Subject 4",
          "Mock Email Subject 5"
        ]
      }
    };
  } else {
    // Real API implementation
    try {
      const headers = await getAuthHeaders();
      
      // Step 1: Setup email connection
      const setupResponse = await fetch(`${API_CONFIG.baseUrl}/project/setup_email`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          project_id: projectId,
          imap_server: settings.imapServer,
          email: settings.emailAddress,
          password: settings.password,
          sender_filter: settings.senderFilter,
          subject_keywords: settings.subjectKeywords ? [settings.subjectKeywords] : undefined,
          date_range: (settings.startDate || settings.endDate) ? {
            start: settings.startDate || new Date().toISOString(),
            end: settings.endDate
          } : undefined,
        }),
      });
      
      if (!setupResponse.ok) {
        throw new Error(`Failed to connect to email server with status: ${setupResponse.status}`);
      }
      
      // Step 2: Ingest emails
      const ingestResponse = await fetch(`${API_CONFIG.baseUrl}/project/ingest_emails?project_id=${projectId}`, {
        method: 'POST',
        headers,
      });
      
      if (!ingestResponse.ok) {
        throw new Error(`Failed to ingest emails with status: ${ingestResponse.status}`);
      }
      
      const ingestResult = await ingestResponse.json();
      
      return {
        success: true,
        message: 'Connected to email server and fetched emails successfully',
        emails: {
          count: ingestResult.count || 0,
          subjects: ingestResult.subjects || []
        }
      };
    } catch (error) {
      console.error('Error connecting to email server:', error);
      return {
        success: false,
        message: `Failed to connect to email server: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
    }
  }
}

/**
 * Function to summarize emails
 */
export async function summarizeEmails(
  projectId: string
): Promise<{ 
  success: boolean;
  message: string;
  count: number;
  summaries: Array<{
    id: string;
    subject: string;
    summary: string;
  }>;
}> {
  if (API_CONFIG.useMocks) {
    // Mock implementation
    await new Promise(resolve => setTimeout(resolve, API_CONFIG.mockDelay * 3));
    
    return {
      success: true,
      message: "Successfully summarized emails",
      count: 1,
      summaries: [
        {
          id: Math.random().toString(36).substring(2, 15),
          subject: "Mock Email Subject",
          summary: "This is a mock summary of the emails. It includes key points from the conversation thread, important dates and action items mentioned in the emails."
        }
      ]
    };
  } else {
    // Real API implementation
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${API_CONFIG.baseUrl}/project/summarize_emails?project_id=${projectId}`, {
        method: 'POST',
        headers,
      });
      
      if (!response.ok) {
        throw new Error(`Failed to summarize emails with status: ${response.status}`);
      }
      
      const result = await response.json();
      
      return {
        success: result.success || true,
        message: result.message || "Successfully summarized emails",
        count: result.count || 0,
        summaries: result.summaries || []
      };
    } catch (error) {
      console.error('Error summarizing emails:', error);
      throw error;
    }
  }
}

/**
 * Function to delete a project
 */
export async function deleteProject(projectId: string): Promise<boolean> {
  if (API_CONFIG.useMocks) {
    // Mock implementation
    await new Promise(resolve => setTimeout(resolve, API_CONFIG.mockDelay));
    
    // Always succeed in mock mode
    return true;
  } else {
    // Real API implementation
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${API_CONFIG.baseUrl}/project/${projectId}`, {
        method: 'DELETE',
        headers,
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete project with status: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error('Error deleting project:', error);
      return false;
    }
  }
}

/**
 * Function to create a new project
 */
/**
 * Function to upload web page content to the server
 */
export async function uploadWebPage(
  projectId: string,
  url: string,
  withScreenshot: boolean = false
): Promise<{
  status: string;
  url: string;
  title: string;
  chunks_created: number;
}> {
  if (API_CONFIG.useMocks) {
    // Mock implementation
    await new Promise(resolve => setTimeout(resolve, API_CONFIG.mockDelay * 2));
    
    return {
      status: "success",
      url: url,
      title: `Mock Web Page: ${url}`,
      chunks_created: Math.floor(Math.random() * 10) + 5, // Random number between 5-15
    };
  } else {
    // Real API implementation
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${API_CONFIG.baseUrl}/project/upload_web`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          project_id: projectId,
          url: url,
          with_screenshot: false
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Web page upload failed with status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error uploading web page:', error);
      throw error;
    }
  }
}

export async function createProject(name: string): Promise<Project | null> {
  if (API_CONFIG.useMocks) {
    // Mock implementation
    await new Promise(resolve => setTimeout(resolve, API_CONFIG.mockDelay));
    
    return {
      id: Math.random().toString(36).substring(2, 10),
      name,
      createdAt: new Date(),
    };
  } else {
    // Real API implementation
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${API_CONFIG.baseUrl}/project/create`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ name }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create project with status: ${response.status}`);
      }
      
      const project = await response.json();
      
      return {
        id: project.id,
        name: project.name,
        createdAt: new Date(project.created_at),
      };
    } catch (error) {
      console.error('Error creating project:', error);
      return null;
    }
  }
}
