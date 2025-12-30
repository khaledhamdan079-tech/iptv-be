"""
Simple script to run the FastAPI server
"""
import os
import uvicorn

if __name__ == "__main__":
    # Railway uses PORT environment variable, default to 3000 for local development
    port = int(os.environ.get("PORT", 3000))
    # Disable reload to ensure clean startup
    # Use workers=1 for Railway (single worker is fine for most cases)
    # Increase timeout for slow startup
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disabled for production
        workers=1,  # Single worker for Railway
        timeout_keep_alive=30,  # Keep connections alive longer
        log_level="info"  # Set log level
    )

