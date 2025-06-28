# Setup Guide - Smart Job Application Tracker

This guide will walk you through setting up the Smart Job Application Tracker from scratch.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Node.js 18+** - [Download here](https://nodejs.org/)
- **Git** - [Download here](https://git-scm.com/)

## Step 1: Clone and Setup Project

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd job-tracker
   ```

2. **Make the startup script executable:**
   ```bash
   chmod +x start.sh
   ```

## Step 2: Google Cloud Platform Setup

### 2.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "Smart Job Tracker")
4. Click "Create"

### 2.2 Enable Gmail API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on "Gmail API" and then "Enable"

### 2.3 Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen:
   - User Type: External
   - App name: "Smart Job Application Tracker"
   - User support email: Your email
   - Developer contact information: Your email
   - Save and continue through the steps

4. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Name: "Smart Job Tracker Web Client"
   - Authorized redirect URIs:
     - `http://localhost:8000/auth/callback` (for development)
     - `https://your-domain.com/auth/callback` (for production)

5. Click "Create"
6. **Important:** Download the JSON file and note your Client ID and Client Secret

### 2.4 Configure Environment Variables

1. **Copy the environment template:**
   ```bash
   cd backend
   cp env.example .env
   ```

2. **Edit the `.env` file:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Add your Google OAuth credentials:**
   ```env
   # Google OAuth Configuration
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here

   # Security
   SECRET_KEY=your_secret_key_here_make_it_long_and_random
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # CORS Configuration
   FRONTEND_URL=http://localhost:5173

   # Server Configuration
   HOST=0.0.0.0
   PORT=8000

   # Gmail API Scopes
   GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly
   ```

4. **Generate a secure secret key:**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Copy the output and replace `your_secret_key_here_make_it_long_and_random` with it.

## Step 3: Run the Application

### Option A: Using the Startup Script (Recommended)

```bash
./start.sh
```

This script will:
- Check prerequisites
- Set up Python virtual environment
- Install dependencies
- Start both backend and frontend servers

### Option B: Manual Setup

#### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the backend server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

#### Frontend Setup

1. **Open a new terminal and navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

## Step 4: Access the Application

1. **Frontend:** Open [http://localhost:5173](http://localhost:5173)
2. **Backend API:** Open [http://localhost:8000](http://localhost:8000)
3. **API Documentation:** Open [http://localhost:8000/docs](http://localhost:8000/docs)

## Step 5: First Login

1. Click "Sign in with Google" on the login page
2. You'll be redirected to Google's OAuth consent screen
3. Grant the necessary permissions (Gmail read access)
4. You'll be redirected back to the dashboard

## Troubleshooting

### Common Issues

#### 1. "Invalid redirect URI" Error
- Make sure your redirect URI in Google Cloud Console matches exactly: `http://localhost:8000/auth/callback`
- Check that you're using the correct Client ID and Client Secret

#### 2. "Gmail API not enabled" Error
- Go to Google Cloud Console → APIs & Services → Library
- Search for "Gmail API" and enable it

#### 3. "Module not found" Errors
- Make sure you're in the correct virtual environment
- Run `pip install -r requirements.txt` again

#### 4. "Port already in use" Error
- Check if another process is using port 8000 or 5173
- Kill the process or change the port in the configuration

#### 5. CORS Errors
- Make sure the frontend URL in your `.env` file is correct
- Check that both servers are running

### Debug Mode

To run in debug mode with more detailed logs:

```bash
# Backend
cd backend
source env/bin/activate
uvicorn main:app --reload --port 8000 --log-level debug

# Frontend
cd frontend
npm run dev
```

### Demo Mode (No Gmail API)

If you want to test without setting up Google OAuth:

1. **Modify the backend to use demo data:**
   ```python
   # In backend/main.py, add this import at the top:
   from demo_data import generate_demo_emails, generate_demo_stats, generate_demo_email_detail
   
   # Then modify the get_emails function to return demo data when no user tokens exist
   ```

2. **This will provide sample job application emails for testing**

## Production Deployment

### Backend Deployment (Render)

1. Create a Render account
2. Connect your GitHub repository
3. Create a new Web Service
4. Set environment variables in Render dashboard
5. Deploy

### Frontend Deployment (Vercel)

1. Create a Vercel account
2. Import your GitHub repository
3. Configure build settings
4. Deploy

### Environment Variables for Production

```env
GOOGLE_CLIENT_ID=your_production_client_id
GOOGLE_CLIENT_SECRET=your_production_client_secret
FRONTEND_URL=https://your-domain.com
SECRET_KEY=your_production_secret_key
```

## Security Notes

- Never commit your `.env` file to version control
- Use strong, unique secret keys
- Regularly rotate your OAuth credentials
- Monitor your Google Cloud Console for API usage
- Consider implementing rate limiting for production

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs in both terminal windows
3. Check the browser's developer console for errors
4. Verify your Google Cloud Console configuration
5. Ensure all environment variables are set correctly

## Next Steps

Once the application is running:

1. **Explore the dashboard** - View your job application statistics
2. **Test the email categorization** - Send yourself test emails with job-related subjects
3. **Customize the categories** - Modify the categorization keywords in `backend/main.py`
4. **Add features** - Implement additional functionality like notes, reminders, etc.

Happy job hunting! 🚀 