from odoo import http, fields
from odoo.http import request
import werkzeug
import logging
import json
from odoo.addons.survey.controllers.main import Survey

_logger = logging.getLogger(__name__)

def get_device_token():
    """Get device token from cookie or URL, do not generate a new one"""
    # Check URL first (for remote access)
    device_token = request.httprequest.args.get('device_token')
    if device_token:
        _logger.info(f"Using device_token from URL: {device_token}")
        # Update cookie with URL-provided token
        response = request.make_response('')
        response.set_cookie(
            'device_token',
            device_token,
            max_age=31536000,  # 1 year in seconds
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        return device_token
    
    # Fall back to cookie
    device_token = request.httprequest.cookies.get('device_token')
    if not device_token:
        _logger.warning("No device_token found in cookie or URL")
        return None  # No generation, return None
    _logger.info(f"Using device_token from cookie: {device_token}")
    return device_token

def ensure_device_token_in_url(url):
    """Ensure device_token is included in URL if available"""
    device_token = get_device_token()
    if not device_token:
        return url  # Return unchanged URL if no token
    separator = '&' if '?' in url else '?'
    return f"{url}{separator}device_token={device_token}"
