"""
Application constants
"""

APP_NAME = "cramclub"

RETRY_TIME = 60   # seconds

CUSTOM_FIELD_CONTACTID = "2184"

CUSTOM_FIELD_FEDERAL = "2170"
CUSTOM_FIELD_STATE = "2171"

def dot_or_nothing(instance):
    return '.' + instance if instance else ''
