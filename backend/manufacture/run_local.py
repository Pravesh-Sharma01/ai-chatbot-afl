#!/usr/bin/env python3
"""
Simple script to run the claim backend locally
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8004"))
    print(f"🚀 Starting Claims Planner on http://localhost:{port}")
    print(f"📚 API docs available at http://localhost:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

