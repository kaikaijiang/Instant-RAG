import os
import json
from typing import List, Dict, Any, Optional
import aiohttp
from pydantic import BaseModel

# Import config from main
try:
    from main import config
except ImportError:
    # Default empty config if not available
    config = {}

class ChatMessage(BaseModel):
    role: str
    content: str

class LLMService:
    """
    Service for interacting with Google Gemini Flash 2.0 LLM.
    """
    
    def __init__(self):
        """
        Initialize the LLM service.
        """
        # Get API key from environment variable
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY environment variable not set")
        
        # API endpoint with correct model name
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    async def generate_response(
        self, 
        messages: List[ChatMessage], 
        temperature: float = None,
        max_tokens: int = None,
        context: Optional[str] = None
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of chat messages
            temperature: Temperature for generation (overrides config)
            max_tokens: Maximum number of tokens to generate (overrides config)
            context: Additional context to provide to the LLM
            
        Returns:
            The generated response
        """
        # Get parameters from config if available, otherwise use defaults
        llm_config = config.get('llm', {})
        
        # Use parameters in this order of precedence:
        # 1. Explicitly passed parameters
        # 2. Config file values
        # 3. Default values
        temp = temperature if temperature is not None else llm_config.get('temperature', 0.8)
        tokens = max_tokens if max_tokens is not None else llm_config.get('max_tokens', 8192)
        top_p = llm_config.get('top_p', 0.95)
        top_k = llm_config.get('top_k', 40)
        
        # Prepare the request payload
        payload = {
            "contents": [
                {
                    "role": msg.role,
                    "parts": [{"text": msg.content}]
                }
                for msg in messages
            ],
            "generationConfig": {
                "temperature": temp,
                "maxOutputTokens": tokens,
                "topP": top_p,
                "topK": top_k
            }
        }
        
        # Add context if provided
        if context:
            # Add context as a system message
            payload["contents"].insert(0, {
                "role": "user",
                "parts": [{"text": f"Context information: {context}"}]
            })
        
        # Make the API request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}?key={self.api_key}",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Error from Gemini API: {error_text}")
                
                result = await response.json()
                
                # Extract the response text
                try:
                    response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                    return response_text
                except (KeyError, IndexError) as e:
                    raise Exception(f"Unexpected response format: {str(e)}")
    
    async def summarize_text(self, text: str, max_length: int = 500) -> str:
        """
        Summarize the given text.
        
        Args:
            text: The text to summarize
            max_length: Maximum length of the summary
            
        Returns:
            The summary
        """
        prompt = f"Please summarize the following text in a concise manner, not exceeding {max_length} characters:\n\n{text}"
        
        messages = [ChatMessage(role="user", content=prompt)]
        
        return await self.generate_response(messages, temperature=0.3)
    
    async def answer_question(
        self, 
        question: str, 
        relevant_documents: List[str],
        chat_history: Optional[List[ChatMessage]] = None
    ) -> str:
        """
        Answer a question based on the relevant documents.
        
        Args:
            question: The question to answer
            relevant_documents: List of relevant document texts
            chat_history: Optional chat history
            
        Returns:
            The answer
        """
        # Prepare context from relevant documents
        context = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(relevant_documents)])
        
        # Prepare messages
        messages = []
        
        # Add chat history if provided
        if chat_history:
            messages.extend(chat_history)
        
        # Add the current question
        messages.append(ChatMessage(role="user", content=question))
        
        # Generate response with context
        return await self.generate_response(messages, context=context)
