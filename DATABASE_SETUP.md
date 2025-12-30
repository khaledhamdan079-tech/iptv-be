# Database Setup Guide

## Overview

This project now includes a local database to store all content from Xtream Codes API (movies, series, episodes, live TV channels, and categories). This allows you to:

- Query content locally (faster than API calls)
- Search and filter content
- Manage your own content metadata
- Build custom features on top of the data

## Database Technology

- **SQLite** by default (simple, no setup required)
- Can be switched to **PostgreSQL** for production (set `DATABASE_URL` environment variable)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `sqlalchemy` - ORM for database operations
- `psycopg2-binary` - PostgreSQL driver (optional, only needed for PostgreSQL)

### 2. Initialize Database

Run the initialization script:

```bash
python init_database.py
```

This creates all necessary tables:
- `playlists` - Xtream Codes playlist configurations
- `categories` - Content categories (movies, series, live TV)
- `movies` - Movie/VOD content
- `series` - TV Series
- `episodes` - Series episodes
- `live_channels` - Live TV channels

### 3. Sync Data from Xtream Codes

#### Option A: Using API Endpoint (Recommended)

```bash
# Sync all content
curl -X POST "http://localhost:3000/api/db/sync?playlist_id=0&include_episodes=true"

# Sync only movies
curl -X POST "http://localhost:3000/api/db/sync/movies?playlist_id=0"

# Sync only series
curl -X POST "http://localhost:3000/api/db/sync/series?playlist_id=0"

# Sync only live TV
curl -X POST "http://localhost:3000/api/db/sync/live?playlist_id=0"
```

#### Option B: Using Python Script

Create a script to sync:

```python
from app.database import SessionLocal
from app.services.db_sync import DatabaseSyncService
from app.services.xtream_codes import XtreamCodesService

db = SessionLocal()
service = XtreamCodesService("http://ddgo770.live:2095", "had130", "589548655")
sync_service = DatabaseSyncService(db)

playlist = sync_service.get_or_create_playlist(
    base_url="http://ddgo770.live:2095",
    username="had130",
    password="589548655"
)

# Sync all content
results = sync_service.sync_all(playlist, service, include_episodes=True)
print(f"Sync results: {results}")
```

## API Endpoints

### Sync Endpoints

- `POST /api/db/sync` - Sync all content
  - Parameters:
    - `playlist_id` (default: 0)
    - `include_episodes` (default: true)
    - `include_movie_info` (default: false, slow!)

- `POST /api/db/sync/movies` - Sync movies only
- `POST /api/db/sync/series` - Sync series only
- `POST /api/db/sync/live` - Sync live TV channels only

### Query Endpoints

- `GET /api/db/movies` - Get movies
  - Parameters: `playlist_id`, `category_id`, `search`, `page`, `limit`
  
- `GET /api/db/movies/{movie_id}` - Get movie details

- `GET /api/db/series` - Get series
  - Parameters: `playlist_id`, `category_id`, `search`, `page`, `limit`

- `GET /api/db/series/{series_id}` - Get series with episodes

- `GET /api/db/live` - Get live TV channels
  - Parameters: `playlist_id`, `category_id`, `search`, `page`, `limit`

- `GET /api/db/categories` - Get categories
  - Parameters: `playlist_id`, `category_type` (movie/series/live)

- `GET /api/db/stats` - Get database statistics

## Database Schema

### Movies Table
- `id` - Primary key
- `stream_id` - Original stream ID from Xtream Codes
- `name` - Movie title
- `container_extension` - File format (mp4, mkv, etc.)
- `plot`, `cast`, `director`, `genre`, `year` - Metadata
- `video_info`, `audio_info` - Codec information (JSON)
- `last_synced` - Last sync timestamp

### Series Table
- `id` - Primary key
- `series_id` - Original series ID from Xtream Codes
- `name` - Series title
- `plot`, `cast`, `genre` - Metadata
- `episodes` - Relationship to episodes table

### Episodes Table
- `id` - Primary key
- `series_id` - Foreign key to series
- `episode_id` - Original episode ID from Xtream Codes
- `episode_num` - Episode number
- `season` - Season number
- `container_extension` - File format
- `duration`, `video_info`, `audio_info` - Media info

### Live Channels Table
- `id` - Primary key
- `stream_id` - Original stream ID
- `name` - Channel name
- `epg_channel_id` - EPG channel ID
- `tv_archive` - Archive support flag

### Categories Table
- `id` - Primary key
- `category_id` - Original category ID from API
- `category_name` - Category name
- `category_type` - Type: 'movie', 'series', or 'live'

## Usage Examples

### Sync All Content

```bash
curl -X POST "http://localhost:3000/api/db/sync?playlist_id=0"
```

### Search Movies

```bash
curl "http://localhost:3000/api/db/movies?search=action&page=1&limit=20"
```

### Get Series with Episodes

```bash
curl "http://localhost:3000/api/db/series/1?include_episodes=true"
```

### Get Database Statistics

```bash
curl "http://localhost:3000/api/db/stats"
```

## Switching to PostgreSQL

For production, you can use PostgreSQL:

1. Set environment variable:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost/iptv_db"
   ```

2. Or in `.env` file:
   ```
   DATABASE_URL=postgresql://user:password@localhost/iptv_db
   ```

3. The database will automatically use PostgreSQL instead of SQLite.

## Maintenance

### Regular Sync

Set up a cron job or scheduled task to sync data regularly:

```bash
# Sync every 6 hours
0 */6 * * * curl -X POST "http://localhost:3000/api/db/sync?playlist_id=0"
```

### Database Backup

For SQLite:
```bash
cp iptv_content.db iptv_content_backup.db
```

For PostgreSQL:
```bash
pg_dump iptv_db > backup.sql
```

## Notes

- First sync may take a while depending on content size
- Episodes sync is optional (can be slow for large series)
- Movie info sync is optional (very slow, fetches detailed info for each movie)
- Database is automatically initialized on application startup
- All timestamps are stored in UTC

