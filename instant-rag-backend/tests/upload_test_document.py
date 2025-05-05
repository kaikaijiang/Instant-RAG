import asyncio
import os
import json
import aiohttp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def get_first_project_id():
    """
    Get the ID of the first project in the database.
    """
    url = "http://localhost:8000/project/list"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                result = await response.json()
                if result["projects"]:
                    return result["projects"][0]["id"]
            
            return None

async def upload_test_document():
    """
    Upload a test document to the first project.
    """
    # Get the first project ID
    project_id = await get_first_project_id()
    
    if not project_id:
        print("No projects found. Please create a project first.")
        return
    
    print(f"Using project ID: {project_id}")
    
    # API endpoint
    url = "http://localhost:8000/project/upload_docs"
    
    # Test file path
    test_file_path = os.path.join(os.path.dirname(__file__), "test_files", "test.md")
    
    if not os.path.exists(test_file_path):
        print(f"Test file not found: {test_file_path}")
        return
    
    # Prepare form data
    data = aiohttp.FormData()
    data.add_field("project_id", project_id)
    
    # Add file - we need to keep the file open until the request is complete
    f = open(test_file_path, "rb")
    data.add_field("files", f, filename="test.md", content_type="text/markdown")
    
    # Make the request
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print("Upload Response:")
                    print(json.dumps(result, indent=2))
                else:
                    print(f"Error: {response.status}")
                    print(await response.text())
    finally:
        # Close the file
        f.close()

if __name__ == "__main__":
    # Run the function
    asyncio.run(upload_test_document())
