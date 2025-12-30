# How to Add Movies and Episodes to Xtream Codes

## Understanding the System

### Current Situation
- Your account (`had130`) is a **regular user account**, not an admin account
- The `/c/` endpoint is a **client portal** for set-top boxes, not an admin panel
- Admin panel is not accessible through standard web URLs
- Content addition requires **admin-level access** or **direct server access**

## How Content is Actually Added

### Method 1: Direct Server Access (Most Common)

Admins typically add content by:

1. **Upload Video Files to Server**
   ```
   Location: /home/xtreamcodes/iptv_xtream_codes/wwwdir/
   
   Movies: /movie/{username}/{password}/{stream_id}.{extension}
   Example: /movie/had130/589548655/137517.mkv
   
   Episodes: /series/{username}/{password}/{episode_id}.{extension}
   Example: /series/had130/589548655/35846.mp4
   ```

2. **Add Database Entry**
   - Xtream Codes uses MySQL database
   - Insert record into `streams` table (for movies)
   - Insert record into `episodes` table (for series episodes)

### Method 2: Admin Panel (If Available)

If admin panel is accessible:
- Usually on port 25500 or via SSH
- Requires admin account credentials
- Web interface for uploading and managing content

### Method 3: API (If Admin Account Available)

If you have admin account, you might be able to use API endpoints:
- POST requests to admin endpoints
- Requires proper authentication and data structure

## Content Structure Required

### Movie Entry Structure

**File Location:**
```
/movie/{username}/{password}/{stream_id}.{extension}
```

**Database Entry (streams table):**
```sql
INSERT INTO streams (
    stream_display_name,
    stream_type,
    stream_id,
    category_id,
    container_extension,
    stream_icon,
    added,
    direct_source
) VALUES (
    'Movie Name',
    'movie',
    137517,
    '144',
    'mkv',
    'https://image.tmdb.org/t/p/w500/...',
    UNIX_TIMESTAMP(),
    ''
);
```

**API Structure (if using API):**
```json
{
    "name": "Movie Name",
    "stream_type": "movie",
    "stream_id": 137517,
    "category_id": "144",
    "container_extension": "mkv",
    "stream_icon": "https://...",
    "added": "1721908872",
    "direct_source": ""
}
```

### Episode Entry Structure

**File Location:**
```
/series/{username}/{password}/{episode_id}.{extension}
```

**Database Entry (episodes table):**
```sql
INSERT INTO episodes (
    id,
    episode_num,
    title,
    season,
    series_id,
    container_extension,
    added,
    direct_source
) VALUES (
    '35846',
    1,
    'S01E01',
    '1',
    1,
    'mp4',
    UNIX_TIMESTAMP(),
    ''
);
```

**API Structure (if using API):**
```json
{
    "id": "35846",
    "episode_num": 1,
    "title": "S01E01",
    "season": "1",
    "series_id": 1,
    "container_extension": "mp4",
    "added": "1721908872",
    "direct_source": ""
}
```

## What You Need

### To Add Content, You Need:

1. **Server Access**
   - SSH access to the server
   - Or FTP/SFTP access
   - Or file upload capability

2. **Database Access**
   - MySQL database credentials
   - Write permissions to `streams` and `episodes` tables
   - Or admin API access

3. **Admin Account** (if using web interface)
   - Admin-level credentials
   - Access to admin panel

## Alternative Solutions

### If You Don't Have Admin Access:

#### Option 1: Request Admin Access
- Contact the server administrator
- Request admin account or API access
- Explain your use case

#### Option 2: Build Custom Content Management
Create your own system that:
- Stores content metadata in your own database
- Provides stream URLs through your API
- Manages content separately from Xtream Codes
- Works as a layer on top of Xtream Codes

#### Option 3: Use External Storage + Proxy
- Store videos on external storage (S3, etc.)
- Create proxy endpoints that serve videos
- Map to Xtream Codes structure
- Add metadata through your own API

## Example: Custom Content Management System

You could build a system that:

1. **Stores Content Metadata**
   ```python
   # Your own database
   {
       "id": "custom_123",
       "title": "Movie Name",
       "type": "movie",
       "stream_url": "https://your-storage.com/movie.mp4",
       "category": "Action",
       "metadata": {...}
   }
   ```

2. **Provides API Endpoints**
   ```python
   GET /api/content/movies
   GET /api/content/series/{id}/episodes
   GET /api/content/stream/{id}
   ```

3. **Proxies to Xtream Codes**
   - Your API provides content list
   - Stream URLs point to your proxy
   - Proxy fetches from external storage
   - Transparent to the client

## Next Steps

1. **Check Server Access**: Do you have SSH/FTP access to the server?
2. **Check Database Access**: Do you have MySQL credentials?
3. **Contact Admin**: Request admin access or API documentation
4. **Build Custom Solution**: If admin access isn't available, build your own content management layer

## Files Reference

- `XTREAM_ADMIN_INVESTIGATION.md`: Full investigation results
- `find_admin_panel.py`: Script to find admin panel URLs

