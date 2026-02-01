from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

app = FastAPI(
    title="listky.top",
    description="One-word usernames. Simple lists. Maximum privacy.",
    version="0.1.0"
)

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head><title>listky.top</title></head>
        <body style="font-family: system-ui; padding: 40px; max-width: 700px;">
            <h1>listky.top</h1>
            <p>Welcome to the minimalist list platform.</p>
            <p>One-word username signup + 6-digit PIN + zero personal data.</p>
            <p>Currently in early development.</p>
            <p><a href="/hello/test">Try hello endpoint</a></p>
        </body>
    </html>
    """

@app.get("/hello/{name}")
async def hello(name: str):
    return {"message": f"Hello {name}! Your username would live at listky.top/{name}"}

# Placeholder for future signup
@app.get("/status")
async def status():
    return {"status": "running", "version": "0.1.0", "features": "hello world only"}