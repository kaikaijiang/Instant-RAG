import numpy as np
from typing import List, Union, Optional, Tuple
import os
import asyncio
import time
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    """
    Service for generating embeddings using the BGE-small-en model.
    Implemented as a singleton to ensure the model is loaded only once.
    """
    
    _instance: Optional['EmbeddingService'] = None
    
    def __new__(cls):
        """
        Singleton pattern to ensure only one instance of the embedding service exists.
        """
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._model = None
            cls._instance._model_name = 'BAAI/bge-small-en'
            cls._instance._model_loaded = False
            cls._instance._model_loading = False
            cls._instance._load_lock = asyncio.Lock()
        return cls._instance
    
    @property
    def model(self):
        """
        Get the embedding model, loading it if necessary.
        """
        if self._model is None:
            # Load the model
            self._model = SentenceTransformer(self._model_name)
            self._model_loaded = True
        return self._model
    
    async def ensure_model_loaded(self):
        """
        Ensure the model is loaded, waiting if it's currently being loaded by another task.
        """
        if self._model_loaded:
            return
        
        async with self._load_lock:
            if not self._model_loaded and not self._model_loading:
                self._model_loading = True
                # Run model loading in a thread pool to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: self.model)
                self._model_loading = False
                self._model_loaded = True
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            The embedding as a list of floats
        """
        # Ensure model is loaded
        await self.ensure_model_loaded()
        
        # Run the embedding generation in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, self._generate_embedding_sync, text)
        return embedding
    
    def _generate_embedding_sync(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text synchronously.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            The embedding as a list of floats
        """
        # Generate the embedding
        embedding = self.model.encode(text)
        
        # Convert to list of floats
        return embedding.tolist()
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for the given texts.
        
        Args:
            texts: The texts to generate embeddings for
            
        Returns:
            The embeddings as a list of lists of floats
        """
        # Ensure model is loaded
        await self.ensure_model_loaded()
        
        # Run the embedding generation in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, self._generate_embeddings_sync, texts)
        return embeddings
    
    def _generate_embeddings_sync(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for the given texts synchronously.
        
        Args:
            texts: The texts to generate embeddings for
            
        Returns:
            The embeddings as a list of lists of floats
        """
        # Generate the embeddings
        embeddings = self.model.encode(texts)
        
        # Convert to list of lists of floats
        return embeddings.tolist()
    
    async def similarity_search(self, query_embedding: List[float], document_embeddings: List[List[float]], top_k: int = 5) -> List[int]:
        """
        Find the most similar documents to the query.
        
        Args:
            query_embedding: The embedding of the query
            document_embeddings: The embeddings of the documents
            top_k: The number of results to return
            
        Returns:
            The indices of the most similar documents
        """
        # Convert to numpy arrays
        query_embedding_np = np.array(query_embedding)
        document_embeddings_np = np.array(document_embeddings)
        
        # Compute cosine similarities
        similarities = np.dot(document_embeddings_np, query_embedding_np) / (
            np.linalg.norm(document_embeddings_np, axis=1) * np.linalg.norm(query_embedding_np)
        )
        
        # Get the indices of the top_k most similar documents
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        return top_indices.tolist()
    
    async def batch_similarity_search(self, query_embedding: List[float], document_embeddings: List[List[float]], top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Find the most similar documents to the query and return their indices and similarity scores.
        
        Args:
            query_embedding: The embedding of the query
            document_embeddings: The embeddings of the documents
            top_k: The number of results to return
            
        Returns:
            A list of tuples containing (index, similarity_score) for the most similar documents
        """
        # Convert to numpy arrays
        query_embedding_np = np.array(query_embedding)
        document_embeddings_np = np.array(document_embeddings)
        
        # Compute cosine similarities
        similarities = np.dot(document_embeddings_np, query_embedding_np) / (
            np.linalg.norm(document_embeddings_np, axis=1) * np.linalg.norm(query_embedding_np)
        )
        
        # Get the indices and scores of the top_k most similar documents
        top_indices = np.argsort(similarities)[::-1][:top_k]
        top_scores = similarities[top_indices]
        
        # Return as list of tuples (index, score)
        return [(int(idx), float(score)) for idx, score in zip(top_indices, top_scores)]
