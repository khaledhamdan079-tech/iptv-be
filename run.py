"""
Simple script to run the FastAPI server
"""
import os
import uvicorn

if __name__ == "__main__":
    # Railway uses PORT environment variable, default to 3000 for local development
    port = int(os.environ.get("PORT", 3000))
    # Disable reload to ensure clean startup
    # If you need auto-reload, use: uvicorn app.main:app --reload
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Disabled for clean restart
    )

