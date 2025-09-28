from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Auth0
from app.auth import Auth0Service
auth_service = Auth0Service(app)

# Import and register routes
from app.routes import register_routes
register_routes(app, auth_service)