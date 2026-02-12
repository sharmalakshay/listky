import os
from typing import Optional
from fastapi import FastAPI, Form, Request, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Import core modules
from core.database import init_db, get_db
from core.auth import (
    create_session, get_session_user, clear_session,
    is_valid_username, is_valid_pin, is_valid_slug
)
from core.api import (
    create_user, authenticate_user, get_user_info,
    create_list, get_list, update_list, delete_list, get_user_lists,
    get_trending_public_lists, record_list_view,
    ListkyError, UserAlreadyExistsError, InvalidCredentialsError, 
    RateLimitError, ListNotFoundError, UnauthorizedError
)
from core.privacy import get_client_ip

# Load environment variables
load_dotenv()

app = FastAPI(title="listky.top", description="One-word lists. Privacy first.")

# Setup templates and static files
templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Initialize DB on startup
init_db()

def make_links(text):
    """Convert URLs in text to clickable links"""
    import re
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:]'
    return re.sub(url_pattern, r'<a href="\g<0>" target="_blank" rel="noopener">\g<0></a>', text)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db = Depends(get_db)):
    current_user = get_session_user(request)
    
    # Get trending lists
    trending_data = get_trending_public_lists(db, days=7, limit=5)
    
    context = {
        "request": request,
        "current_user": current_user,
        "trending_lists": trending_data,
        "welcome_message": f"Welcome back, {current_user}!" if current_user else None
    }
    
    return templates.TemplateResponse("home.html", context)

@app.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(request: Request, username: str = Form(...), pin: str = Form(...), 
                 pin_confirm: str = Form(...), db = Depends(get_db)):
    try:
        if pin != pin_confirm:
            raise ListkyError("PINs do not match")
        
        client_ip = get_client_ip(request)
        result = create_user(username, pin, client_ip, db)
        
        return RedirectResponse(url="/login?signup=success", status_code=303)
        
    except (ListkyError, UserAlreadyExistsError) as e:
        # In a real implementation, you'd pass the error to the template
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, signup: Optional[str] = None):
    context = {
        "request": request,
        "signup_success": signup == "success"
    }
    return templates.TemplateResponse("login.html", context)

@app.post("/login")
async def login(request: Request, username: str = Form(...), pin: str = Form(...), 
               db = Depends(get_db)):
    try:
        client_ip = get_client_ip(request)
        result = authenticate_user(username, pin, client_ip, db)
        
        # Create session
        session_token = create_session(result["username"])
        
        # Set cookie and redirect
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="session",
            value=session_token,
            max_age=24*3600,  # 24 hours
            httponly=True,
            samesite="lax"
        )
        return response
        
    except (InvalidCredentialsError, RateLimitError) as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/logout")
async def logout(request: Request):
    session_token = request.cookies.get('session')
    if session_token:
        clear_session(session_token)
    
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="session")
    return response

@app.get("/status")
async def status():
    return {"status": "ok", "version": "1.0"}

@app.get("/{username}", response_class=HTMLResponse)
async def user_profile(username: str, request: Request, db = Depends(get_db)):
    username = username.lower()
    
    if not is_valid_username(username):
        raise HTTPException(status_code=404, detail="User not found")
    
    user_info = get_user_info(username, db)
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    
    public_lists = get_user_lists(username, include_private=False, db=db)
    
    context = {
        "request": request,
        "user_info": user_info,
        "username": username,
        "lists": public_lists,
        "current_user": get_session_user(request)
    }
    
    # For now, return a simple response (we'd create a user_profile.html template)
    return f"""
    <html>
        <head><title>{username} - listky.top</title></head>
        <body>
            <h1>{username}'s Lists</h1>
            <ul>
                {''.join([f'<li><a href="/{username}/{list_item["slug"]}">{list_item["title"]}</a></li>' for list_item in public_lists])}
            </ul>
        </body>
    </html>
    """

@app.get("/{username}/{slug}", response_class=HTMLResponse)
async def view_list(username: str, slug: str, request: Request, db = Depends(get_db)):
    username = username.lower()
    
    if not is_valid_username(username) or not is_valid_slug(slug):
        raise HTTPException(status_code=404, detail="List not found")
    
    list_data = get_list(username, slug, db)
    if not list_data:
        raise HTTPException(status_code=404, detail="List not found")
    
    # Check if list is public
    if not list_data["is_public"]:
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>Private List</h1>
                <p>This list is private and not publicly accessible.</p>
            </body>
        </html>
        """)
    
    # Record view
    record_list_view(username, slug, request, db)
    
    # Format content with clickable links
    formatted_content = make_links(list_data["content"].replace('\n', '<br>'))
    
    return f"""
    <html>
        <head>
            <title>{list_data["title"]} by {username} - listky.top</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: system-ui, -apple-system, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; line-height: 1.6; }}
                .content {{ background: #f8f9fa; padding: 1.5rem; border-radius: 4px; margin: 2rem 0; border-left: 4px solid #007acc; }}
            </style>
        </head>
        <body>
            <h1>{list_data["title"]}</h1>
            <p>By <a href="/{username}">{username}</a> • Created {list_data["created_at"][:10]}</p>
            <div class="content">{formatted_content}</div>
            <p><a href="/{username}">← More lists by {username}</a> | <a href="/">← Home</a></p>
        </body>
    </html>
    """

# Additional endpoints would be implemented similarly...
# For now, this shows the pattern of using the core modules