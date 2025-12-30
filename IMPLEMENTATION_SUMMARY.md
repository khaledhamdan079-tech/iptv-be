# Token-Based Stream URLs - Implementation Summary

## ✅ Python Backend Changes (COMPLETE)

### 1. Token Extraction Method (`app/services/xtream_codes.py`)

**Added**: `get_stream_url_with_token()` method
- Makes GET request to base stream URL
- Extracts token from 302 redirect's `Location` header
- Handles different IP addresses in redirect (e.g., `ddgo770.live` → `194.76.0.168`)
- Returns full URL with token parameter
- Falls back gracefully if token unavailable

### 2. Stream URL Generation Updates

**Movies** (`get_movie_stream_url`):
- ✅ Attempts to get token for MP4 URLs (container_extension)
- ✅ Adds `has_token` flag to URL metadata
- ✅ Returns URL with token when available

**Episodes** (`get_episode_stream_url`):
- ✅ Same token support for series episodes
- ✅ Uses `series` stream type for token extraction

### 3. Recommended URL Priority (`app/routes/xtream.py`)

**Updated priority order** (for both movies and episodes):
1. `direct_source` (if available)
2. **Container extension (mp4) WITH token** ← NEW! (matches APK)
3. Container extension (mp4) without token
4. Segments-based m3u8
5. Direct m3u8
6. TS format

### 4. API Response Structure

**Endpoints updated**:
- ✅ `/api/xtream/vod/stream-url` - Returns URLs with tokens
- ✅ `/api/xtream/series/episode/stream-url` - Returns URLs with tokens

**Response includes**:
```json
{
  "success": true,
  "stream_urls": [
    {
      "url": "http://194.76.0.168:2095/movie/.../296314.mp4?token=...",
      "format": "mp4",
      "type": "video",
      "quality": "original",
      "has_token": true  // ← NEW
    },
    // ... other options
  ],
  "recommended_url": "http://194.76.0.168:2095/movie/.../296314.mp4?token=...",
  "recommended_format": "mp4"
}
```

## 📱 Flutter App Changes Needed

### Quick Start (Simplest Approach)

**Just use `recommended_url`** - The backend already prioritizes URLs with tokens:

```dart
// Get stream URLs
final response = await apiService.getMovieStreamUrls(vodId);
final recommendedUrl = response['recommended_url'];

// Use directly - it already has token if available
await _initializePlayer(recommendedUrl);
```

### Optional: Enhanced Support

1. **Add `has_token` field** to `XtreamStreamUrl` model
2. **Prioritize token URLs** when selecting from `stream_urls` array
3. **Skip proxy** for URLs with tokens (they work directly)

See `FLUTTER_CHANGES_NEEDED.md` for detailed Flutter changes.

## 🔄 How It Works

### Flow Diagram

```
1. Flutter App
   └─> GET /api/xtream/vod/stream-url?vod_id=296314

2. Backend
   ├─> Get movie info (get_vod_info)
   ├─> Construct base URL: http://ddgo770.live:2095/movie/.../296314.mp4
   ├─> GET request to base URL (no token)
   │   └─> 302 Redirect
   │       └─> Location: http://194.76.0.168:2095/movie/.../296314.mp4?token=...
   ├─> Extract token URL from Location header
   └─> Return URL with token

3. Flutter App
   └─> Use URL with token directly for playback
       └─> Video plays! ✅
```

## ✅ Benefits

1. **Matches APK Behavior**: Uses same token-based authentication
2. **Better Compatibility**: Tokens ensure proper authentication
3. **Direct Playback**: URLs work directly without proxy (faster)
4. **Backward Compatible**: Falls back gracefully if token unavailable
5. **Automatic**: Backend handles token extraction automatically

## 🧪 Testing

### Test Token Extraction

```python
from app.services.xtream_codes import XtreamCodesService

service = XtreamCodesService("http://ddgo770.live:2095", "had130", "589548655")
url_with_token = service.get_stream_url_with_token("296314", "movie", "mp4")

# Should return: http://194.76.0.168:2095/movie/had130/589548655/296314.mp4?token=...
print(url_with_token)
```

### Test API Endpoint

```bash
curl "http://localhost:8000/api/xtream/vod/stream-url?vod_id=296314&playlist_id=0"
```

Expected response should include:
- `recommended_url` with token
- `stream_urls` array with `has_token: true` for MP4 URLs

## 📝 Notes

- **Token extraction timeout**: 5 seconds (to avoid blocking)
- **Tokens are not cached**: Obtained on-demand (may expire)
- **Different IP handling**: Redirects to different IPs are handled automatically
- **Fallback behavior**: If token extraction fails, returns URL without token

## 🚀 Status

- ✅ **Backend**: Complete and ready
- 📱 **Flutter**: Needs minor updates (see `FLUTTER_CHANGES_NEEDED.md`)

The backend is production-ready. The Flutter app should work with minimal changes (just use `recommended_url`).

