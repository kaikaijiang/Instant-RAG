import fitz  # PyMuPDF
import base64
import io
from PIL import Image
import pytesseract
from typing import List, Dict, Tuple, Optional, Any, BinaryIO, Union
import os
import uuid
import json
import re
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import asyncio
import docx
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from langchain.text_splitter import RecursiveCharacterTextSplitter
from services.logging_service import LoggingService
from utils.text_chunker import TextChunker

class DocumentProcessor:
    """
    Service for processing different types of documents and extracting text and images.
    """
    
    def __init__(self):
        """
        Initialize the document processor.
        """
        self.logger = LoggingService()
        self.text_chunker = TextChunker(chunk_size=400, chunk_overlap=50)
        self.http_client = httpx.AsyncClient(timeout=60.0)  # 60 seconds timeout for downloading web content
        
    def clean_pdf_text(self, text: str) -> str:
        """
        Clean text extracted from PDF documents.
        
        Args:
            text: The raw text extracted from a PDF
            
        Returns:
            Cleaned text with removed artifacts and normalized spacing
        """
        # Remove multiple spaces, line breaks
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove page numbers if they are standalone lines
        text = re.sub(r'\bPage\s*\d+\b', '', text, flags=re.IGNORECASE)

        # Remove common header/footer patterns (adjust as needed)
        text = re.sub(r'(Confidential|Draft|Company Name).*?\n', '', text, flags=re.IGNORECASE)

        return text
        
    def semantic_chunk_text(self, text: str) -> List[str]:
        """
        Split text into semantic chunks using LangChain's RecursiveCharacterTextSplitter.
        
        Args:
            text: The text to split into chunks
            
        Returns:
            A list of text chunks
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        return splitter.split_text(text)
    
    def process_file(
        self, 
        file_content: bytes, 
        file_name: str, 
        file_type: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Process a file and extract text chunks and images.
        
        Args:
            file_content: The file content as a binary stream
            file_name: The name of the file
            file_type: The MIME type of the file
            
        Returns:
            A tuple containing:
                - A list of dictionaries with chunk text, page number, and images
                - The total number of pages processed
        """
        self.logger.info(f"Processing file: {file_name} of type {file_type}")
        
        # Determine the source type based on file extension or MIME type
        source_type = self._determine_source_type(file_name, file_type)
        
        if source_type == "pdf":
            return self._process_pdf(file_content, file_name)
        elif source_type == "markdown":
            return self._process_markdown(file_content, file_name)
        elif source_type == "text":
            return self._process_text(file_content, file_name)
        elif source_type == "docx":
            return self._process_docx(file_content, file_name)
        elif source_type == "image":
            return self._process_image(file_content, file_name)
        else:
            self.logger.warning(f"Unsupported file type: {file_type} for file {file_name}")
            return [], 0
    
    def _determine_source_type(self, file_name: str, file_type: str) -> str:
        """
        Determine the source type based on file extension or MIME type.
        
        Args:
            file_name: The name of the file
            file_type: The MIME type of the file
            
        Returns:
            The source type: 'pdf', 'markdown', 'text', 'docx', 'image', or 'unknown'
        """
        # Check file extension
        ext = os.path.splitext(file_name)[1].lower()
        
        if ext == ".pdf" or file_type == "application/pdf":
            return "pdf"
        elif ext in [".md", ".markdown"] or file_type == "text/markdown":
            return "markdown"
        elif ext == ".txt" or file_type == "text/plain":
            return "text"
        elif ext == ".docx" or file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "docx"
        elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"] or file_type.startswith("image/"):
            return "image"
        else:
            return "unknown"
    
    def _process_pdf(self, file_content: bytes, file_name: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Process a PDF file and extract text chunks and page screenshots.
        
        Args:
            file_content: The file content as a binary stream
            file_name: The name of the file
            
        Returns:
            A tuple containing:
                - A list of dictionaries with chunk text, page number, and page screenshots
                - The total number of pages processed
        """
        self.logger.info(f"Processing PDF: {file_name}")
        
        # Use the file content directly
        content = file_content
        
        # Open the PDF
        doc = fitz.open(stream=content, filetype="pdf")
        
        result = []
        total_pages = len(doc)
        
        for page_num, page in enumerate(doc):
            # Extract text from the page
            text = page.get_text()
            
            # Clean the extracted text
            cleaned_text = self.clean_pdf_text(text)
            
            # Create a screenshot of the page
            # Render the page to a pixmap (image)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            
            # Convert pixmap to PNG image bytes
            image_bytes = pix.tobytes("png")
            
            # Convert image to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            
            # Add data URI prefix for proper display in image viewers
            image_base64_with_prefix = f"data:image/png;base64,{image_base64}"
            
            # Create a single image entry for the page screenshot
            page_screenshot = {
                "id": f"{page_num}_screenshot",
                "base64": image_base64_with_prefix,
                "mime_type": "png"
            }
            
            # Use semantic chunking instead of basic chunking
            chunks = self.semantic_chunk_text(cleaned_text)
            
            # Create a result entry for each chunk
            for chunk_index, chunk_text in enumerate(chunks):
                chunk_id = f"{file_name}_p{page_num+1}_c{chunk_index+1}"
                
                result.append({
                    "chunk_id": chunk_id,
                    "chunk_text": chunk_text,
                    "page_number": page_num + 1,
                    "images": [],  # No images by default
                    "source_type": "pdf",
                    "page_has_images": True,  # Always true since we have a screenshot
                    "doc_name":file_name
                })
            
            # Add a special chunk that contains the page screenshot
            image_chunk_id = f"{file_name}_p{page_num+1}_screenshot"
            result.append({
                "chunk_id": image_chunk_id,
                "chunk_text": f"[Page {page_num + 1} screenshot]",
                "page_number": page_num + 1,
                "images": [page_screenshot],
                "images_base64": [page_screenshot],  # Add images_base64 field for compatibility with chat service
                "source_type": "pdf",
                "is_image_chunk": True,
                "doc_name":file_name
            })
        
        doc.close()
        
        self.logger.info(f"Processed PDF: {file_name} - {total_pages} pages, {len(result)} chunks")
        return result, total_pages
    
    def _process_markdown(self, file_content: bytes, file_name: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Process a Markdown file and extract text chunks.
        
        Args:
            file_content: The file content as bytes
            file_name: The name of the file
            
        Returns:
            A tuple containing:
                - A list of dictionaries with chunk text and page number
                - The total number of pages processed (always 1 for markdown)
        """
        self.logger.info(f"Processing Markdown: {file_name}")
        
        # Use the file content directly
        content = file_content
        
        text = content.decode("utf-8", errors="replace")
        
        # Clean the text
        cleaned_text = self.clean_pdf_text(text)
        
        # Use semantic chunking instead of basic chunking
        chunks = self.semantic_chunk_text(cleaned_text)
        
        result = []
        
        # Create a result entry for each chunk
        for chunk_index, chunk_text in enumerate(chunks):
            chunk_id = f"{file_name}_c{chunk_index+1}"
            
            result.append({
                "chunk_id": chunk_id,
                "chunk_text": chunk_text,
                "page_number": 1,  # Markdown files are considered single-page
                "images": [],  # No images in markdown (we could parse image links in the future)
                "source_type": "markdown",
                "doc_name":file_name
            })
        
        self.logger.info(f"Processed Markdown: {file_name} - 1 page, {len(result)} chunks")
        return result, 1
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize a URL by standardizing protocol, removing unnecessary query parameters,
        and ensuring consistent formatting.
        
        Args:
            url: The URL to normalize
            
        Returns:
            A normalized version of the URL
        """
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Standardize protocol (prefer https)
        scheme = 'https' if parsed_url.scheme in ('http', 'https') else parsed_url.scheme
        
        # Remove trailing slashes from path
        path = parsed_url.path.rstrip('/')
        if not path:
            path = '/'
        
        # Parse and filter query parameters (could be extended to remove tracking params like utm_*)
        query_params = parse_qs(parsed_url.query)
        filtered_params = {k: v for k, v in query_params.items() if not k.startswith('utm_')}
        query_string = urlencode(filtered_params, doseq=True) if filtered_params else ''
        
        # Reconstruct the URL
        normalized_url = urlunparse((
            scheme,
            parsed_url.netloc,
            path,
            parsed_url.params,
            query_string,
            ''  # Remove fragment
        ))
        
        return normalized_url
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if a string is a properly formatted URL.
        
        Args:
            url: The URL to validate
            
        Returns:
            True if the URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            # Check if scheme and netloc are present
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    async def process_web_content(self, url: str, with_screenshot: bool = True) -> Tuple[List[Dict[str, Any]], str, int]:
        """
        Process a web page by downloading content, cleaning HTML, and optionally taking a screenshot.
        
        Args:
            url: The URL of the web page to process
            with_screenshot: Whether to take a screenshot of the web page
            
        Returns:
            A tuple containing:
                - A list of dictionaries with chunk text, page number, and images
                - The title of the web page
                - The total number of chunks created
        """
        # Validate the URL
        if not self.validate_url(url):
            raise ValueError(f"Invalid URL format: {url}")
        
        # Normalize the URL
        normalized_url = self.normalize_url(url)
        self.logger.info(f"Processing web content from URL: {normalized_url} (original: {url})")
        
        # Download the web page content
        response = await self.http_client.get(normalized_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the title
        title = soup.title.string if soup.title else "Untitled Web Page"
        
        # Clean the HTML by removing unwanted elements
        for element in soup.select('script, style, nav, footer, header, [style*="display:none"], [style*="display: none"], [hidden]'):
            element.decompose()
        
        # Extract the main content
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        # Extract text from the main content
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
        
        # Clean the text
        cleaned_text = self.clean_pdf_text(text)  # Reusing the PDF text cleaning method
        
        # Use semantic chunking
        chunks = self.semantic_chunk_text(cleaned_text)
        
        result = []
        
        # Create a result entry for each chunk
        for chunk_index, chunk_text in enumerate(chunks):
            chunk_id = f"{normalized_url.replace('://', '_').replace('/', '_')}_c{chunk_index+1}"
            
            result.append({
                "chunk_id": chunk_id,
                "chunk_text": chunk_text,
                "page_number": 1,  # Web pages are considered single-page
                "images": [],  # No images by default
                "source_type": "web",
                "page_has_images": False,
                "doc_name": normalized_url
            })
        
        
        self.logger.info(f"Processed web content from URL: {url} - {len(chunks)} chunks")
        return result, title, len(result)
    
    
    def _process_text(self, file_content: bytes, file_name: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Process a plain text file and extract text chunks.
        
        Args:
            file_content: The file content as bytes
            file_name: The name of the file
            
        Returns:
            A tuple containing:
                - A list of dictionaries with chunk text and page number
                - The total number of pages processed (always 1 for text files)
        """
        self.logger.info(f"Processing Text: {file_name}")
        
        # Decode the text content
        text = file_content.decode("utf-8", errors="replace")
        
        # Clean the text
        cleaned_text = self.clean_pdf_text(text)
        
        # Use semantic chunking
        chunks = self.semantic_chunk_text(cleaned_text)
        
        result = []
        
        # Create a result entry for each chunk
        for chunk_index, chunk_text in enumerate(chunks):
            chunk_id = f"{file_name}_c{chunk_index+1}"
            
            result.append({
                "chunk_id": chunk_id,
                "chunk_text": chunk_text,
                "page_number": 1,  # Text files are considered single-page
                "images": [],  # No images in text files
                "source_type": "text",
                "doc_name": file_name
            })
        
        self.logger.info(f"Processed Text: {file_name} - 1 page, {len(result)} chunks")
        return result, 1
    
    def _process_docx(self, file_content: bytes, file_name: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Process a DOCX file and extract text chunks.
        
        Args:
            file_content: The file content as bytes
            file_name: The name of the file
            
        Returns:
            A tuple containing:
                - A list of dictionaries with chunk text and page number
                - The total number of pages processed (always 1 for DOCX files since we don't track pages)
        """
        self.logger.info(f"Processing DOCX: {file_name}")
        
        # Create a BytesIO object from the file content
        docx_bytes = io.BytesIO(file_content)
        
        try:
            # Open the DOCX file
            doc = docx.Document(docx_bytes)
            
            # Extract text from paragraphs
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            
            # Join paragraphs with newlines
            text = "\n".join(paragraphs)
            
            # Clean the text
            cleaned_text = self.clean_pdf_text(text)
            
            # Use semantic chunking
            chunks = self.semantic_chunk_text(cleaned_text)
            
            result = []
            
            # Create a result entry for each chunk
            for chunk_index, chunk_text in enumerate(chunks):
                chunk_id = f"{file_name}_c{chunk_index+1}"
                
                result.append({
                    "chunk_id": chunk_id,
                    "chunk_text": chunk_text,
                    "page_number": 1,  # DOCX files are considered single-page for simplicity
                    "images": [],  # We're not extracting images from DOCX files
                    "source_type": "docx",
                    "doc_name": file_name
                })
            
            self.logger.info(f"Processed DOCX: {file_name} - 1 page, {len(result)} chunks")
            return result, 1
        except Exception as e:
            self.logger.error(f"Error processing DOCX file {file_name}: {str(e)}")
            return [], 0
    
    def _process_image(self, file_content: bytes, file_name: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Process an image file, convert to base64, and optionally extract text with OCR.
        
        Args:
            file_content: The file content as bytes
            file_name: The name of the file
            
        Returns:
            A tuple containing:
                - A list with a single dictionary containing the image and any extracted text
                - The total number of pages processed (always 1 for images)
        """
        self.logger.info(f"Processing Image: {file_name}")
        
        # Use the file content directly
        content = file_content
        
        # Convert image to base64
        image_base64 = base64.b64encode(content).decode("utf-8")
        
        # Determine MIME type from file extension
        ext = os.path.splitext(file_name)[1].lower()
        mime_type = f"image/{ext[1:]}" if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"] else "image/unknown"
        
        # Add data URI prefix for proper display in image viewers
        image_base64_with_prefix = f"data:image/{ext[1:]};base64,{image_base64}"
        
        # Optional: Extract text with OCR
        # This is marked as optional in the requirements, so we'll include it but it can be disabled
        try:
            # Open the image with PIL
            image = Image.open(io.BytesIO(content))
            
            # Extract text with pytesseract
            text = pytesseract.image_to_string(image)
            
            # Clean and chunk the text if any was extracted
            if text and not text.isspace():
                # Clean the extracted text
                cleaned_text = self.clean_pdf_text(text)
                # Use semantic chunking
                chunks = self.semantic_chunk_text(cleaned_text)
            else:
                chunks = ["[Image with no extractable text]"]
        except Exception as e:
            self.logger.error(f"Error performing OCR on image {file_name}: {str(e)}")
            chunks = ["[Image with no extractable text]"]
        
        result = []
        
        # Create a result entry for each chunk
        for chunk_index, chunk_text in enumerate(chunks):
            chunk_id = f"{file_name}_c{chunk_index+1}"
            
            # Create image entry
            image_entry = {
                "id": "0",
                "base64": image_base64_with_prefix,
                "mime_type": mime_type
            }
            
            result.append({
                "chunk_id": chunk_id,
                "chunk_text": chunk_text,
                "page_number": 1,  # Images are considered single-page
                "images": [image_entry],
                "images_base64": [image_entry],  # Add images_base64 field for compatibility with chat service
                "source_type": "image",
                "doc_name": file_name
            })
        
        self.logger.info(f"Processed Image: {file_name} - 1 page, {len(result)} chunks")
        return result, 1
