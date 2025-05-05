import { create } from 'zustand';
import { sendChatMessage } from '@/services/api';
import { useProjectStore } from './useProjectStore';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: {
    documentName: string;
    pageNumber?: number;
  }[];
  images?: string[]; // Base64 encoded images
  references?: string[]; // Document names or URLs referenced in the message
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setIsLoading: (isLoading: boolean) => void;
  sendMessage: (content: string, topK?: number) => Promise<void>;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  
  addMessage: (message) => set((state) => ({
    messages: [
      ...state.messages,
      {
        ...message,
        id: Math.random().toString(36).substring(2, 15),
        timestamp: new Date(),
      },
    ],
  })),
  
  setIsLoading: (isLoading) => set({
    isLoading,
  }),
  
  sendMessage: async (content, topK = 5) => {
    console.log("sendMessage function called with:", content, topK);
    
    // Add user message
    get().addMessage({
      role: 'user',
      content,
    });
    
    // Set loading state
    get().setIsLoading(true);
    
    try {
      // Get the selected project ID from the project store
      const { selectedProjectId } = useProjectStore.getState();
      console.log("Selected project ID:", selectedProjectId);
      
      // If no project is selected, show an error message
      if (!selectedProjectId) {
        throw new Error('No project selected. Please select a project first.');
      }
      
      console.log("About to call sendChatMessage API with:", selectedProjectId, content, topK);
      
      // Call the real API function with the selected project ID and topK
      const response = await sendChatMessage(selectedProjectId, content, topK);

      
      // Parse the response content as JSON
      const parsedResponse = JSON.parse(response.content);
      console.log("Parsed response:", parsedResponse);
      
      // Extract the reply text from the parsed JSON
      const replyText = parsedResponse.reply_text;
      
      // Check if there are base64 images in the response and format them properly
      let base64Images;
      console.log("Checking for base64 images in response:", parsedResponse);
      
      // Check for both possible field names (base64 and img_base64)
      const base64Field = parsedResponse.base64 || parsedResponse.img_base64;
      
      // Check if there are document references in the response
      let documentReferences;
      if (parsedResponse.doc_name && Array.isArray(parsedResponse.doc_name) && parsedResponse.doc_name.length > 0) {
        console.log("Found document references:", parsedResponse.doc_name);
        documentReferences = parsedResponse.doc_name;
      }
      
      if (base64Field) {
        console.log("Found base64 field:", base64Field);
        console.log("Is array?", Array.isArray(base64Field));
        console.log("Length:", base64Field ? base64Field.length : 0);
      }
      
      if (base64Field && Array.isArray(base64Field) && base64Field.length > 0) {
        console.log("Processing base64 images...");
        
        // Format each base64 string with the proper data URL prefix if it doesn't already have one
        base64Images = base64Field.map((img: string, index: number) => {
          console.log(`Processing image ${index}:`, typeof img, img ? img.substring(0, 30) + '...' : 'undefined');
          
          // Check if the string already starts with a data URL prefix
          if (img && typeof img === 'string') {
            if (img.startsWith('data:')) {
              console.log(`Image ${index} already has data URL prefix`);
              return img;
            }
            // Otherwise, add the appropriate data URL prefix (assuming it's a PNG image)
            console.log(`Adding data URL prefix to image ${index}`);
            return `data:image/png;base64,${img}`;
          } else {
            console.error(`Invalid base64 image at index ${index}:`, img);
            return null;
          }
        }).filter(Boolean) as string[]; // Remove any null values and assert as string[]
        
        console.log("Formatted base64 images:", base64Images);
      } else {
        console.log("No valid base64 images found in the response");
      }
      
      // Add assistant message with the reply text, images, and document references if available
      const messageToAdd = {
        role: 'assistant' as const,
        content: replyText || "No reply text found in response",
        images: base64Images && base64Images.length > 0 ? base64Images : undefined,
        references: documentReferences
      };
      
      console.log("Adding assistant message:", messageToAdd);
      console.log("Has images?", !!messageToAdd.images);
      console.log("Image count:", messageToAdd.images ? messageToAdd.images.length : 0);
      
      get().addMessage(messageToAdd);
    } catch (error) {
      console.log("Error caught in sendMessage:", error);
      console.error("Error sending message:", error);
      // Add error message as assistant response
      get().addMessage({
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to get response from server'}`,
      });
    } finally {
      // Set loading state to false
      get().setIsLoading(false);
    }
  },
  
  clearMessages: () => set({
    messages: [],
  }),
}));

// Subscribe to project changes
let currentProjectId: string | null = null;

// Setup subscription to project store changes
useProjectStore.subscribe((state) => {
  const newProjectId = state.selectedProjectId;
  
  // Only clear messages when project ID actually changes
  if (newProjectId !== currentProjectId) {
    currentProjectId = newProjectId;
    useChatStore.getState().clearMessages();
  }
});
