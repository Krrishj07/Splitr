from flask import Flask

app = Flask(__name__)

# Import and register routes
from app.routes import register_routes
register_routes(app)