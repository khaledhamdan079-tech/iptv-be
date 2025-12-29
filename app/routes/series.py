"""
Series routes
"""
from fastapi import APIRouter, HTTPException, Query
from app.services.scraper import scraper

router = APIRouter()


@router.get("/popular")
async def get_popular_series():
    """Get popular/top series"""
    try:
        series = scraper.get_popular_series()
        return {
            "success": True,
            "count": len(series),
            "data": series
        }
    except Exception as e:
        error_msg = str(e)
        # Provide more helpful error messages
        if "DNS resolution failed" in error_msg or "getaddrinfo failed" in error_msg:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Site is not accessible",
                    "message": error_msg,
                    "suggestion": "The website may be down, blocked, or the URL has changed. Please check the site availability or update the base URL in the scraper configuration."
                }
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-site")
async def check_site_availability():
    """Check if the default site is accessible"""
    try:
        result = scraper.check_site_availability('topcinema')
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-url")
async def get_series_details_by_url(
    url: str = Query(..., description="Full series URL")
):
    """Get series details using full URL (recommended)"""
    try:
        series_details = scraper.get_series_details(url)
        
        return {
            "success": True,
            "data": series_details
        }
    except HTTPException:
        raise
    except Exception as e:
        # Handle encoding errors in error messages
        error_msg = str(e)
        try:
            error_msg.encode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            error_msg = "Error processing series request. Please check the series URL."
        except Exception:
            error_msg = "Error processing series request. Please check the series URL."
        
        try:
            safe_msg = error_msg.encode('utf-8', errors='replace').decode('utf-8')
        except:
            safe_msg = "Error processing series request. Please check the series URL."
        
        raise HTTPException(status_code=500, detail=safe_msg)

