# M3U8 Stream Solution

## Problem
Direct m3u8 URLs from Xtream Codes return empty HTML responses instead of HLS playlists.

## Solution
We discovered that the Xtream Codes server provides **TS segments** at:
```
/segments/{username}/{password}/{stream_id}/{segment_number}.ts
```

We can generate a valid m3u8 playlist by:
1. Discovering available TS segments
2. Creating an m3u8 playlist that references these segments
3. Serving the playlist through a backend endpoint

## Implementation

### Backend Endpoint
**`GET /api/xtream/segments/m3u8`**

**Parameters:**
- `stream_id` (required): Episode or movie ID
- `type` (required): `"series"` or `"movie"`
- `playlist_id` (optional): Playlist ID (default: 0)

**How it works:**
1. Discovers available TS segments by checking `/segments/{username}/{password}/{stream_id}/{n}.ts`
2. Generates a valid m3u8 playlist with all discovered segments
3. Returns the playlist with proper MIME type (`application/vnd.apple.mpegurl`)

**Example:**
```
GET /api/xtream/segments/m3u8?stream_id=35846&type=series&playlist_id=0
```

**Response:**
```
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:10.0,
http://ddgo770.live:2095/segments/had130/589548655/35846/0.ts
#EXTINF:10.0,
http://ddgo770.live:2095/segments/had130/589548655/35846/1.ts
...
#EXT-X-ENDLIST
```

### Integration
The segments-based m3u8 URL is automatically added to the stream URLs list with priority:
1. `direct_source` (if available)
2. `container_extension` (mp4, etc.)
3. **Segments-based m3u8** ← NEW!
4. Direct m3u8 (usually doesn't work)
5. TS format

### Flutter App
The Flutter app will automatically receive the segments-based m3u8 URL in the `stream_urls` array. It will be prioritized over the direct m3u8 URL since it's marked with `is_segments_based: true`.

## Testing Results

### Segments Discovery
- ✅ Segments are accessible at `/segments/{username}/{password}/{id}/{n}.ts`
- ✅ Segments return valid TS data (`video/mp2t` or `application/octet-stream`)
- ✅ Segments are numbered sequentially (0, 1, 2, ...)
- ✅ Can discover up to 1000+ segments per episode/movie

### M3U8 Playlist
- ✅ Generated playlists are valid HLS format
- ✅ All segments are properly referenced
- ✅ Playlist includes proper HLS headers (`#EXTM3U`, `#EXT-X-VERSION`, etc.)

## Benefits

1. **Working HLS streams**: Provides functional m3u8 playlists when direct m3u8 fails
2. **Automatic discovery**: No need to know segment count in advance
3. **Standard HLS format**: Compatible with all HLS players
4. **Fallback support**: If segments aren't available, falls back to mp4

## Usage

The segments-based m3u8 URL is automatically included in the response from:
- `GET /api/xtream/series/episode/stream-url`
- `GET /api/xtream/vod/stream-url`

The Flutter app will automatically use it when:
- Direct m3u8 fails
- User prefers HLS format
- Segments are available

## Notes

- Segment discovery may take a few seconds for long videos
- Maximum 1000 segments checked (reasonable limit)
- If no segments found, endpoint returns 404 with helpful error message
- Segments use the same authentication as regular streams

