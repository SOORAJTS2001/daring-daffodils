#!/usr/bin/env python3
"""
Simple HTTP server to serve the mobile page
Solves CORS issues when loading PyScript files
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

# Configuration
PORT = 8000
HOST = "localhost"
MOBILE_PAGE_DIR = "mobile_page"

def start_server():
    """Start HTTP server in the mobile_page directory"""
    
    # Change to mobile_page directory
    mobile_page_path = Path(__file__).parent / MOBILE_PAGE_DIR
    
    if not mobile_page_path.exists():
        print(f"Error: {MOBILE_PAGE_DIR} directory not found!")
        return
    
    os.chdir(mobile_page_path)
    
    # Create HTTP server
    handler = http.server.SimpleHTTPRequestHandler
    
    # Add CORS headers to allow cross-origin requests
    class CORSHTTPRequestHandler(handler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()
    
    with socketserver.TCPServer((HOST, PORT), CORSHTTPRequestHandler) as httpd:
        url = f"http://{HOST}:{PORT}"
        print(f"🚀 Mobile page server starting at: {url}")
        print(f"📁 Serving files from: {mobile_page_path.absolute()}")
        print(f"🌐 Open in browser: {url}/index.html")
        print("📱 Use this URL to access your PyScript mobile app")
        print("\n💡 Tip: Keep this server running while testing your app")
        print("⏹️  Press Ctrl+C to stop the server\n")
        
        # Optionally open browser automatically
        try:
            webbrowser.open(f"{url}/index.html")
            print("🔗 Opening browser automatically...")
        except:
            print("🔗 Please open the URL manually in your browser")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")

if __name__ == "__main__":
    start_server()
