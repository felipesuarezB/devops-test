import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager
from flask_restful import Api
from app.config import Config

db = SQLAlchemy()
ma = Marshmallow()
jwt = JWTManager()

def configure_logging(app):
    """Configure logging for the application"""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_format = app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler()  # Output to console/Docker logs
        ]
    )
    
    # Configure Flask logger
    app.logger.setLevel(log_level)
    
    # Configure SQLAlchemy logger (optional - can be verbose)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure logging
    configure_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    
    # Initialize API
    api = Api(app)
    
    # Register blueprints and resources
    from app.api.resources import BlacklistResource, BlacklistCheckResource
    from app.api.auth import AuthResource
    api.add_resource(AuthResource, '/auth/token')
    api.add_resource(BlacklistResource, '/blacklists')
    api.add_resource(BlacklistCheckResource, '/blacklists/<string:email>')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Blacklist API is running v6'}, 200
    
    # Create database tables (commented out - use init_db.py script instead)
    # with app.app_context():
    #     db.create_all()
    #     app.logger.info("Database tables created successfully")
    
    app.logger.info("Blacklist API application initialized successfully")
    return app
