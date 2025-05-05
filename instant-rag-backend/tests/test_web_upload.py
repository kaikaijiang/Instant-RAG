import asyncio
import httpx
import json
import uuid
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_PROJECT_NAME = "Web Upload Test Project"
# Choose one of these URLs to test with
TEST_URL = "https://en.wikipedia.org/wiki/Artificial_intelligence"  # Larger page, might take longer
# TEST_URL = "https://example.com"  # Simple page, faster to process
# Whether to take a screenshot of the web page (set to False for faster processing)
WITH_SCREENSHOT = True
# Increase timeout to 180 seconds to allow for web page processing
TIMEOUT = 180.0

async def create_test_project():
    """Create a test project if it doesn't exist."""
    async with httpx.AsyncClient() as client:
        # Check if project already exists
        response = await client.get(f"{API_BASE_URL}/project/list")
        projects = response.json()["projects"]
        
        for project in projects:
            if project["name"] == TEST_PROJECT_NAME:
                print(f"Using existing project: {project['name']} (ID: {project['id']})")
                return project["id"]
        
        # Create a new project
        response = await client.post(
            f"{API_BASE_URL}/project/create",
            json={"name": TEST_PROJECT_NAME, "description": "Test project for web content upload"}
        )
        
        if response.status_code == 201:
            project_id = response.json()["id"]
            print(f"Created new project: {TEST_PROJECT_NAME} (ID: {project_id})")
            return project_id
        else:
            print(f"Failed to create project: {response.text}")
            return None

async def upload_web_content(project_id, url, with_screenshot=True):
    """Upload web content to the project."""
    print(f"Uploading web content from URL: {url}")
    if with_screenshot:
        print(f"This may take a while as the server needs to download the page, take a screenshot, and process the content...")
    else:
        print(f"This may take a while as the server needs to download the page and process the content...")
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT)) as client:
            response = await client.post(
                f"{API_BASE_URL}/project/upload_web",
                json={"project_id": project_id, "url": url, "with_screenshot": with_screenshot}
            )
        
            if response.status_code == 200:
                result = response.json()
                print(f"Successfully uploaded web content:")
                print(f"  Title: {result['title']}")
                print(f"  URL: {result['url']}")
                print(f"  Chunks created: {result['chunks_created']}")
                return result
            else:
                print(f"Failed to upload web content: {response.text}")
                return None
    except httpx.ReadTimeout:
        print(f"Request timed out after {TIMEOUT} seconds. The server might still be processing the request.")
        print(f"You can check the server logs for more information.")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

async def main():
    """Main function to run the test."""
    # Create a test project
    project_id = await create_test_project()
    if not project_id:
        print("Exiting due to project creation failure.")
        return
    
    # Upload web content
    result = await upload_web_content(project_id, TEST_URL, WITH_SCREENSHOT)
    if not result:
        print("Exiting due to web content upload failure.")
        return
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
