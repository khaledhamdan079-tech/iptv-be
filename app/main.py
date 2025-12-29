"""
Main FastAPI application for IPTV Arabic Backend
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import series, episodes, search, maso, xtream, maso
import sys

app = FastAPI(
    title="IPTV Arabic Backend",
    description="Backend API for Arabic translated series streaming",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler for encoding errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions, especially Unicode encoding errors"""
    error_msg = str(exc)
    
    # Handle encoding errors
    try:
        error_msg.encode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        error_msg = "An error occurred processing your request. Please try again."
    except Exception:
        error_msg = "An error occurred processing your request. Please try again."
    
    # Ensure safe encoding for response
    try:
        safe_msg = error_msg.encode('utf-8', errors='replace').decode('utf-8')
    except:
        safe_msg = "An error occurred processing your request. Please try again."
    
    return JSONResponse(
        status_code=500,
        content={"detail": safe_msg}
    )

# Include routers
app.include_router(series.router, prefix="/api/series", tags=["series"])
app.include_router(episodes.router, prefix="/api/episodes", tags=["episodes"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(maso.router)
app.include_router(xtream.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IPTV Arabic Backend API",
        "endpoints": {
            "health": "/health",
            "site_status": "/api/site-status",
            "series": "/api/series",
            "episodes": "/api/episodes",
            "search": "/api/search",
            "maso": "/api/maso",
            "xtream": "/api/xtream"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "message": "IPTV Arabic Backend is running"}


@app.get("/api/debug/html")
async def debug_html():
    """Debug endpoint to see raw HTML structure"""
    from app.services.scraper import scraper
    try:
        base_url = scraper.get_base_url()
        html = scraper.fetch_page(base_url)
        
        # Return first 5000 characters and some stats
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        # Try to find common elements
        all_links = soup.find_all('a', href=True)
        all_images = soup.find_all('img')
        all_articles = soup.find_all('article')
        all_divs_with_class = soup.find_all('div', class_=True)
        
        # Get sample of classes used
        classes_found = set()
        for div in all_divs_with_class[:50]:
            if div.get('class'):
                classes_found.update(div.get('class'))
        
        return {
            "success": True,
            "url": base_url,
            "html_length": len(html),
            "preview": html[:2000],  # First 2000 chars
            "stats": {
                "total_links": len(all_links),
                "total_images": len(all_images),
                "total_articles": len(all_articles),
                "sample_classes": list(classes_found)[:20],
                "sample_links": [a.get('href') for a in all_links[:10] if a.get('href')],
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/site-status")
async def site_status():
    """Check status of all configured sites (may take time)"""
    from app.services.scraper import scraper
    import asyncio
    
    # Run checks in background to avoid blocking
    status = {}
    for site_key in scraper.base_urls.keys():
        try:
            # Use shorter timeout for status check
            result = scraper.check_site_availability(site_key)
            status[site_key] = result
        except Exception as e:
            status[site_key] = {
                'available': False,
                'error': str(e),
                'url': scraper.base_urls.get(site_key, 'unknown')
            }
    
    # Find working domain (with timeout)
    working_url = None
    try:
        working_url = scraper.find_working_domain()
    except:
        pass
    
    return {
        "success": True,
        "data": status,
        "working_domain": working_url,
        "current_base_url": scraper.base_urls.get(scraper.primary_domain, 'unknown')
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)

