import json
from js import WebSocket
from js import clearTimeout
from js import console
from js import document
from js import setTimeout
from js import window
from pyodide.ffi import create_proxy

ws_url = f"ws://{window.location.hostname}:{window.location.port}/ws"
console.log(f"Starting off with {ws_url}")
ws = WebSocket.new(ws_url)

# Initial touch coordinates (updated on touch start)
START_X = 0
START_Y = 0

# Browser viewport dimensions
BROWSER_HEIGHT = window.innerHeight
BROWSER_WIDTH = window.innerWidth

# Number of fingers currently touching the screen
NO_OF_FINGERS = 1

# Timer handle for detecting long-press gestures
PRESS_TIMER = None

# Flag indicating whether a drag gesture is currently active
IS_DRAGGING = False

# Flag indicating if a drag gesture was cancelled due to movement
DRAG_CANCELLED = False

# Duration (in milliseconds) to recognize a long-press before enabling drag
LONG_PRESS_TIME = 300  # ms

# Minimum movement (in pixels) to consider the gesture as a drag/scroll rather than a tap
MOVE_THRESHOLD = 5  # px


def create_toast(message="Hello from PyScript 🎉"):
    """
    Create an in-page toast notification element.

    Parameters:
        message (str): The text to display in the toast.

    Returns:
        JS DOM element: The created toast <div> element, appended to document.body.

    Notes:
        - Positioned fixed at the bottom center of the viewport.
        - Initially hidden (opacity 0); can be animated in/out using CSS transitions.
    """
    toast = document.createElement("div")
    toast.innerText = message
    toast.id = "toast"
    style = toast.style
    style.position = "fixed"
    style.bottom = "30px"
    style.left = "50%"
    style.transform = "translateX(-50%)"
    style.background = "#333"
    style.color = "white"
    style.padding = "14px 20px"
    style.borderRadius = "10px"
    style.fontSize = "16px"
    style.zIndex = 999999
    style.opacity = "0"
    style.transition = "opacity 0.5s ease, bottom 0.5s ease"

    document.body.appendChild(toast)  # ← this is missing
    return toast


async def sendCoords(x, y, click, fingers, type_):
    """
    Send touch coordinates and event information to the WebSocket server.

    Parameters:
        x (float): Normalized X-coordinate (relative to viewport width).
        y (float): Normalized Y-coordinate (relative to viewport height).
        click (bool): Whether the gesture is a click/tap.
        fingers (int): Number of fingers involved in the touch event.
        type_ (str): Type of gesture ('touch', 'drag', 'scroll').

    Returns:
        None

    Notes:
        - Converts click to 1/0 before sending.
        - Includes browser width and height in the payload.
    """
    payload = {
        "x": x,
        "y": y,
        "click": 1 if click else 0,
        "fingers": fingers,
        "browser_width": BROWSER_WIDTH,
        "browser_height": BROWSER_HEIGHT,
        "type": type_,
    }
    console.log(x, y, click, fingers, type_)
    console.log("Sending coordinates", payload)
    ws.send(json.dumps(payload))


async def touch_start(event):
    """
    Handle the start of a touch gesture on the touch area.

    Parameters:
        event (JS TouchEvent): The touchstart event from the browser.

    Effects:
        - Records initial touch coordinates (startX, startY).
        - Records number of fingers in contact.
        - Sets up a long-press timer to enable drag mode if the press lasts LONG_PRESS_TIME.
    """
    global START_X, START_Y, NO_OF_FINGERS, IS_DRAGGING, DRAG_CANCELLED, PRESS_TIMER
    touch = event.touches.item(0)  # ✅ JS method to access first touch
    START_X = touch.clientX
    START_Y = touch.clientY
    NO_OF_FINGERS = event.touches.length
    IS_DRAGGING = False
    DRAG_CANCELLED = False

    def enable_drag():
        global IS_DRAGGING
        if not DRAG_CANCELLED:
            IS_DRAGGING = True
            console.log("Long press → drag mode enabled")

    PRESS_TIMER = setTimeout(create_proxy(enable_drag), LONG_PRESS_TIME)


async def touch_move(event):
    """
    Handle movement during a touch gesture.

    Parameters:
        event (JS TouchEvent): The touchmove event from the browser.

    Effects:
        - Cancels drag initiation if movement exceeds MOVE_THRESHOLD before long-press.
    """
    global DRAG_CANCELLED
    touch = event.touches.item(0)
    dx = abs(touch.clientX - START_X)
    dy = abs(touch.clientY - START_Y)

    if not IS_DRAGGING and (dx > MOVE_THRESHOLD or dy > MOVE_THRESHOLD):
        DRAG_CANCELLED = True
        clearTimeout(PRESS_TIMER)


async def touch_end(event):
    """
    Handle the end of a touch gesture.

    Parameters:
        event (JS TouchEvent): The touchend event from the browser.

    Effects:
        - Clears the long-press timer.
        - Computes gesture type: 'touch', 'drag', or 'scroll'.
        - Normalizes end coordinates relative to browser dimensions.
        - Sends gesture data via sendCoords to the WebSocket server.
    """
    global PRESS_TIMER
    clearTimeout(PRESS_TIMER)

    # ✅ Access first changed touch via .item(0)
    touch = event.changedTouches.item(0)
    endX = touch.clientX
    endY = touch.clientY

    deltaX = (endX - START_X) / BROWSER_WIDTH
    deltaY = (endY - START_Y) / BROWSER_HEIGHT

    click = False
    if IS_DRAGGING:
        type_ = "drag"
    elif DRAG_CANCELLED:
        type_ = "scroll"
    else:
        type_ = "touch"
        click = True

    console.log(f"Type: {type_}, End coords: ({endX}, {endY})")
    await sendCoords(deltaX, deltaY, click, NO_OF_FINGERS, type_)


def update_textarea(text):
    """
    Update the content of the 'copiedText' textarea element.

    Parameters:
        text (str | None): Text to display in the textarea. Empty string if None.

    Effects:
        - Logs the update action.
        - Replaces the textarea content with the provided text.
    """
    console.log("Update textarea")
    doc = document.getElementById("copiedText")
    doc.value = text if text else ""


touch_area = document.getElementById("touchArea")
touch_area.addEventListener("touchstart", create_proxy(touch_start), {"passive": True})
touch_area.addEventListener("touchmove", create_proxy(touch_move), {"passive": True})
touch_area.addEventListener("touchend", create_proxy(touch_end), {"passive": True})


def onopen(event):  # <-- accept event arg
    """
    Handle WebSocket connection opening.

    Parameters:
        event (JS Event): The WebSocket 'open' event.

    Effects:
        - Logs connection success to the console.
    """
    console.log("Connection opened from page")


def onmessage(event):
    """
    Handle incoming WebSocket messages.

    Parameters:
        event (JS MessageEvent): The WebSocket 'message' event.

    Effects:
        - Parses JSON data from the server.
        - If 'copied_text' is present, updates the textarea using update_textarea().
    """
    data = json.loads(event.data)
    console.log(data)
    if data and data.get("copied_text"):
        update_textarea(data["copied_text"])


def onclose(event):
    """
    Handle WebSocket connection closure.

    Parameters:
        event (JS Event): The WebSocket 'close' event.

    Effects:
        - Logs connection closure to the console.
    """
    console.log("Connection closed")


# Add event listeners
ws.addEventListener("open", create_proxy(onopen))
ws.addEventListener("message", create_proxy(onmessage))
ws.addEventListener("close", create_proxy(onclose))
