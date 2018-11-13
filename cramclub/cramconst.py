"""
Application constants
"""

APP_NAME = "cramclub"

RETRY_TIME = 60   # seconds

CUSTOM_FIELDS = 'custom_fields'
CUSTOM_FIELD_CONTACTID = '2184'

CUSTOM_FIELD_FEDERAL = '2170'
CUSTOM_FIELD_STATE = '2171'

def dot_or_nothing(value):
    """Prefix with a dot (.) if value is not empty."""
    return '.' + value if value else ''
