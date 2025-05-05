# Docker Setup for Instant-RAG Backend

This directory contains Docker configuration files for the Instant-RAG backend application.

## Files

- `Dockerfile`: Build configuration for the Python FastAPI backend application
- `docker-compose.yml`: Compose file that sets up the backend API and PostgreSQL database
- `init-db.sql`: SQL script to initialize the PostgreSQL database with required extensions
- `.env.example`: Example environment variables needed for the application

## Usage

### Running the Backend Only

To build and run just the backend container:

```bash
# Navigate to the backend directory
cd instant-rag-backend

# Build the Docker image
docker build -t instant-rag-backend -f .docker/Dockerfile .

# Run the container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/instant_rag \
  -e GEMINI_API_KEY=your-gemini-api-key \
  -e ENCRYPTION_KEY=your-encryption-key \
  -e JWT_SECRET_KEY=your-jwt-secret-key \
  instant-rag-backend
```

Note: When running the backend container alone, you'll need to have a PostgreSQL database available at the URL specified in the DATABASE_URL environment variable.

### Running the Backend with Database

To run the backend with its PostgreSQL database:

1. Copy the example environment file and modify as needed:

```bash
cp .docker/.env.example .docker/.env
```

2. Edit `.docker/.env` to set your API keys and secrets.

3. Start the services using docker-compose:

```bash
# Navigate to the backend directory
cd instant-rag-backend

# Start the services
docker-compose -f .docker/docker-compose.yml up -d
```

4. The API will be available at http://localhost:8000

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_API_KEY`: API key for Google Gemini AI
- `ENCRYPTION_KEY`: Key used for encrypting sensitive data
- `JWT_SECRET_KEY`: Secret key for JWT token generation and validation
- `HOST`: Host to bind the server to (default: 0.0.0.0)
- `PORT`: Port to run the server on (default: 8000)
- `DEBUG`: Enable debug mode (default: False)

## Development

For development, it's recommended to run the application outside of Docker using:

```bash
python run.py
```

The Docker setup is primarily intended for production or testing environments.

## Database Initialization

The PostgreSQL database is initialized with the pgvector extension enabled, which is required for vector embeddings used in the RAG functionality. The initialization script is in `init-db.sql`.

## Volumes

The docker-compose setup includes the following volumes:

- `postgres_data`: Persistent storage for the PostgreSQL database
- `uploads`: Directory for uploaded documents
- `data`: Directory for application data, including email data
- `logs`: Directory for application logs
