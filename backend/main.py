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
import jwt
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# In-memory storage fallback (for development/testing)
user_tokens = {}

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

# JWT Secret (in production, use a secure secret)
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

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
    """Save user token data to Supabase."""
    try:
        # Store in Supabase
        result = supabase.table('user_tokens').upsert({
            'user_id': user_id,
            'token_data': json.dumps(token_data),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).execute()
        print(f"Token saved to Supabase for user {user_id}")
    except Exception as e:
        print(f"Error saving token to Supabase: {e}")
        # Fallback to in-memory storage
        user_tokens[user_id] = token_data

def get_user_token_db(user_id):
    """Get user token data from Supabase."""
    try:
        # Try Supabase first
        result = supabase.table('user_tokens').select('*').eq('user_id', user_id).execute()
        if result.data:
            token_record = result.data[0]
            return json.loads(token_record['token_data'])
    except Exception as e:
        print(f"Error getting token from Supabase: {e}")
    
    # Fallback to in-memory storage
    return user_tokens.get(user_id)

def save_user_email_mapping(user_id, email):
    """Save user email mapping to Supabase."""
    try:
        result = supabase.table('user_emails').upsert({
            'user_id': user_id,
            'email': email,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).execute()
        print(f"Email mapping saved to Supabase: {email} -> {user_id}")
    except Exception as e:
        print(f"Error saving email mapping to Supabase: {e}")

def get_user_id_by_email(email):
    """Get user ID by email from Supabase."""
    try:
        result = supabase.table('user_emails').select('user_id').eq('email', email).execute()
        if result.data:
            return result.data[0]['user_id']
    except Exception as e:
        print(f"Error getting user ID by email from Supabase: {e}")
    return None

# Session management
def create_user_token(user_id: str, email: str) -> str:
    """Create a JWT token for user session."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_user_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode user JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user from request cookies or headers."""
    # Check for token in cookies first
    token = request.cookies.get("user_token")
    if not token:
        # Check for token in Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if token:
        return verify_user_token(token)
    return None

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Smart Job Application Tracker API"}

@app.get("/auth/login")
async def login():
    """Initiate Google OAuth login."""
    try:
        # Use environment variable for backend URL
        backend_url = os.getenv("BACKEND_URL", "https://job-tracker-backend-pij9.onrender.com")
        
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
        # Use environment variable for backend URL
        backend_url = os.getenv("BACKEND_URL", "https://job-tracker-backend-pij9.onrender.com")
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
        
        # Get user info from Gmail API
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile['emailAddress']
        
        # Check if user already exists (by email)
        existing_user_id = get_user_id_by_email(user_email)
        if existing_user_id:
            user_id = existing_user_id
            print(f"Existing user {user_email} logged in")
        else:
            user_id = secrets.token_urlsafe(32)
            print(f"New user {user_email} created")
        
        # Store credentials
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        save_user_token_db(user_id, token_data)
        
        # Store user email mapping
        save_user_email_mapping(user_id, user_email)
        
        # Create session token
        session_token = create_user_token(user_id, user_email)
        
        print(f"Stored credentials for user {user_id} ({user_email})")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        
        # Redirect with session token
        response = RedirectResponse(url=f"{frontend_url}/dashboard?user_id={user_id}")
        response.set_cookie(
            key="user_token",
            value=session_token,
            httponly=True,
            secure=True,  # Use HTTPS in production
            samesite="lax",
            max_age=JWT_EXPIRATION_HOURS * 3600  # Convert hours to seconds
        )
        return response
        
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

@app.get("/auth/session")
async def check_session(request: Request):
    """Check if user has a valid session."""
    user = get_current_user(request)
    if user:
        return {
            "authenticated": True,
            "user_id": user["user_id"],
            "email": user["email"]
        }
    return {"authenticated": False}

@app.get("/auth/logout")
async def logout():
    """Logout user by clearing session."""
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie("user_token")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 