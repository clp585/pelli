#!/usr/bin/env python
"""
Simple script to run the FastAPI backend server
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)

