# Database Quick Start

## 🚀 Quick Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize database (already done!):**
   ```bash
   python init_database.py
   ```

3. **Start the server:**
   ```bash
   python run.py
   ```

4. **Sync data from Xtream Codes:**
   ```bash
   # Using curl
   curl -X POST "http://localhost:3000/api/db/sync?playlist_id=0"
   
   # Or visit in browser:
   # http://localhost:3000/api/db/sync?playlist_id=0
   ```

## 📊 Available Endpoints

### Sync Data
- `POST /api/db/sync` - Sync all content (movies, series, episodes, live TV)
- `POST /api/db/sync/movies` - Sync movies only
- `POST /api/db/sync/series` - Sync series only
- `POST /api/db/sync/live` - Sync live TV only

### Query Data
- `GET /api/db/movies` - List movies (with pagination, search, filters)
- `GET /api/db/movies/{id}` - Get movie details
- `GET /api/db/series` - List series
- `GET /api/db/series/{id}` - Get series with episodes
- `GET /api/db/live` - List live TV channels
- `GET /api/db/categories` - List categories
- `GET /api/db/stats` - Get database statistics

## 🔍 Example Queries

### Search Movies
```
GET /api/db/movies?search=action&page=1&limit=20
```

### Get Movies by Category
```
GET /api/db/movies?category_id=144&page=1&limit=50
```

### Get Series with Episodes
```
GET /api/db/series/1?include_episodes=true
```

### Get Database Stats
```
GET /api/db/stats
```

## 📝 What Gets Stored

- ✅ Movies (VOD) - All metadata, ratings, plot, cast, etc.
- ✅ Series - All series information
- ✅ Episodes - All episodes with season/episode numbers
- ✅ Live TV Channels - Channel names, EPG info, archive support
- ✅ Categories - For movies, series, and live TV

## 🔄 Sync Strategy

- **Initial Sync**: Run full sync once to populate database
- **Regular Sync**: Set up cron job to sync every 6-12 hours
- **Incremental**: The sync service updates existing records and adds new ones

## 💡 Tips

1. **First sync may take time** - Be patient, especially if syncing episodes
2. **Episodes are optional** - Set `include_episodes=false` for faster sync
3. **Movie info is slow** - Set `include_movie_info=false` unless you need detailed codec info
4. **Use pagination** - For large datasets, use `page` and `limit` parameters
5. **Search is case-insensitive** - Use `search` parameter for filtering

## 🗄️ Database Location

- **SQLite**: `./iptv_content.db` (in project root)
- **PostgreSQL**: Set `DATABASE_URL` environment variable

## 📚 Full Documentation

See `DATABASE_SETUP.md` for complete documentation.

