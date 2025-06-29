from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json
import base64
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv
import secrets
from supabase import create_client, Client

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Smart Job Application Tracker",
    description="A FastAPI backend for tracking job applications via Gmail integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "https://*.vercel.app",  # Allow all Vercel deployments
        "https://*.onrender.com",  # Allow Render deployments
        "https://job-tracker-frontend-tau.vercel.app",  # Your specific Vercel domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Pydantic models
class EmailSummary(BaseModel):
    id: str
    subject: str
    snippet: str
    from_email: str
    date: str
    category: str
    company: Optional[str] = None
    gmail_url: str

class EmailDetail(BaseModel):
    id: str
    subject: str
    body: str
    from_email: str
    date: str
    category: str
    company: Optional[str] = None
    gmail_url: str

class DashboardStats(BaseModel):
    total_applications: int
    applications_sent: int
    rejected: int
    interview_scheduled: int
    offer_received: int
    categories: Dict[str, int]

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Email categorization keywords
CATEGORY_KEYWORDS = {
    "applications_sent": [
        "application submitted", "application received", "thank you for applying",
        "application confirmation", "we received your application", "application status"
    ],
    "rejected": [
        "unfortunately", "regret to inform", "not moving forward", "not selected",
        "other candidates", "position filled", "rejection", "decline"
    ],
    "interview_scheduled": [
        "interview", "schedule", "meeting", "call", "discussion", "next steps",
        "interview invitation", "interview request"
    ],
    "offer_received": [
        "offer", "congratulations", "welcome", "job offer", "employment offer",
        "we're excited to offer", "offer letter"
    ]
}

def categorize_email(subject: str, snippet: str) -> str:
    """Categorize email based on subject and snippet content."""
    content = f"{subject} {snippet}".lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in content:
                return category
    
    return "applications_sent"  # Default category

def extract_company_name(from_email: str, subject: str) -> Optional[str]:
    """Extract company name from email address or subject."""
    # Try to extract from email domain
    if '@' in from_email:
        domain = from_email.split('@')[1]
        # Remove common email providers
        if domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']:
            return domain.split('.')[0].title()
    
    # Try to extract from subject line
    # Look for common patterns like "Company Name - Job Title"
    subject_parts = subject.split(' - ')
    if len(subject_parts) > 1:
        return subject_parts[0].strip()
    
    return None

def get_gmail_service(credentials_dict: Dict[str, Any]):
    """Build Gmail service from credentials."""
    try:
        # Debug: Print what we're trying to use
        print(f"Building Gmail service with credentials: {list(credentials_dict.keys())}")
        print(f"Has refresh_token: {credentials_dict.get('refresh_token') is not None}")
        print(f"Has token: {credentials_dict.get('token') is not None}")
        
        # If refresh_token is None, we need to handle this case
        if credentials_dict.get('refresh_token') is None:
            print("Warning: No refresh token available. This might cause issues with token refresh.")
            # For now, we'll still try to use the access token
            # In a production app, you'd want to handle this differently
        
        credentials = Credentials.from_authorized_user_info(credentials_dict)
        service = build('gmail', 'v1', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error building Gmail service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to build Gmail service: {str(e)}")

def get_user_emails(service, max_results: int = 50) -> List[Dict[str, Any]]:
    """Fetch emails from Gmail API."""
    try:
        # Broader search query to find more potential job-related emails
        query = "subject:(application OR interview OR offer OR rejection OR job OR position OR hiring OR career OR resume OR cv) OR from:(noreply OR careers OR jobs OR hiring OR recruit OR talent OR hr OR human.resources)"
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=min(max_results, 50)  # Limit to 50 emails for faster loading
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for message in messages:
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='metadata',
                metadataHeaders=['Subject', 'From', 'Date']
            ).execute()
            
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Get snippet
            snippet = msg.get('snippet', '')
            
            # Categorize email
            category = categorize_email(subject, snippet)
            
            # Extract company name
            company = extract_company_name(from_email, subject)
            
            # Create Gmail URL
            gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{message['id']}"
            
            emails.append({
                'id': message['id'],
                'subject': subject,
                'snippet': snippet,
                'from_email': from_email,
                'date': date,
                'category': category,
                'company': company,
                'gmail_url': gmail_url
            })
        
        return emails
    
    except HttpError as error:
        raise HTTPException(status_code=500, detail=f"Gmail API error: {str(error)}")

# Helper functions for Supabase token storage

def save_user_token_db(user_id, token_data):
    data = {
        "user_id": user_id,
        "token": token_data['token'],
        "refresh_token": token_data['refresh_token'],
        "token_uri": token_data['token_uri'],
        "client_id": token_data['client_id'],
        "client_secret": token_data['client_secret'],
        "scopes": ','.join(token_data['scopes']) if isinstance(token_data['scopes'], list) else str(token_data['scopes'])
    }
    supabase.table("user_tokens").upsert(data).execute()

def get_user_token_db(user_id):
    result = supabase.table("user_tokens").select("*").eq("user_id", user_id).execute()
    if result.data and len(result.data) > 0:
        row = result.data[0]
        return {
            "token": row["token"],
            "refresh_token": row["refresh_token"],
            "token_uri": row["token_uri"],
            "client_id": row["client_id"],
            "client_secret": row["client_secret"],
            "scopes": row["scopes"].split(",") if row["scopes"] else []
        }
    return None

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Smart Job Application Tracker API"}

@app.get("/auth/login")
async def login():
    """Initiate Google OAuth login."""
    try:
        # Use backend URL for redirect URI since we need to handle the callback
        backend_url = "http://localhost:8001"
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [f"{backend_url}/auth/callback"]
                }
            },
            scopes=[os.getenv("GMAIL_SCOPES", "https://www.googleapis.com/auth/gmail.readonly")]
        )
        
        flow.redirect_uri = f"{backend_url}/auth/callback"
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to ensure refresh token
        )
        
        return {"authorization_url": authorization_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create authorization URL: {str(e)}")

@app.get("/auth/callback")
async def auth_callback(code: str, state: Optional[str] = None):
    """Handle OAuth callback and exchange code for tokens."""
    try:
        backend_url = "http://localhost:8001"
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [f"{backend_url}/auth/callback"]
                }
            },
            scopes=[os.getenv("GMAIL_SCOPES", "https://www.googleapis.com/auth/gmail.readonly")]
        )
        flow.redirect_uri = f"{backend_url}/auth/callback"
        flow.fetch_token(code=code)
        credentials = flow.credentials
        user_id = secrets.token_urlsafe(32)
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        save_user_token_db(user_id, token_data)
        print(f"Stored credentials for user {user_id}")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}/dashboard?user_id={user_id}")
    except Exception as e:
        print(f"Auth callback error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/emails")
async def get_emails(
    user_id: str,
    max_results: int = 100,
    category: Optional[str] = None,
    company: Optional[str] = None
):
    """Get categorized emails for the user."""
    token_data = get_user_token_db(user_id)
    if not token_data:
        raise HTTPException(status_code=401, detail="User not authenticated")
    try:
        service = get_gmail_service(token_data)
        emails = get_user_emails(service, max_results)
        print(f"Found {len(emails)} emails for user {user_id}")
        if category:
            emails = [email for email in emails if email['category'] == category]
        if company:
            emails = [email for email in emails if email['company'] and company.lower() in email['company'].lower()]
        email_summaries = [EmailSummary(**email) for email in emails]
        return {"emails": email_summaries}
    except Exception as e:
        print(f"Error fetching emails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")

@app.get("/emails/{email_id}")
async def get_email_detail(email_id: str, user_id: str):
    """Get detailed email content."""
    token_data = get_user_token_db(user_id)
    if not token_data:
        raise HTTPException(status_code=401, detail="User not authenticated")
    try:
        service = get_gmail_service(token_data)
        message = service.users().messages().get(
            userId='me',
            id=email_id,
            format='full'
        ).execute()
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        category = categorize_email(subject, body)
        company = extract_company_name(from_email, subject)
        gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{email_id}"
        email_detail = EmailDetail(
            id=email_id,
            subject=subject,
            body=body,
            from_email=from_email,
            date=date,
            category=category,
            company=company,
            gmail_url=gmail_url
        )
        return email_detail
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch email details: {str(e)}")

@app.get("/dashboard/stats")
async def get_dashboard_stats(user_id: str):
    """Get dashboard statistics."""
    token_data = get_user_token_db(user_id)
    if not token_data:
        raise HTTPException(status_code=401, detail="User not authenticated")
    try:
        service = get_gmail_service(token_data)
        emails = get_user_emails(service, max_results=1000)
        categories = {}
        for email in emails:
            category = email['category']
            categories[category] = categories.get(category, 0) + 1
        stats = DashboardStats(
            total_applications=len(emails),
            applications_sent=categories.get('applications_sent', 0),
            rejected=categories.get('rejected', 0),
            interview_scheduled=categories.get('interview_scheduled', 0),
            offer_received=categories.get('offer_received', 0),
            categories=categories
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 