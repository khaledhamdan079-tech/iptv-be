# Railway Troubleshooting Guide

## Server Not Responding / Slow Startup

### 1. Check Railway Logs

In Railway dashboard:
1. Go to your project
2. Click on your service
3. Click "Deployments" tab
4. Click on the latest deployment
5. Click "View Logs"

Look for:
- Errors during startup
- Timeout errors
- Memory/CPU limits
- Import errors

### 2. Common Issues

#### Issue: Server takes too long to start
**Solution:**
- The server now uses lazy loading for Maso API calls
- Playlists are cached for 5 minutes
- Check if there are network timeouts in logs

#### Issue: 499 Client Closed Request
**Solution:**
- Railway has a 30-second timeout for HTTP requests
- Large data fetches are now cached
- Timeouts increased to 30 seconds for API calls

#### Issue: Memory/CPU Limits
**Solution:**
- Check Railway resource usage in dashboard
- Free tier has limited resources
- Consider upgrading if needed

### 3. Quick Health Check

Test these endpoints to verify server is running:

```bash
# Health check (should be instant)
curl https://your-app.railway.app/health

# Root endpoint (should be instant)
curl https://your-app.railway.app/

# Swagger UI
https://your-app.railway.app/docs
```

### 4. Restart the Service

In Railway dashboard:
1. Go to your service
2. Click "Settings"
3. Click "Restart" button

### 5. Check Environment Variables

Make sure these are set (if needed):
- `PORT` - Automatically set by Railway
- Any API keys or credentials

### 6. View Real-time Logs

In Railway dashboard:
1. Go to your service
2. Click "Logs" tab
3. Watch for errors in real-time

### 7. Common Error Messages

#### "No start command was found"
- Check `Procfile` exists with: `web: python run.py`
- Or set start command in Railway dashboard: `Settings > Deploy > Start Command`

#### "Module not found"
- Check `requirements.txt` includes all dependencies
- Railway should auto-install, but verify in build logs

#### "Port already in use"
- Railway sets PORT automatically, don't hardcode it
- Use `os.environ.get("PORT", 3000)` in code

### 8. Performance Optimization

The server now includes:
- ✅ Lazy loading of Maso API service (no blocking on startup)
- ✅ Caching of playlists (5 min TTL)
- ✅ Caching of movies/series lists (10 min TTL)
- ✅ Async request handling
- ✅ Increased timeouts for slow APIs

### 9. Force Rebuild

If issues persist:
1. Go to Railway dashboard
2. Click on your service
3. Click "Settings"
4. Click "Clear Build Cache"
5. Redeploy

### 10. Check Railway Status

Visit: https://status.railway.app/
- Check if Railway is experiencing issues
- Check service status

## Debugging Commands

### Local Testing
```bash
# Test server locally
python run.py

# Check if server starts quickly
time python run.py
```

### Check Dependencies
```bash
# Verify all packages are installed
pip list

# Check for missing imports
python -c "from app.main import app; print('OK')"
```

## Contact Support

If issues persist:
1. Check Railway logs for specific errors
2. Check Railway status page
3. Review this troubleshooting guide
4. Check GitHub issues (if applicable)
