#!/bin/bash

# This script tests the Docker setup by:
# 1. Building and starting the containers
# 2. Waiting for the API to become available
# 3. Making a simple request to the API
# 4. Stopping the containers

# Set variables
API_URL="http://localhost:8000"
MAX_RETRIES=30
RETRY_INTERVAL=2

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "No .env file found. Creating from example..."
    cp .env.example .env
    echo "Please edit the .env file with your API keys before continuing."
    exit 1
fi

# Build and start the containers
echo "Building and starting containers..."
docker-compose up -d --build

# Wait for the API to become available
echo "Waiting for the API to become available..."
for i in $(seq 1 $MAX_RETRIES); do
    if curl -s -o /dev/null -w "%{http_code}" $API_URL | grep -q "200"; then
        echo "API is available!"
        break
    fi
    
    if [ $i -eq $MAX_RETRIES ]; then
        echo "API did not become available after $MAX_RETRIES retries."
        echo "Check the logs with 'docker-compose logs app'"
        docker-compose down
        exit 1
    fi
    
    echo "Waiting for API to start (attempt $i/$MAX_RETRIES)..."
    sleep $RETRY_INTERVAL
done

# Test the API
echo "Testing the API..."
RESPONSE=$(curl -s $API_URL)
if echo $RESPONSE | grep -q "Welcome to Instant-RAG API"; then
    echo "API test successful!"
    echo "Response: $RESPONSE"
else
    echo "API test failed."
    echo "Response: $RESPONSE"
    docker-compose down
    exit 1
fi

# Show API documentation URL
echo "API documentation is available at:"
echo "- Swagger UI: $API_URL/docs"
echo "- ReDoc: $API_URL/redoc"

# Ask if user wants to stop the containers
read -p "Do you want to stop the containers? (y/n): " STOP_CONTAINERS
if [[ $STOP_CONTAINERS =~ ^[Yy]$ ]]; then
    echo "Stopping containers..."
    docker-compose down
    echo "Containers stopped."
else
    echo "Containers are still running."
    echo "You can stop them later with 'docker-compose down'"
fi

exit 0
