"""
Error handling module.
Provides user-friendly error messages and error handling utilities.
"""
from typing import Dict, Optional

# User-friendly error messages
ERROR_MESSAGES: Dict[str, str] = {
    "FileNotFoundError": "The image file could not be found. Please check the file path and try again.",
    "ValidationError": "Invalid settings provided. Please check your input and try again.",
    "RateLimitError": "Too many requests. Please wait a moment and try again.",
    "ServerError": "The AI service is temporarily unavailable. Please try again in a few minutes.",
    "ConnectionError": "Could not connect to the AI service. Please check your internet connection.",
    "TimeoutError": "The request took too long to complete. Please try again.",
    "PermissionError": "Permission denied. Please check file permissions.",
    "ValueError": "Invalid value provided. Please check your settings.",
    "KeyError": "Missing required information. Please try again.",
    "OSError": "A system error occurred. Please try again or contact support.",
}

# Error suggestions
ERROR_SUGGESTIONS: Dict[str, str] = {
    "FileNotFoundError": "Make sure the file exists and the path is correct.",
    "ValidationError": "Review your settings and ensure all required fields are filled correctly.",
    "RateLimitError": "Wait 30-60 seconds before trying again.",
    "ServerError": "The service may be experiencing high load. Try again in a few minutes.",
    "ConnectionError": "Check your internet connection and firewall settings.",
    "TimeoutError": "Try using a lower resolution or simpler settings.",
    "PermissionError": "Check that you have read/write permissions for the file/folder.",
    "ValueError": "Double-check all numeric values and dropdown selections.",
    "KeyError": "Refresh the page and try again.",
    "OSError": "Check available disk space and file system permissions.",
}


def get_user_friendly_error(error: Exception, include_suggestion: bool = True) -> str:
    """
    Convert a technical error into a user-friendly message.
    
    Args:
        error: The exception that occurred
        include_suggestion: Whether to include a suggestion
        
    Returns:
        User-friendly error message
    """
    error_type = type(error).__name__
    base_message = ERROR_MESSAGES.get(error_type, f"An error occurred: {str(error)}")
    
    if include_suggestion:
        suggestion = ERROR_SUGGESTIONS.get(error_type, "")
        if suggestion:
            return f"{base_message} {suggestion}"
    
    return base_message


def format_error_response(error: Exception, status_code: int = 500) -> tuple:
    """
    Format an error for JSON response.
    
    Args:
        error: The exception that occurred
        status_code: HTTP status code
        
    Returns:
        Tuple of (json_response, status_code)
    """
    from flask import jsonify
    
    user_message = get_user_friendly_error(error)
    
    return jsonify({
        "status": "error",
        "message": user_message,
        "error_type": type(error).__name__
    }), status_code

