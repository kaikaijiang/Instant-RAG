import requests
import json
import sys
import time
from typing import Dict, Any, List, Optional

# Base URL for the API
BASE_URL = "http://localhost:8000"

def print_response(response: requests.Response) -> None:
    """
    Print a formatted response.
    """
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print()

def test_root() -> None:
    """
    Test the root endpoint.
    """
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print_response(response)

def test_create_project(name: str, description: Optional[str] = None) -> Optional[str]:
    """
    Test creating a project.
    """
    print(f"Creating project '{name}'...")
    data = {"name": name}
    if description:
        data["description"] = description
    
    response = requests.post(
        f"{BASE_URL}/project/create",
        json=data
    )
    print_response(response)
    
    if response.status_code == 201:
        return response.json().get("id")
    return None

def test_list_projects() -> List[Dict[str, Any]]:
    """
    Test listing projects.
    """
    print("Listing projects...")
    response = requests.get(f"{BASE_URL}/project/list")
    print_response(response)
    
    if response.status_code == 200:
        return response.json().get("projects", [])
    return []

def test_upload_document(project_id: str, file_path: str) -> bool:
    """
    Test uploading a document.
    """
    print(f"Uploading document '{file_path}' to project '{project_id}'...")
    with open(file_path, "rb") as f:
        files = {"files": (file_path.split("/")[-1], f)}
        data = {"project_id": project_id}
        response = requests.post(
            f"{BASE_URL}/project/upload_docs",
            files=files,
            data=data
        )
    print_response(response)
    
    return response.status_code == 200

def test_get_project_documents(project_id: str) -> List[Dict[str, Any]]:
    """
    Test getting project documents.
    """
    print(f"Getting documents for project '{project_id}'...")
    response = requests.get(f"{BASE_URL}/project/documents/{project_id}")
    print_response(response)
    
    if response.status_code == 200:
        return response.json().get("documents", [])
    return []

def test_chat_query(project_id: str, query: str) -> Optional[Dict[str, Any]]:
    """
    Test querying the chat.
    """
    print(f"Sending chat query '{query}' to project '{project_id}'...")
    response = requests.post(
        f"{BASE_URL}/chat/query",
        params={"project_id": project_id},
        json={"content": query}
    )
    print_response(response)
    
    if response.status_code == 200:
        return response.json()
    return None

def test_delete_project(project_id: str) -> bool:
    """
    Test deleting a project.
    """
    print(f"Deleting project '{project_id}'...")
    response = requests.delete(f"{BASE_URL}/project/{project_id}")
    print_response(response)
    
    return response.status_code == 200

def main() -> None:
    """
    Run the tests.
    """
    # Test root endpoint
    test_root()
    
    # Test creating a project
    project_id = test_create_project("Test Project", "A test project for API verification")
    if not project_id:
        print("Failed to create project. Exiting.")
        sys.exit(1)
    
    # Test listing projects
    projects = test_list_projects()
    
    # Test uploading a document
    # Note: You need to have a test document available
    # test_upload_document(project_id, "path/to/test/document.pdf")
    
    # Test getting project documents
    # test_get_project_documents(project_id)
    
    # Test chat query
    # Note: This will only work if you have documents uploaded
    # test_chat_query(project_id, "What is this document about?")
    
    # Test deleting the project
    test_delete_project(project_id)
    
    # Verify the project was deleted
    projects_after = test_list_projects()
    if len(projects_after) < len(projects):
        print("Project was successfully deleted.")
    else:
        print("Failed to delete project.")

if __name__ == "__main__":
    main()
