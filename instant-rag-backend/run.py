import uvicorn
import os
import argparse
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Global variable to store configuration
config = {}

def load_config(config_file):
    """Load configuration from YAML file"""
    global config
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        print(f"Configuration loaded from {config_file}")
    except Exception as e:
        print(f"Error loading configuration: {e}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Instant-RAG backend server')
    parser.add_argument('-c', '--config', help='Path to configuration file')
    parser.add_argument('-p', '--port', type=int, help='Port to run the server on')
    args = parser.parse_args()
    
    # Load configuration if provided
    if args.config:
        load_config(args.config)
    
    # Get configuration from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = args.port if args.port else int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )
