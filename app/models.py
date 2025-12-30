"""
Database models for IPTV content
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Playlist(Base):
    """Xtream Codes playlist configuration"""
    __tablename__ = "playlists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    base_url = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    movies = relationship("Movie", back_populates="playlist")
    series = relationship("Series", back_populates="playlist")
    live_channels = relationship("LiveChannel", back_populates="playlist")
    categories = relationship("Category", back_populates="playlist")


class Category(Base):
    """Content categories (for movies, series, live TV)"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    category_id = Column(String, nullable=False, index=True)  # Original category_id from API
    category_name = Column(String, nullable=False)
    category_type = Column(String, nullable=False)  # 'movie', 'series', 'live'
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    playlist = relationship("Playlist", back_populates="categories")
    movies = relationship("Movie", back_populates="category")
    series = relationship("Series", back_populates="category")
    live_channels = relationship("LiveChannel", back_populates="category")


class Movie(Base):
    """Movies/VOD content"""
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Original data from Xtream Codes API
    stream_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False, index=True)
    stream_type = Column(String, default="movie")
    stream_icon = Column(String, nullable=True)
    rating = Column(String, nullable=True)
    rating_5based = Column(Integer, default=0)
    added = Column(String, nullable=True)  # Unix timestamp as string
    container_extension = Column(String, nullable=True)  # mp4, mkv, etc.
    custom_sid = Column(String, nullable=True)
    direct_source = Column(String, nullable=True)
    
    # Extended info (from get_vod_info)
    movie_image = Column(String, nullable=True)
    backdrop_path = Column(Text, nullable=True)  # JSON array as string
    tmdb_id = Column(String, nullable=True)
    youtube_trailer = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    plot = Column(Text, nullable=True)
    cast = Column(Text, nullable=True)
    director = Column(String, nullable=True)
    releasedate = Column(String, nullable=True)
    duration_secs = Column(Integer, nullable=True)
    duration = Column(String, nullable=True)
    video_info = Column(JSON, nullable=True)  # Video codec info
    audio_info = Column(JSON, nullable=True)  # Audio codec info
    bitrate = Column(Integer, nullable=True)
    year = Column(String, nullable=True)
    mpaa = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_synced = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    playlist = relationship("Playlist", back_populates="movies")
    category = relationship("Category", back_populates="movies")


class Series(Base):
    """TV Series"""
    __tablename__ = "series"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Original data from Xtream Codes API
    series_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False, index=True)
    cover = Column(String, nullable=True)
    plot = Column(Text, nullable=True)
    cast = Column(Text, nullable=True)
    director = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    releaseDate = Column(String, nullable=True)
    last_modified = Column(String, nullable=True)
    rating = Column(String, nullable=True)
    rating_5based = Column(Integer, nullable=True)
    backdrop_path = Column(Text, nullable=True)  # JSON array as string
    youtube_trailer = Column(String, nullable=True)
    episode_run_time = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_synced = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    playlist = relationship("Playlist", back_populates="series")
    category = relationship("Category", back_populates="series")
    episodes = relationship("Episode", back_populates="series", cascade="all, delete-orphan")


class Episode(Base):
    """Series Episodes"""
    __tablename__ = "episodes"
    
    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("series.id"), nullable=False)
    
    # Original data from Xtream Codes API
    episode_id = Column(String, nullable=False, index=True)  # Original 'id' field
    episode_num = Column(Integer, nullable=False)
    title = Column(String, nullable=True)
    season = Column(String, nullable=False, index=True)
    container_extension = Column(String, nullable=True)  # mp4, mkv, etc.
    custom_sid = Column(String, nullable=True)
    added = Column(String, nullable=True)  # Unix timestamp as string
    direct_source = Column(String, nullable=True)
    
    # Extended info (from get_series_info)
    duration_secs = Column(Integer, nullable=True)
    duration = Column(String, nullable=True)
    video_info = Column(JSON, nullable=True)  # Video codec info
    audio_info = Column(JSON, nullable=True)  # Audio codec info
    bitrate = Column(Integer, nullable=True)
    info = Column(JSON, nullable=True)  # Other episode info
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_synced = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    series = relationship("Series", back_populates="episodes")


class LiveChannel(Base):
    """Live TV Channels"""
    __tablename__ = "live_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Original data from Xtream Codes API
    stream_id = Column(String, nullable=False, unique=True, index=True)
    num = Column(Integer, nullable=True)
    name = Column(String, nullable=False, index=True)
    stream_type = Column(String, default="live")
    stream_icon = Column(String, nullable=True)
    epg_channel_id = Column(String, nullable=True)
    added = Column(String, nullable=True)  # Unix timestamp as string
    category_name = Column(String, nullable=True)
    category_id_api = Column(String, nullable=True)  # Original category_id from API
    custom_sid = Column(String, nullable=True)
    tv_archive = Column(Integer, default=0)
    direct_source = Column(String, nullable=True)
    tv_archive_duration = Column(Integer, nullable=True)
    
    # Extended info (from get_live_info)
    info = Column(JSON, nullable=True)  # Additional channel info
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_synced = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    playlist = relationship("Playlist", back_populates="live_channels")
    category = relationship("Category", back_populates="live_channels")

