import httpx
import asyncio
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_EMAIL = "test_f8690a46-4577-40c6-a071-e7f7bb46bc2d@example.com"
TEST_PASSWORD = "password123"

async def register_user():
    """Register a test user."""
    async with httpx.AsyncClient() as client:
        # Register a new admin user
        response = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        print(f"Registration response status code: {response.status_code}")
        
        try:
            if response.status_code == 201:
                print(f"User registered successfully:")
                print(f"Email: {TEST_EMAIL}")
                print(f"Password: {TEST_PASSWORD}")
                print(f"Role: {response.json()['role']}")
            elif response.status_code == 403:
                print("Registration failed: A user already exists.")
                print("Trying to login with the test credentials...")
                
                # Try to login with the test credentials
                await login_user()
            else:
                print(f"Registration failed with status code: {response.status_code}")
                try:
                    print(response.json())
                except:
                    print(f"Response text: {response.text}")
        except Exception as e:
            print(f"Error processing response: {e}")
            print(f"Response text: {response.text}")

async def login_user():
    """Test user login."""
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
        
        print(f"Login response status code: {response.status_code}")
        
        try:
            if response.status_code == 200:
                print(f"Login successful with:")
                print(f"Email: {TEST_EMAIL}")
                print(f"Password: {TEST_PASSWORD}")
            else:
                print(f"Login failed with status code: {response.status_code}")
                try:
                    print(response.json())
                except:
                    print(f"Response text: {response.text}")
        except Exception as e:
            print(f"Error processing response: {e}")
            print(f"Response text: {response.text}")

if __name__ == "__main__":
    asyncio.run(register_user())
