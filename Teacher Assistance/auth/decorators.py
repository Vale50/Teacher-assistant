from functools import wraps
from flask import request, jsonify
import jwt
import os

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token if provided
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # If no token, call function with current_user=None
        if not token:
            return f(current_user=None, *args, **kwargs)
        
        # If token is provided, validate it
        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return f(current_user=None, *args, **kwargs)
                
            return f(current_user=current_user, *args, **kwargs)
            
        except:
            # If token is invalid, call function with current_user=None
            return f(current_user=None, *args, **kwargs)
            
    return decorated