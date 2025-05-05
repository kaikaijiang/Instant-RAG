from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import imaplib
import email
from email.header import decode_header
import os
import re
import json
#import aiohttp
import shutil
from uuid import uuid4
import base64
import asyncio
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from models.email import EmailSettings, EmailSummary
from models.rag_chunk import RagChunk
from services.llm_service import LLMService
from services.embedding_service import EmbeddingService
from services.logging_service import LoggingService

logger = LoggingService()

class EmailService:
    """
    Service for handling email-related operations.
    """
    
    # Secret key for encryption (in production, this should be stored securely)
    _ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "instant_rag_default_encryption_key_12345")
    
    @staticmethod
    def _get_encryption_key(salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Generate an encryption key using PBKDF2.
        
        Args:
            salt: Optional salt for key derivation
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(EmailService._ENCRYPTION_KEY.encode()))
        return key, salt
    
    @staticmethod
    def _encrypt_password(password: str) -> Tuple[str, str]:
        """
        Encrypt a password.
        
        Args:
            password: The password to encrypt
            
        Returns:
            Tuple of (encrypted_password, salt_base64)
        """
        key, salt = EmailService._get_encryption_key()
        f = Fernet(key)
        encrypted_password = f.encrypt(password.encode()).decode()
        salt_base64 = base64.b64encode(salt).decode()
        return encrypted_password, salt_base64
    
    @staticmethod
    def _decrypt_password(encrypted_password: str, salt_base64: str) -> str:
        """
        Decrypt a password.
        
        Args:
            encrypted_password: The encrypted password
            salt_base64: The salt used for encryption
            
        Returns:
            The decrypted password
        """
        salt = base64.b64decode(salt_base64)
        key, _ = EmailService._get_encryption_key(salt)
        f = Fernet(key)
        return f.decrypt(encrypted_password.encode()).decode()
    
    @staticmethod
    async def save_email_settings(
        db: AsyncSession,
        project_id: str,
        imap_server: str,
        email_address: str,
        password: str,
        sender_filter: Optional[str] = None,
        subject_keywords: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> EmailSettings:
        """
        Save email settings for a project.
        
        Args:
            db: Database session
            project_id: ID of the project
            imap_server: IMAP server address
            email_address: Email address
            password: Email password
            sender_filter: Filter emails by sender
            subject_keywords: Filter emails by subject keywords
            start_date: Start date for email range
            end_date: End date for email range
            
        Returns:
            The created email settings
        """
        logger.info(f"Saving email settings for project {project_id}")
        
        # Encrypt the password
        encrypted_password, salt = EmailService._encrypt_password(password)
        
        # Convert subject_keywords to string if it's a list
        if isinstance(subject_keywords, list):
            subject_keywords = ",".join(subject_keywords)
        
        # Check if settings already exist for this project
        result = await db.execute(
            select(EmailSettings).where(EmailSettings.project_id == project_id)
        )
        existing_settings = result.scalars().first()
        
        if existing_settings:
            # Update existing settings
            existing_settings.imap_server = imap_server
            existing_settings.email_address = email_address
            existing_settings.password = encrypted_password
            existing_settings.password_salt = salt
            existing_settings.sender_filter = sender_filter
            existing_settings.subject_keywords = subject_keywords
            existing_settings.start_date = start_date
            existing_settings.end_date = end_date
            
            await db.commit()
            logger.info(f"Updated email settings for project {project_id}")
            return existing_settings
        else:
            # Create new settings
            email_settings = EmailSettings(
                project_id=project_id,
                imap_server=imap_server,
                email_address=email_address,
                password=encrypted_password,
                password_salt=salt,
                sender_filter=sender_filter,
                subject_keywords=subject_keywords,
                start_date=start_date,
                end_date=end_date
            )
            
            db.add(email_settings)
            await db.commit()
            await db.refresh(email_settings)
            logger.info(f"Created new email settings for project {project_id}")
            return email_settings
    
    @staticmethod
    async def get_email_settings(db: AsyncSession, project_id: str) -> Optional[EmailSettings]:
        """
        Get email settings for a project.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            The email settings if found, None otherwise
        """
        result = await db.execute(
            select(EmailSettings).where(EmailSettings.project_id == project_id)
        )
        return result.scalars().first()
    
    @staticmethod
    def _decode_email_subject(subject):
        """
        Decode email subject.
        
        Args:
            subject: The encoded subject
            
        Returns:
            The decoded subject
        """
        decoded_subject = ""
        if subject:
            decoded_chunks = decode_header(subject)
            for chunk, encoding in decoded_chunks:
                if isinstance(chunk, bytes):
                    if encoding:
                        decoded_subject += chunk.decode(encoding, errors='replace')
                    else:
                        decoded_subject += chunk.decode('utf-8', errors='replace')
                else:
                    decoded_subject += chunk
        return decoded_subject
    
    @staticmethod
    def _get_email_body(msg):
        """
        Extract plain text body from email message.
        
        Args:
            msg: The email message
            
        Returns:
            The plain text body
        """
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Get plain text content
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='replace')
                        break
                    except Exception as e:
                        logger.error(f"Error decoding email body: {str(e)}")
                        body = "Error decoding email body"
        else:
            # Not multipart - get payload directly
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors='replace')
            except Exception as e:
                logger.error(f"Error decoding email body: {str(e)}")
                body = "Error decoding email body"
        
        # Clean the body
        clean_body = EmailService._clean_email_body(body)
        return clean_body
    
    @staticmethod
    def _clean_email_body(body: str) -> str:
        """
        Clean the email body by removing unnecessary characters and text.
        
        Args:
            body: The raw email body text
            
        Returns:
            The cleaned email body
        """
        if not body:
            return ""
        
        # Remove email signature blocks (common patterns)
        signature_patterns = [
            r"--\s*\n.*",  # Standard signature separator
            r"Sent from my .*",  # Mobile signatures
            r"Get Outlook for .*",  # Outlook signatures
            r"________________________________.*",  # Outlook separator
            r"On .* wrote:.*",  # Reply headers
            r"From:.*Sent:.*To:.*Subject:.*",  # Forwarded email headers
        ]
        
        cleaned_body = body
        
        # Apply signature pattern removals
        for pattern in signature_patterns:
            cleaned_body = re.sub(pattern, "", cleaned_body, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove excessive whitespace
        cleaned_body = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned_body)
        
        # Remove common email disclaimer texts
        disclaimer_patterns = [
            r"CONFIDENTIALITY NOTICE:.*",
            r"This email and any files.*",
            r"This message is confidential.*",
            r"The information contained in this.*",
            r"DISCLAIMER:.*",
        ]
        
        for pattern in disclaimer_patterns:
            cleaned_body = re.sub(pattern, "", cleaned_body, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags if any
        cleaned_body = re.sub(r"<[^>]+>", "", cleaned_body)
        
        # Remove URLs
        cleaned_body = re.sub(r"https?://\S+", "[URL]", cleaned_body)
        
        # Remove excessive spaces
        cleaned_body = re.sub(r" +", " ", cleaned_body)
        
        # Remove leading/trailing whitespace
        cleaned_body = cleaned_body.strip()
        
        return cleaned_body
    
    @staticmethod
    def _parse_date(date_str):
        """
        Parse email date string to datetime.
        
        Args:
            date_str: The date string
            
        Returns:
            Datetime object or None if parsing fails
        """
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return None
    
    @staticmethod
    async def fetch_emails(db: AsyncSession, project_id: str) -> List[Dict[str, Any]]:
        """
        Fetch emails for a project based on the email settings.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            List of fetched emails
        """
        logger.info(f"Fetching emails for project {project_id}")
        
        # Get email settings
        email_settings = await EmailService.get_email_settings(db, project_id)
        if not email_settings:
            raise ValueError(f"No email settings found for project {project_id}")
        
        # Decrypt password
        password = EmailService._decrypt_password(
            email_settings.password, 
            email_settings.password_salt
        )
        
        # Parse subject keywords if provided
        subject_keywords = []
        if email_settings.subject_keywords:
            if ',' in email_settings.subject_keywords:
                subject_keywords = [kw.strip() for kw in email_settings.subject_keywords.split(',')]
            else:
                subject_keywords = [email_settings.subject_keywords.strip()]
        
        # Parse date range
        start_date = None
        end_date = None
        if email_settings.start_date:
            try:
                start_date = datetime.fromisoformat(email_settings.start_date)
            except ValueError:
                logger.warning(f"Invalid start date format: {email_settings.start_date}")
        
        if email_settings.end_date:
            try:
                end_date = datetime.fromisoformat(email_settings.end_date)
            except ValueError:
                logger.warning(f"Invalid end date format: {email_settings.end_date}")
        
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "emails", project_id)
        os.makedirs(data_dir, exist_ok=True)
        
        # Connect to IMAP server
        try:
            logger.info(f"Connecting to IMAP server: {email_settings.imap_server}")
            mail = imaplib.IMAP4_SSL(email_settings.imap_server)
            logger.info(f"Logging in with email: {email_settings.email_address}")
            mail.login(email_settings.email_address, password)
            logger.info("Login successful, selecting INBOX")
            mail.select('INBOX')
            logger.info("INBOX selected successfully")
            
            # Build search criteria
            search_criteria = []
            
            # Add date range if provided
            if start_date:
                # Format: DD-MMM-YYYY
                date_str = start_date.strftime("%d-%b-%Y")
                search_criteria.append(f'SINCE {date_str}')
            
            if end_date:
                # Format: DD-MMM-YYYY
                date_str = end_date.strftime("%d-%b-%Y")
                search_criteria.append(f'BEFORE {date_str}')
            
            # Add sender filter if provided
            if email_settings.sender_filter:
                search_criteria.append(f'FROM "{email_settings.sender_filter}"')
            
            # Combine search criteria
            if search_criteria:
                search_command = ' '.join(search_criteria)
                logger.info(f"Searching with criteria: {search_command}")
                status, data = mail.search(None, search_command)
            else:
                logger.info("Searching for ALL emails")
                status, data = mail.search(None, 'ALL')
            
            if status != 'OK':
                raise Exception(f"Error searching emails: {status}")
            
            logger.info(f"Search completed with status: {status}")
            
            # Get email IDs
            email_ids = data[0].split()
            logger.info(f"Found {len(email_ids)} emails matching criteria")
            
            # Limit to 50 most recent emails
            if len(email_ids) > 200:
                email_ids = email_ids[-200:]
                logger.info(f"Limiting to 200 most recent emails")
            
            # Fetch and process emails
            emails = []
            
            for email_id in email_ids:
                status, data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    logger.warning(f"Error fetching email {email_id}: {status}")
                    continue
                
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract email details
                subject = EmailService._decode_email_subject(msg['Subject'])
                sender = msg['From']
                date = msg['Date']
                date_obj = EmailService._parse_date(date)
                
                # Apply subject keyword filter if provided
                if subject_keywords:
                    subject_match = False
                    for keyword in subject_keywords:
                        if keyword.lower() in subject.lower():
                            subject_match = True
                            break
                    
                    if not subject_match:
                        continue
                
                # Extract body
                body = EmailService._get_email_body(msg)
                
                # Add to results
                emails.append({
                    "id": email_id.decode(),
                    "subject": subject,
                    "sender": sender,
                    "date": date_obj.isoformat() if date_obj else date,
                    "body": body
                })

            
            # Save emails to file
            with open(os.path.join(data_dir, "raw_emails.jsonl"), 'w') as f:
                for email_data in emails:
                    f.write(json.dumps(email_data) + '\n')
            
            logger.info(f"Successfully fetched {len(emails)} emails for project {project_id}")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            raise Exception(f"Error fetching emails: {str(e)}")
        finally:
            try:
                mail.logout()
            except:
                pass
    
    @staticmethod
    async def summarize_emails(db: AsyncSession, project_id: str) -> List[Dict[str, Any]]:
        """
        Summarize emails for a project and store as RAG chunks.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            List of summarized emails with their IDs
        """
        logger.info(f"------- Summarizing emails for project {project_id}")
        
        # Check if raw emails exist
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "emails", project_id)
        raw_emails_path = os.path.join(data_dir, "raw_emails.jsonl")
        
        if not os.path.exists(raw_emails_path):
            # Try to fetch emails first
            await EmailService.fetch_emails(db, project_id)
            
            if not os.path.exists(raw_emails_path):
                raise ValueError(f"No raw emails found for project {project_id}")
        
        # Load raw emails
        emails = []
        with open(raw_emails_path, 'r') as f:
            for line in f:
                if line.strip():
                    emails.append(json.loads(line))
        
        if not emails:
            raise ValueError(f"No emails found in raw_emails.jsonl for project {project_id}")
        
        # Get Gemini API key
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        # Initialize embedding service
        embedding_service = EmbeddingService()
        
        # Import Document model and DocumentStatus enum
        from models.document import Document, DocumentStatus
        
        # Create a document record for emails if it doesn't exist
        email_doc_id = f"email_{project_id}"
        result = await db.execute(
            select(Document).where(Document.id == email_doc_id)
        )
        email_document = result.scalars().first()
        
        if not email_document:
            logger.info(f"Creating document record for emails in project {project_id}")
            email_document = Document(
                id=email_doc_id,
                name="Email Collection",
                size=0,  # Not applicable for emails
                type="application/email",
                project_id=project_id,
                uploaded_at=datetime.now(),
                status=DocumentStatus.COMPLETED,
                content="Email collection processed via IMAP"
            )
            db.add(email_document)
            await db.commit()
            await db.refresh(email_document)
        
        # Process each email
        summaries = []
        
        for email_data in emails:
            try:
                
                # Create a simple summary without using LLM
                logger.info(f"Creating basic summary for email: {email_data['subject']}")
                              
                # Create a simple summary
                summary_text = f"Email from {email_data['sender']} with subject '{email_data['subject']}' received on {email_data['date']}. Content preview: {email_data['body']}"
                
                try:
                    # Generate embedding for the summary
                    logger.info(f"Generating embedding for email: {email_data['subject']}")
                    embedding = await embedding_service.generate_embedding(summary_text)
                    logger.info(f"Successfully generated embedding for email: {email_data['subject']}")
                    
                    # Create RAG chunk
                    logger.info(f"Creating RAG chunk for email: {email_data['subject']}")
                    rag_chunk = RagChunk(
                        project_id=project_id,
                        document_id=email_document.id,  # Use the document ID we created
                        chunk_id=f"email_{email_data['id']}",
                        chunk_text=summary_text,
                        embedding=embedding,
                        page_number=None,
                        doc_name=email_data['subject'],
                        source_type='email',
                        created_at=datetime.now()
                    )
                    logger.info(f"Successfully created RAG chunk for email: {email_data['subject']}")
                except Exception as e:
                    logger.error(f"Error in embedding or RAG chunk creation: {str(e)}")
                    # Create RAG chunk without embedding for testing
                    logger.info(f"Creating RAG chunk without embedding for email: {email_data['subject']}")
                    rag_chunk = RagChunk(
                        project_id=project_id,
                        document_id=email_document.id,
                        chunk_id=f"email_{email_data['id']}",
                        chunk_text=summary_text,
                        embedding=None,  # Skip embedding for now
                        page_number=None,
                        doc_name=email_data['subject'],
                        source_type='email',
                        created_at=datetime.now()
                    )
                
                db.add(rag_chunk)
                
                # Add to summaries list with the format expected by the EmailSummary schema
                # Ensure the id is a string, not None
                summaries.append({
                    "id": str(rag_chunk.id) if rag_chunk.id is not None else f"email_{uuid4()}",
                    "subject": email_data['subject'],
                    "summary": summary_text
                })
                
                # Create a small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error summarizing email {email_data['id']}: {str(e)}")
                continue
        
        # Commit all changes
        await db.commit()

        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
        
        logger.info(f"Successfully summarized {len(summaries)} emails for project {project_id}")
        return summaries
    
    @staticmethod
    async def get_email_summaries(db: AsyncSession, project_id: str) -> List[EmailSummary]:
        """
        Get all email summaries for a project.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            List of email summaries
        """
        # Query RAG chunks with source_type='email'
        result = await db.execute(
            select(RagChunk)
            .where(RagChunk.project_id == project_id)
            .where(RagChunk.source_type == 'email')
            .order_by(RagChunk.created_at.desc())
        )
        
        rag_chunks = result.scalars().all()
        
        # Convert to EmailSummary objects for API compatibility
        email_summaries = []
        for chunk in rag_chunks:
            # Ensure the id is a string, not None
            summary_id = str(chunk.id) if chunk.id is not None else f"email_{uuid4()}"
            
            summary = EmailSummary(
                id=summary_id,
                project_id=chunk.project_id,
                summary=chunk.chunk_text,
                timestamp=chunk.created_at
            )
            email_summaries.append(summary)
        
        return email_summaries
