import os
import hashlib
import bcrypt
import sqlite3
import re
import secrets
from datetime import datetime, timedelta, date
from typing import Optional, Union
from fastapi import FastAPI, Form, Request, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from dotenv import load_dotenv
from database import init_db, get_db

# Load environment variables
load_dotenv()

app = FastAPI(title="listky.top", description="One-word lists. Privacy first.")

# Configuration
PIN_SALT = os.getenv("PIN_SALT", "default_development_salt_change_in_production")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Simple session storage (in-memory, for v1 simplicity)
active_sessions = {}  # session_token -> {username: str, expires: datetime}

# Initialize DB on startup
init_db()

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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db = Depends(get_db)):
    # Check if user is logged in
    current_user = get_session_user(request)
    
    # Get trending lists
    cursor = db.cursor()
    cursor.execute("""
        SELECT l.username, l.slug, l.title, COUNT(DISTINCT v.ip_hash) as view_count
        FROM lists l
        LEFT JOIN views v ON l.id = v.list_id AND v.view_date >= date('now', '-7 days')
        WHERE l.is_public = 1
        GROUP BY l.id
        ORDER BY view_count DESC, l.created_at DESC
        LIMIT 10
    """)
    trending = cursor.fetchall()
    
    trending_html = ""
    if trending:
        trending_html = "<h2>Trending Lists (last 7 days)</h2><ul>"
        for username, slug, title, views in trending:
            trending_html += f'<li><a href="/{username}/{slug}">{title}</a> by <a href="/{username}">{username}</a> ({views} views)</li>'
        trending_html += "</ul>"
    
    # Show different buttons based on login status
    if current_user:
        actions_html = f"""
            <div class="actions">
                <a href="/{current_user}">👤 My Profile</a>
                <a href="/{current_user}/create">📝 Create List</a>
                <a href="/{current_user}/manage">⚙️ Manage Lists</a>
                <a href="/logout">🚪 Log Out</a>
            </div>
            """
        welcome_html = f'<p class="welcome">Welcome back, <strong>{current_user}</strong>!</p>'
    else:
        actions_html = """
            <div class="actions">
                <a href="/signup">Sign Up</a>
                <a href="/login">Log In</a>
            </div>
            """
        welcome_html = ""
    return f"""
    <html>
        <head>
            <title>listky.top</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: system-ui, -apple-system, sans-serif; padding: 20px; max-width: 700px; margin: 0 auto; line-height: 1.5; }}
                h1 {{ margin-bottom: 0.5rem; }}
                .tagline {{ color: #666; margin-bottom: 2rem; }}
                .welcome {{ background: #e8f4fd; padding: 1rem; border-radius: 4px; margin: 1rem 0; border-left: 4px solid #007acc; color: #0066aa; }}
                .actions {{ margin: 2rem 0; }}
                .actions a {{ display: inline-block; margin-right: 1rem; margin-bottom: 0.5rem; padding: 0.5rem 1rem; background: #007acc; color: white; text-decoration: none; border-radius: 4px; }}
                .actions a:hover {{ background: #005c99; }}
                ul {{ padding-left: 1.2rem; }}
                li {{ margin: 0.5rem 0; }}
                .footer {{ margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #eee; color: #666; font-size: 0.9rem; }}
            </style>
        </head>
        <body>
            <h1>listky.top</h1>
            <p class="tagline"><strong>One word. One PIN. Zero bullshit.</strong></p>
            <p>The dumbest, most private, minimalist list-sharing platform on the internet.</p>
            
            {welcome_html}
            {actions_html}
            
            {trending_html}
            
            <div class="footer">
                <p>No tracking, no analytics, no bullshit. Your PIN is your only key - lose it and your account is gone forever.</p>
                <p><a href="https://github.com/sharmalakshay/listky" target="_blank">Source Code</a> | AGPL-3.0 Licensed</p>
            </div>
        </body>
    </html>
    """

@app.get("/signup", response_class=HTMLResponse)
async def signup_form():
    return """
    <html>
        <head>
            <title>Sign Up - listky.top</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: system-ui, -apple-system, sans-serif; padding: 20px; max-width: 400px; margin: 0 auto; line-height: 1.5; }
                h1 { margin-bottom: 0.5rem; }
                .form-group { margin: 1rem 0; }
                label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
                input[type="text"], input[type="password"] { width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }
                button { padding: 0.75rem 1.5rem; background: #007acc; color: white; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; width: 100%; }
                button:hover { background: #005c99; }
                .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 1rem; border-radius: 4px; margin: 1rem 0; }
                .back { margin-top: 2rem; }
                .back a { color: #007acc; text-decoration: none; }
            </style>
        </head>
        <body>
            <h1>Sign Up</h1>
            <div class="warning">
                <strong>⚠️ Warning:</strong> There is NO account recovery. If you forget your PIN, your account is lost forever. Choose wisely.
            </div>
            
            <form method="post" action="/signup">
                <div class="form-group">
                    <label for="username">Username (3-20 alphanumeric chars)</label>
                    <input type="text" id="username" name="username" required pattern="[a-zA-Z0-9]{3,20}" placeholder="yourname">
                </div>
                
                <div class="form-group">
                    <label for="pin">6-digit PIN</label>
                    <input type="password" id="pin" name="pin" required pattern="\\d{6}" placeholder="123456" maxlength="6">
                </div>
                
                <div class="form-group">
                    <label for="pin_confirm">Confirm PIN</label>
                    <input type="password" id="pin_confirm" name="pin_confirm" required pattern="\\d{6}" placeholder="123456" maxlength="6">
                </div>
                
                <button type="submit">Create Account</button>
            </form>
            
            <div class="back">
                <a href="/">← Back to Home</a>
            </div>
        </body>
    </html>
    """

@app.post("/signup")
async def signup(request: Request, username: str = Form(...), pin: str = Form(...), pin_confirm: str = Form(...), db = Depends(get_db)):
    # Validate input
    if not is_valid_username(username):
        raise HTTPException(status_code=400, detail="Invalid username format")
    
    if not is_valid_pin(pin):
        raise HTTPException(status_code=400, detail="PIN must be exactly 6 digits")
    
    if pin != pin_confirm:
        raise HTTPException(status_code=400, detail="PINs don't match")
    
    # Check if username exists
    cursor = db.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (username.lower(),))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    pin_hash = hash_pin(pin)
    ip_hash = hash_ip(get_client_ip(request))
    
    cursor.execute("""
        INSERT INTO users (username, pin_hash, last_ip_hash)
        VALUES (?, ?, ?)
    """, (username.lower(), pin_hash, ip_hash))
    db.commit()
    
    # Redirect to login
    return RedirectResponse(url="/login?signup=success", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_form(signup: Optional[str] = None):
    success_msg = ""
    if signup == "success":
        success_msg = '<div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 1rem; border-radius: 4px; margin: 1rem 0; color: #155724;">Account created successfully! Now log in with your PIN.</div>'
    
    return f"""
    <html>
        <head>
            <title>Log In - listky.top</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: system-ui, -apple-system, sans-serif; padding: 20px; max-width: 400px; margin: 0 auto; line-height: 1.5; }}
                h1 {{ margin-bottom: 0.5rem; }}
                .form-group {{ margin: 1rem 0; }}
                label {{ display: block; margin-bottom: 0.5rem; font-weight: bold; }}
                input[type="text"], input[type="password"] {{ width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }}
                button {{ padding: 0.75rem 1.5rem; background: #007acc; color: white; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; width: 100%; }}
                button:hover {{ background: #005c99; }}
                .back {{ margin-top: 2rem; }}
                .back a {{ color: #007acc; text-decoration: none; }}
            </style>
        </head>
        <body>
            <h1>Log In</h1>
            {success_msg}
            
            <form method="post" action="/login">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label for="pin">PIN</label>
                    <input type="password" id="pin" name="pin" required maxlength="6">
                </div>
                
                <button type="submit">Log In</button>
            </form>
            
            <div class="back">
                <a href="/">← Back to Home</a> | <a href="/signup">Need an account?</a>
            </div>
        </body>
    </html>
    """

@app.post("/login")
async def login(request: Request, username: str = Form(...), pin: str = Form(...), db = Depends(get_db)):
    username = username.lower().strip()
    
    if not is_valid_username(username):
        raise HTTPException(status_code=400, detail="Invalid username")
    
    if not is_valid_pin(pin):
        raise HTTPException(status_code=400, detail="Invalid PIN format")
    
    # Check rate limit
    if not check_rate_limit(username, db):
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")
    
    cursor = db.cursor()
    cursor.execute("SELECT pin_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    
    if not result or not verify_pin(pin, result[0]):
        # Update failed attempts
        cursor.execute("""
            UPDATE users 
            SET failed_attempts = failed_attempts + 1, last_fail = ?
            WHERE username = ?
        """, (datetime.now().isoformat(), username))
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Reset failed attempts on success
    ip_hash = hash_ip(get_client_ip(request))
    cursor.execute("""
        UPDATE users 
        SET failed_attempts = 0, last_fail = NULL, last_ip_hash = ?
        WHERE username = ?
    """, (ip_hash, username))
    db.commit()
    
    # Create session and set cookie
    session_token = create_session(username)
    response = RedirectResponse(url=f"/{username}", status_code=303)
    response.set_cookie(
        key="session",
        value=session_token,
        max_age=86400,  # 24 hours
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    return response

@app.get("/logout")
async def logout(request: Request):
    session_token = request.cookies.get('session')
    if session_token:
        clear_session(session_token)
    
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session")
    return response

@app.get("/status")
async def status(db = Depends(get_db)):
    return {"status": "running", "database": "sqlite ready", "version": "v1.0"}

@app.get("/{username}", response_class=HTMLResponse)
async def user_profile(username: str, request: Request, db = Depends(get_db)):
    username = username.lower()
    
    if not is_valid_username(username):
        raise HTTPException(status_code=404, detail="User not found")
    
    cursor = db.cursor()
    cursor.execute("SELECT username, created_at FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get public lists
    cursor.execute("""
        SELECT slug, title, created_at, updated_at
        FROM lists 
        WHERE username = ? AND is_public = 1
        ORDER BY updated_at DESC
    """, (username,))
    public_lists = cursor.fetchall()
    
    # Check if this is the user's own profile using session authentication
    current_user = get_session_user(request)
    is_owner = current_user == username
    
    lists_html = ""
    if public_lists:
        lists_html = "<h2>Public Lists</h2><ul>"
        for slug, title, created, updated in public_lists:
            lists_html += f'<li><a href="/{username}/{slug}">{title}</a> <small>(updated {updated[:10]})</small></li>'
        lists_html += "</ul>"
    else:
        if is_owner:
            lists_html = "<p>You haven't created any public lists yet.</p>"
        else:
            lists_html = "<p>No public lists yet.</p>"
    
    # Add management links if this is the owner
    manage_html = ""
    if is_owner:
        manage_html = f"""
        <div style="background: #e8f4fd; padding: 1rem; border-radius: 4px; margin: 1rem 0; border-left: 4px solid #007acc;">
            <h3>Your Account</h3>
            <p><a href="/{username}/create">📝 Create New List</a></p>
            <p><a href="/{username}/manage">⚙️ Manage All Lists</a></p>
            <p><a href="/logout">🚪 Log Out</a></p>
        </div>
        """
    
    return f"""
    <html>
        <head>
            <title>{username} - listky.top</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: system-ui, -apple-system, sans-serif; padding: 20px; max-width: 700px; margin: 0 auto; line-height: 1.5; }}
                h1 {{ margin-bottom: 0.5rem; }}
                ul {{ padding-left: 1.2rem; }}
                li {{ margin: 0.5rem 0; }}
                a {{ color: #007acc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .back {{ margin-top: 2rem; }}
                small {{ color: #666; }}
            </style>
        </head>
        <body>
            <h1>{username}</h1>
            <p>Member since {user[1][:10]}</p>
            
            {manage_html}
            {lists_html}
            
            <div class="back">
                <a href="/">← Back to Home</a>
            </div>
        </body>
    </html>
    """

@app.get("/{username}/create", response_class=HTMLResponse)
async def create_list_form(username: str, request: Request):
    username = username.lower()
    
    if not is_valid_username(username):
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is authenticated
    current_user = get_session_user(request)
    if current_user != username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return f"""
    <html>
        <head>
            <title>Create List - {username} - listky.top</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: system-ui, -apple-system, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; line-height: 1.5; }}
                h1 {{ margin-bottom: 0.5rem; }}
                .form-group {{ margin: 1rem 0; }}
                label {{ display: block; margin-bottom: 0.5rem; font-weight: bold; }}
                input[type="text"], input[type="password"], textarea {{ width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }}
                textarea {{ height: 200px; resize: vertical; }}
                button {{ padding: 0.75rem 1.5rem; background: #007acc; color: white; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; }}
                button:hover {{ background: #005c99; }}
                .checkbox-group {{ display: flex; align-items: center; }}
                .checkbox-group input {{ width: auto; margin-right: 0.5rem; }}
                .back {{ margin-top: 2rem; }}
                .back a {{ color: #007acc; text-decoration: none; }}
            </style>
        </head>
        <body>
            <h1>Create New List</h1>
            
            <form method="post" action="/{username}/create">
                <div class="form-group">
                    <label for="title">List Title</label>
                    <input type="text" id="title" name="title" required maxlength="100" placeholder="My Awesome List">
                </div>
                
                <div class="form-group">
                    <label for="slug">URL Slug (letters, numbers, hyphens only)</label>
                    <input type="text" id="slug" name="slug" required pattern="[a-zA-Z0-9-]{{1,50}}" placeholder="my-awesome-list">
                    <small>Will be accessible at: listky.top/{username}/your-slug</small>
                </div>
                
                <div class="form-group">
                    <label for="content">List Content (plain text + links)</label>
                    <textarea id="content" name="content" required placeholder="• Item 1&#10;• Item 2&#10;• Check out https://example.com&#10;• Item 4"></textarea>
                </div>
                
                <div class="form-group checkbox-group">
                    <input type="checkbox" id="is_public" name="is_public" value="1">
                    <label for="is_public">Make this list public (visible to everyone and in trending)</label>
                </div>
                
                <button type="submit">Create List</button>
            </form>
            
            <div class="back">
                <a href="/{username}">← Back to Profile</a>
            </div>
        </body>
    </html>
    """

@app.post("/{username}/create")
async def create_list(username: str, request: Request, title: str = Form(...), 
                     slug: str = Form(...), content: str = Form(...), 
                     is_public: Optional[str] = Form(None), db = Depends(get_db)):
    username = username.lower()
    
    if not is_valid_username(username) or not is_valid_slug(slug):
        raise HTTPException(status_code=400, detail="Invalid input")
    
    # Check if user is authenticated
    current_user = get_session_user(request)
    if current_user != username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    cursor = db.cursor()
    
    # Check if slug already exists for this user
    cursor.execute("SELECT id FROM lists WHERE username = ? AND slug = ?", (username, slug))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="A list with this slug already exists")
    
    # Create list
    is_public_bool = bool(is_public)
    cursor.execute("""
        INSERT INTO lists (username, slug, title, content, is_public)
        VALUES (?, ?, ?, ?, ?)
    """, (username, slug, title.strip(), content.strip(), is_public_bool))
    db.commit()
    
    return RedirectResponse(url=f"/{username}/{slug}", status_code=303)

@app.get("/{username}/manage", response_class=HTMLResponse)
async def manage_lists(username: str, request: Request, db = Depends(get_db)):
    username = username.lower()
    
    if not is_valid_username(username):
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is authenticated
    current_user = get_session_user(request)
    if current_user != username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get all lists for this user
    cursor = db.cursor()
    cursor.execute("""
        SELECT slug, title, is_public, created_at, updated_at
        FROM lists 
        WHERE username = ?
        ORDER BY updated_at DESC
    """, (username,))
    lists = cursor.fetchall()
    
    lists_html = ""
    if lists:
        lists_html = "<h2>Your Lists</h2>"
        for slug, title, is_public, created, updated in lists:
            visibility = "🌍 Public" if is_public else "🔒 Private"
            lists_html += f"""
            <div style="border: 1px solid #ddd; padding: 1rem; margin: 1rem 0; border-radius: 4px; background: #f9f9f9;">
                <h3><a href="/{username}/{slug}" style="color: #007acc; text-decoration: none;">{title}</a></h3>
                <p><strong>Status:</strong> {visibility} | <strong>Updated:</strong> {updated[:10]}</p>
                <p>
                    <a href="/{username}/{slug}/edit" style="color: #007acc; text-decoration: none;">✏️ Edit</a> | 
                    <a href="/{username}/{slug}/delete" style="color: #dc3545; text-decoration: none;" onclick="return confirm('Are you sure? This cannot be undone!')">🗑️ Delete</a>
                </p>
            </div>
            """
    else:
        lists_html = f"<p>You haven't created any lists yet. <a href='/{username}/create'>Create your first list!</a></p>"
    
    return f"""
    <html>
        <head>
            <title>Manage Lists - {username} - listky.top</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: system-ui, -apple-system, sans-serif; padding: 20px; max-width: 700px; margin: 0 auto; line-height: 1.5; }}
                h1, h2, h3 {{ margin-bottom: 0.5rem; }}
                a {{ color: #007acc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .create-btn {{ display: inline-block; background: #28a745; color: white; padding: 0.75rem 1.5rem; border-radius: 4px; text-decoration: none; margin-bottom: 2rem; }}
                .create-btn:hover {{ background: #218838; color: white; text-decoration: none; }}
                .back {{ margin-top: 2rem; }}
            </style>
        </head>
        <body>
            <h1>Manage Your Lists</h1>
            
            <a href="/{username}/create" class="create-btn">+ Create New List</a>
            
            {lists_html}
            
            <div class="back">
                <a href="/{username}">← Back to Profile</a>
            </div>
        </body>
    </html>
    """

@app.get("/{username}/{slug}", response_class=HTMLResponse)
async def view_list(username: str, slug: str, request: Request, db = Depends(get_db)):
    username = username.lower()
    
    if not is_valid_username(username) or not is_valid_slug(slug):
        raise HTTPException(status_code=404, detail="List not found")
    
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, title, content, is_public, created_at, updated_at
        FROM lists 
        WHERE username = ? AND slug = ?
    """, (username, slug))
    list_data = cursor.fetchone()
    
    if not list_data:
        raise HTTPException(status_code=404, detail="List not found")
    
    list_id, title, content, is_public, created_at, updated_at = list_data
    
    # Check if list is private
    if not is_public:
        # For v1, we'll just show a message that it's private
        # In v2, we could add PIN authentication for private list access
        return f"""
        <html>
            <head>
                <title>Private List - listky.top</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: system-ui, -apple-system, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; line-height: 1.5; }}
                </style>
            </head>
            <body>
                <h1>Private List</h1>
                <p>This list is private and not publicly accessible.</p>
                <p><a href="/{username}">← Back to {username}'s profile</a></p>
            </body>
        </html>
        """
    
    # Track view for trending
    ip_hash = hash_ip(get_client_ip(request))
    today = date.today().isoformat()
    
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO views (list_id, view_date, ip_hash)
            VALUES (?, ?, ?)
        """, (list_id, today, ip_hash))
        db.commit()
    except:
        pass  # Ignore view tracking errors
    
    # Convert URLs in content to clickable links
    import re
    def make_links(text):
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:]'
        return re.sub(url_pattern, r'<a href="\g<0>" target="_blank" rel="noopener">\g<0></a>', text)
    
    formatted_content = make_links(content.replace('\n', '<br>'))
    
    return f"""
    <html>
        <head>
            <title>{title} by {username} - listky.top</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta property="og:title" content="{title}">
            <meta property="og:description" content="A list by {username} on listky.top">
            <style>
                body {{ font-family: system-ui, -apple-system, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; line-height: 1.6; }}
                h1 {{ margin-bottom: 0.5rem; }}
                .meta {{ color: #666; margin-bottom: 2rem; }}
                .content {{ background: #f8f9fa; padding: 1.5rem; border-radius: 4px; margin: 2rem 0; border-left: 4px solid #007acc; }}
                .back {{ margin-top: 2rem; }}
                .back a {{ color: #007acc; text-decoration: none; }}
                a {{ color: #007acc; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="meta">
                By <a href="/{username}">{username}</a> • 
                Created {created_at[:10]} • 
                Updated {updated_at[:10]}
            </div>
            
            <div class="content">
                {formatted_content}
            </div>
            
            <div class="back">
                <a href="/{username}">← More lists by {username}</a> | 
                <a href="/">← Home</a>
            </div>
        </body>
    </html>
    """

@app.get("/{username}/{slug}/edit", response_class=HTMLResponse)
async def edit_list_form(username: str, slug: str, request: Request, db = Depends(get_db)):
    username = username.lower()
    
    if not is_valid_username(username) or not is_valid_slug(slug):
        raise HTTPException(status_code=404, detail="List not found")
    
    # Check if user is authenticated
    current_user = get_session_user(request)
    if current_user != username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get list data
    cursor = db.cursor()
    cursor.execute("""
        SELECT title, content, is_public
        FROM lists 
        WHERE username = ? AND slug = ?
    """, (username, slug))
    list_data = cursor.fetchone()
    
    if not list_data:
        raise HTTPException(status_code=404, detail="List not found")
    
    title, content, is_public = list_data
    checked = "checked" if is_public else ""
    
    return f"""
    <html>
        <head>
            <title>Edit: {title} - listky.top</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: system-ui, -apple-system, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; line-height: 1.5; }}
                h1 {{ margin-bottom: 0.5rem; }}
                .form-group {{ margin: 1rem 0; }}
                label {{ display: block; margin-bottom: 0.5rem; font-weight: bold; }}
                input[type="text"], textarea {{ width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }}
                textarea {{ height: 200px; resize: vertical; }}
                button {{ padding: 0.75rem 1.5rem; background: #007acc; color: white; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; }}
                button:hover {{ background: #005c99; }}
                .checkbox-group {{ display: flex; align-items: center; }}
                .checkbox-group input {{ width: auto; margin-right: 0.5rem; }}
                .back {{ margin-top: 2rem; }}
                .back a {{ color: #007acc; text-decoration: none; }}
            </style>
        </head>
        <body>
            <h1>Edit: {title}</h1>
            
            <form method="post" action="/{username}/{slug}/update">
                <div class="form-group">
                    <label for="title">List Title</label>
                    <input type="text" id="title" name="title" required maxlength="100" value="{title}">
                </div>
                
                <div class="form-group">
                    <label for="content">List Content</label>
                    <textarea id="content" name="content" required>{content}</textarea>
                </div>
                
                <div class="form-group checkbox-group">
                    <input type="checkbox" id="is_public" name="is_public" value="1" {checked}>
                    <label for="is_public">Make this list public</label>
                </div>
                
                <button type="submit">Save Changes</button>
            </form>
            
            <div class="back">
                <a href="/{username}/{slug}">← View List</a> | 
                <a href="/{username}/manage">← Manage Lists</a>
            </div>
        </body>
    </html>
    """

@app.post("/{username}/{slug}/update")
async def update_list(username: str, slug: str, request: Request, title: str = Form(...), 
                     content: str = Form(...), is_public: Optional[str] = Form(None), 
                     db = Depends(get_db)):
    username = username.lower()
    
    if not is_valid_username(username) or not is_valid_slug(slug):
        raise HTTPException(status_code=400, detail="Invalid input")
    
    # Check if user is authenticated
    current_user = get_session_user(request)
    if current_user != username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Update list
    is_public_bool = bool(is_public)
    cursor = db.cursor()
    cursor.execute("""
        UPDATE lists 
        SET title = ?, content = ?, is_public = ?, updated_at = CURRENT_TIMESTAMP
        WHERE username = ? AND slug = ?
    """, (title.strip(), content.strip(), is_public_bool, username, slug))
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="List not found")
    
    db.commit()
    return RedirectResponse(url=f"/{username}/{slug}", status_code=303)

@app.get("/{username}/{slug}/delete", response_class=HTMLResponse)
async def delete_list_form(username: str, slug: str, request: Request):
    username = username.lower()
    
    # Check if user is authenticated
    current_user = get_session_user(request)
    if current_user != username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return f"""
    <html>
        <head>
            <title>Delete List - {username} - listky.top</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: system-ui, -apple-system, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; line-height: 1.5; }}
                h1 {{ margin-bottom: 0.5rem; }}
                .warning {{ background: #f8d7da; border: 1px solid #f5c6cb; padding: 1rem; border-radius: 4px; margin: 1rem 0; color: #721c24; }}
                .form-group {{ margin: 1rem 0; }}
                button {{ padding: 0.75rem 1.5rem; background: #dc3545; color: white; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; }}
                button:hover {{ background: #c82333; }}
                .cancel {{ padding: 0.75rem 1.5rem; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; text-decoration: none; display: inline-block; margin-left: 1rem; }}
                .cancel:hover {{ background: #5a6268; color: white; text-decoration: none; }}
                .back {{ margin-top: 2rem; }}
                .back a {{ color: #007acc; text-decoration: none; }}
            </style>
        </head>
        <body>
            <h1>Delete List: {slug}</h1>
            
            <div class="warning">
                <strong>⚠️ Warning:</strong> This action cannot be undone. The list will be permanently deleted.
            </div>
            
            <form method="post" action="/{username}/{slug}/delete" style="display: inline;">
                <button type="submit" onclick="return confirm('Are you absolutely sure? This cannot be undone!')">Permanently Delete</button>
                <a href="/{username}/manage" class="cancel">Cancel</a>
            </form>
            
            <div class="back">
                <a href="/{username}/manage">← Back to Manage Lists</a>
            </div>
        </body>
    </html>
    """

@app.post("/{username}/{slug}/delete")
async def delete_list(username: str, slug: str, request: Request, db = Depends(get_db)):
    username = username.lower()
    
    if not is_valid_username(username) or not is_valid_slug(slug):
        raise HTTPException(status_code=400, detail="Invalid input")
    
    # Check if user is authenticated
    current_user = get_session_user(request)
    if current_user != username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Delete list (views will be cascade deleted due to foreign key)
    cursor = db.cursor()
    cursor.execute("DELETE FROM lists WHERE username = ? AND slug = ?", (username, slug))
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="List not found")
    
    db.commit()
    return RedirectResponse(url=f"/{username}/manage", status_code=303)