"""SLIS Backend Server (Optional)

The main application runs entirely in the browser.
This server only serves static files.

Usage:
    python -m src.main
    
Or use any static server:
    python -m http.server 8080
"""

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="SLIS", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).parent.parent

if (ROOT / "static").exists():
    app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

(ROOT / "models").mkdir(exist_ok=True)
app.mount("/models", StaticFiles(directory=str(ROOT / "models")), name="models")

@app.get("/")
async def index():
    return FileResponse(str(ROOT / "index.html"))

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

def main():
    logger.info("SLIS Server starting on http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()