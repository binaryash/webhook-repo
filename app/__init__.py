from flask import Flask
from app.webhook.routes import webhook

def create_app():
    app = Flask(__name__)
    
    # Register the blueprint
    app.register_blueprint(webhook)
    
    return app
