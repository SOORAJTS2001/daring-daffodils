#!/usr/bin/env python3
"""
WebSocket server to replace Firebase Realtime DB
Receives data from mobile page and broadcasts to browser extension
Also provides HTTP endpoint for browser extension compatibility
"""

import asyncio
import json
import logging
import websockets
from websockets.server import serve
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store connected clients and latest data
connected_clients = set()
latest_data = {}

class CORSHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP server for browser extension compatibility"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/data':
            # Send latest data to browser extension
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.end_headers()
            
            response_data = latest_data if latest_data else {}
            self.wfile.write(json.dumps(response_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass

def start_http_server():
    """Start HTTP server for browser extension compatibility"""
    http_host = "localhost"
    http_port = 8766
    
    server = HTTPServer((http_host, http_port), CORSHTTPRequestHandler)
    logger.info(f"HTTP server for extension compatibility: http://{http_host}:{http_port}/data")
    server.serve_forever()

async def register_client(websocket):
    """Register a new client connection"""
    connected_clients.add(websocket)
    logger.info(f"Client connected. Total clients: {len(connected_clients)}")
    
    # Send latest data to new client if available
    if latest_data:
        try:
            await websocket.send(json.dumps(latest_data))
        except websockets.exceptions.ConnectionClosed:
            pass

async def unregister_client(websocket):
    """Unregister a client connection"""
    connected_clients.discard(websocket)
    logger.info(f"Client disconnected. Total clients: {len(connected_clients)}")

async def broadcast_to_extensions(data):
    """Broadcast data to all connected browser extensions"""
    if not connected_clients:
        return
    
    message = json.dumps(data)
    disconnected = []
    
    for websocket in connected_clients.copy():
        try:
            await websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            disconnected.append(websocket)
    
    # Clean up disconnected clients
    for websocket in disconnected:
        connected_clients.discard(websocket)

async def handle_client(websocket, path):
    """Handle WebSocket client connections"""
    await register_client(websocket)
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Filter out empty or invalid data
                if not data or not isinstance(data, dict):
                    logger.debug("Ignoring empty or invalid data")
                    continue
                
                # Only accept coordinate data with required fields
                required_fields = ['x', 'y', 'type']
                if not all(field in data for field in required_fields):
                    logger.debug(f"Ignoring data without required fields: {data}")
                    continue
                
                # Store latest valid data
                global latest_data
                latest_data = data
                
                logger.info(f"Received valid data: {data}")
                
                # Broadcast to all other connected clients (browser extensions)
                await broadcast_to_extensions(data)
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await unregister_client(websocket)

async def main():
    """Start both WebSocket and HTTP servers"""
    websocket_host = "localhost"
    websocket_port = 8765
    
    logger.info(f"Starting WebSocket server on ws://{websocket_host}:{websocket_port}")
    logger.info("Starting HTTP server for browser extension compatibility...")
    
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # Start WebSocket server
    async with serve(handle_client, websocket_host, websocket_port):
        logger.info("Both servers are running...")
        logger.info("- WebSocket: For mobile app connection")
        logger.info("- HTTP: For browser extension compatibility")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
