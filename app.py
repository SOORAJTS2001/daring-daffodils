# ruff : noqa
import socket
from contextlib import asynccontextmanager

import qrcode
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel

PORT = 8000
HOST = "0.0.0.0"
RELOAD = False
console = Console()


def get_wifi_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def get_server_url():
    ip = get_wifi_ip()
    return f"http://{ip}:{PORT}"


def generate_qr_ascii(url: str) -> str:
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make()
    # Capture ASCII QR into a string
    import io, sys

    buf = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = buf
    qr.print_ascii(invert=True)
    sys.stdout = sys_stdout
    return buf.getvalue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    url = get_server_url()
    mobile_page_url = f"{url}/mobile_page"
    qr_ascii = generate_qr_ascii(mobile_page_url)

    qr_panel = Panel.fit(qr_ascii, title="Scan to Open", border_style="green")
    steps_panel = Panel.fit(
        "\n".join(
            [
                f"[bold cyan]1.[/bold cyan] Connect to the same Wi-Fi network",
                f"[bold cyan]2.[/bold cyan] Scan the QR code",
                f"[bold cyan]  [/bold cyan] Or [yellow]{mobile_page_url}[/yellow]",
                f"[bold cyan]3.[/bold cyan] Go to the scroll area and enjoy!",
            ]
        ),
        title="Steps",
        border_style="blue",
    )

    console.print(Columns([qr_panel, steps_panel]))
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/resource", StaticFiles(directory="mobile_page/"), name="resource")


# Store connected clients
connected_clients: list[WebSocket] = []


@app.get("/mobile_page")
async def get_mobile_page():
    with open("mobile_page/index.html") as f:
        return HTMLResponse(f.read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for client in connected_clients:
                if client != websocket:
                    await client.send_text(data)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


if __name__ == "__main__":
    uvicorn.run("app:app", host=HOST, port=PORT, reload=RELOAD)
