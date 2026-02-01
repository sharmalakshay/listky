from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from database import init_db, get_db
import sqlite3

app = FastAPI(title="listky.top", description="One-word lists. Privacy first.")

# Initialize DB on startup
init_db()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head><title>listky.top</title></head>
        <body style="font-family: system-ui; padding: 40px; max-width: 700px;">
            <h1>listky.top</h1>
            <p>Minimalist lists platform – one word username + 6-digit PIN</p>
            <p>Sign up works! Try creating your account at /signup</p>
            <p>Currently running v1 prototype</p>
        </body>
    </html>
    """

@app.get("/status")
async def status(db = Depends(get_db)):
    return {"status": "running", "database": "sqlite ready"}