# IPTV Arabic Backend

A backend API for streaming Arabic-translated series from various sources like FaselHD and similar sites.

**Note**: The Flutter app has been moved to a separate directory (`../iptv-flutter-app/`). This project contains only the Python backend for deployment to Railway.

## Features

- 🔍 Search for Arabic-translated series
- 📺 Get series details and episode lists
- 🎬 Retrieve video links for episodes
- ⚡ Caching for improved performance
- 🌐 RESTful API endpoints
- 🐍 Built with Python and FastAPI

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

**⚠️ Important: Use a virtual environment to avoid dependency conflicts!**

1. Clone or navigate to the project directory:
```bash
cd "iptv BE"
```

2. Create a virtual environment (highly recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - On Windows:
   ```bash
   venv\Scripts\activate
   ```
   - On Linux/Mac:
   ```bash
   source venv/bin/activate
   ```

4. Upgrade pip (recommended):
```bash
python -m pip install --upgrade pip
```

5. Install dependencies:
```bash
pip install -r requirements.txt
```

### If you encounter dependency conflicts:

If you see dependency conflicts with packages like `google-cloud-storage` or `google-genai`, it's because you have them installed globally. The best solution is to use a virtual environment (steps 2-3 above) to isolate this project's dependencies.

Alternatively, you can install with `--no-deps` flag and manually install only what's needed, but using a virtual environment is strongly recommended.

## Usage

### Start the server:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3000
```

Or use the simple script:
```bash
python run.py
```

The server will start on `http://localhost:3000`

### Interactive API Documentation:

FastAPI provides automatic interactive API documentation:
- Swagger UI: `http://localhost:3000/docs`
- ReDoc: `http://localhost:3000/redoc`

## API Endpoints

### Health Check
```
GET /health
```

### Search Series
```
GET /api/search?q=<query>&type=<filter_type>
```

**Parameters:**
- `q` (required): Search query
- `type` (optional): Filter by type - `"movies"`, `"series"`, or `"all"` (default: `"all"`)

**Examples:**
```
GET /api/search?q=house
GET /api/search?q=house&type=series
GET /api/search?q=صراع العروش&type=all
```

### Get Popular Series
```
GET /api/series/popular
```

### Get Series Details
```
GET /api/series/by-url?url=<series_url>
```

**Parameters:**
- `url` (required): Full URL to the series page

**Example:**
```
GET /api/series/by-url?url=https://topcinema.media/series/house/
```

**Response:** Returns series details including all seasons and episodes

### Get Episode Video Links
```
GET /api/episodes/by-url?url=<episode_url>
```

**Parameters:**
- `url` (required): Full URL to the episode page

**Example:**
```
GET /api/episodes/by-url?url=https://topcinema.media/series/house-episode-1/
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": [...],
  "count": 10
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message"
}
```

## Important Notes

⚠️ **For Personal Testing Only**

This application is designed for personal testing purposes. Please note:

1. **Web Scraping**: The scraper may need adjustments based on the actual HTML structure of target sites. You may need to update selectors in `app/services/scraper.py`.

2. **Legal Considerations**: 
   - Ensure you have permission to scrape the target websites
   - Respect robots.txt and rate limits
   - This is for personal use only

3. **Site Structure Changes**: Websites frequently change their structure. You may need to update the CSS selectors in the scraper service if the target sites update their HTML.

4. **Rate Limiting**: Consider adding rate limiting to avoid overwhelming target servers.

## Customization

### Adding New Sources

To add new Arabic translation sites, update the `base_urls` dictionary in `app/services/scraper.py`:

```python
self.base_urls = {
    'faselhd': 'https://faselhd.com',
    'newsite': 'https://newsite.com',
}
```

### Adjusting Selectors

The CSS selectors in the scraper service may need to be adjusted based on the actual HTML structure of target sites. Inspect the target website's HTML and update the selectors accordingly.

## Troubleshooting

1. **No results found**: The website structure may have changed. Inspect the HTML and update selectors in `app/services/scraper.py`.

2. **Connection errors**: Check your internet connection and ensure the target sites are accessible.

3. **CORS issues**: The backend includes CORS middleware. If you're building a frontend, ensure it's configured correctly.

## Development

The project uses:
- FastAPI for the server framework
- BeautifulSoup4 for HTML parsing
- Requests for HTTP requests
- cachetools for caching
- Uvicorn as the ASGI server

## Deployment

See `RAILWAY_DEPLOYMENT.md` for detailed Railway deployment instructions.

## License

For personal testing purposes only.
