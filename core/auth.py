import os
import hashlib
import bcrypt
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request

# Configuration
PIN_SALT = os.getenv("PIN_SALT", "default_development_salt_change_in_production")

# Simple session storage (in-memory, for v1 simplicity)
active_sessions = {}  # session_token -> {username: str, expires: datetime}

def hash_pin(pin: str) -> str:
    """Hash a PIN with bcrypt"""
    return bcrypt.hashpw((pin + PIN_SALT).encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_pin(pin: str, hashed: str) -> bool:
    """Verify a PIN against its hash"""
    return bcrypt.checkpw((pin + PIN_SALT).encode('utf-8'), hashed.encode('utf-8'))

def hash_ip(ip: str) -> str:
    """Hash IP address with salt for privacy-preserving storage"""
    return hashlib.sha256((ip + PIN_SALT).encode('utf-8')).hexdigest()

def get_client_ip(request: Request) -> str:
    """Get client IP from request, handling proxies"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host

def is_valid_username(username: str) -> bool:
    """Validate username: 3-20 alphanumeric chars"""
    return bool(re.match(r'^[a-zA-Z0-9]{3,20}$', username))

def is_valid_pin(pin: str) -> bool:
    """Validate PIN: exactly 6 digits"""
    return bool(re.match(r'^\d{6}$', pin))

def is_valid_slug(slug: str) -> bool:
    """Validate list slug: alphanumeric + hyphens, 1-50 chars"""
    return bool(re.match(r'^[a-zA-Z0-9-]{1,50}$', slug))

def create_session(username: str) -> str:
    """Create a new session token for the user"""
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(hours=24)  # 24 hour sessions
    active_sessions[token] = {
        'username': username,
        'expires': expires
    }
    return token

def get_session_user(request: Request) -> Optional[str]:
    """Get the username from the session token in cookies"""
    session_token = request.cookies.get('session')
    if not session_token or session_token not in active_sessions:
        return None
    
    session_data = active_sessions[session_token]
    if datetime.now() > session_data['expires']:
        # Session expired, clean it up
        del active_sessions[session_token]
        return None
    
    return session_data['username']

def clear_session(session_token: str):
    """Clear a session token"""
    if session_token in active_sessions:
        del active_sessions[session_token]

def check_rate_limit(username: str, db) -> bool:
    """Check if user is rate limited due to failed login attempts"""
    cursor = db.cursor()
    cursor.execute("SELECT failed_attempts, last_fail FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    
    if not result:
        return True  # User doesn't exist, allow
    
    failed_attempts, last_fail_str = result
    
    if failed_attempts < 4:
        return True
    
    if not last_fail_str:
        return True
        
    last_fail = datetime.fromisoformat(last_fail_str)
    now = datetime.now()
    
    # Progressive lockouts: 4+ fails = 5 min, 6+ fails = 15 min, 8+ fails = 60 min
    if failed_attempts >= 8:
        lockout_minutes = 60
    elif failed_attempts >= 6:
        lockout_minutes = 15
    else:
        lockout_minutes = 5
    
    return (now - last_fail) > timedelta(minutes=lockout_minutes)