import httpx
import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_EMAIL = "test_f8690a46-4577-40c6-a071-e7f7bb46bc2d@example.com"
TEST_PASSWORD = "password123"

async def login_and_list_projects():
    """Login and list projects."""
    async with httpx.AsyncClient() as client:
        # Login with the test user
        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Login response status code: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return
        
        # Get the access token
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        print(f"Access token: {access_token}")
        
        # Create a project for this user
        create_project_response = await client.post(
            f"{BASE_URL}/project/create",
            json={
                "name": "Test Project from API",
                "description": "This is a test project created from the API"
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"Create project response status code: {create_project_response.status_code}")
        
        if create_project_response.status_code == 201:
            project = create_project_response.json()
            print(f"Project created: {project}")
        else:
            print(f"Failed to create project: {create_project_response.text}")
        
        # List projects
        projects_response = await client.get(
            f"{BASE_URL}/project/list",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"Projects response status code: {projects_response.status_code}")
        
        try:
            if projects_response.status_code == 200:
                projects = projects_response.json()
                print(f"Projects: {projects}")
            else:
                print(f"Failed to list projects: {projects_response.text}")
        except Exception as e:
            print(f"Error processing response: {e}")
            print(f"Response text: {projects_response.text}")

if __name__ == "__main__":
    asyncio.run(login_and_list_projects())
