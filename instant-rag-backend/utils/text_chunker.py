import re
import tiktoken
from typing import List, Optional, Tuple

class TextChunker:
    """
    Utility for chunking text into smaller pieces for embedding.
    """
    
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Number of tokens to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # OpenAI's encoding
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks of approximately chunk_size tokens with overlap.
        
        Args:
            text: The text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or text.isspace():
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        # Split text into sentences
        sentences = self._split_into_sentences(text)
        
        # Create chunks
        chunks = []
        current_chunk = []
        current_chunk_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence))
            
            # If adding this sentence would exceed the chunk size and we already have content,
            # finish the current chunk and start a new one
            if current_chunk_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                # Keep some sentences for overlap
                overlap_size = 0
                overlap_sentences = []
                
                for s in reversed(current_chunk):
                    s_tokens = len(self.tokenizer.encode(s))
                    if overlap_size + s_tokens <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += s_tokens
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_chunk_tokens = overlap_size
            
            # Add the sentence to the current chunk
            current_chunk.append(sentence)
            current_chunk_tokens += sentence_tokens
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace and normalizing line endings.
        
        Args:
            text: The text to clean
            
        Returns:
            Cleaned text
        """
        # Replace multiple newlines with a single newline
        text = re.sub(r'\n+', '\n', text)
        
        # Replace multiple spaces with a single space
        text = re.sub(r' +', ' ', text)
        
        # Strip leading and trailing whitespace
        text = text.strip()
        
        return text
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: The text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting based on common punctuation
        # This is a basic implementation and could be improved
        sentence_endings = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_endings, text)
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
