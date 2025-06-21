"""Utility functions for the Flask application"""
import json
from flask import jsonify, request

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, error_code, message, status_code=400):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def extract_compound_id(request):
    """
    Extract and validate compound_id from request headers
    
    Args:
        request: Flask request object
        
    Returns:
        str: Valid compound_id
        
    Raises:
        APIError: If compound_id is invalid or missing
    """
    # Get compound_id from header
    compound_id = request.headers.get('X-Compound-ID')
    
    # Validate compound_id exists
    if not compound_id:
        raise APIError('MISSING_COMPOUND_ID', 'X-Compound-ID header is required')
    
    # Additional validation can be added here if needed
    # For example, check if compound_id exists in the database
    
    return compound_id


def create_response(data=None, status='success', error=None, status_code=200):
    """
    Create a standardized API response
    
    Args:
        data: Response data
        status: Response status ('success' or 'error')
        error: Error details if status is 'error'
        status_code: HTTP status code
        
    Returns:
        Flask response object
    """
    response = {
        'status': status,
    }
    
    if data is not None:
        response['data'] = data
        
    if error is not None:
        response['error'] = error
        
    return jsonify(response), status_code
