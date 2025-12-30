# Token-Based Stream URLs Implementation

## Discovery from APK Analysis

The APK uses **token-based authentication** for stream URLs:

```
GET http://194.76.0.168:2095/movie/had130/589548655/296314.mp4?token=...
```

The token is obtained by making a HEAD request to the stream URL, which returns a **302 redirect** with the token in the `Location` header.

## Implementation

### 1. New Method: `get_stream_url_with_token()`

Added to `app/services/xtream_codes.py`:

- Makes a HEAD request to the base stream URL
- Extracts token from 302 redirect's `Location` header
- Returns full URL with token parameter
- Falls back to base URL if token extraction fails

### 2. Updated Stream URL Generation

**Movies** (`get_movie_stream_url`):
- Now attempts to get token for MP4 URLs (container_extension)
- Adds `has_token` flag to URL metadata

**Episodes** (`get_episode_stream_url`):
- Same token support for series episodes
- Uses `series` stream type instead of `movie`

### 3. Updated Recommended URL Logic

**Priority order** (for both movies and episodes):
1. `direct_source` (if available)
2. **Container extension (mp4, etc.) WITH token** ← NEW! (matches APK)
3. Container extension (mp4, etc.) without token
4. Segments-based m3u8
5. Direct m3u8
6. TS format

## How It Works

1. **Client requests stream URL** from `/api/xtream/vod/stream-url` or `/api/xtream/series/episode/stream-url`

2. **Backend generates URLs**:
   - For MP4 (container_extension), makes HEAD request to get token
   - Returns URL with token: `/movie/{username}/{password}/{stream_id}.mp4?token=...`

3. **Client uses URL with token**:
   - Direct playback works (token authenticates the request)
   - No need for proxy in most cases

4. **Fallback**:
   - If token extraction fails, returns URL without token
   - Proxy endpoint can still handle it

## Benefits

✅ **Matches APK behavior** - Uses same token-based authentication  
✅ **Better compatibility** - Tokens ensure proper authentication  
✅ **Direct playback** - URLs work directly without proxy  
✅ **Backward compatible** - Falls back gracefully if token unavailable  

## Testing

To test token extraction:

```python
from app.services.xtream_codes import XtreamCodesService

service = XtreamCodesService("http://194.76.0.168:2095", "had130", "589548655")
url_with_token = service.get_stream_url_with_token("296314", "movie", "mp4")
print(url_with_token)  # Should include ?token=...
```

## Notes

- Token extraction uses a 5-second timeout to avoid blocking
- Tokens are obtained on-demand (not cached) as they may expire
- The proxy endpoint (`/api/xtream/stream/proxy`) already handles redirects with tokens, so it works with or without explicit tokens

