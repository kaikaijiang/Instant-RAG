import asyncio
import os
import sys
import aiohttp
import json
from pathlib import Path

# Add the current directory to the path so we can import from the backend package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_document_upload():
    """
    Test the document upload endpoint by uploading test files.
    """
    print("Testing document upload endpoint...")
    
    # Create a test project first
    project_id = await create_test_project()
    
    # Get the test files
    test_files_dir = Path(__file__) / "test_files"
    test_pdf = test_files_dir / "test.pdf"
    test_md = test_files_dir / "test.md"
    test_image = test_files_dir / "test.jpg"
    
    # Check if test files exist
    if not test_pdf.exists() or not test_md.exists() or not test_image.exists():
        print("Test files not found. Please make sure the test files exist in the test_files directory.")
        return
    
    # Upload the test files
    async with aiohttp.ClientSession() as session:
        # Prepare the form data
        data = aiohttp.FormData()
        data.add_field('project_id', project_id)
        
        # Add the test files
        data.add_field('files', 
                      open(test_pdf, 'rb'),
                      filename=test_pdf.name,
                      content_type='application/pdf')
        
        data.add_field('files', 
                      open(test_md, 'rb'),
                      filename=test_md.name,
                      content_type='text/markdown')
        
        data.add_field('files', 
                      open(test_image, 'rb'),
                      filename=test_image.name,
                      content_type='image/jpeg')
        
        # Send the request
        print(f"Uploading files to project {project_id}...")
        async with session.post('http://localhost:8000/project/upload_docs', data=data) as response:
            if response.status == 200:
                result = await response.json()
                print("Upload successful!")
                print(f"Documents processed: {len(result['documents_processed'])}")
                print(f"Total chunks created: {result['total_chunks']}")
                
                # Print details for each document
                for doc in result['documents_processed']:
                    print(f"Document: {doc['document_name']}")
                    print(f"  Type: {doc['document_type']}")
                    print(f"  Pages processed: {doc['pages_processed']}")
                    print(f"  Chunks created: {doc['chunks_created']}")
            else:
                print(f"Upload failed with status {response.status}")
                print(await response.text())

async def create_test_project():
    """
    Create a test project for document upload.
    
    Returns:
        The ID of the created project.
    """
    async with aiohttp.ClientSession() as session:
        project_data = {
            "name": "Test Document Upload Project",
            "description": "A project for testing document upload functionality"
        }
        
        async with session.post('http://localhost:8000/project/create', 
                               json=project_data) as response:
            if response.status == 201:
                result = await response.json()
                print(f"Created test project with ID: {result['id']}")
                return result['id']
            else:
                print(f"Failed to create test project: {response.status}")
                print(await response.text())
                sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_document_upload())
