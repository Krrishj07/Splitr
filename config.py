import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Auth0 Configuration
    AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
    AUTH0_CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID')
    AUTH0_CLIENT_SECRET = os.environ.get('AUTH0_CLIENT_SECRET')
    AUTH0_AUDIENCE = os.environ.get('AUTH0_AUDIENCE', f"https://{AUTH0_DOMAIN}/api/v2/")
    
    # Auth0 URLs
    AUTH0_BASE_URL = f"https://{AUTH0_DOMAIN}"
    AUTH0_AUTHORIZE_URL = f"{AUTH0_BASE_URL}/authorize"
    AUTH0_TOKEN_URL = f"{AUTH0_BASE_URL}/oauth/token"
    AUTH0_USERINFO_URL = f"{AUTH0_BASE_URL}/userinfo"

    # External URL overrides (optional)
    # If set, this will be used to construct absolute callback/logout URLs
    EXTERNAL_BASE_URL = os.environ.get('EXTERNAL_BASE_URL')  # e.g., "http://localhost:8000"
    # Optional hints for url_for(_external=True)
    SERVER_NAME = os.environ.get('SERVER_NAME')  # e.g., "localhost:8000"
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME')  # e.g., "http"