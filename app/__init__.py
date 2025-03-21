from flask import Flask
from .routes import bp
from .database import init_db, populate_mock_data
from .config import Config
import logging

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # Register blueprints or routes
    from .routes import bp
    app.register_blueprint(bp)

    # Initialize database
    init_db(app)
    populate_mock_data(app)

    return app
