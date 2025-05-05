import httpx
import asyncio
import json
import os
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_EMAIL = f"test_{uuid4()}@example.com"
TEST_PASSWORD = "password123"

# Global variables to store tokens
admin_token = None

async def test_register():
    """Test user registration."""
    global admin_token
    
    async with httpx.AsyncClient() as client:
        # Register a new admin user
        response = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        print(f"Register response: {response.status_code}")
        print(response.json())
        
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["email"] == TEST_EMAIL
        assert response.json()["role"] == "admin"

async def test_login():
    """Test user login."""
    global admin_token
    
    async with httpx.AsyncClient() as client:
        # Login with the admin user
        response = await client.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Login response: {response.status_code}")
        print(response.json())
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
        
        admin_token = response.json()["access_token"]

async def test_create_project():
    """Test creating a project with authentication."""
    global admin_token
    
    async with httpx.AsyncClient() as client:
        # Create a project
        response = await client.post(
            f"{BASE_URL}/project/create",
            json={
                "name": "Test Project",
                "description": "A test project created with authentication"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        print(f"Create project response: {response.status_code}")
        print(response.json())
        
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["name"] == "Test Project"
        assert "user_id" in response.json()
        
        # Store the project ID for later tests
        project_id = response.json()["id"]
        
        # List projects
        response = await client.get(
            f"{BASE_URL}/project/list",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        print(f"List projects response: {response.status_code}")
        print(response.json())
        
        assert response.status_code == 200
        assert "projects" in response.json()
        assert len(response.json()["projects"]) > 0
        
        # Delete the project
        response = await client.delete(
            f"{BASE_URL}/project/{project_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        print(f"Delete project response: {response.status_code}")
        print(response.json())
        
        assert response.status_code == 200
        assert response.json()["success"] is True

async def test_register_second_user():
    """Test that registering a second user fails."""
    
    async with httpx.AsyncClient() as client:
        # Try to register a second user
        response = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": f"second_{uuid4()}@example.com",
                "password": "password123"
            }
        )
        
        print(f"Register second user response: {response.status_code}")
        print(response.json())
        
        # Should fail with 403 Forbidden
        assert response.status_code == 403

async def main():
    """Run all tests."""
    await test_register()
    await test_login()
    await test_create_project()
    await test_register_second_user()

if __name__ == "__main__":
    asyncio.run(main())
