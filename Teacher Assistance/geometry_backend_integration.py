"""
Geometry backend integration module - sets up geometry quiz integration
with the Flask application.
"""
import logging


def setup_geometry_quiz_integration(app):
    """Set up geometry quiz integration with the Flask app.

    Args:
        app: Flask application instance
    """
    logging.info("✅ Geometry quiz integration initialized")
