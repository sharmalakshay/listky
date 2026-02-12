import os
import hashlib
from datetime import date
from fastapi import Request

# Configuration
PIN_SALT = os.getenv("PIN_SALT", "default_development_salt_change_in_production")

def hash_ip(ip: str) -> str:
    """Hash IP address with salt for privacy-preserving storage"""
    return hashlib.sha256((ip + PIN_SALT).encode('utf-8')).hexdigest()

def get_client_ip(request: Request) -> str:
    """Get client IP from request, handling proxies"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host

def track_list_view(list_id: int, request: Request, db) -> bool:
    """
    Track a list view in a privacy-preserving way.
    Uses hashed IP + date to prevent double-counting while preserving privacy.
    
    Returns True if view was successfully tracked, False otherwise.
    """
    try:
        ip_hash = hash_ip(get_client_ip(request))
        today = date.today().isoformat()
        
        cursor = db.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO views (list_id, view_date, ip_hash)
            VALUES (?, ?, ?)
        """, (list_id, today, ip_hash))
        db.commit()
        return True
    except Exception:
        # Ignore view tracking errors - privacy tracking should never break core functionality
        return False

def get_trending_lists(db, days: int = 7, limit: int = 10):
    """
    Get trending public lists based on unique daily views.
    Privacy-preserving: counts unique hashed IPs per day, not actual IPs.
    """
    cursor = db.cursor()
    cursor.execute("""
        SELECT l.username, l.slug, l.title, COUNT(DISTINCT v.ip_hash) as view_count
        FROM lists l
        JOIN views v ON l.id = v.list_id 
        WHERE l.is_public = 1 
        AND v.view_date >= date('now', '-{} days')
        GROUP BY l.id, l.username, l.slug, l.title
        ORDER BY view_count DESC
        LIMIT ?
    """.format(days), (limit,))
    return cursor.fetchall()

def anonymize_user_data(username: str, db):
    """
    Anonymize user data while preserving functionality.
    Called when user requests data deletion or for GDPR compliance.
    
    Note: This is a placeholder for future privacy compliance features.
    """
    # This would implement data anonymization while preserving list functionality
    # For now, this is just a placeholder for the privacy module structure
    pass