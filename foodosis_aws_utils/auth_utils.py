from . import rds_utils

def validate_user(username, password):
    # Use the secure validation method
    if username.endswith('@gmail.com'):
        return rds_utils.validate_user_secure(username, password)
    return False