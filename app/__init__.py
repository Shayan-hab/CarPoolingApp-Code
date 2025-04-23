from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Single instance of SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Load configurations
    app.config.from_object(Config)

    # Initialize the database with the app
    db.init_app(app)

    # Import models and create tables
    with app.app_context():
        from .models import User, DriverProfile
        db.create_all()  # Ensures tables are created in the database

        # Register Blueprints
        from .routes import bp as main_bp
        app.register_blueprint(main_bp)

    return app
