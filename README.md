# Smart Job Application Tracker

A personal web application that connects to your Gmail account, fetches job-related emails, categorizes them, and displays the results in an organized dashboard to help manage and visualize your job application process.

## Features

- 🔐 **Google OAuth2 Authentication** - Secure sign-in with Gmail
- 📧 **Gmail Integration** - Automatically fetch and categorize job-related emails
- 📊 **Dashboard** - Visual overview of your job application status
- 🏷️ **Smart Categorization** - Automatically categorize emails as Applications, Rejections, Interviews, or Offers
- 🔍 **Search & Filter** - Find applications by company or status
- 📱 **Responsive Design** - Works on desktop and mobile devices

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Google OAuth2** - Authentication with Gmail
- **Gmail API** - Email fetching and processing
- **Uvicorn** - ASGI server

### Frontend
- **React 18** - Modern React with hooks
- **Vite** - Fast build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **Axios** - HTTP client for API requests
- **React Router** - Client-side routing

## Project Structure

```
job-tracker/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment variables template
│   └── env/                 # Python virtual environment
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   ├── App.jsx         # Main app component
│   │   └── main.jsx        # App entry point
│   ├── package.json        # Node.js dependencies
│   └── tailwind.config.js  # TailwindCSS configuration
└── README.md               # This file
```

## Quick Start

### Prerequisites

1. **Python 3.11+** installed
2. **Node.js 18+** installed
3. **Google Cloud Platform** account with Gmail API enabled
4. **OAuth 2.0 credentials** configured

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Google OAuth credentials
   ```

5. **Run the backend server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to `http://localhost:5173`

## Google Cloud Setup

1. **Create a Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Gmail API:**
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it

3. **Create OAuth 2.0 Credentials:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:8000/auth/callback` (for development)
     - `https://your-domain.com/auth/callback` (for production)

4. **Download credentials:**
   - Download the JSON file
   - Extract `client_id` and `client_secret` for your `.env` file

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here

# Security
SECRET_KEY=your_secret_key_here

# CORS
FRONTEND_URL=http://localhost:5173
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/auth/login` | Redirect to Google OAuth |
| GET | `/auth/callback` | OAuth callback handler |
| GET | `/emails` | Get categorized emails |
| GET | `/emails/{email_id}` | Get specific email details |

## Development

### Backend Development
- The backend runs on `http://localhost:8000`
- API documentation available at `http://localhost:8000/docs`
- Uses hot reload for development

### Frontend Development
- The frontend runs on `http://localhost:5173`
- Uses Vite for fast development builds
- Hot module replacement enabled

## Deployment

### Backend Deployment
- **Render**: Easy deployment with automatic builds
- **Railway**: Simple container deployment
- **AWS EC2**: Full control over infrastructure

### Frontend Deployment
- **Vercel**: Optimized for React applications
- **Netlify**: Great for static sites
- **GitHub Pages**: Free hosting option

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Happy job hunting! 🚀** 