from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, text
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4
import os
import logging
import numpy as np

from models.chat import ChatMessage, ChatRole
from models.document import Document
from models.rag_chunk import RagChunk
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService, ChatMessage as LLMChatMessage
from services.logging_service import LoggingService
import json
import re
from jsonschema import validate, ValidationError

# Expected JSON response schema
expected_keys = {"reply_text", "citation"}

def extract_valid_response_json(model_output: str, schema: dict) -> dict:
    """
    Extract valid JSON from potentially malformed model output.
    
    Args:
        model_output: The raw output string from the model
        schema: JSON schema to validate against
        
    Returns:
        Parsed JSON object or None if parsing fails
    """
    logger = LoggingService.get_logger("json_extractor")
    
    # First attempt: Try to parse the entire output as JSON directly
    try:
        parsed = json.loads(model_output.strip())
        if set(parsed.keys()).issuperset(expected_keys):
            validate(instance=parsed, schema=schema)
            return parsed
    except (json.JSONDecodeError, ValidationError) as e:
        logger.debug(f"Direct JSON parsing failed: {str(e)}")
    
    # Second attempt: Extract JSON-like objects with balanced braces
    # This regex finds the outermost JSON object with balanced braces
    json_pattern = re.compile(r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\})', re.DOTALL)
    matches = json_pattern.findall(model_output)
    
    for match in matches:
        try:
            # Try to parse each match
            parsed = json.loads(match)
            if set(parsed.keys()).issuperset(expected_keys):
                validate(instance=parsed, schema=schema)
                return parsed
        except (json.JSONDecodeError, ValidationError) as e:
            logger.debug(f"JSON match parsing failed: {str(e)}")
    
    # Third attempt: More aggressive approach to fix common JSON errors
    try:
        # Extract text between the first { and the last }
        json_start = model_output.find('{')
        if json_start >= 0:
            json_text = model_output[json_start:]
            json_end = json_text.rfind('}')
            if json_end >= 0:
                json_text = json_text[:json_end+1]
                
                # Fix common JSON issues
                # 1. Remove trailing commas before closing brackets
                json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
                
                # 2. Fix unquoted keys
                json_text = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', json_text)
                
                # 3. Fix escaped newlines in strings
                # First, identify string content
                def fix_strings(match):
                    # Replace literal newlines with \n in string values
                    s = match.group(0)
                    if '\n' in s:
                        s = s.replace('\n', '\\n')
                    return s
                
                # Find all string values and fix newlines
                json_text = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_strings, json_text)
                
                # 4. Handle missing quotes around string values
                json_text = re.sub(r':\s*([^",\{\}\[\]\s][^",\{\}\[\]\s]*)\s*([,\}\]])', r': "\1"\2', json_text)
                
                try:
                    parsed = json.loads(json_text)
                    if set(parsed.keys()).issuperset(expected_keys):
                        # Validate but don't fail if validation fails at this point
                        try:
                            validate(instance=parsed, schema=schema)
                        except ValidationError as e:
                            logger.warning(f"Schema validation warning: {str(e)}")
                        return parsed
                except json.JSONDecodeError as e:
                    logger.debug(f"Aggressive JSON fixing failed: {str(e)}")
    except Exception as e:
        logger.debug(f"Exception during aggressive JSON fixing: {str(e)}")
    
    # Fourth attempt: Manual extraction of expected fields
    try:
        # First try to find "reply_text" with quoted key
        reply_pattern = re.compile(r'"reply_text"\s*:\s*"((?:[^"\\]|\\.)*)(?:"|$)', re.DOTALL)
        reply_match = reply_pattern.search(model_output)
        
        # If not found, try with unquoted key
        if not reply_match:
            reply_pattern = re.compile(r'reply_text\s*:\s*"((?:[^"\\]|\\.)*)(?:"|$)', re.DOTALL)
            reply_match = reply_pattern.search(model_output)
        
        # Extract citation array with quoted key
        citation_pattern = re.compile(r'"citation"\s*:\s*\[(.*?)\]', re.DOTALL)
        citation_match = citation_pattern.search(model_output)
        
        # If not found, try with unquoted key
        if not citation_match:
            citation_pattern = re.compile(r'citation\s*:\s*\[(.*?)\]', re.DOTALL)
            citation_match = citation_pattern.search(model_output)
        
        if reply_match:
            # Process escape sequences properly
            reply_text = reply_match.group(1)
            
            # Handle all common escape sequences
            escape_map = {
                '\\n': '\n',   # newline
                '\\"': '"',    # quote
                '\\\\': '\\',  # backslash
                '\\t': '\t',   # tab
                '\\r': '\r',   # carriage return
                '\\b': '\b',   # backspace
                '\\f': '\f'    # form feed
            }
            
            # Replace all escape sequences
            for escaped, unescaped in escape_map.items():
                reply_text = reply_text.replace(escaped, unescaped)
            
            citations = []
            if citation_match:
                citation_text = citation_match.group(1)
                
                # First try to extract quoted citations
                citation_items = re.findall(r'"((?:[^"\\]|\\.)*)(?:"|$)', citation_text)
                
                # If no quoted citations found, try to extract unquoted citations
                if not citation_items:
                    citation_items = re.findall(r'([^,\s\[\]]+)', citation_text)
                
                citations = citation_items
            
            result = {
                "reply_text": reply_text,
                "citation": citations
            }
            
            # Validate but don't fail if validation fails
            try:
                validate(instance=result, schema=schema)
            except ValidationError as e:
                logger.warning(f"Manual extraction validation warning: {str(e)}")
            
            return result
    except Exception as e:
        logger.debug(f"Manual extraction failed: {str(e)}")
    
    # Final fallback: Create a minimal valid response
    logger.error("All JSON extraction methods failed, returning None")
    return None

class ChatService:
    """
    Service for handling chat-related operations.
    """
    
    @staticmethod
    async def process_rag_query(
        db: AsyncSession,
        project_id: str,
        question: str,
        top_k: int = 5
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process a RAG query using the rag_chunks table.
        
        Args:
            db: Database session
            project_id: ID of the project
            question: User question
            top_k: Number of top chunks to retrieve
            
        Returns:
            Tuple of (answer, citations)
        """
        # Set up logging
        logger = LoggingService.get_logger("chat_service")
        
        try:
            # Generate embedding for the question
            embedding_service = EmbeddingService()
            question_embedding = await embedding_service.generate_embedding(question)
            
            distance_threshold = 0.4
            # Normalize the embedding
            question_embedding_np = np.array(question_embedding)
            normalized_question_embedding = (question_embedding_np / np.linalg.norm(question_embedding_np)).tolist()
            
            # Search the rag_chunks table using pgvector
            # We use the <=> operator for cosine distance
            # Note: Lower distance means higher similarity
            result = await db.execute(
                select(RagChunk)
                .where(RagChunk.project_id == project_id)
                .where(RagChunk.embedding.is_not(None))  # Only consider chunks with embeddings
                .order_by(RagChunk.embedding.cosine_distance(normalized_question_embedding))
                .limit(top_k)
            )
                        
            text_chunks = result.scalars().all()
            
            # Get the page numbers of the retrieved chunks to find associated image chunks
            page_numbers = [(chunk.document_id, chunk.page_number) for chunk in text_chunks]
            
            # Retrieve image chunks for the same pages
            image_chunks = []
            if page_numbers:
                # Create a list of OR conditions for each (document_id, page_number) pair
                from sqlalchemy import or_
                conditions = [
                    ((RagChunk.document_id == doc_id) & (RagChunk.page_number == page_num))
                    for doc_id, page_num in page_numbers
                ]
                
                # Query for image chunks (those with embedding=None) that match the page numbers
                image_result = await db.execute(
                    select(RagChunk)
                    .where(RagChunk.project_id == project_id)
                    .where(RagChunk.embedding.is_(None))  # Only image chunks have null embeddings
                    .where(or_(*conditions))
                )
                
                image_chunks = image_result.scalars().all()
            
            # Combine text and image chunks
            chunks = text_chunks + image_chunks
            
            # If no chunks found, return a generic response
            if not chunks:
                return (
                    "I don't have any relevant information to answer your question. Please upload some documents first.",
                    []
                )
            
            # Extract information from chunks
            context_parts = []
            citations = []
            img_citations = []
            
            # Import the config from main
            from main import config
            
            # Get chat parameters from config if available, otherwise use defaults
            chat_config = config.get('chat', {})
            
            # Track total token count to avoid exceeding Gemini's context window
            total_tokens = 0
            max_tokens = chat_config.get('max_tokens', 30000)  # Get from config or use default
            
            # Process text chunks first (add to context)
            for chunk in text_chunks:
                # Add citation for text chunk
                citation = {
                    "chunk_id": chunk.chunk_id,
                    "doc_name": chunk.doc_name,
                    "page_number": chunk.page_number,
                    "source_type": chunk.source_type,
                }
                
                citations.append(citation)

                chunk_txt_with_citations = chunk.chunk_text + f"[CITATION::CHUNK_ID: {chunk.chunk_id}]"
            
                # Estimate token count (rough approximation: 4 chars ≈ 1 token)
                chunk_tokens = len(chunk_txt_with_citations) // 4
                
                # If adding this chunk would exceed the limit, skip it
                if total_tokens + chunk_tokens > max_tokens:
                    continue
                
                # Add chunk to context
                context_parts.append(chunk_txt_with_citations)
                total_tokens += chunk_tokens
                
                
            # Process image chunks (only add to citations, not to context)
            for chunk in image_chunks:
                # Add citation for image chunk with images
                if chunk.images_base64:
                    citation = {
                        "chunk_id": chunk.chunk_id,
                        "doc_name": chunk.doc_name,
                        "page_number": chunk.page_number,
                        "source_type": chunk.source_type,
                        "images_base64": chunk.images_base64
                    }
                    citations.append(citation)
                    img_citations.append(citation)
            
            # Build the context string
            # Import the config from main
            from main import config
            
            # Use system_prompt from config if available, otherwise use default
            system_prompt = config.get('system_prompt', """You are a helpful assistant answering user questions based on retrieved context chunks from documents.

                                Each chunk ends with a citation in the format:
                                [CITATION::CHUNK_ID:: "<chunk_id>"]

                                Some chunks may not be relevant to the user's question. You must decide whether to use the context or rely on your general knowledge.

                                Your task:

                                1. Analyze the user's question carefully.
                                2. Review the context chunks and determine if any are relevant to answering the question.
                                3. Use only relevant chunks to form your answer. If none are useful, rely on your general knowledge.
                                4. Format your response clearly using **paragraphs and newlines** for readability.
                                5. Return the result as a **valid JSON object**, and nothing else. Start with `{` and end with `}`.

                                **Important rules:**
                                - Do NOT include raw `[CITATION::CHUNK_ID:: ...]` markers in the `reply_text`.
                                - Only include `chunk_id`s in the `citation` array if the chunk was actually used in the answer.
                                - If no chunk was used, return an empty citation list.
                                - Follow the schema exactly. Any deviation is considered an error.

                                JSON Schema:

                                {
                                "reply_text": "Your full answer (formatted with newlines)",
                                "citation": ["chunk_id_1", "chunk_id_2"]
                                }
                                """)
            
            context = system_prompt + """\n\nContext:
                        """ + "\n\n".join(context_parts) + f"\n\nUser Question: {question}\n\nRespond with a JSON object that fully matches the schema above."


            
            # Log the raw prompt for debugging
            logger.info(f"RAG Prompt: {context}")
            
            # Send prompt to Gemini Flash 2.0 API
            llm_service = LLMService()
            
            # Create a message for the LLM
            message = LLMChatMessage(role="user", content=context)
            
            # Get the API key from environment
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            
            # Generate response
            answer = await llm_service.generate_response([message])
            
            # Log the raw response for debugging
            logger.info(f"LLM Response: {answer}")
        
            # Define the expected JSON schema
            json_schema = {
                "type": "object",
                "required": ["reply_text", "citation"],
                "properties": {
                    "reply_text": {"type": "string"},
                    "citation": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
            
            # Try to extract valid JSON from the response
            img_screenshot_chunk_ids = []
            img_screenshot_base64=[]
            ref_doc_names=[]
            answer_json = extract_valid_response_json(answer, json_schema)
            
            if answer_json:
                if "citation" in answer_json and isinstance(answer_json["citation"], list):
                    for citation in answer_json["citation"]:
                        parts = citation.rsplit("_", 1)
                        if len(parts) == 2:
                            base = parts[0] + "_"  # Keep the trailing underscore
                            img_screenshot_chunk_ids.append(base+"screenshot")
                            logger.info(f"Base citation: {base}")
                        else:
                            logger.info(f"Unexpected citation format: {citation}")

                        for citation_item in citations:
                            if(citation == citation_item["chunk_id"]):
                                ref_doc_names.append(citation_item["doc_name"])
                                logger.info(f"add doc name as reference: {ref_doc_names}")

                else:
                    logger.info("Citation field not found or not a list.")
                
                img_screenshot_chunk_ids = list(set(img_screenshot_chunk_ids))
                for chunk_img_id_used in img_screenshot_chunk_ids:
                    for img_citation in img_citations:
                        if img_citation["chunk_id"] == chunk_img_id_used:
                            img_obj =  json.loads(img_citation["images_base64"])
                            base64_string = img_obj[0]["base64"]
                            img_screenshot_base64.append(base64_string)
                            break
                
                if len(img_screenshot_base64) > 0:
                    answer_json["img_base64"] = img_screenshot_base64

                ref_doc_names = list(set(ref_doc_names))
                if len(ref_doc_names) > 0:
                    answer_json["doc_name"] = ref_doc_names


            else:
                logger.error("Failed to parse valid JSON from LLM response")
                # If JSON parsing fails, try to return the raw answer as fallback
                try:
                    answer_json = {"reply_text": answer, "citation": []}
                except Exception as e:
                    logger.error(f"Error creating fallback JSON: {str(e)}")
                    answer_json = {"reply_text": "Error processing response", "citation": []}

            # Return the reply_text from the parsed JSON instead of the raw answer
            return json.dumps(answer_json), citations
            #return answer_json.get("reply_text", answer), citations
            
        except Exception as e:
            logger.error(f"Error in process_rag_query: {str(e)}")
            # Return a graceful fallback
            return (
                "I'm sorry, I encountered an error while processing your question. Please try again later.",
                []
            )
    
    @staticmethod
    async def add_message(
        db: AsyncSession,
        project_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[str]] = None
    ) -> ChatMessage:
        """
        Add a chat message.
        
        Args:
            db: Database session
            project_id: ID of the project
            role: Role of the message sender (user or assistant)
            content: Message content
            citations: Optional document citations
            images: Optional base64 encoded images
            
        Returns:
            The created chat message
        """
        chat_message = ChatMessage(
            project_id=project_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            citations=citations,
            images=images
        )
        
        db.add(chat_message)
        await db.commit()
        await db.refresh(chat_message)
        
        return chat_message
    
    @staticmethod
    async def get_chat_history(db: AsyncSession, project_id: str, limit: int = 50) -> List[ChatMessage]:
        """
        Get chat history for a project.
        
        Args:
            db: Database session
            project_id: ID of the project
            limit: Maximum number of messages to return
            
        Returns:
            List of chat messages
        """
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.project_id == project_id)
            .order_by(ChatMessage.timestamp)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def process_query(
        db: AsyncSession,
        project_id: str,
        query: str
    ) -> ChatMessage:
        """
        Process a user query and generate a response.
        
        Args:
            db: Database session
            project_id: ID of the project
            query: User query
            
        Returns:
            The assistant's response message
        """
        # Add user message to chat history
        user_message = await ChatService.add_message(
            db=db,
            project_id=project_id,
            role=ChatRole.USER,
            content=query
        )
        
        # Get project documents
        result = await db.execute(
            select(Document)
            .where(Document.project_id == project_id)
            .where(Document.embedding.is_not(None))  # Only consider documents with embeddings
        )
        documents = result.scalars().all()
        
        # If no documents with embeddings, return a generic response
        if not documents:
            return await ChatService.add_message(
                db=db,
                project_id=project_id,
                role=ChatRole.ASSISTANT,
                content="I don't have any documents to reference for this project. Please upload some documents first."
            )
        
        # Generate embedding for the query
        embedding_service = EmbeddingService()
        query_embedding = await embedding_service.generate_embedding(query)
        
        # Get document embeddings
        document_embeddings = [doc.embedding for doc in documents]
        
        # Find most relevant documents
        top_indices = await embedding_service.similarity_search(
            query_embedding=query_embedding,
            document_embeddings=document_embeddings,
            top_k=5  # Get top 5 most relevant documents
        )
        
        # Get the relevant document texts
        relevant_documents = [documents[i].content for i in top_indices]
        
        # Get chat history
        chat_history = await ChatService.get_chat_history(db, project_id, limit=10)
        
        # Convert to LLM chat messages
        llm_chat_history = [
            LLMChatMessage(role=msg.role, content=msg.content)
            for msg in chat_history[-6:]  # Use last 6 messages for context
        ]
        
        # Generate response using LLM
        llm_service = LLMService()
        response_text = await llm_service.answer_question(
            question=query,
            relevant_documents=relevant_documents,
            chat_history=llm_chat_history
        )
        
        # Prepare citations
        citations = [
            {
                "documentName": documents[i].name,
                "pageNumber": None  # We don't have page numbers in this implementation
            }
            for i in top_indices
        ]
        
        # Add assistant message to chat history
        assistant_message = await ChatService.add_message(
            db=db,
            project_id=project_id,
            role=ChatRole.ASSISTANT,
            content=response_text,
            citations=citations
        )
        
        return assistant_message
