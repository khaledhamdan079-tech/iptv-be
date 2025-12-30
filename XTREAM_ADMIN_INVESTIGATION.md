# Xtream Codes Admin Investigation

## Summary

Investigation into how administrators add movies and episodes to Xtream Codes servers.

## Findings

### 1. Account Type
- Current account (`had130`) appears to be a **regular user account**, not an admin account
- All admin API endpoints return `user_info` instead of actual admin responses
- This suggests the account lacks admin privileges

### 2. Admin Panel
- `/c/` is **NOT** the admin panel - it's the **client portal** (stalker_portal) for set-top boxes
- Shows "Your STB is not supported" with options: reload portal, account info, payment
- Standard admin URLs (`/admin`, `/panel`) return 404
- Port 25500 (common admin panel port) is not accessible
- Admin panel likely requires:
  - Admin account credentials (different from regular user)
  - Direct server access (SSH)
  - Or access to a different port/service

### 3. API Endpoints Tested
All tested endpoints return `user_info` (suggesting they're not available or require admin privileges):
- `add_vod`, `add_movie`, `upload_vod`, `create_vod`
- `add_series`, `add_episode`, `upload_series`, `create_series`
- `add_vod_info`, `add_episode_info`
- `manage_vod`, `manage_series`

### 4. Content Structure

#### Movie Structure (from API)
```json
{
  "num": 1,
  "name": "Movie Name",
  "stream_type": "movie",
  "stream_id": 137517,
  "stream_icon": "https://...",
  "rating": "0",
  "rating_5based": 0,
  "added": "1721908872",
  "category_id": "144",
  "container_extension": "mkv",
  "custom_sid": null,
  "direct_source": ""
}
```

#### Episode Structure (from API)
```json
{
  "id": "35846",
  "episode_num": 1,
  "title": "S01E01",
  "container_extension": "mp4",
  "info": {
    "duration_secs": 2167,
    "duration": "00:36:07",
    "video": {...},
    "audio": {...}
  },
  "custom_sid": null,
  "added": "...",
  "season": "1",
  "direct_source": ""
}
```

## How Admins Typically Add Content

### Method 1: Web Admin Panel
1. Access admin panel (usually at `/c/` or `/admin`)
2. Login with admin credentials
3. Use web interface to:
   - Upload video files
   - Add metadata (title, description, etc.)
   - Assign categories
   - Set stream URLs

### Method 2: Direct File Upload + Database Entry
1. **Upload video file** to server storage:
   - Location: Usually `/home/xtreamcodes/iptv_xtream_codes/wwwdir/`
   - Structure: `/movie/{username}/{password}/{stream_id}.{extension}`
   - Or: `/series/{username}/{password}/{episode_id}.{extension}`

2. **Add database entry**:
   - Xtream Codes uses MySQL database
   - Tables: `streams`, `streams_sys`, `episodes`, etc.
   - Insert record with proper structure

### Method 3: API (If Available)
- Requires admin-level account
- POST requests to admin endpoints
- Proper data structure matching existing content

### Method 4: Third-Party Tools
- Xtream Codes Manager
- IPTV Manager tools
- Custom scripts with database access

## Required Information to Add Content

### For Movies:
- `name`: Movie title
- `stream_type`: "movie"
- `stream_id`: Unique ID
- `category_id`: Category ID
- `container_extension`: File extension (mp4, mkv, etc.)
- `stream_icon`: Poster/thumbnail URL
- `added`: Unix timestamp
- Video file must be accessible at: `/movie/{username}/{password}/{stream_id}.{extension}`

### For Episodes:
- `id`: Episode ID
- `episode_num`: Episode number
- `title`: Episode title
- `season`: Season number
- `series_id`: Parent series ID
- `container_extension`: File extension
- `info`: Detailed metadata (duration, video/audio codecs, etc.)
- Video file must be accessible at: `/series/{username}/{password}/{episode_id}.{extension}`

## Recommendations

### If You Have Admin Access:
1. **Use Web Admin Panel**: Most reliable method
   - Access: `http://ddgo770.live:2095/c/`
   - Login with admin credentials
   - Use the interface to add content

2. **Direct Database Access** (if you have server access):
   - Connect to MySQL database
   - Insert records into appropriate tables
   - Ensure video files are in correct location

### If You Don't Have Admin Access:
1. **Request Admin Credentials**: Contact server administrator
2. **Use API with Admin Account**: If admin API endpoints exist
3. **Alternative**: Build a content management system that:
   - Stores content metadata
   - Provides stream URLs
   - Manages content separately from Xtream Codes

## Next Steps

1. **Check Admin Panel**: Try accessing `http://ddgo770.live:2095/c/` with admin credentials
2. **Verify Account Type**: Check if your account has admin privileges
3. **Contact Server Admin**: Request admin access or API documentation
4. **Investigate Database**: If you have server access, examine the database structure
5. **Build Custom Solution**: Create your own content management layer if admin access isn't available

## Files Created

- `investigate_xtream_admin.py`: Script to test admin API endpoints
- `test_xtream_add_content.py`: Script to test POST requests and analyze content structure

