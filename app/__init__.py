# LifeConnect API - Main entry point
"""
Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    
Or for production:
    gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
"""

from app.main import app

__all__ = ["app"]
