import asyncio
import json
import os
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()

# Check if GEMINI_API_KEY is set
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("Warning: GEMINI_API_KEY environment variable is not set.")
    print("Please set it in your .env file or export it in your shell.")
    print("You can use the example key from .env.example for testing.")
    exit(1)

async def get_first_project_id():
    """
    Get the ID of the first project in the database.
    """
    url = "http://localhost:8000/project/list"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            
            if response.status_code == 200:
                result = response.json()
                if result["projects"]:
                    return result["projects"][0]["id"]
            
            return None
        except Exception as e:
            print(f"Error getting projects: {str(e)}")
            return None

async def test_chat_query():
    """
    Test the /chat/query endpoint.
    """
    # API endpoint
    url = "http://localhost:8000/chat/query"
    
    # Get the first project ID
    project_id = await get_first_project_id()
    
    if not project_id:
        print("No projects found. Please create a project first.")
        return
    
    print(f"Using project ID: {project_id}")
    
    # Sample question
    question = "What are the key features of this project?"
    
    # Request payload
    payload = {
        "project_id": project_id,
        "question": question,
        "top_k": 10
    }
    
    # Make the request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                print("Chat Query Response:")
                print(json.dumps(result, indent=2))
                
                # Print the answer
                print("\nAnswer:")
                print(result["answer"])
                
                # Print the citations
                print("\nCitations:")
                for i, citation in enumerate(result["citations"], 1):
                    print(f"Citation {i}:")
                    print(f"  Document: {citation['doc_name']}")
                    print(f"  Page: {citation['page_number'] or 'N/A'}")
                    print(f"  Source Type: {citation['source_type']}")
                    if citation.get("images_base64"):
                        print(f"  Images: {len(citation['images_base64'])} image(s)")
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Exception: {str(e)}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_chat_query())
