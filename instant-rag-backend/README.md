# Instant-RAG Backend

This is the backend API for the Instant-RAG application, built with FastAPI, PostgreSQL, and pgvector.

## Features

- RESTful API with FastAPI
- PostgreSQL database with pgvector for vector embeddings
- SQLAlchemy ORM for database interactions
- Google Gemini Flash 2.0 for LLM capabilities
- BGE-small-en for embeddings
- Email ingestion and summarization
- Document upload and processing
- RAG-based chat functionality

## Project Structure

```
backend/
├── api/                # API routes and schemas
│   ├── routes/         # API route handlers
│   └── schemas.py      # Pydantic models for request/response
├── models/             # SQLAlchemy models
├── services/           # Business logic
├── utils/              # Utility functions
├── uploads/            # Directory for uploaded files
├── .env.example        # Example environment variables
├── main.py             # FastAPI application
├── requirements.txt    # Python dependencies
└── run.py              # Script to run the server
```

## Prerequisites

- Python 3.9+
- PostgreSQL with pgvector extension
- Google Gemini API key

## Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/instant-rag.git
cd instant-rag/backend
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a PostgreSQL database:

```bash
createdb instant_rag
```

5. Install the pgvector extension in your PostgreSQL database:

```sql
CREATE EXTENSION vector;
```

6. Initialize the database:

```bash
python init_db.py
```

This will create all the necessary tables and set up the pgvector extension. If you want to seed the database with sample data, uncomment the line at the bottom of the script.

7. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

7. Edit the `.env` file with your configuration:

```
DATABASE_URL=postgresql+asyncpg://yourusername:yourpassword@localhost/instant_rag
GEMINI_API_KEY=your_gemini_api_key_here
```

## Running the Server

```bash
python run.py
```

The API will be available at http://localhost:8000.

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Project Endpoints

- `POST /project/create` - Create a new project
- `DELETE /project/{id}` - Delete a project
- `GET /project/list` - List all projects
- `GET /project/documents/{id}` - Get all documents for a project
- `POST /project/upload_docs` - Upload documents to a project, process them, and create RAG chunks

### Document Ingestion

The document ingestion process follows these steps:

1. **Upload**: Documents are uploaded via `POST /project/upload_docs` endpoint using multipart/form-data
   - Supported formats: PDF, Markdown, and image files
   - Each file is saved to disk and a database record is created

2. **Processing**:
   - PDF files: Text is extracted per page using PyMuPDF, along with embedded images
   - Markdown files: Content is read as plain text
   - Image files: Optionally processed with OCR using pytesseract

3. **Chunking**:
   - Text is split into chunks of approximately 300-500 tokens
   - A token-aware chunker ensures semantic coherence

4. **Embedding**:
   - Each chunk is embedded using BAAI/bge-small-en model
   - Embeddings are normalized to unit length

5. **Storage**:
   - Chunks are stored in the `rag_chunks` table with their embeddings
   - Images are stored as base64 encoded strings

6. **Response**:
   - The API returns a summary of processed documents
   - Includes document names, types, pages processed, and chunks created

To test document ingestion:

```bash
# First, create test files
python ./tests/create_test_files.py

# Then run the test script
python ./tests/test_document_upload.py
```

### Email Ingestion and Summarization

The email ingestion and summarization process follows these steps:

1. **Setup**: Configure email settings via `POST /project/setup_email` endpoint
   - Provide IMAP server, email credentials, and optional filters
   - Password is securely stored using AES encryption
   - Filters can include sender email, subject keywords, and date range

2. **Ingestion**: Fetch emails via `POST /project/ingest_emails` endpoint
   - Connects to the mailbox using IMAP
   - Applies configured filters (sender, subject keywords, date range)
   - Fetches up to 50 matching emails
   - Extracts subject, sender, date, and plain text body
   - Stores raw emails in `/data/emails/{project_id}/raw_email.jsonl`

3. **Summarization**: Process emails via `POST /project/summarize_emails` endpoint
   - Loads raw email texts from previous ingestion
   - For each email, calls Google Gemini Flash 2.0 API to generate a summary
   - Embeds each summary using the local BGE-small-en model
   - Stores summaries as RAG chunks with source_type='email'
   - Makes summaries available for RAG-based queries

Email-related endpoints:

- `POST /project/setup_email` - Configure email settings for a project
- `POST /project/ingest_emails` - Fetch and process emails based on configured settings
- `POST /project/summarize_emails` - Generate and store summaries of ingested emails

To test email ingestion and summarization:

```bash
# Run the test script
python ./tests/test_email_api.py
```

Note: For the test script to work properly, you'll need to:
1. Set up a valid GEMINI_API_KEY in your .env file
2. Update the test script with valid email credentials

### Chat Endpoints

- `POST /chat/query` - Send a query to the chat and get a response
- `GET /chat/history/{project_id}` - Get chat history for a project

## Development

To run the server in development mode with auto-reload:

```bash
DEBUG=True python run.py -c .config/config.yaml -p 8000
```

## Docker Deployment

A Docker setup is provided for easy deployment:

1. Navigate to the Docker configuration directory:

```bash
cd .docker
```

2. Create a `.env` file based on the example:

```bash
cp .env.example .env
```

3. Edit the `.env` file with your API keys:

```
GEMINI_API_KEY=your_gemini_api_key_here
ENCRYPTION_KEY=your_encryption_key_here
```

4. Run the application using the provided script:

```bash
./run.sh
```

Or manually with Docker Compose:

```bash
docker-compose up -d
```

The API will be available at http://localhost:8000.

For more details, see the [Docker README](.docker/README.md).
