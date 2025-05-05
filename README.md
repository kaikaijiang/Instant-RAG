# Instant-RAG

A one-click template that turns any folder of PDFs, markdown files or web pages into a chat interface (RAG-style) with citations and source previews.

## Overview

Instant-RAG is an AI-powered multi-project RAG (Retrieval-Augmented Generation) system. It allows you to create and manage multiple projects, upload documents, and chat with AI using your documents as context.

## Features

- **Multi-project Management**: Create and manage multiple RAG projects
- **Document Processing**: Upload and process documents (PDF, TXT, DOCX)
- **Email Integration**: Ingest and summarize emails for RAG-based queries
- **Chat Interface**: Chat with AI using your documents as context
- **Citations**: Get answers with citations to source documents
- **Modern UI**: Dark mode UI with clean, modern design

## Project Structure

The project consists of two main components:

```
Instant-RAG/
├── instant-rag-ui/        # Frontend Next.js application
├── instant-rag-backend/   # Backend FastAPI application
└── README.md              # This file
```

### Frontend Structure (instant-rag-ui)

```
instant-rag-ui/
├── src/
│   ├── app/                 # Next.js App Router
│   ├── components/          # React components
│   │   ├── ui/              # shadcn/ui components
│   │   ├── SidebarProjects.tsx
│   │   ├── ProjectWorkspace.tsx
│   │   └── AppLayout.tsx
│   ├── hooks/               # Custom React hooks
│   │   ├── useProjectStore.ts
│   │   └── useFileUpload.ts
│   ├── services/            # API services
│   │   └── api.ts
│   └── utils/               # Utility functions
│       └── helpers.ts
```

### Backend Structure (instant-rag-backend)

```
instant-rag-backend/
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

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL with pgvector extension
- Google Gemini API key
- Docker and Docker Compose (optional, for containerized deployment)

### Backend Setup (instant-rag-backend)

1. Create a virtual environment and activate it:

```bash
cd instant-rag-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a PostgreSQL database:

```bash
createdb instant_rag
```

4. Install the pgvector extension in your PostgreSQL database:

```sql
CREATE EXTENSION vector;
```

5. Initialize the database:

```bash
python init_db.py
```

6. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

7. Edit the `.env` file with your configuration:

```
DATABASE_URL=postgresql+asyncpg://yourusername:yourpassword@localhost/instant_rag
GEMINI_API_KEY=your_gemini_api_key_here
```

8. Run the backend server:

```bash
python run.py -c config/config.yaml -p 8000
```

The API will be available at http://localhost:8000.

### Frontend Setup (instant-rag-ui)

1. Install dependencies:

```bash
cd instant-rag-ui
npm install
```

2. Run the development server:

```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

#### Next.js Startup Flow

When you run `npm run dev`, the Next.js development server starts and follows this flow:

1. The entry point is `src/app/layout.tsx` which defines the root HTML structure
2. Then `src/app/page.tsx` is loaded as the main page component
3. The page component renders `AppLayout` which sets up the main application structure with sidebar and workspace areas

#### Configuring API Connection

The frontend has been configured to support both real API calls and mock implementations. You can control this behavior using environment variables:

1. Create a `.env.local` file in the root of the frontend project with the following options:

```
# Backend API URL (defaults to http://localhost:8000 if not set)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Set to 'true' to use mock implementations instead of real API calls
NEXT_PUBLIC_USE_MOCK_API=false
```

2. The API configuration is managed through the `API_CONFIG` object in `src/services/api.ts`:

```typescript
const API_CONFIG = {
  // Base URL for the API - defaults to localhost:8000 if not set in environment
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // Set to true to use mock implementations instead of real API calls
  useMocks: process.env.NEXT_PUBLIC_USE_MOCK_API === 'true' || false,
  
  // Artificial delay for mock responses (in ms)
  mockDelay: 800
};
```

3. Each API function checks the `useMocks` flag to determine whether to use the mock implementation or make a real API call:

```typescript
export async function fetchProjects(): Promise<Project[]> {
  if (API_CONFIG.useMocks) {
    // Mock implementation
    // ...
  } else {
    // Real API implementation
    // ...
  }
}
```

This configuration allows you to:
- Develop the frontend without a running backend by setting `NEXT_PUBLIC_USE_MOCK_API=true`
- Connect to a backend running on a different host or port by changing `NEXT_PUBLIC_API_URL`
- Easily switch between mock and real implementations for testing purposes

#### API Integration

The frontend has been updated to properly integrate with the backend API:

1. The project store (`useProjectStore.ts`) now uses the API service to:
   - Load projects from the backend when the application starts
   - Create new projects by sending POST requests to the backend
   - Delete projects by sending DELETE requests to the backend
   - Show loading states during API operations

2. The SidebarProjects component has been updated to:
   - Call `loadProjects()` when the component mounts
   - Display a loading indicator while projects are being fetched
   - Disable buttons during API operations

This ensures that when you create a project in the frontend UI, it will be properly sent to the backend API and stored in the database.

### Docker Deployment

You can also run the entire application stack using Docker and Docker Compose. This is the recommended approach for production deployments.

#### Prerequisites

- Docker and Docker Compose installed on your system
- Google Gemini API key

#### Quick Start

1. Clone the repository:

```bash
git clone https://github.com/yourusername/Instant-RAG.git
cd Instant-RAG
```

2. Create a `.env` file based on the example:

```bash
cp .env.example .env
```

3. Edit the `.env` file to set your API keys and secrets:

```
NEXTAUTH_SECRET=your-secret-key-for-jwt-encryption
GEMINI_API_KEY=your-gemini-api-key-here
ENCRYPTION_KEY=your-encryption-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

4. Start the application stack:

```bash
docker-compose up -d
```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

#### Individual Docker Setups

Both the frontend and backend components have their own Docker configurations in their respective `.docker` directories:

- **Frontend**: `instant-rag-ui/.docker/`
- **Backend**: `instant-rag-backend/.docker/`

Each directory contains:
- `Dockerfile`: Build configuration for the component
- `docker-compose.yml`: Compose file for running the component
- `.env.example`: Example environment variables
- `README.md`: Detailed instructions for Docker deployment

You can use these individual setups if you want to run only one component in Docker.

## Usage

1. **Create a Project**: Click the "+" button in the sidebar to create a new project.
2. **Upload Documents**: Select a project, then use the drag-and-drop area to upload documents.
3. **Email Integration** (Optional):
   - Configure email settings via the UI
   - Ingest emails from your configured mailbox
   - Generate summaries of ingested emails
4. **Chat with AI**: Once documents are uploaded, use the chat interface to ask questions about your documents.

## User Management

### Initializing the First User

The system is designed to allow only the first user to register as an admin. This is a security measure to prevent unauthorized access.

1. **Register the First User (Admin)**:

   You can register the first user (admin) using the registration API endpoint:

   ```bash
   curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@example.com", "password": "your_secure_password"}'
   ```

   Alternatively, you can use the provided test script:

   ```bash
   cd instant-rag-backend
   python tests/register_test_user.py
   ```

   Note: The registration endpoint will only work for the first user. After that, it will return a 403 Forbidden error.

2. **Create Additional Users**:

   After the first user is created, you can create additional users using the `create_test_user.py` script:

   ```bash
   cd instant-rag-backend
   python tests/create_test_user.py
   ```

   This script will create a test user with a random email and the password "password123".

   You can modify the script to create users with specific credentials:

   ```python
   # In create_test_user.py
   # Change these values to create a user with specific credentials
   email = "user@example.com"
   password = "your_secure_password"
   role = "user"  # or "admin"
   ```

3. **Login with a User**:

   Once a user is created, you can log in using the login API endpoint:

   ```bash
   curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=your_secure_password"
   ```

   Alternatively, you can use the provided test script:

   ```bash
   cd instant-rag-backend
   python tests/test_project_list.py
   ```

   This script will log in with the test user and create a test project.

### Deleting Users

Currently, there is no direct API endpoint to delete users. However, you can delete users directly from the database:

```sql
-- Connect to your PostgreSQL database
psql instant_rag

-- List all users
SELECT id, email, role FROM users;

-- Delete a specific user
DELETE FROM users WHERE email = 'user@example.com';
```

Note: Deleting a user will also delete all projects and documents associated with that user due to the cascade delete constraint.

## Testing

### Backend Testing

Several test scripts are available in the backend directory:

```bash
# Test user registration and login
python tests/register_test_user.py
python tests/create_test_user.py
python tests/test_project_list.py

# Test document upload
python tests/create_test_files.py
python tests/test_document_upload.py

# Test email API
python tests/test_email_api.py

# Test chat query
python tests/test_chat_query.py

# List available projects
python tests/list_projects.py
```

### Frontend Testing

```bash
# Run tests
npm test

# Build for production
npm run build
```

## API Documentation

Once the backend server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key API Endpoints

#### Project Endpoints

- `POST /project/create` - Create a new project
- `DELETE /project/{id}` - Delete a project
- `GET /project/list` - List all projects
- `GET /project/documents/{id}` - Get all documents for a project
- `POST /project/upload_docs` - Upload documents to a project

#### Email Endpoints

- `POST /project/setup_email` - Configure email settings for a project
- `POST /project/ingest_emails` - Fetch and process emails based on configured settings
- `POST /project/summarize_emails` - Generate and store summaries of ingested emails

#### Chat Endpoints

- `POST /chat/query` - Send a query to the chat and get a response
- `GET /chat/history/{project_id}` - Get chat history for a project

### Chat Query Endpoint

The `/chat/query` endpoint allows users to ask questions to their selected project (documents + emails).

**Request Format**:

```json
{
  "project_id": "string",
  "question": "string",
  "top_k": 5
}
```

**Response Format**:

```json
{
  "answer": "LLM answer text",
  "citations": [
    {
      "doc_name": "document_name.pdf",
      "page_number": 3,
      "source_type": "pdf",
      "images_base64": ["base64_encoded_image_1", "base64_encoded_image_2"]
    },
    {
      "doc_name": "another_document.md",
      "page_number": null,
      "source_type": "markdown",
      "images_base64": null
    }
  ]
}
```

## Development

### Frontend Development

- **Add new shadcn/ui components**:
  ```bash
  cd instant-rag-ui
  npx shadcn@latest add [component-name]
  ```

- **Build for production**:
  ```bash
  cd instant-rag-ui
  npm run build
  ```

### Backend Development

To run the server in development mode with auto-reload:

```bash
cd instant-rag-backend
DEBUG=True python run.py -c config/config.yaml -p 8000
```

## License

MIT
