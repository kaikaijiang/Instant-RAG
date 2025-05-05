# Docker Setup for Instant-RAG Frontend

This directory contains Docker configuration files for the Instant-RAG frontend application.

## Files

- `Dockerfile`: Multi-stage build for the Next.js frontend application
- `docker-compose.yml`: Compose file that sets up the frontend, backend, and database services
- `.dockerignore`: Specifies files to exclude from the Docker build context
- `.env.example`: Example environment variables needed for the application

## Usage

### Running the Frontend Only

To build and run just the frontend container:

```bash
# Navigate to the frontend directory
cd instant-rag-ui

# Build the Docker image
docker build -t instant-rag-frontend -f .docker/Dockerfile .

# Run the container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  -e NEXTAUTH_SECRET=your-secret-key \
  -e NEXTAUTH_URL=http://localhost:3000 \
  instant-rag-frontend
```

### Running the Complete Stack

To run the complete application stack (frontend, backend, and database):

1. Copy the example environment file and modify as needed:

```bash
cp .docker/.env.example .docker/.env
```

2. Edit `.docker/.env` to set your API keys and secrets.

3. Start the services using docker-compose:

```bash
# Navigate to the frontend directory
cd instant-rag-ui

# Start the services
docker-compose -f .docker/docker-compose.yml up -d
```

4. Access the application at http://localhost:3000

## Environment Variables

### Frontend Environment Variables

- `NEXT_PUBLIC_API_URL`: URL of the backend API (default: http://backend:8000 in Docker)
- `NEXT_PUBLIC_USE_MOCK_API`: Set to 'true' to use mock implementations instead of real API calls
- `NEXTAUTH_SECRET`: Secret key for JWT encryption
- `NEXTAUTH_URL`: URL of the NextAuth.js service (default: http://localhost:3000)

### Backend Environment Variables

- `GEMINI_API_KEY`: API key for Google Gemini AI
- `ENCRYPTION_KEY`: Key used for encrypting sensitive data
- `JWT_SECRET_KEY`: Secret key for JWT token generation and validation

## Development

For development, it's recommended to run the application outside of Docker using:

```bash
npm run dev
```

The Docker setup is primarily intended for production or testing environments.
