# APK Live TV Channels Investigation

## Key Findings

### 1. Live TV Categories
- **Endpoint**: `get_live_categories`
- **Result**: 85 categories found
- **Format**: List of category objects with `category_id`, `category_name`, `parent_id`

### 2. Live TV Streams
- **Endpoint**: `get_live_streams`
- **Result**: 3,645 live streams found
- **Format**: List of stream objects with:
  - `stream_id`: Unique stream identifier
  - `name`: Channel name
  - `stream_type`: "live"
  - `category_id`: Category the stream belongs to
  - `stream_icon`: Channel logo URL
  - `epg_channel_id`: EPG channel ID (can be null)
  - `direct_source`: Direct source URL (usually empty)
  - `tv_archive`: Whether TV archive is available (0 or 1)
  - `tv_archive_duration`: Archive duration in hours

### 3. Stream URL Pattern
**Working Pattern**: `/live/{username}/{password}/{stream_id}.{ext}`

- ✅ `.m3u8` - Returns 302 redirect with token
- ✅ `.ts` - Returns 302 redirect with token
- ❌ No extension - Returns 401 (Unauthorized)

**Example**:
```
http://ddgo770.live:2095/live/had130/589548655/1.m3u8
→ Redirects to: http://{server_ip}:{port}/live/had130/589548655/1.m3u8?token={token}
```

### 4. EPG (Electronic Program Guide)
- **XMLTV Format**: `xmltv.php?username={username}&password={password}`
  - Returns XML format EPG data
  - Content-Type: `application/xml; charset=utf-8`
  
- **JSON Format**: `get_short_epg` or `get_simple_data_table`
  - Returns JSON with `epg_listings` array
  - May be empty if no EPG data available

### 5. Stream Info
- **Endpoint**: `get_live_info&stream_id={stream_id}`
- Returns user_info and server_info (same as other info endpoints)

### 6. Filtering by Category
- **Endpoint**: `get_live_streams&category_id={category_id}`
- Returns only streams in the specified category

## Implementation Plan

### Backend Service Methods Needed
1. `get_live_categories()` - Get all live TV categories
2. `get_live_streams(category_id=None)` - Get live streams (optionally filtered by category)
3. `get_live_info(stream_id)` - Get info for a specific live stream
4. `get_live_stream_url(stream_id, format='m3u8')` - Generate stream URL for a live channel
5. `get_epg()` - Get EPG data (XML or JSON)

### API Routes Needed
1. `GET /api/xtream/live/categories` - Get live TV categories
2. `GET /api/xtream/live/streams` - Get live streams (with optional category filter)
3. `GET /api/xtream/live/info` - Get live stream info
4. `GET /api/xtream/live/stream-url` - Get live stream URL
5. `GET /api/xtream/live/epg` - Get EPG data

### Stream URL Generation
Live streams use the same token-based authentication as VOD:
1. Request: `/live/{username}/{password}/{stream_id}.m3u8`
2. Server redirects: `302` with token URL
3. Token URL: `http://{server_ip}:{port}/live/{username}/{password}/{stream_id}.m3u8?token={token}`

The proxy endpoint should work for live streams too (same pattern as VOD).

## Differences from VOD

| Feature | VOD (Movies/Series) | Live TV |
|---------|---------------------|---------|
| Path | `/movie/` or `/series/` | `/live/` |
| Stream ID | `stream_id` from episode/movie | `stream_id` from live stream |
| Format | MP4 (container_extension) | M3U8 or TS |
| Archive | N/A | TV Archive available (some streams) |
| EPG | N/A | Available via xmltv.php |

## Notes

- Live streams primarily use **M3U8 or TS format** (not MP4 like VOD)
- The same proxy endpoint can be used for live streams
- EPG data may not be available for all channels
- TV Archive allows watching past broadcasts (if enabled)

