"""
Unified shape renderer module - provides a single entry point for rendering
any geometry shape type.
"""
import logging


def render_shape_unified(data):
    """Render a geometry shape from the given data dict.

    Args:
        data: dict with keys 'type', 'measurements', 'question_context'

    Returns:
        dict with 'success', 'image' (base64), and metadata
    """
    try:
        from app import EnhancedFixedGeometryRenderer
        renderer = EnhancedFixedGeometryRenderer()
        return renderer.render_shape_correctly(data)
    except Exception as e:
        logging.error(f"❌ Unified shape render error: {e}")
        return {'success': False, 'error': str(e)}
