# TS Segments Investigation Results

## Problem
ExoPlayer was getting 404 errors when trying to fetch TS segments from the generated m3u8 playlist.

## Investigation Findings

### Critical Discovery
**The server does NOT actually provide TS segments at the `/segments/` path.**

### Test Results

1. **HEAD Request Behavior**:
   - Returns: `200 OK`
   - Content-Type: `video/mp2t`
   - Content-Length: `0`
   - **This is misleading** - HEAD says segments exist, but they don't

2. **GET Request Behavior**:
   - Returns: `404 Not Found`
   - Content-Type: `text/html`
   - Response: HTML 404 error page
   - **Segments don't actually exist**

3. **Tested Content**:
   - Movie ID 137517: ✗ No segments
   - Other movies: ✗ No segments
   - Episodes: ✗ No segments

### Conclusion
**This Xtream Codes server does not provide TS segments at `/segments/{username}/{password}/{stream_id}/{segment_number}.ts`**

The server misleads by returning `200 OK` for HEAD requests, but actual GET requests return `404 Not Found`.

## Solution

### 1. Updated Segment Discovery
- Changed from HEAD to GET requests (with Range header)
- Verifies segments return actual TS data (starts with 0x47 sync byte)
- Detects HTML error pages and rejects them
- More robust validation

### 2. Error Handling
- Clear error messages when segments don't exist
- Recommends using MP4 format instead

### 3. Recommendation
**For this server, use MP4 format (container_extension) instead of segments-based m3u8.**

The MP4 format is available in the `stream_urls` list and works reliably.

## Code Changes

1. **`app/routes/xtream.py`**:
   - Updated `check_segment()` to use GET requests instead of HEAD
   - Added validation for TS sync byte (0x47)
   - Added detection of HTML error pages
   - Improved error messages

2. **Proxy endpoint**:
   - Already handles TS segments correctly as binary data
   - Skips HTML validation for TS segments

## Impact

- **Segments-based m3u8 will not work** for this server
- **MP4 format should be used** instead (already prioritized in stream_urls)
- The Flutter app will automatically fall back to MP4 when segments m3u8 returns 404

## Future Considerations

If segments become available in the future:
- The current implementation will automatically detect them
- No code changes needed
- Segments will be prioritized over direct m3u8 (but still after MP4)

