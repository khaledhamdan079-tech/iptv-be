"""
Episodes routes
"""
from fastapi import APIRouter, HTTPException, Query
from app.services.scraper import scraper

router = APIRouter()


@router.get("/by-url")
async def get_episode_video_links_by_url(
    url: str = Query(..., description="Full episode URL")
):
    """Get video links for a specific episode using full URL (recommended)"""
    try:
        video_links = scraper.get_episode_video_links(url)
        
        if not video_links:
            raise HTTPException(status_code=404, detail="No video links found for this episode")
        
        return {
            "success": True,
            "count": len(video_links),
            "data": video_links
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        # Check if it's a 404 from the site
        if "404" in error_msg or "Not Found" in error_msg:
            raise HTTPException(
                status_code=404,
                detail="Episode not found. The URL may be incorrect or the episode may have been removed."
            )
        # Handle encoding issues in error messages
        try:
            error_msg.encode('utf-8')
        except:
            error_msg = "Error processing episode URL. Please check the URL and try again."
        raise HTTPException(status_code=500, detail=error_msg)



