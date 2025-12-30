# mitmproxy Setup Guide for APK Network Analysis

## Installation (Recommended: Use Virtual Environment)

**⚠️ Important**: mitmproxy has dependency conflicts with FastAPI. Use a virtual environment to avoid issues.

### Option 1: Use Setup Script (Windows)

1. **Run the setup script**:
   ```bash
   setup_mitmproxy_env.bat
   ```

2. **Start mitmproxy**:
   ```bash
   run_mitmproxy.bat
   ```
   Or for web UI:
   ```bash
   run_mitmweb.bat
   ```

### Option 2: Manual Virtual Environment Setup

1. **Create virtual environment**:
   ```bash
   python -m venv mitmproxy_env
   ```

2. **Activate it**:
   - Windows: `mitmproxy_env\Scripts\activate.bat`
   - Linux/Mac: `source mitmproxy_env/bin/activate`

3. **Install mitmproxy**:
   ```bash
   pip install --upgrade pip
   pip install mitmproxy
   ```

### Option 3: Direct Installation (Not Recommended)

If you want to install directly (may cause dependency conflicts):
```bash
pip install mitmproxy
```

## Setup on Android Device

1. **Start mitmproxy**:
   ```bash
   mitmproxy -p 8080
   ```

2. **Configure Android device to use proxy**:
   - Settings → Wi-Fi → Long press your network → Modify
   - Proxy: Manual
   - Host: Your computer's IP (e.g., 192.168.1.100)
   - Port: 8080

3. **Install mitmproxy certificate on Android**:
   - Open browser on device: http://mitm.it
   - Download Android certificate
   - Install it: Settings → Security → Install from storage

## Usage

1. **Start mitmproxy**:
   ```bash
   mitmproxy -p 8080
   ```

2. **Use the APK** - All network requests will appear in mitmproxy

3. **Export URLs**:
   - Press `e` to export flow
   - Or use `mitmdump` to save to file:
     ```bash
     mitmdump -p 8080 -w traffic.mitm
     ```

## Alternative: mitmweb (Web UI)

```bash
mitmweb -p 8080
```
Then open http://127.0.0.1:8081 in your browser for a web interface.


