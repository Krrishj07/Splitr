import json
import requests
from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
from config import Config

class Auth0Service:
    def __init__(self, app):
        self.app = app
        self.oauth = OAuth(app)
        
        # Configure Auth0
        self.auth0 = self.oauth.register(
            'auth0',
            client_id=Config.AUTH0_CLIENT_ID,
            client_secret=Config.AUTH0_CLIENT_SECRET,
            server_metadata_url=f'https://{Config.AUTH0_DOMAIN}/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid profile email'
            }
        )
    
    def requires_auth(self, f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'profile' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated
    
    def login(self):
        """Initiate Auth0 login"""
        # Generate and store nonce for security
        nonce = generate_token()
        session['auth_nonce'] = nonce
        
        # Build redirect_uri, honoring EXTERNAL_BASE_URL if provided
        if Config.EXTERNAL_BASE_URL:
            base = Config.EXTERNAL_BASE_URL.rstrip('/')
            redirect_uri = f"{base}{url_for('callback')}"
        else:
            redirect_uri = url_for('callback', _external=True)
        return self.auth0.authorize_redirect(
            redirect_uri,
            nonce=nonce
        )
    
    def passwordless_login(self, email, connection='email'):
        """Initiate passwordless login"""
        url = f"https://{Config.AUTH0_DOMAIN}/passwordless/start"
        
        # Generate and store nonce
        nonce = generate_token()
        session['auth_nonce'] = nonce
        
        payload = {
            'client_id': Config.AUTH0_CLIENT_ID,
            'client_secret': Config.AUTH0_CLIENT_SECRET,
            'connection': connection,
            'email': email,
            'send': 'link',
            'authParams': {
                'scope': 'openid profile email',
                'response_type': 'code',
                'redirect_uri': (Config.EXTERNAL_BASE_URL.rstrip('/') + url_for('callback')) if Config.EXTERNAL_BASE_URL else url_for('callback', _external=True),
                'nonce': nonce
            }
        }
        
        headers = {'content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        return response.status_code == 200
    
    def callback(self):
        """Handle Auth0 callback"""
        try:
            # Get the nonce from session
            nonce = session.get('auth_nonce')
            if not nonce:
                return "Authentication failed: Missing nonce", 400
            
            # Get the access token
            token = self.auth0.authorize_access_token()
            session['jwt_payload'] = token
            
            # Parse ID token with nonce
            resp = self.auth0.parse_id_token(token, nonce=nonce)
            
            # Clean up nonce from session
            session.pop('auth_nonce', None)
            
            # Store user profile
            session['profile'] = {
                'user_id': resp['sub'],
                'name': resp.get('name', ''),
                'email': resp.get('email', ''),
                'picture': resp.get('picture', ''),
                'email_verified': resp.get('email_verified', False)
            }
            
            return redirect(url_for('dashboard'))
        except Exception as e:
            # Clean up nonce on error
            session.pop('auth_nonce', None)
            return f"Authentication failed: {str(e)}", 400
    
    def logout(self):
        """Logout user"""
        session.clear()
        if Config.EXTERNAL_BASE_URL:
            base = Config.EXTERNAL_BASE_URL.rstrip('/')
            return_url = f"{base}{url_for('index')}"
        else:
            return_url = url_for('index', _external=True)
        return redirect(
            f"https://{Config.AUTH0_DOMAIN}/v2/logout?"
            f"returnTo={return_url}&"
            f"client_id={Config.AUTH0_CLIENT_ID}"
        )
    
    def get_user_profile(self):
        """Get current user profile from session"""
        return session.get('profile')
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return 'profile' in session