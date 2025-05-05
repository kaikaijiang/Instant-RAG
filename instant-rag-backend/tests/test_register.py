import asyncio
import httpx
import json
import sys
import os

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_register():
    """
    Test the user registration endpoint.
    """
    # Define the API URL
    api_url = "http://localhost:8000/auth/register"
    
    # Define the user data
    user_data = {
        "email": "test_user@example.com",
        "password": "password123"
    }
    
    # Make the request
    async with httpx.AsyncClient() as client:
        response = await client.post(
            api_url,
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
    
    # Print the response
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Return success if the status code is 201 (Created)
    return response.status_code == 201

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_register())
    
    # Exit with the appropriate status code
    sys.exit(0 if success else 1)
