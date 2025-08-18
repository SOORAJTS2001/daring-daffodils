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

# The port on which the FastAPI server will listen
PORT = 8000

# The host address for the server
# "0.0.0.0" makes the server accessible from any network interface
HOST = "0.0.0.0"

# Whether to enable auto-reload of the server on code changes
# Useful in development; should be False in production
RELOAD = False

# Rich console object for styled terminal output
# Used to print QR codes, instructions, and panels in a readable format
console = Console()


def get_wifi_ip():
    """
    Retrieve the local IP address of the machine on the current Wi-Fi/network.

    Returns:
        str: The local IP address (e.g., '192.168.1.10').

    Notes:
        - Uses a temporary UDP socket to determine the outbound interface.
        - No actual network traffic is sent to the remote host (8.8.8.8).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def get_server_url():
    """
    Construct the full HTTP URL of the server using the local Wi-Fi IP and port.

    Returns:
        str: URL in the format "http://<local_ip>:<port>".

    Notes:
        - Relies on get_wifi_ip() to obtain the host IP.
    """
    ip = get_wifi_ip()
    return f"http://{ip}:{PORT}"


def generate_qr_ascii(url: str) -> str:
    """
    Generate an ASCII representation of a QR code for a given URL.

    Parameters:
        url (str): The URL or text to encode in the QR code.

    Returns:
        str: QR code rendered as ASCII characters.

    Notes:
        - Uses the qrcode library.
        - The QR code is inverted for better visibility in terminal output.
    """
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make()
    # Capture ASCII QR into a string
    import io
    import sys

    buf = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = buf
    qr.print_ascii(invert=True)
    sys.stdout = sys_stdout
    return buf.getvalue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for displaying connection instructions.

    Parameters:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None

    Effects:
        - Prints an ASCII QR code to the terminal for connecting a mobile device.
        - Prints step-by-step instructions in the terminal using rich panels.
        - Runs once when the application starts and cleans up after shutdown.
    """
    url = get_server_url()
    mobile_page_url = f"{url}/mobile_page"
    qr_ascii = generate_qr_ascii(mobile_page_url)

    qr_panel = Panel.fit(qr_ascii, title="Scan to Open", border_style="green")
    steps_panel = Panel.fit(
        "\n".join(
            [
                "[bold cyan]1.[/bold cyan] Connect to the same Wi-Fi network",
                "[bold cyan]2.[/bold cyan] Scan the QR code",
                f"[bold cyan]  [/bold cyan] Or [yellow]{mobile_page_url}[/yellow]",
                "[bold cyan]3.[/bold cyan] That's it, Now do your Misclick!",
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
    """
    Serve the main HTML page for mobile clients.

    Returns:
        HTMLResponse: The contents of "mobile_page/index.html" as an HTML response.

    Notes:
        - The HTML page allows the mobile device to interact with the WebSocket server.
    """
    with open("mobile_page/index.html") as f:
        return HTMLResponse(f.read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint to broadcast messages between connected clients.

    Parameters:
        websocket (WebSocket): The incoming WebSocket connection.

    Effects:
        - Accepts the WebSocket connection and adds it to the connected clients list.
        - Receives messages from one client and forwards them to all other connected clients.
        - Removes the client from the list when it disconnects.
    """
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
