import asyncio
import json
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()

async def list_projects():
    """
    List all projects in the database.
    """
    # API endpoint
    url = "http://localhost:8000/project/list"
    
    # Make the request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                print("Projects:")
                print(json.dumps(result, indent=2))
                
                # Print a more readable list
                print("\nAvailable Projects:")
                for i, project in enumerate(result["projects"], 1):
                    print(f"{i}. ID: {project['id']}")
                    print(f"   Name: {project['name']}")
                    print(f"   Description: {project['description'] or 'N/A'}")
                    print(f"   Created: {project['created_at']}")
                    print()
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Exception: {str(e)}")

if __name__ == "__main__":
    # Run the function
    asyncio.run(list_projects())
