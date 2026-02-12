"""
Core API module for listky.top

This module provides the core data and business logic functions that can be used by:
1. The web interface (main.py)
2. Premium features (analytics, advanced search, etc.)
3. Future mobile apps or third-party integrations

All functions return data structures, not HTML/web responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from core.auth import hash_pin, verify_pin, check_rate_limit, is_valid_username, is_valid_pin, is_valid_slug
from core.privacy import hash_ip, track_list_view, get_trending_lists
from core.plugins import on_user_created, on_user_login, on_list_created, on_list_viewed, on_list_updated, on_list_deleted

class ListkyError(Exception):
    """Base exception for listky API errors"""
    pass

class UserAlreadyExistsError(ListkyError):
    pass

class InvalidCredentialsError(ListkyError):
    pass

class RateLimitError(ListkyError):
    pass

class ListNotFoundError(ListkyError):
    pass

class UnauthorizedError(ListkyError):
    pass

# User Management API

def create_user(username: str, pin: str, client_ip: str, db) -> Dict[str, Any]:
    """
    Create a new user account.
    
    Returns: {"success": True, "username": str} or raises exception
    """
    username = username.lower()
    
    if not is_valid_username(username):
        raise ListkyError("Invalid username: must be 3-20 alphanumeric characters")
    
    if not is_valid_pin(pin):
        raise ListkyError("Invalid PIN: must be exactly 6 digits")
    
    # Check if username exists
    cursor = db.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        raise UserAlreadyExistsError(f"Username '{username}' is already taken")
    
    # Create user
    pin_hash = hash_pin(pin)
    ip_hash = hash_ip(client_ip)
    
    cursor.execute("""
        INSERT INTO users (username, pin_hash, last_ip_hash)
        VALUES (?, ?, ?)
    """, (username, pin_hash, ip_hash))
    db.commit()
    
    # Emit plugin hook for user creation
    on_user_created(username=username, client_ip=client_ip)
    
    return {"success": True, "username": username}

def authenticate_user(username: str, pin: str, client_ip: str, db) -> Dict[str, Any]:
    """
    Authenticate a user with username and PIN.
    
    Returns: {"success": True, "username": str} or raises exception
    """
    username = username.lower()
    
    if not check_rate_limit(username, db):
        raise RateLimitError("Too many failed attempts. Please try again later.")
    
    cursor = db.cursor()
    cursor.execute("SELECT pin_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    
    if not result or not verify_pin(pin, result[0]):
        # Record failed attempt
        cursor.execute("""
            UPDATE users 
            SET failed_attempts = failed_attempts + 1, last_fail = ? 
            WHERE username = ?
        """, (datetime.now().isoformat(), username))
        db.commit()
        raise InvalidCredentialsError("Invalid username or PIN")
    
    # Successful login - reset failed attempts and update IP
    ip_hash = hash_ip(client_ip)
    cursor.execute("""
        UPDATE users 
        SET failed_attempts = 0, last_fail = NULL, last_ip_hash = ?
        WHERE username = ?
    """, (ip_hash, username))
    db.commit()
    
    # Emit plugin hook for user login
    on_user_login(username=username, client_ip=client_ip)
    
    return {"success": True, "username": username}

def get_user_info(username: str, db) -> Optional[Dict[str, Any]]:
    """Get basic user information (no sensitive data)"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT username, created_at 
        FROM users 
        WHERE username = ?
    """, (username.lower(),))
    result = cursor.fetchone()
    
    if not result:
        return None
        
    return {
        "username": result[0],
        "created_at": result[1]
    }

# List Management API

def create_list(username: str, slug: str, title: str, content: str, is_public: bool, db) -> Dict[str, Any]:
    """
    Create a new list.
    
    Returns: {"success": True, "list_id": int, "slug": str} or raises exception
    """
    username = username.lower()
    
    if not is_valid_slug(slug):
        raise ListkyError("Invalid slug: must be 1-50 alphanumeric characters and hyphens")
    
    if not title or len(title) > 200:
        raise ListkyError("Title must be 1-200 characters")
    
    if not content or len(content) > 10000:
        raise ListkyError("Content must be 1-10,000 characters")
    
    # Check if list already exists for this user
    cursor = db.cursor()
    cursor.execute("SELECT id FROM lists WHERE username = ? AND slug = ?", (username, slug))
    if cursor.fetchone():
        raise ListkyError(f"List '{slug}' already exists for user '{username}'")
    
    # Create list
    cursor.execute("""
        INSERT INTO lists (username, slug, title, content, is_public)
        VALUES (?, ?, ?, ?, ?)
    """, (username, slug, title, content, is_public))
    db.commit()
    
    list_id = cursor.lastrowid
    
    # Emit plugin hook for list creation
    on_list_created(username=username, slug=slug, title=title, is_public=is_public)
    
    return {"success": True, "list_id": list_id, "slug": slug}

def get_list(username: str, slug: str, db) -> Optional[Dict[str, Any]]:
    """Get a list by username and slug"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, title, content, is_public, created_at, updated_at
        FROM lists 
        WHERE username = ? AND slug = ?
    """, (username.lower(), slug))
    result = cursor.fetchone()
    
    if not result:
        return None
    
    return {
        "id": result[0],
        "username": username,
        "slug": slug,
        "title": result[1],
        "content": result[2],
        "is_public": bool(result[3]),
        "created_at": result[4],
        "updated_at": result[5]
    }

def update_list(username: str, slug: str, title: str, content: str, is_public: bool, db) -> Dict[str, Any]:
    """Update an existing list"""
    username = username.lower()
    
    if not title or len(title) > 200:
        raise ListkyError("Title must be 1-200 characters")
    
    if not content or len(content) > 10000:
        raise ListkyError("Content must be 1-10,000 characters")
    
    cursor = db.cursor()
    cursor.execute("""
        UPDATE lists 
        SET title = ?, content = ?, is_public = ?, updated_at = CURRENT_TIMESTAMP
        WHERE username = ? AND slug = ?
    """, (title, content, is_public, username, slug))
    
    if cursor.rowcount == 0:
        raise ListNotFoundError(f"List '{slug}' not found for user '{username}'")
    
    db.commit()
    
    # Emit plugin hook for list update
    on_list_updated(username=username, slug=slug, title=title)
    
    return {"success": True}

def delete_list(username: str, slug: str, db) -> Dict[str, Any]:
    """Delete a list"""
    cursor = db.cursor()
    cursor.execute("DELETE FROM lists WHERE username = ? AND slug = ?", (username.lower(), slug))
    
    if cursor.rowcount == 0:
        raise ListNotFoundError(f"List '{slug}' not found for user '{username}'")
    
    db.commit()
    
    # Emit plugin hook for list deletion
    on_list_deleted(username=username, slug=slug)
    
    return {"success": True}

def get_user_lists(username: str, include_private: bool = False, db = None) -> List[Dict[str, Any]]:
    """Get all lists for a user"""
    cursor = db.cursor()
    
    if include_private:
        cursor.execute("""
            SELECT slug, title, is_public, created_at, updated_at
            FROM lists 
            WHERE username = ?
            ORDER BY updated_at DESC
        """, (username.lower(),))
    else:
        cursor.execute("""
            SELECT slug, title, is_public, created_at, updated_at
            FROM lists 
            WHERE username = ? AND is_public = 1
            ORDER BY updated_at DESC
        """, (username.lower(),))
    
    results = cursor.fetchall()
    return [{
        "username": username,
        "slug": result[0],
        "title": result[1],
        "is_public": bool(result[2]),
        "created_at": result[3],
        "updated_at": result[4]
    } for result in results]

# Discovery & Analytics API

def get_trending_public_lists(db, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
    """Get trending public lists"""
    results = get_trending_lists(db, days, limit)
    return [{
        "username": result[0],
        "slug": result[1],
        "title": result[2],
        "view_count": result[3]
    } for result in results]

def record_list_view(username: str, slug: str, request, db) -> bool:
    """Record a view for a list"""
    list_data = get_list(username, slug, db)
    if not list_data or not list_data["is_public"]:
        return False
    
    # Track the view
    success = track_list_view(list_data["id"], request, db)
    
    # Emit plugin hook for list view
    if success:
        from core.privacy import get_client_ip
        viewer_ip = get_client_ip(request)
        on_list_viewed(username=username, slug=slug, viewer_ip=viewer_ip)
    
    return success