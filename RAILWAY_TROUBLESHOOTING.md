# Railway Deployment Troubleshooting

## "No start command was found" Error

If you see this error, Railway doesn't know how to start your application. Here's how to fix it:

### Solution 1: Set Start Command in Railway Dashboard

1. Go to your Railway project: https://railway.app
2. Click on your service
3. Go to the **"Settings"** tab
4. Scroll down to the **"Deploy"** section
5. Find **"Start Command"** field
6. Enter: `python run.py`
7. Click **"Save"** or **"Deploy"**

### Solution 2: Verify Procfile

The project includes a `Procfile` with:
```
web: python run.py
```

Make sure this file is in the root directory and committed to Git.

### Solution 3: Check railway.json

The project includes `railway.json` with:
```json
{
  "deploy": {
    "startCommand": "python run.py"
  }
}
```

### Solution 4: Manual Start Command via Railway CLI

If using Railway CLI:
```bash
railway variables set START_COMMAND="python run.py"
```

## Other Common Issues

### Port Binding Errors

Railway automatically sets the `PORT` environment variable. The `run.py` file already uses it:
```python
port = int(os.environ.get("PORT", 3000))
```

If you see port errors, make sure you're using `0.0.0.0` as the host (already configured).

### Dependencies Not Found

Make sure `requirements.txt` is in the root directory and includes all dependencies:
- fastapi
- uvicorn[standard]
- requests
- beautifulsoup4
- lxml
- etc.

### Build Failures

1. Check Railway build logs for specific errors
2. Ensure Python version is compatible (3.8+)
3. Check that all dependencies in `requirements.txt` are valid

### Application Not Starting

1. Check Railway logs: Service → "Deployments" → Click on deployment → "View Logs"
2. Verify the start command is correct
3. Check that `run.py` exists and is executable
4. Ensure `app/main.py` exists and is valid

## Quick Fix Checklist

- [ ] Start command set in Railway dashboard: `python run.py`
- [ ] `Procfile` exists in root: `web: python run.py`
- [ ] `railway.json` exists with start command
- [ ] `requirements.txt` is in root directory
- [ ] `run.py` exists and is valid
- [ ] `app/main.py` exists and is valid
- [ ] All files committed to Git
- [ ] Railway service is connected to GitHub repo

## Still Having Issues?

1. Check Railway logs for specific error messages
2. Verify all files are pushed to GitHub
3. Try redeploying: Service → "Deployments" → "Redeploy"
4. Check Railway status page: https://status.railway.app


