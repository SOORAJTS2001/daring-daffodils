# Daring Daffodils - Mobile Touch & Sensor Interface

A web-based mobile touchpad and sensor interface that captures touch gestures, device orientation, and motion data to control a desktop application via WebSocket.

## Features

- 🖱️ **Touch Interface**: Touch, drag, and scroll detection
- 🧭 **Device Orientation**: Gyroscope data (alpha, beta, gamma)
- 🏃 **Motion Sensors**: Accelerometer and rotation rate data
- 📡 **Real-time Communication**: WebSocket connection between mobile and desktop
- 🔒 **HTTPS Support**: Secure connection for device sensor access
- 📱 **Mobile Optimized**: Works on iOS and Android devices

## Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip install fastapi uvicorn cryptography

# Or using conda
conda install fastapi uvicorn cryptography
```

### 2. Generate SSL Certificates (Required for HTTPS)

#### Option A: Using the Python script (Recommended)

```bash
python generate_cert.py
```

This will create:
- `server.key` - Private key
- `server.crt` - SSL certificate

#### Option B: Using OpenSSL (if available)

```bash
openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

### 3. Start the Server

```bash
python app.py
```

The server will automatically detect SSL certificates and start in HTTPS mode.

### 4. Access the Interface

- **Local access**: `https://localhost:8000/mobile_page`
- **Mobile access**: `https://YOUR_IP:8000/mobile_page`

## Certificate Generation Details

### Why HTTPS is Required

Modern browsers require HTTPS for accessing device sensors like:
- DeviceOrientationEvent (gyroscope)
- DeviceMotionEvent (accelerometer)
- Other sensitive APIs

### Self-Signed Certificate Setup

The `generate_cert.py` script creates a self-signed certificate with:

```python
# Key specifications
- RSA 2048-bit encryption
- Valid for 365 days
- Subject Alternative Names for localhost and IP addresses
- SHA256 signature algorithm
```

### Certificate Files

- **server.key**: Private key file (keep secure)
- **server.crt**: Public certificate file
- **Files are valid for**: 1 year from generation date

### Browser Security Warnings

When using self-signed certificates, browsers will show security warnings:

1. **Chrome/Edge**: Click "Advanced" → "Proceed to localhost (unsafe)"
2. **Firefox**: Click "Advanced" → "Accept the Risk and Continue"
3. **Safari**: Click "Show Details" → "Visit this website"

## Network Setup for Mobile Access

### 1. Find Your Computer's IP Address

**Windows:**
```powershell
ipconfig | findstr "IPv4"
```

**macOS/Linux:**
```bash
ifconfig | grep "inet "
```

### 2. Configure Firewall

**Windows Firewall:**
```powershell
# Allow inbound connections on port 8000
New-NetFirewallRule -DisplayName "Python HTTPS Server" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

**macOS:**
```bash
# System Preferences → Security & Privacy → Firewall → Options
# Add Python to allowed applications
```

### 3. Network Requirements

- Both devices must be on the same WiFi network
- Port 8000 must be accessible
- Router should allow device-to-device communication

## Project Structure

```
daring-daffodils/
├── app.py                          # FastAPI server with WebSocket
├── generate_cert.py                # SSL certificate generator
├── server.key                      # SSL private key (generated)
├── server.crt                      # SSL certificate (generated)
├── mobile_page/
│   ├── index.html                  # Web interface
│   └── py-scripts/
│       └── mobile_page.py          # PyScript client code
└── README.md                       # This file
```

## API Reference

### WebSocket Messages

The application sends JSON messages over WebSocket with different types:

#### Touch Events
```json
{
  "type": "touch|drag|scroll",
  "x": 0.5,
  "y": 0.3,
  "click": 1,
  "fingers": 1,
  "browser_width": 375,
  "browser_height": 667
}
```

#### Device Orientation
```json
{
  "type": "orientation",
  "alpha": 45.2,    // Z-axis rotation (compass)
  "beta": 10.5,     // X-axis rotation (front-back tilt)
  "gamma": -5.3,    // Y-axis rotation (left-right tilt)
  "browser_width": 375,
  "browser_height": 667
}
```

#### Device Motion
```json
{
  "type": "motion",
  "acceleration": {
    "x": 0.1,        // m/s²
    "y": 0.2,
    "z": 9.8
  },
  "rotation_rate": {
    "alpha": 1.2,    // degrees/second
    "beta": 0.5,
    "gamma": -0.8
  },
  "browser_width": 375,
  "browser_height": 667
}
```

## Troubleshooting

### Common Issues

1. **"Device sensors not working"**
   - Ensure you're using HTTPS
   - Check if using a real mobile device (not desktop browser)
   - Grant permissions when prompted (iOS)

2. **"Cannot connect to server"**
   - Verify both devices are on same WiFi
   - Check firewall settings
   - Ensure port 8000 is not blocked

3. **"SSL Certificate errors"**
   - Regenerate certificates with `python generate_cert.py`
   - Accept security warnings in browser
   - Clear browser cache if persistent

4. **"WebSocket connection failed"**
   - Check server logs for errors
   - Verify WebSocket URL in browser console
   - Ensure no proxy blocking connections

### Debug Mode

Enable debug logging by checking browser console:
- Open Developer Tools (F12)
- Check Console tab for sensor events
- Look for WebSocket connection messages

### Server Logs

The FastAPI server provides detailed logs:
- WebSocket connections
- Data type identification
- Client connect/disconnect events

## Development

### Adding New Sensor Data

1. Add event listener in `mobile_page.py`:
```python
async def new_sensor_handler(event):
    # Process sensor data
    await send_new_data(processed_data)

window.addEventListener("newsensor", create_proxy(new_sensor_handler))
```

2. Add data handler in `app.py`:
```python
if data_type == "newsensor":
    print(f"New sensor data: {parsed_data}")
```

### Custom Gestures

Modify the touch event handlers in `mobile_page.py` to add:
- Multi-finger gestures
- Swipe detection
- Pinch/zoom recognition
- Custom timing patterns

## Security Notes

⚠️ **Important Security Considerations**

- Self-signed certificates should only be used for development
- Never use in production without proper SSL certificates
- Keep `server.key` file secure and never commit to version control
- Consider using Let's Encrypt for production deployments

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on both desktop and mobile
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section above
- Review browser console for error messages
- Verify network connectivity between devices
- Ensure certificates are properly generated
