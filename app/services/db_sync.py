"""
Service to sync data from Xtream Codes API to local database
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

from app.models import (
    Playlist, Category, Movie, Series, Episode, LiveChannel
)
from app.services.xtream_codes import XtreamCodesService


class DatabaseSyncService:
    """Service to sync Xtream Codes data to local database"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_playlist(
        self, 
        base_url: str, 
        username: str, 
        password: str,
        name: Optional[str] = None
    ) -> Playlist:
        """Get or create a playlist record"""
        playlist = self.db.query(Playlist).filter(
            Playlist.base_url == base_url,
            Playlist.username == username
        ).first()
        
        if not playlist:
            playlist = Playlist(
                name=name or f"{base_url}",
                base_url=base_url,
                username=username,
                password=password
            )
            self.db.add(playlist)
            self.db.commit()
            self.db.refresh(playlist)
        
        return playlist
    
    def sync_categories(
        self, 
        playlist: Playlist, 
        service: XtreamCodesService,
        category_type: str = "movie"
    ) -> int:
        """Sync categories from Xtream Codes API"""
        count = 0
        
        try:
            if category_type == "movie":
                categories = service.get_vod_categories()
            elif category_type == "series":
                categories = service.get_series_categories()
            elif category_type == "live":
                categories = service.get_live_categories()
            else:
                return 0
            
            for cat_data in categories:
                category_id = str(cat_data.get('category_id', ''))
                category_name = cat_data.get('category_name', 'Unknown')
                
                # Check if category exists
                existing = self.db.query(Category).filter(
                    Category.playlist_id == playlist.id,
                    Category.category_id == category_id,
                    Category.category_type == category_type
                ).first()
                
                if not existing:
                    category = Category(
                        playlist_id=playlist.id,
                        category_id=category_id,
                        category_name=category_name,
                        category_type=category_type
                    )
                    self.db.add(category)
                    count += 1
                else:
                    # Update name if changed
                    if existing.category_name != category_name:
                        existing.category_name = category_name
                        existing.updated_at = datetime.utcnow()
                        count += 1
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error syncing {category_type} categories: {e}")
        
        return count
    
    def sync_movies(
        self, 
        playlist: Playlist, 
        service: XtreamCodesService,
        category_id: Optional[str] = None
    ) -> int:
        """Sync movies from Xtream Codes API"""
        count = 0
        updated = 0
        
        try:
            movies = service.get_vod_streams(category_id)
            
            for movie_data in movies:
                stream_id = str(movie_data.get('stream_id', ''))
                if not stream_id:
                    continue
                
                # Get category
                cat_id_api = str(movie_data.get('category_id', ''))
                category = None
                if cat_id_api:
                    category = self.db.query(Category).filter(
                        Category.playlist_id == playlist.id,
                        Category.category_id == cat_id_api,
                        Category.category_type == 'movie'
                    ).first()
                
                # Check if movie exists
                existing = self.db.query(Movie).filter(
                    Movie.playlist_id == playlist.id,
                    Movie.stream_id == stream_id
                ).first()
                
                if existing:
                    # Update existing
                    existing.name = movie_data.get('name', existing.name)
                    existing.stream_icon = movie_data.get('stream_icon', existing.stream_icon)
                    existing.rating = movie_data.get('rating', existing.rating)
                    existing.rating_5based = movie_data.get('rating_5based', existing.rating_5based)
                    existing.added = movie_data.get('added', existing.added)
                    existing.container_extension = movie_data.get('container_extension', existing.container_extension)
                    existing.direct_source = movie_data.get('direct_source', existing.direct_source)
                    existing.category_id = category.id if category else existing.category_id
                    existing.updated_at = datetime.utcnow()
                    existing.last_synced = datetime.utcnow()
                    updated += 1
                else:
                    # Create new
                    movie = Movie(
                        playlist_id=playlist.id,
                        category_id=category.id if category else None,
                        stream_id=stream_id,
                        name=movie_data.get('name', ''),
                        stream_type=movie_data.get('stream_type', 'movie'),
                        stream_icon=movie_data.get('stream_icon'),
                        rating=movie_data.get('rating'),
                        rating_5based=movie_data.get('rating_5based', 0),
                        added=movie_data.get('added'),
                        container_extension=movie_data.get('container_extension'),
                        custom_sid=movie_data.get('custom_sid'),
                        direct_source=movie_data.get('direct_source', ''),
                        last_synced=datetime.utcnow()
                    )
                    self.db.add(movie)
                    count += 1
                
                # Commit in batches to avoid memory issues
                if (count + updated) % 100 == 0:
                    self.db.commit()
            
            self.db.commit()
            print(f"Synced {count} new movies, updated {updated} existing movies")
        except Exception as e:
            self.db.rollback()
            print(f"Error syncing movies: {e}")
            raise
        
        return count + updated
    
    def sync_movie_info(self, movie: Movie, service: XtreamCodesService) -> bool:
        """Sync detailed movie info from get_vod_info"""
        try:
            vod_info = service.get_vod_info(movie.stream_id)
            if not vod_info or 'info' not in vod_info:
                return False
            
            info = vod_info.get('info', {})
            movie_data = vod_info.get('movie_data', {})
            
            # Update movie with detailed info
            movie.movie_image = info.get('movie_image')
            movie.backdrop_path = json.dumps(info.get('backdrop_path', [])) if info.get('backdrop_path') else None
            movie.tmdb_id = info.get('tmdb_id')
            movie.youtube_trailer = info.get('youtube_trailer')
            movie.genre = info.get('genre')
            movie.plot = info.get('plot')
            movie.cast = info.get('cast')
            movie.director = info.get('director')
            movie.releasedate = info.get('releasedate')
            movie.duration_secs = info.get('duration_secs')
            movie.duration = info.get('duration')
            movie.video_info = info.get('video')
            movie.audio_info = info.get('audio')
            movie.bitrate = info.get('bitrate')
            movie.year = info.get('year')
            movie.mpaa = info.get('mpaa')
            
            # Update from movie_data if available
            if movie_data:
                if movie_data.get('container_extension'):
                    movie.container_extension = movie_data.get('container_extension')
                if movie_data.get('direct_source'):
                    movie.direct_source = movie_data.get('direct_source')
            
            movie.last_synced = datetime.utcnow()
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error syncing movie info for {movie.stream_id}: {e}")
            return False
    
    def sync_series(
        self, 
        playlist: Playlist, 
        service: XtreamCodesService,
        category_id: Optional[str] = None
    ) -> int:
        """Sync series from Xtream Codes API"""
        count = 0
        updated = 0
        
        try:
            series_list = service.get_series(category_id)
            
            for series_data in series_list:
                series_id_api = str(series_data.get('series_id', series_data.get('id', '')))
                if not series_id_api:
                    continue
                
                # Get category
                cat_id_api = str(series_data.get('category_id', ''))
                category = None
                if cat_id_api:
                    category = self.db.query(Category).filter(
                        Category.playlist_id == playlist.id,
                        Category.category_id == cat_id_api,
                        Category.category_type == 'series'
                    ).first()
                
                # Check if series exists
                existing = self.db.query(Series).filter(
                    Series.playlist_id == playlist.id,
                    Series.series_id == series_id_api
                ).first()
                
                if existing:
                    # Update existing
                    existing.name = series_data.get('name', existing.name)
                    existing.cover = series_data.get('cover', existing.cover)
                    existing.plot = series_data.get('plot', existing.plot)
                    existing.cast = series_data.get('cast', existing.cast)
                    existing.director = series_data.get('director', existing.director)
                    existing.genre = series_data.get('genre', existing.genre)
                    existing.releaseDate = series_data.get('releaseDate', existing.releaseDate)
                    existing.last_modified = series_data.get('last_modified', existing.last_modified)
                    existing.rating = series_data.get('rating', existing.rating)
                    existing.rating_5based = series_data.get('rating_5based', existing.rating_5based)
                    existing.backdrop_path = json.dumps(series_data.get('backdrop_path', [])) if series_data.get('backdrop_path') else existing.backdrop_path
                    existing.youtube_trailer = series_data.get('youtube_trailer', existing.youtube_trailer)
                    existing.episode_run_time = series_data.get('episode_run_time', existing.episode_run_time)
                    existing.category_id = category.id if category else existing.category_id
                    existing.updated_at = datetime.utcnow()
                    existing.last_synced = datetime.utcnow()
                    updated += 1
                else:
                    # Create new
                    series = Series(
                        playlist_id=playlist.id,
                        category_id=category.id if category else None,
                        series_id=series_id_api,
                        name=series_data.get('name', ''),
                        cover=series_data.get('cover'),
                        plot=series_data.get('plot'),
                        cast=series_data.get('cast'),
                        director=series_data.get('director'),
                        genre=series_data.get('genre'),
                        releaseDate=series_data.get('releaseDate'),
                        last_modified=series_data.get('last_modified'),
                        rating=series_data.get('rating'),
                        rating_5based=series_data.get('rating_5based'),
                        backdrop_path=json.dumps(series_data.get('backdrop_path', [])) if series_data.get('backdrop_path') else None,
                        youtube_trailer=series_data.get('youtube_trailer'),
                        episode_run_time=series_data.get('episode_run_time'),
                        last_synced=datetime.utcnow()
                    )
                    self.db.add(series)
                    count += 1
                
                # Commit in batches
                if (count + updated) % 100 == 0:
                    self.db.commit()
            
            self.db.commit()
            print(f"Synced {count} new series, updated {updated} existing series")
        except Exception as e:
            self.db.rollback()
            print(f"Error syncing series: {e}")
            raise
        
        return count + updated
    
    def sync_series_episodes(
        self, 
        series: Series, 
        service: XtreamCodesService
    ) -> int:
        """Sync episodes for a series"""
        count = 0
        updated = 0
        
        try:
            series_info = service.get_series_info(series.series_id)
            if not series_info or 'episodes' not in series_info:
                return 0
            
            episodes_data = series_info.get('episodes', {})
            
            for season_num, episodes_list in episodes_data.items():
                for episode_data in episodes_list:
                    episode_id_api = str(episode_data.get('id', ''))
                    if not episode_id_api:
                        continue
                    
                    # Check if episode exists
                    existing = self.db.query(Episode).filter(
                        Episode.series_id == series.id,
                        Episode.episode_id == episode_id_api
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.episode_num = episode_data.get('episode_num', existing.episode_num)
                        existing.title = episode_data.get('title', existing.title)
                        existing.season = str(season_num)
                        existing.container_extension = episode_data.get('container_extension', existing.container_extension)
                        existing.custom_sid = episode_data.get('custom_sid', existing.custom_sid)
                        existing.added = episode_data.get('added', existing.added)
                        existing.direct_source = episode_data.get('direct_source', existing.direct_source)
                        existing.duration_secs = episode_data.get('info', {}).get('duration_secs', existing.duration_secs)
                        existing.duration = episode_data.get('info', {}).get('duration', existing.duration)
                        existing.video_info = episode_data.get('info', {}).get('video')
                        existing.audio_info = episode_data.get('info', {}).get('audio')
                        existing.bitrate = episode_data.get('info', {}).get('bitrate', existing.bitrate)
                        existing.info = episode_data.get('info')
                        existing.updated_at = datetime.utcnow()
                        existing.last_synced = datetime.utcnow()
                        updated += 1
                    else:
                        # Create new
                        episode = Episode(
                            series_id=series.id,
                            episode_id=episode_id_api,
                            episode_num=episode_data.get('episode_num', 0),
                            title=episode_data.get('title'),
                            season=str(season_num),
                            container_extension=episode_data.get('container_extension'),
                            custom_sid=episode_data.get('custom_sid'),
                            added=episode_data.get('added'),
                            direct_source=episode_data.get('direct_source', ''),
                            duration_secs=episode_data.get('info', {}).get('duration_secs'),
                            duration=episode_data.get('info', {}).get('duration'),
                            video_info=episode_data.get('info', {}).get('video'),
                            audio_info=episode_data.get('info', {}).get('audio'),
                            bitrate=episode_data.get('info', {}).get('bitrate'),
                            info=episode_data.get('info'),
                            last_synced=datetime.utcnow()
                        )
                        self.db.add(episode)
                        count += 1
            
            self.db.commit()
            print(f"Synced {count} new episodes, updated {updated} existing episodes for series {series.series_id}")
        except Exception as e:
            self.db.rollback()
            print(f"Error syncing episodes for series {series.series_id}: {e}")
            raise
        
        return count + updated
    
    def sync_live_channels(
        self, 
        playlist: Playlist, 
        service: XtreamCodesService,
        category_id: Optional[str] = None
    ) -> int:
        """Sync live TV channels from Xtream Codes API"""
        count = 0
        updated = 0
        
        try:
            channels = service.get_live_streams(category_id)
            
            for channel_data in channels:
                stream_id = str(channel_data.get('stream_id', ''))
                if not stream_id:
                    continue
                
                # Get category
                cat_id_api = str(channel_data.get('category_id', ''))
                category = None
                if cat_id_api:
                    category = self.db.query(Category).filter(
                        Category.playlist_id == playlist.id,
                        Category.category_id == cat_id_api,
                        Category.category_type == 'live'
                    ).first()
                
                # Check if channel exists
                existing = self.db.query(LiveChannel).filter(
                    LiveChannel.playlist_id == playlist.id,
                    LiveChannel.stream_id == stream_id
                ).first()
                
                if existing:
                    # Update existing
                    existing.num = channel_data.get('num', existing.num)
                    existing.name = channel_data.get('name', existing.name)
                    existing.stream_icon = channel_data.get('stream_icon', existing.stream_icon)
                    existing.epg_channel_id = channel_data.get('epg_channel_id', existing.epg_channel_id)
                    existing.added = channel_data.get('added', existing.added)
                    existing.category_name = channel_data.get('category_name', existing.category_name)
                    existing.category_id_api = cat_id_api
                    existing.custom_sid = channel_data.get('custom_sid', existing.custom_sid)
                    existing.tv_archive = channel_data.get('tv_archive', existing.tv_archive)
                    existing.direct_source = channel_data.get('direct_source', existing.direct_source)
                    existing.tv_archive_duration = channel_data.get('tv_archive_duration', existing.tv_archive_duration)
                    existing.category_id = category.id if category else existing.category_id
                    existing.updated_at = datetime.utcnow()
                    existing.last_synced = datetime.utcnow()
                    updated += 1
                else:
                    # Create new
                    channel = LiveChannel(
                        playlist_id=playlist.id,
                        category_id=category.id if category else None,
                        stream_id=stream_id,
                        num=channel_data.get('num'),
                        name=channel_data.get('name', ''),
                        stream_type=channel_data.get('stream_type', 'live'),
                        stream_icon=channel_data.get('stream_icon'),
                        epg_channel_id=channel_data.get('epg_channel_id'),
                        added=channel_data.get('added'),
                        category_name=channel_data.get('category_name'),
                        category_id_api=cat_id_api,
                        custom_sid=channel_data.get('custom_sid'),
                        tv_archive=channel_data.get('tv_archive', 0),
                        direct_source=channel_data.get('direct_source', ''),
                        tv_archive_duration=channel_data.get('tv_archive_duration'),
                        last_synced=datetime.utcnow()
                    )
                    self.db.add(channel)
                    count += 1
                
                # Commit in batches
                if (count + updated) % 100 == 0:
                    self.db.commit()
            
            self.db.commit()
            print(f"Synced {count} new channels, updated {updated} existing channels")
        except Exception as e:
            self.db.rollback()
            print(f"Error syncing live channels: {e}")
            raise
        
        return count + updated
    
    def sync_all(
        self,
        playlist: Playlist,
        service: XtreamCodesService,
        include_episodes: bool = True,
        include_movie_info: bool = False
    ) -> Dict[str, int]:
        """Sync all content from Xtream Codes API"""
        results = {
            'categories_movie': 0,
            'categories_series': 0,
            'categories_live': 0,
            'movies': 0,
            'series': 0,
            'episodes': 0,
            'live_channels': 0
        }
        
        print(f"Starting sync for playlist: {playlist.name}")
        
        # Sync categories
        print("Syncing movie categories...")
        results['categories_movie'] = self.sync_categories(playlist, service, 'movie')
        
        print("Syncing series categories...")
        results['categories_series'] = self.sync_categories(playlist, service, 'series')
        
        print("Syncing live TV categories...")
        results['categories_live'] = self.sync_categories(playlist, service, 'live')
        
        # Sync movies
        print("Syncing movies...")
        results['movies'] = self.sync_movies(playlist, service)
        
        # Sync series
        print("Syncing series...")
        results['series'] = self.sync_series(playlist, service)
        
        # Sync episodes (if requested)
        if include_episodes:
            print("Syncing episodes...")
            series_list = self.db.query(Series).filter(
                Series.playlist_id == playlist.id
            ).all()
            
            for series in series_list:
                try:
                    episode_count = self.sync_series_episodes(series, service)
                    results['episodes'] += episode_count
                except Exception as e:
                    print(f"Error syncing episodes for series {series.series_id}: {e}")
                    continue
        
        # Sync live channels
        print("Syncing live TV channels...")
        results['live_channels'] = self.sync_live_channels(playlist, service)
        
        # Sync detailed movie info (if requested - slow!)
        if include_movie_info:
            print("Syncing detailed movie info (this may take a while)...")
            movies = self.db.query(Movie).filter(
                Movie.playlist_id == playlist.id
            ).limit(100).all()  # Limit to avoid timeout
            
            for movie in movies:
                self.sync_movie_info(movie, service)
        
        print(f"Sync complete! Results: {results}")
        return results

