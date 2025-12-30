# Step 3: Configure Android Device for Proxy

## Part 1: Find Your Computer's IP Address

### On Windows:

1. **Open Command Prompt** (Press `Win + R`, type `cmd`, press Enter)

2. **Run this command**:
   ```bash
   ipconfig
   ```

3. **Look for "IPv4 Address"** under your active network adapter:
   - Usually under "Wireless LAN adapter Wi-Fi" or "Ethernet adapter"
   - Example: `192.168.1.100` or `192.168.0.50`
   - **Write this IP down** - you'll need it!

### Alternative: Check Network Settings

1. Open **Settings** → **Network & Internet** → **Wi-Fi**
2. Click on your connected network
3. Look for "IPv4 address"

---

## Part 2: Configure Proxy on Android Device

### Method 1: Wi-Fi Settings (Recommended)

1. **Open Settings** on your Android device

2. **Go to Wi-Fi** (or Network & Internet → Wi-Fi)

3. **Long press** on your connected Wi-Fi network
   - Or tap the network name, then tap the gear icon ⚙️

4. **Tap "Modify"** or "Edit" (may vary by Android version)

5. **Scroll down** and expand **"Advanced options"** or **"Proxy"**

6. **Set Proxy to "Manual"**

7. **Enter the following**:
   - **Proxy hostname**: `192.168.1.100` (use YOUR computer's IP from Part 1)
   - **Proxy port**: `8080`
   - **Bypass proxy for**: (leave empty, or add: `localhost,127.0.0.1`)

8. **Tap "Save"** or the checkmark ✓

### Method 2: Using Android 10+ (Quick Settings)

1. **Long press** on Wi-Fi icon in quick settings
2. Tap on your network name
3. Tap **"Advanced"** or **"Modify network"**
4. Change **"Proxy"** to **"Manual"**
5. Enter your computer's IP and port `8080`
6. **Save**

---

## Part 3: Install mitmproxy Certificate on Android

### Step 1: Download Certificate

1. **Make sure mitmproxy is running** (run `run_mitmweb.bat`)

2. **On your Android device**, open a web browser (Chrome, Firefox, etc.)

3. **Navigate to**: `http://mitm.it`

4. **You'll see a page with different platforms** - tap **"Android"**

5. **Download the certificate**:
   - File will be named something like: `mitmproxy-ca-cert.cer`
   - Or it may download automatically

### Step 2: Install Certificate

#### For Android 7.0 and below:
1. Open **Settings** → **Security**
2. Tap **"Install from storage"** or **"Install certificates"**
3. Navigate to **Downloads** folder
4. Select the `mitmproxy-ca-cert.cer` file
5. Give it a name (e.g., "mitmproxy")
6. Tap **"OK"**

#### For Android 8.0 and above:
1. Open **Settings** → **Security** → **Encryption & credentials**
2. Tap **"Install a certificate"**
3. Select **"CA certificate"**
4. Tap **"Install anyway"** (if warned)
5. Navigate to **Downloads** folder
6. Select the `mitmproxy-ca-cert.cer` file
7. Give it a name (e.g., "mitmproxy")
8. Tap **"OK"**

#### For Android 14+ (May require different steps):
1. Open **Settings** → **Security & privacy** → **More security settings**
2. Tap **"Encryption & credentials"**
3. Tap **"Install a certificate"**
4. Select **"CA certificate"**
5. Navigate to Downloads and select the certificate

### Step 3: Verify Certificate is Installed

1. Go to **Settings** → **Security** → **Encryption & credentials** → **Trusted credentials**
2. Look for **"mitmproxy"** or **"user"** tab
3. You should see the certificate listed

---

## Part 4: Test the Connection

1. **On your Android device**, open a web browser

2. **Visit any website** (e.g., google.com)

3. **Check mitmweb** (http://127.0.0.1:8081) - you should see the request appear!

4. **If you see the request**, the proxy is working! ✅

5. **If you don't see anything**:
   - Make sure mitmproxy is running
   - Check that the IP address is correct
   - Make sure both devices are on the same Wi-Fi network
   - Try disabling and re-enabling the proxy

---

## Troubleshooting

### "Certificate not trusted" error:
- Make sure you installed the certificate as a **CA certificate**, not a user certificate
- Try uninstalling and reinstalling the certificate
- Some apps may still not trust the certificate (this is normal for some apps)

### "Can't connect" or "No internet":
- Make sure mitmproxy is running on your computer
- Check that the IP address is correct
- Make sure both devices are on the same Wi-Fi network
- Try turning Wi-Fi off and on again on Android

### "Proxy not working":
- Double-check the proxy settings (IP and port 8080)
- Make sure mitmproxy is listening on port 8080
- Check Windows Firewall - it might be blocking port 8080

### Can't see requests in mitmweb:
- Make sure you're using the APK (not just browser)
- Some apps use certificate pinning and won't work with proxy
- Try using ADB logcat as an alternative (see `ADB_LOGCAT_SETUP.md`)

---

## Next Steps

Once the proxy is configured:
1. ✅ Open the APK on your device
2. ✅ Navigate to video playback
3. ✅ Click play on a movie/series
4. ✅ Check mitmweb (http://127.0.0.1:8081) for URLs

