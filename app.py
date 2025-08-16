# ruff : noqa

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="mobile_page"), name="static")

# Store connected clients
connected_clients: list[WebSocket] = []


@app.get("/mobile_page")
async def get_page2():
    with open("mobile_page/index.html") as f:
        return HTMLResponse(f.read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"New WebSocket connection. Total clients: {len(connected_clients)}")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data: {data}")

            # Try to parse and identify the data type
            try:
                parsed_data = json.loads(data)
                data_type = parsed_data.get("type", "unknown")
                print(f"Data type: {data_type}")
            except json.JSONDecodeError:
                print("Failed to parse JSON data")

            for client in connected_clients:
                if client != websocket:
                    await client.send_text(data)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


if __name__ == "__main__":
    # HTTPS configuration
    ssl_config = {"ssl_keyfile": "server.key", "ssl_certfile": "server.crt"}

    print("🔒 Starting HTTPS server...")
    print("📍 Access your app at: https://localhost:8000/mobile_page")
    print("🚨 You'll see a security warning - click 'Advanced' and 'Proceed to localhost (unsafe)'")

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, ssl_keyfile="server.key", ssl_certfile="server.crt")
