"""
Renderer migration module - provides backward-compatible renderer factory.
Creates an EnhancedFixedGeometryRenderer instance for use in the app.
"""
import logging


def create_renderer_for_app():
    """Create and return the geometry renderer for the Flask app.

    Returns an EnhancedFixedGeometryRenderer instance which handles
    all shape types including triangles, circles, rectangles, polygons, etc.
    """
    try:
        # Import the renderer class from the main app module
        # This is defined in app.py as EnhancedFixedGeometryRenderer
        from app import EnhancedFixedGeometryRenderer
        renderer = EnhancedFixedGeometryRenderer()
        logging.info("✅ Created EnhancedFixedGeometryRenderer via renderer_migration")
        return renderer
    except ImportError:
        logging.warning("⚠️ EnhancedFixedGeometryRenderer not available, returning None")
        return None


def get_unified_renderer():
    """Get the unified shape renderer instance."""
    return create_renderer_for_app()
