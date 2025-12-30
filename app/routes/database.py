"""
API routes for querying local database
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import (
    Playlist, Category, Movie, Series, Episode, LiveChannel
)
from app.services.db_sync import DatabaseSyncService
from app.services.xtream_codes import XtreamCodesService
from app.routes.xtream import get_playlist_service
from app.services.maso_api import MasoAPIService

router = APIRouter(prefix="/api/db", tags=["database"])


# ==================== SYNC ENDPOINTS ====================

@router.post("/sync")
async def sync_all_content(
    playlist_id: int = Query(0, description="Playlist ID (default: 0)"),
    include_episodes: bool = Query(True, description="Include episodes sync"),
    include_movie_info: bool = Query(False, description="Include detailed movie info (slow)"),
    db: Session = Depends(get_db)
):
    """Sync all content from Xtream Codes API to local database"""
    try:
        # Get playlist service to get credentials
        service = get_playlist_service(playlist_id)
        if not service:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # Get or create playlist in database
        sync_service = DatabaseSyncService(db)
        playlist = sync_service.get_or_create_playlist(
            base_url=service.base_url,
            username=service.username,
            password=service.password,
            name=f"Playlist {playlist_id}"
        )
        
        # Sync all content
        results = sync_service.sync_all(
            playlist=playlist,
            service=service,
            include_episodes=include_episodes,
            include_movie_info=include_movie_info
        )
        
        return {
            "success": True,
            "playlist_id": playlist.id,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/sync/movies")
async def sync_movies(
    playlist_id: int = Query(0, description="Playlist ID (default: 0)"),
    category_id: Optional[str] = Query(None, description="Category ID to filter"),
    db: Session = Depends(get_db)
):
    """Sync movies from Xtream Codes API"""
    try:
        service = get_playlist_service(playlist_id)
        if not service:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        sync_service = DatabaseSyncService(db)
        playlist = sync_service.get_or_create_playlist(
            base_url=service.base_url,
            username=service.username,
            password=service.password
        )
        
        count = sync_service.sync_movies(playlist, service, category_id)
        
        return {
            "success": True,
            "synced": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/sync/series")
async def sync_series(
    playlist_id: int = Query(0, description="Playlist ID (default: 0)"),
    category_id: Optional[str] = Query(None, description="Category ID to filter"),
    db: Session = Depends(get_db)
):
    """Sync series from Xtream Codes API"""
    try:
        service = get_playlist_service(playlist_id)
        if not service:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        sync_service = DatabaseSyncService(db)
        playlist = sync_service.get_or_create_playlist(
            base_url=service.base_url,
            username=service.username,
            password=service.password
        )
        
        count = sync_service.sync_series(playlist, service, category_id)
        
        return {
            "success": True,
            "synced": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/sync/live")
async def sync_live_channels(
    playlist_id: int = Query(0, description="Playlist ID (default: 0)"),
    category_id: Optional[str] = Query(None, description="Category ID to filter"),
    db: Session = Depends(get_db)
):
    """Sync live TV channels from Xtream Codes API"""
    try:
        service = get_playlist_service(playlist_id)
        if not service:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        sync_service = DatabaseSyncService(db)
        playlist = sync_service.get_or_create_playlist(
            base_url=service.base_url,
            username=service.username,
            password=service.password
        )
        
        count = sync_service.sync_live_channels(playlist, service, category_id)
        
        return {
            "success": True,
            "synced": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ==================== QUERY ENDPOINTS ====================

@router.get("/movies")
async def get_movies(
    playlist_id: Optional[int] = Query(None, description="Filter by playlist ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get movies from local database"""
    query = db.query(Movie)
    
    if playlist_id:
        query = query.filter(Movie.playlist_id == playlist_id)
    
    if category_id:
        query = query.filter(Movie.category_id == category_id)
    
    if search:
        query = query.filter(Movie.name.ilike(f"%{search}%"))
    
    total = query.count()
    offset = (page - 1) * limit
    movies = query.offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": m.id,
                "stream_id": m.stream_id,
                "name": m.name,
                "stream_icon": m.stream_icon,
                "rating": m.rating,
                "category_id": m.category_id,
                "container_extension": m.container_extension,
                "plot": m.plot,
                "year": m.year,
                "duration": m.duration,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "last_synced": m.last_synced.isoformat() if m.last_synced else None
            }
            for m in movies
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0
        }
    }


@router.get("/movies/{movie_id}")
async def get_movie(
    movie_id: int,
    db: Session = Depends(get_db)
):
    """Get movie details from local database"""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    return {
        "success": True,
        "data": {
            "id": movie.id,
            "stream_id": movie.stream_id,
            "name": movie.name,
            "stream_icon": movie.stream_icon,
            "rating": movie.rating,
            "rating_5based": movie.rating_5based,
            "category_id": movie.category_id,
            "container_extension": movie.container_extension,
            "plot": movie.plot,
            "cast": movie.cast,
            "director": movie.director,
            "genre": movie.genre,
            "year": movie.year,
            "releasedate": movie.releasedate,
            "duration": movie.duration,
            "duration_secs": movie.duration_secs,
            "video_info": movie.video_info,
            "audio_info": movie.audio_info,
            "bitrate": movie.bitrate,
            "tmdb_id": movie.tmdb_id,
            "youtube_trailer": movie.youtube_trailer,
            "backdrop_path": movie.backdrop_path,
            "created_at": movie.created_at.isoformat() if movie.created_at else None,
            "last_synced": movie.last_synced.isoformat() if movie.last_synced else None
        }
    }


@router.get("/series")
async def get_series(
    playlist_id: Optional[int] = Query(None, description="Filter by playlist ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get series from local database"""
    query = db.query(Series)
    
    if playlist_id:
        query = query.filter(Series.playlist_id == playlist_id)
    
    if category_id:
        query = query.filter(Series.category_id == category_id)
    
    if search:
        query = query.filter(Series.name.ilike(f"%{search}%"))
    
    total = query.count()
    offset = (page - 1) * limit
    series_list = query.offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "series_id": s.series_id,
                "name": s.name,
                "cover": s.cover,
                "plot": s.plot,
                "genre": s.genre,
                "rating": s.rating,
                "category_id": s.category_id,
                "episode_count": len(s.episodes),
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "last_synced": s.last_synced.isoformat() if s.last_synced else None
            }
            for s in series_list
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0
        }
    }


@router.get("/series/{series_id}")
async def get_series_details(
    series_id: int,
    include_episodes: bool = Query(True, description="Include episodes"),
    db: Session = Depends(get_db)
):
    """Get series details with episodes from local database"""
    series = db.query(Series).filter(Series.id == series_id).first()
    
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    episodes_data = None
    if include_episodes:
        episodes = db.query(Episode).filter(Episode.series_id == series.id).order_by(
            Episode.season, Episode.episode_num
        ).all()
        
        # Group by season
        episodes_by_season = {}
        for ep in episodes:
            season = ep.season
            if season not in episodes_by_season:
                episodes_by_season[season] = []
            episodes_by_season[season].append({
                "id": ep.id,
                "episode_id": ep.episode_id,
                "episode_num": ep.episode_num,
                "title": ep.title,
                "season": ep.season,
                "container_extension": ep.container_extension,
                "duration": ep.duration,
                "duration_secs": ep.duration_secs
            })
        
        episodes_data = episodes_by_season
    
    return {
        "success": True,
        "data": {
            "id": series.id,
            "series_id": series.series_id,
            "name": series.name,
            "cover": series.cover,
            "plot": series.plot,
            "cast": series.cast,
            "director": series.director,
            "genre": series.genre,
            "releaseDate": series.releaseDate,
            "rating": series.rating,
            "rating_5based": series.rating_5based,
            "youtube_trailer": series.youtube_trailer,
            "backdrop_path": series.backdrop_path,
            "category_id": series.category_id,
            "episodes": episodes_data,
            "created_at": series.created_at.isoformat() if series.created_at else None,
            "last_synced": series.last_synced.isoformat() if series.last_synced else None
        }
    }


@router.get("/live")
async def get_live_channels(
    playlist_id: Optional[int] = Query(None, description="Filter by playlist ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get live TV channels from local database"""
    query = db.query(LiveChannel)
    
    if playlist_id:
        query = query.filter(LiveChannel.playlist_id == playlist_id)
    
    if category_id:
        query = query.filter(LiveChannel.category_id == category_id)
    
    if search:
        query = query.filter(LiveChannel.name.ilike(f"%{search}%"))
    
    total = query.count()
    offset = (page - 1) * limit
    channels = query.offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": c.id,
                "stream_id": c.stream_id,
                "name": c.name,
                "stream_icon": c.stream_icon,
                "epg_channel_id": c.epg_channel_id,
                "category_id": c.category_id,
                "category_name": c.category_name,
                "tv_archive": c.tv_archive,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "last_synced": c.last_synced.isoformat() if c.last_synced else None
            }
            for c in channels
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0
        }
    }


@router.get("/categories")
async def get_categories(
    playlist_id: Optional[int] = Query(None, description="Filter by playlist ID"),
    category_type: Optional[str] = Query(None, description="Filter by type: movie, series, live"),
    db: Session = Depends(get_db)
):
    """Get categories from local database"""
    query = db.query(Category)
    
    if playlist_id:
        query = query.filter(Category.playlist_id == playlist_id)
    
    if category_type:
        query = query.filter(Category.category_type == category_type)
    
    categories = query.all()
    
    return {
        "success": True,
        "data": [
            {
                "id": c.id,
                "category_id": c.category_id,
                "category_name": c.category_name,
                "category_type": c.category_type,
                "playlist_id": c.playlist_id
            }
            for c in categories
        ],
        "count": len(categories)
    }


@router.get("/stats")
async def get_database_stats(
    playlist_id: Optional[int] = Query(None, description="Filter by playlist ID"),
    db: Session = Depends(get_db)
):
    """Get database statistics"""
    query_filter = {}
    if playlist_id:
        query_filter = {"playlist_id": playlist_id}
    
    movies_count = db.query(Movie).filter_by(**query_filter).count()
    series_count = db.query(Series).filter_by(**query_filter).count()
    episodes_count = db.query(Episode).join(Series).filter_by(**query_filter).count() if query_filter else db.query(Episode).count()
    live_channels_count = db.query(LiveChannel).filter_by(**query_filter).count()
    categories_count = db.query(Category).filter_by(**query_filter).count()
    
    return {
        "success": True,
        "stats": {
            "movies": movies_count,
            "series": series_count,
            "episodes": episodes_count,
            "live_channels": live_channels_count,
            "categories": categories_count,
            "playlist_id": playlist_id
        }
    }

