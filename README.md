# WebSocket Mouse Controller

This project implements a WebSocket-based alternative to Firebase Realtime Database for controlling a browser cursor from a mobile PyScript app.

## Architecture

```
PyScript Mobile App → WebSocket Server → Browser Extension
```

1. **Mobile Page** (`mobile_page/`): PyScript app that sends touch/gesture data
2. **WebSocket Server** (`websocket_server.py`): Python server that relays data
3. **Browser Extension** (`browser_extension/`): Receives data and controls cursor

## Setup Instructions

### 1. Start the WebSocket Server

Run the WebSocket server that will relay data between your mobile app and browser extension:

**Option A: Using the batch file (Windows)**
```bash
./start_websocket_server.bat
```

**Option B: Manual setup**
```bash
pip install -r requirements.txt
python websocket_server.py
```

The server will start on `ws://localhost:8765`

### 2. Start the Mobile Page Server

⚠️ **Important**: PyScript requires a web server to avoid CORS issues. Don't open the HTML file directly!

**Option A: Using the batch file (Windows)**
```bash
./start_mobile_server.bat
```

**Option B: Manual setup**
```bash
python start_mobile_server.py
```

The mobile page will be available at `http://localhost:8000/index.html`

### 3. Load the Browser Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select the `browser_extension` folder
4. The extension will now use WebSocket for real-time communication

### 4. Access the Mobile Page

1. Make sure the mobile page server is running (step 2)
2. Open `http://localhost:8000/index.html` in your browser
3. The page will automatically try to connect to the WebSocket server
4. Touch gestures will be sent via WebSocket to the browser extension

## CORS Error Solution

If you see this error:
```
Access to fetch at 'file:///.../main.py' from origin 'null' has been blocked by CORS policy
```

**Solution**: Use the web server instead of opening HTML files directly:
- ✅ **Correct**: `http://localhost:8000/index.html` 
- ❌ **Incorrect**: `file:///path/to/index.html`

## Features

### WebSocket Benefits over Firebase
- **Real-time communication**: No polling delays
- **Lower latency**: Direct connection between components
- **Offline capable**: Works without internet connection
- **No external dependencies**: Self-contained solution
- **Better error handling**: Immediate connection status feedback

### Fallback Support
Both the mobile app and browser extension include Firebase fallback:
- If WebSocket connection fails, automatically falls back to Firebase
- Seamless switching between connection methods
- Use `toggleConnectionMode()` in browser console to switch manually

### Supported Gestures
- **Touch**: Single finger tap (triggers clicks)
- **Drag**: Single finger drag (selects and copies text)
- **Scroll**: Multi-finger gestures (scrolls the page)

## Configuration

### WebSocket Server
- **Host**: `localhost` (change in `websocket_server.py`)
- **Port**: `8765` (change in both `websocket_server.py` and `main.py`/`websocket_app.js`)

### Switching Between WebSocket and Firebase
In the browser console, you can toggle connection modes:
```javascript
toggleConnectionMode(); // Switches between WebSocket and Firebase
```

## Troubleshooting

### WebSocket Connection Issues
1. Ensure the WebSocket server is running on port 8765
2. Check that no firewall is blocking the connection
3. Verify the WebSocket URL matches in all files

### Extension Not Working
1. Check browser console for errors
2. Verify the extension is loaded and active
3. Ensure content script permissions are granted

### Mobile App Connection Problems
1. Open browser dev tools to see WebSocket connection status
2. Check if falling back to Firebase is working
3. Verify PyScript is loading properly

## File Structure

```
├── websocket_server.py          # WebSocket relay server
├── start_websocket_server.bat   # Windows startup script for WebSocket
├── start_mobile_server.py       # HTTP server for mobile page
├── start_mobile_server.bat      # Windows startup script for mobile server
├── requirements.txt             # Python dependencies
├── mobile_page/
│   ├── index.html              # PyScript mobile interface
│   └── main.py                 # Touch handling with WebSocket support
└── browser_extension/
    ├── manifest.json           # Extension configuration
    ├── background.js           # Extension background script
    ├── websocket_app.js        # WebSocket content script
    └── firebase_app.js         # Original Firebase script (backup)
```

## Development Notes

- The WebSocket server handles multiple client connections
- Data is broadcasted to all connected browser extensions
- Connection reconnection is automatic with 3-second delays
- All coordinate data includes touch type, position, and browser dimensions
