#!/bin/bash

# Check if .env file exists, if not create from example
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit the .env file with your API keys before continuing."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start the containers
echo "Building and starting containers..."
docker-compose up -d --build

# Check if containers are running
if [ $? -eq 0 ]; then
    echo "Containers started successfully!"
    echo "The application is now available at http://localhost:8000"
    echo "API documentation is available at http://localhost:8000/docs"
else
    echo "Failed to start containers. Please check the logs with 'docker-compose logs'."
    exit 1
fi
