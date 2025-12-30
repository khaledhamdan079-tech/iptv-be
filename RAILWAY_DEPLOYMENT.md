# Railway Deployment Guide

## Prerequisites

1. Railway account (sign up at https://railway.app)
2. Railway CLI installed (optional, can use web interface)
3. Git repository (GitHub recommended)

## Deployment Steps

### 1. Prepare the Project

The Flutter app has been moved to a separate directory. The Python backend is ready for deployment.

### 2. Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo" (or use Railway CLI)
4. Connect your repository
5. Select the Python backend directory

### 3. Configure Start Command

**Important**: Railway needs to know how to start your application.

**Option 1: Automatic (Recommended)**
- Railway should automatically detect the `Procfile` or `railway.json`
- If it doesn't, go to your service settings → "Settings" tab
- Under "Start Command", enter: `python run.py`

**Option 2: Manual Configuration**
1. Go to your Railway project dashboard
2. Click on your service
3. Go to "Settings" tab
4. Scroll to "Deploy" section
5. Set "Start Command" to: `python run.py`
6. Save changes

### 4. Configure Environment Variables

Railway will automatically provide a `PORT` environment variable. You don't need to set it manually, but if you want to override it:

1. Go to your service → "Variables" tab
2. Add: `PORT=3000` (optional, Railway sets this automatically)

### 4. Update run.py for Railway

Railway uses the `PORT` environment variable. Update `run.py`:

```python
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
```

### 5. Create Procfile (Optional)

Create a `Procfile` in the root directory:

```
web: python run.py
```

Or use `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python run.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 6. Verify requirements.txt

Ensure `requirements.txt` includes all dependencies:

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
python-dotenv>=1.0.0
cachetools>=5.3.0
brotli>=1.1.0
playwright>=1.40.0
```

### 7. Deploy

1. Push your code to GitHub
2. Railway will automatically detect changes and deploy
3. Wait for deployment to complete
4. Get your Railway URL (e.g., `https://your-app.railway.app`)

### 8. Update Flutter App

Update the API base URL in `flutter_app/lib/services/api_service.dart`:

```dart
static const String baseUrl = 'https://your-app.railway.app';
```

## Post-Deployment

### Test the API

```bash
curl https://your-app.railway.app/health
```

### Update CORS (if needed)

The CORS middleware in `app/main.py` already allows all origins (`allow_origins=["*"]`), so it should work with the Flutter app.

## Troubleshooting

1. **Port binding errors**: Ensure you're using `0.0.0.0` as host
2. **Dependencies not found**: Check `requirements.txt` includes all packages
3. **Playwright issues**: Railway may need additional setup for Playwright browsers
4. **Timeout errors**: Increase timeout in Railway settings if needed

## Monitoring

- Check Railway dashboard for logs
- Monitor API health endpoint
- Check error logs for any issues



