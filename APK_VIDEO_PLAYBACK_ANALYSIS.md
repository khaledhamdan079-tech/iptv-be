# APK Video Playback Analysis

## Summary

After investigating how the APK handles video playback, here are the key findings:

## Key Findings

### 1. Episode/Movie Data Structure
- Episodes and movies contain:
  - `id`: Stream ID (e.g., "35846")
  - `container_extension`: File format (e.g., "mp4")
  - `direct_source`: Usually empty string
  - `info`: Detailed metadata (codec, bitrate, duration, etc.)

### 2. Stream URL Construction
The APK likely constructs stream URLs as:
```
{base_url}/series/{username}/{password}/{stream_id}.{container_extension}
{base_url}/movie/{username}/{password}/{stream_id}.{container_extension}
```

### 3. Authentication Flow
1. Initial request to stream URL returns **302 redirect** with a token
2. Redirect URL format: `http://{server_ip}:{port}/series/{username}/{password}/{stream_id}.{ext}?token={token}`
3. Token URL must be used immediately for playback

### 4. Format Support
- **MP4**: ✅ Works perfectly
  - Returns 206 (Partial Content) with valid MP4 video data
  - Supports range requests
  - Content-Type: `video/mp4`
  
- **M3U8**: ❌ Not supported by this server
  - Returns 200 with empty HTML response
  - Content-Type: `text/html; charset=UTF-8`
  - Server doesn't provide HLS streams

### 5. Alternative Endpoints Tested
- `/play/{username}/{password}/{id}`: Returns 401 (Unauthorized) on GET
- `/stream/{username}/{password}/{id}`: Returns 401 (Unauthorized)
- `/watch/{username}/{password}/{id}`: Returns 401 (Unauthorized)
- `/play/{username}/{password}/{id}.m3u8`: Returns 404

### 6. Token Behavior
- Tokens are format-specific
- Token from `.mp4` redirect cannot be used for `.m3u8`
- Tokens appear to be time-limited (need to be used quickly)

## Conclusion

**The APK uses MP4 format for video playback**, not M3U8. The server only provides MP4 files, not HLS streams.

### Current Implementation Status
✅ **Working**: 
- MP4 stream URLs work correctly
- Proxy handles redirects and authentication
- Flutter app prioritizes MP4 over M3U8

❌ **Not Working**:
- M3U8 streams (server doesn't support them)
- Alternative endpoints require different authentication

### Recommendations
1. **Continue using MP4 format** - it's the only format that works
2. **Remove M3U8 from priority list** - or keep it as a fallback that will gracefully fail
3. **The current implementation is correct** - prioritize `container_extension` (mp4) over m3u8

## Test Results

### MP4 Stream Test
```
URL: http://ddgo770.live:2095/series/had130/589548655/35846.mp4
Status: 302 → 206 (Partial Content)
Content-Type: video/mp4
Result: ✅ Valid MP4 video data
```

### M3U8 Stream Test
```
URL: http://ddgo770.live:2095/series/had130/589548655/35846.m3u8
Status: 302 → 200
Content-Type: text/html; charset=UTF-8
Result: ❌ Empty HTML response
```

