# LifeConnect API - Main entry point
"""
Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    
Or for production:
    gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
"""

# Note: The FastAPI `app` instance is defined in app.main, not imported here.
# Access it via `app.main.app` or use `uvicorn app.main:app` directly.
# Importing it here would trigger the full startup chain on any submodule import.
