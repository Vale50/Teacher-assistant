"""
Migration routes blueprint - handles database migration endpoints.
"""
from flask import Blueprint

migration_bp = Blueprint('migrations', __name__)
