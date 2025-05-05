import asyncio
import os
import json
from dotenv import load_dotenv
import aiohttp
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# API base URL
API_BASE_URL = "http://localhost:8000"

# Gemini API settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

async def summarize_with_gemini(email_text):
    """
    Summarize an email using the Gemini API.
    
    Args:
        email_text: The email text to summarize
        
    Returns:
        The summary text
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": f"Summarize the following email clearly and completely:\n\n{email_text}"}
                        ]
                    }
                ]
            },
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"Error from Gemini API: {error_text}")
                return f"Error generating summary: {error_text[:100]}..."
            
            result = await response.json()
            
            # Extract the summary text
            try:
                summary_text = result["candidates"][0]["content"]["parts"][0]["text"]
                return summary_text
            except (KeyError, IndexError) as e:
                print(f"Unexpected response format from Gemini API: {str(e)}")
                return "Error extracting summary from API response"

async def test_email_api(use_gemini_for_summaries=True):
    """
    Test the email API endpoints.
    """
    print("Testing Email API Endpoints")
    print("==========================")
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Create a test project
        print("\n1. Creating a test project...")
        
        project_data = {
            "name": "Email Test Project",
            "description": "A project for testing email ingestion and summarization"
        }
        
        async with session.post(
            f"{API_BASE_URL}/project/create",
            json=project_data
        ) as response:
            if response.status != 201:
                print(f"Error creating project: {await response.text()}")
                return
            
            project = await response.json()
            project_id = project["id"]
            print(f"Project created with ID: {project_id}")
        
        # Step 2: Set up email settings
        print("\n2. Setting up email settings...")
        
        # Get current date and date 30 days ago
        today = datetime.now().isoformat()
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        # Use the provided app password
        email_password = "password / allowed api access password"
        
        email_settings = {
            "project_id": project_id,
            "imap_server": "imap.gmail.com",
            "email": "your_email",
            "password": email_password,
            "sender_filter": "",  # Leave empty to fetch from all senders
            "subject_keywords": [],  # Empty to match all subjects
            "date_range": {
                "start": thirty_days_ago,
                "end": today
            }
        }
        
        print(f"Connecting to {email_settings['imap_server']} with email {email_settings['email']}")
        
        async with session.post(
            f"{API_BASE_URL}/project/setup_email",
            json=email_settings
        ) as response:
            if response.status != 200:
                print(f"Error setting up email: {await response.text()}")
                return
            
            result = await response.json()
            print(f"Email setup result: {result['message']}")
        
        # Step 3: Ingest emails
        print("\n3. Ingesting emails...")
        
        async with session.post(
            f"{API_BASE_URL}/project/ingest_emails?project_id={project_id}"
        ) as response:
            if response.status != 200:
                print(f"Error ingesting emails: {await response.text()}")
                return
            
            result = await response.json()
            print(f"Ingested {result['count']} emails")
            print("Email subjects:")
            for subject in result['subjects']:
                print(f"  - {subject}")
        
        # Step 4: Summarize emails
        print("\n4. Summarizing emails...")
        
        if use_gemini_for_summaries:
            # Load raw emails from file
            data_dir = os.path.join(os.path.dirname(__file__), "data", "emails", project_id)
            raw_emails_path = os.path.join(data_dir, "raw_emails.jsonl")
            
            if not os.path.exists(raw_emails_path):
                print(f"Error: No raw emails found at {raw_emails_path}")
                return
            
            # Load raw emails
            emails = []
            with open(raw_emails_path, 'r') as f:
                for line in f:
                    if line.strip():
                        emails.append(json.loads(line))
            
            if not emails:
                print("Error: No emails found in raw_emails.jsonl")
                return
            
            # Limit to first 5 emails for testing
            emails = emails[:5]
            
            # Summarize emails using Gemini API
            print(f"Summarizing {len(emails)} emails using Gemini API...")
            summaries = []
            
            for email in emails:
                # Prepare email text for summarization
                email_text = f"Subject: {email['subject']}\nFrom: {email['sender']}\nDate: {email['date']}\n\n{email['body']}"
                
                # Call Gemini API for summarization
                print(f"  Summarizing email: {email['subject']}")
                summary_text = await summarize_with_gemini(email_text)
                
                # Add to summaries list
                summaries.append({
                    "id": f"email_{email['id']}",
                    "subject": email['subject'],
                    "summary": summary_text
                })
            
            print(f"Successfully summarized {len(summaries)} emails with Gemini API")
            print("Email summaries:")
            for summary in summaries:
                print(f"  - Subject: {summary['subject']}")
                print(f"    Summary: {summary['summary'][:100]}...")
                print()
        else:
            # Use the backend API for summarization
            async with session.post(
                f"{API_BASE_URL}/project/summarize_emails?project_id={project_id}"
            ) as response:
                if response.status != 200:
                    print(f"Error summarizing emails: {await response.text()}")
                    return
                
                result = await response.json()
                print(f"Summarized {result['count']} emails")
                print("Email summaries:")
                for summary in result['summaries']:
                    print(f"  - Subject: {summary['subject']}")
                    print(f"    Summary: {summary['summary'][:100]}...")
                    print()
        
        print("\nEmail API test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_email_api())
