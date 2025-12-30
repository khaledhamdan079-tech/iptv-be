# APK Resume/Continue Video Investigation

## Key Finding
**The APK uses URL parameters for resume, not HTTP Range requests.**

## Test Results

### Position Parameters in Stream URLs
The server **preserves position parameters** in the token URL redirect:

```
Original: /movie/{username}/{password}/{id}.mp4?position=1000
Redirect: http://{server_ip}:{port}/movie/{username}/{password}/{id}.mp4?position=1000&token={token}
```

**Supported Parameters:**
- `position` - Position in seconds
- `seek` - Seek position
- `time` - Time position
- `start` - Start position
- `offset` - Offset position
- `resume` - Resume position
- `continue` - Continue position

All of these parameters are **preserved in the redirect URL with token**.

### HTTP Range Requests
- **Status**: ❌ Not supported
- Server returns `200 OK` instead of `206 Partial Content`
- Range header is ignored

### Xtream Codes API
- No dedicated resume/watch history endpoints found
- Standard actions return user_info/server_info only

## How APK Likely Implements Resume

1. **Store Position Locally**: APK stores playback position (in seconds) locally
2. **Add Parameter to URL**: When resuming, adds position parameter to stream URL
3. **Server Includes in Token**: Server preserves parameter in token URL redirect
4. **Player Seeks**: Video player seeks to the position specified in the URL

## Implementation for Flutter App

### Option 1: URL Parameters (Like APK)
```dart
// When resuming:
String resumeUrl = "${streamUrl}?position=${positionInSeconds}";
// Server will include this in token URL
```

### Option 2: HTTP Range (Standard, but not supported)
```dart
// Not supported by this server
headers['Range'] = 'bytes=${byteOffset}-';
```

### Recommendation
**Use URL parameters** (Option 1) to match APK behavior:
- Server supports it
- Position is preserved through redirect
- Works with token authentication

## Code Changes Needed

1. **Backend Proxy**: Support position parameters in stream URLs
2. **Flutter App**: 
   - Store playback position locally
   - Add position parameter when resuming
   - Pass position to video player

## Example Implementation

### Backend (Proxy)
```python
# In proxy_stream endpoint, preserve position parameters
position = request.query_params.get('position') or request.query_params.get('seek')
if position:
    # Include in redirect URL
    url = f"{url}?position={position}"
```

### Flutter
```dart
// Store position
await storage.write(key: 'video_${streamId}_position', value: position.toString());

// Resume
String? savedPosition = await storage.read(key: 'video_${streamId}_position');
if (savedPosition != null) {
  streamUrl = "${streamUrl}?position=$savedPosition";
}
```

