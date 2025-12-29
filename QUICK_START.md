# Quick Start Guide

## For Railway Deployment

1. **Push to GitHub** (if not already done)
2. **Go to Railway.app** and create new project
3. **Connect GitHub repo** and select this directory
4. **Railway will auto-deploy** - wait for deployment
5. **Get your Railway URL** from project settings
6. **Update Flutter app** with Railway URL (in `../iptv-flutter-app/lib/services/api_service.dart`)

## For Local Development

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run server
python run.py
```

Server will start at: `http://localhost:3000`

## API Documentation

Once running, visit: `http://localhost:3000/docs` for interactive API documentation.

## Flutter App

The Flutter app has been moved to: `../iptv-flutter-app/`

To build the Android app:
1. Navigate to `../iptv-flutter-app/`
2. Update `lib/services/api_service.dart` with your Railway URL
3. Run `flutter pub get`
4. Run `flutter build apk`



