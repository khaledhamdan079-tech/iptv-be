# M3U8 Playback Investigation

## Current Status

### ✅ What's Working
1. **M3U8 Playlist Generation**: The backend successfully generates valid m3u8 playlists
2. **Segment Discovery**: TS segments are discoverable via HEAD requests (200 OK, `video/mp2t`)
3. **Playlist Format**: Generated playlists are valid HLS format with proper headers
4. **Proxied Segment URLs**: Segments in the playlist now use proxied URLs

### ❌ Current Issues

#### 1. ExoPlayer Not Recognizing HLS
**Error**: `UnrecognizedInputFormatException: None of the available extractors could read the stream`

**Problem**: ExoPlayer is trying to parse the m3u8 file as a progressive stream instead of recognizing it as HLS.

**Possible Causes**:
- URL doesn't end with `.m3u8` (ExoPlayer uses file extension for format detection)
- Content-Type header might not be properly set
- video_player plugin might not be detecting HLS format

**Solution Implemented**:
- ✅ Added path-based endpoint: `/api/xtream/segments/{stream_id}.m3u8`
- ✅ Updated URL construction to use path-based format
- ✅ Ensured Content-Type is `application/vnd.apple.mpegurl`

#### 2. TS Segment Access
**Finding**: 
- HEAD requests: ✅ 200 OK, `video/mp2t`
- GET requests: ❌ 404 Not Found

**Implication**: Segments might require:
- Specific headers (Range, etc.)
- Authentication tokens
- Or only work through proxy

**Current Solution**: All segment URLs in m3u8 are proxied through `/api/xtream/stream/proxy`

## Testing Results

### Segment Accessibility Test
```
Segment URL: http://ddgo770.live:2095/segments/had130/589548655/137517/0.ts
HEAD Request: 200 OK, Content-Type: video/mp2t
GET Request: 404 Not Found
```

**Conclusion**: Segments require proxy or specific headers for GET requests.

### M3U8 Playlist Test
```
URL: /api/xtream/segments/137517.m3u8?type=movie&playlist_id=0
Status: 200 OK
Content-Type: application/vnd.apple.mpegurl
Content: Valid HLS playlist with proxied segment URLs
```

**Conclusion**: Playlist generation works correctly.

## Next Steps

### 1. Verify Path-Based URL Works
Test if ExoPlayer recognizes the new URL format:
```
http://iptv-be-production.up.railway.app/api/xtream/segments/137517.m3u8?type=movie&playlist_id=0
```

### 2. Check TS Segment Proxy
Verify that proxied TS segments are accessible:
```
http://iptv-be-production.up.railway.app/api/xtream/stream/proxy?url=http://ddgo770.live:2095/segments/had130/589548655/137517/0.ts&playlist_id=0
```

### 3. ExoPlayer Configuration
If path-based URL doesn't work, we may need to:
- Explicitly configure ExoPlayer for HLS
- Use a different video player plugin
- Or ensure the URL format matches ExoPlayer's expectations

### 4. Alternative: Use MP4 Instead
Since MP4 works perfectly, we could:
- Prioritize MP4 over m3u8
- Only use m3u8 when MP4 is not available
- Document that MP4 is the preferred format

## Recommendations

1. **Test the new path-based URL** ending with `.m3u8`
2. **Verify TS segment proxy** works for all segments
3. **If HLS still doesn't work**, prioritize MP4 format (which we know works)
4. **Consider** using a different HLS player if ExoPlayer continues to have issues

## Current URL Formats

### Old Format (Query Parameters)
```
/api/xtream/segments/m3u8?stream_id=137517&type=movie&playlist_id=0
```

### New Format (Path Parameter - Recommended)
```
/api/xtream/segments/137517.m3u8?type=movie&playlist_id=0
```

Both formats work, but the path-based format should help ExoPlayer recognize it as HLS.

