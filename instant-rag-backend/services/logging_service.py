import logging
import sys
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime

class LoggingService:
    """
    Service for logging application events with enhanced monitoring capabilities.
    """
    
    _instance = None
    _loggers = {}
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger for a specific component.
        
        Args:
            name: Name of the component
            
        Returns:
            Logger instance for the component
        """
        if name not in LoggingService._loggers:
            logger = logging.getLogger(f"instant-rag.{name}")
            
            # Set level
            logger.setLevel(logging.DEBUG)
            
            # Create console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            
            # Add handler to logger if not already added
            if not logger.handlers:
                logger.addHandler(console_handler)
                
            # Create logs directory if it doesn't exist
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Create file handler for persistent logging
            log_file = os.path.join(logs_dir, f"instant-rag-{datetime.now().strftime('%Y-%m-%d')}.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)  # Debug level for file logging
            file_handler.setFormatter(formatter)
            
            # Add file handler to logger
            logger.addHandler(file_handler)
            
            LoggingService._loggers[name] = logger
        
        return LoggingService._loggers[name]
    
    def __new__(cls):
        """
        Singleton pattern to ensure only one instance of the logging service exists.
        """
        if cls._instance is None:
            cls._instance = super(LoggingService, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self):
        """
        Initialize the logger with appropriate handlers and formatters.
        """
        self.logger = logging.getLogger("instant-rag")
        self.logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger if not already added
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create file handler for persistent logging
        log_file = os.path.join(logs_dir, f"instant-rag-{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Add file handler to logger if not already added
        if len(self.logger.handlers) < 2:
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """
        Log an info message.
        
        Args:
            message: The message to log
            **kwargs: Additional context to include in the log
        """
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """
        Log a warning message.
        
        Args:
            message: The message to log
            **kwargs: Additional context to include in the log
        """
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """
        Log an error message.
        
        Args:
            message: The message to log
            **kwargs: Additional context to include in the log
        """
        self._log(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """
        Log a debug message.
        
        Args:
            message: The message to log
            **kwargs: Additional context to include in the log
        """
        self._log(logging.DEBUG, message, **kwargs)
    
    def document_processing_start(self, document_name: str, project_id: str, file_type: str):
        """
        Log the start of document processing with structured metadata.
        
        Args:
            document_name: Name of the document being processed
            project_id: ID of the project the document belongs to
            file_type: Type of the document (PDF, Markdown, image)
        """
        self.info(
            f"Started processing document: {document_name}",
            event_type="document_processing_start",
            project_id=project_id,
            document_name=document_name,
            file_type=file_type,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def document_processing_complete(self, document_name: str, project_id: str, 
                                    chunks_created: int, pages_processed: int, 
                                    processing_time_ms: int):
        """
        Log the completion of document processing with metrics.
        
        Args:
            document_name: Name of the document processed
            project_id: ID of the project the document belongs to
            chunks_created: Number of chunks created
            pages_processed: Number of pages processed
            processing_time_ms: Processing time in milliseconds
        """
        self.info(
            f"Completed processing document: {document_name}",
            event_type="document_processing_complete",
            project_id=project_id,
            document_name=document_name,
            chunks_created=chunks_created,
            pages_processed=pages_processed,
            processing_time_ms=processing_time_ms,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def embedding_generation_metrics(self, num_chunks: int, processing_time_ms: int, 
                                    avg_tokens_per_chunk: float):
        """
        Log metrics about embedding generation.
        
        Args:
            num_chunks: Number of chunks embedded
            processing_time_ms: Processing time in milliseconds
            avg_tokens_per_chunk: Average number of tokens per chunk
        """
        self.info(
            f"Generated embeddings for {num_chunks} chunks",
            event_type="embedding_generation",
            num_chunks=num_chunks,
            processing_time_ms=processing_time_ms,
            avg_tokens_per_chunk=avg_tokens_per_chunk,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _log(self, level: int, message: str, **kwargs):
        """
        Log a message with the given level and context.
        
        Args:
            level: The log level
            message: The message to log
            **kwargs: Additional context to include in the log
        """
        # Add context to the message if provided
        if kwargs:
            context_str = " ".join([f"{k}={v}" for k, v in kwargs.items()])
            message = f"{message} - {context_str}"
        
        self.logger.log(level, message)
