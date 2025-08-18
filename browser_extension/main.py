import json
import random
import traceback

# JS objects and APIs exposed to Pyodide
from js import WebSocket
from js import console
from js import document
from js import window
from pyodide.ffi import create_proxy

# Local utility imports
from utils import create_fake_cursor
from utils import fetch_easter_eggs
from utils import get_and_highlight_text_in_rect
from utils import move_and_maybe_click
from utils import show_toast
from utils import trigger_click

# Connect to backend WebSocket server (browser <-> Python extension bridge)
ws = WebSocket.new("ws://localhost:8000/ws")

# Browser/environment metadata
BROWSER_HEIGHT = window.innerHeight
BROWSER_WIDTH = window.innerWidth
EASTER_EGGS_COORDINATES = fetch_easter_eggs()  # pre-scanned Easter egg anchor points

# State & timers
INACTIVITY_TIMER = None
WANDERING = False
WANDERING_PROXY = None
LAST_X = None
LAST_Y = None
LAST_CLICK = 0
LAST_SCROLL_VALUE = None
NEXT_SCROLL_VALUE = 0

# Behavior constants
WANDERING_STEP_X = 100
WANDERING_STEP_Y = 100
WANDERING_STEP_TIME = 500  # ms between cursor hops
INACTIVITY_TIME = 30000  # 1 minute idle → wander mode kicks in
WANDERING_TIME_MAX_LIMIT = 60000  # wander lasts max 60s
WANDERING_TIME_MIN_LIMIT = 10000  # wander lasts min 10s
PROBABILITY_FOR_EASTER_EGG = 0.3  # 10% chance to snap to Easter egg location
PROBABILITY_FOR_SHADOW_MODE = 0.3  # 30% chance of toggling cursor visibility


def random_mode(modes: list):
    """Pick a random subset of modes to activate."""
    k = random.randint(1, len(modes))  # pick at least one
    return random.sample(modes, k)


def start_wandering():
    """
    Trigger wandering mode when no user activity/WebSocket events occur.

    The fake cursor moves around randomly across the screen, with special
    'modes':
      - 'wandering': random movement
      - 'rage': exaggerated fast jumps
      - 'shadow': cursor flickers (visible/hidden)
    It may also click on clickable elements or snap to Easter egg positions.
    """
    global WANDERING, WANDERING_PROXY
    if WANDERING:
        return  # already running
    WANDERING = True
    console.log("⚠️ No WebSocket messages — starting wandering mode")

    # Randomize which "flavors" of wandering get activated
    modes = ["wandering", "rage", "shadow"]
    mode = random_mode(modes)
    show_toast(f"You have activated {', '.join(mode)} mode")

    def wander_step():
        """One movement step of wandering mode."""
        if not WANDERING:
            return  # stop if wandering was canceled

        # Pick a random new location within screen bounds
        x = random.randint(0, BROWSER_WIDTH - 50)
        y = random.randint(0, BROWSER_HEIGHT - 50)

        # Occasionally snap to an Easter egg anchor
        if EASTER_EGGS_COORDINATES and random.random() < PROBABILITY_FOR_EASTER_EGG:
            dx, dy = random.choice(EASTER_EGGS_COORDINATES)
        else:
            dx, dy = x, y

        # Shadow mode: flicker cursor visibility
        if "shadow" in mode and random.random() < PROBABILITY_FOR_SHADOW_MODE:
            console.log("Shadow enabled")
            fake_cursor.style.visibility = "visible" if fake_cursor.style.visibility == "hidden" else "hidden"

        # Rage mode: amplify movement distance
        if "rage" in mode:
            console.log("Rage enabled")
            dx *= 2
            dy *= 2

        # Move fake cursor
        fake_cursor.style.left = f"{dx}px"
        fake_cursor.style.top = f"{dy}px"

        # Try clicking element under cursor (if clickable)
        el = document.elementFromPoint(dx, dy)
        if el:
            tag = el.tagName.lower()
            clickable = (
                tag in ["button", "a", "input", "select"]
                or el.onclick
                or window.getComputedStyle(el).cursor == "pointer"
            )
            if clickable:
                console.log("Clicking:", el)
                trigger_click(el)

        # Schedule next step
        window.setTimeout(WANDERING_PROXY, WANDERING_STEP_TIME)

    # Wrap wander_step for JS callbacks
    WANDERING_PROXY = create_proxy(wander_step)
    wander_step()  # kick it off immediately

    def stop_wandering():
        """Stop wandering after timeout."""
        global WANDERING
        WANDERING = False
        fake_cursor.style.visibility = "visible"  # reset cursor visibility
        console.log("✅ Wandering mode ended — control back to user")

    # Stop wandering after a random duration (10–60s)
    duration = random.randint(WANDERING_TIME_MIN_LIMIT, WANDERING_TIME_MAX_LIMIT)
    window.setTimeout(create_proxy(stop_wandering), duration)
    fake_cursor.style.visibility = "visible"


def reset_inactivity_timer():
    """Reset inactivity countdown — triggers wandering mode after idle time."""
    global INACTIVITY_TIMER
    if INACTIVITY_TIMER is not None:
        window.clearTimeout(INACTIVITY_TIMER)

    def on_timeout(*args):
        start_wandering()

    INACTIVITY_TIMER = window.setTimeout(create_proxy(on_timeout), INACTIVITY_TIME)
    console.log("finished_all")  # debug marker


def send_text(text: str):
    """Send highlighted/copied text to the server over WebSocket."""
    console.log("Sending copied text")
    ws.send(json.dumps({"copied_text": text}))


def drag_and_copy(cursor, offset_x, offset_y):  # noqa: ARG001
    """
    Drag the fake cursor, highlight text along the drag rectangle, and send it.
    """
    # Current cursor coordinates
    current_x = float(cursor.style.left.replace("px", "") or 0)
    current_y = float(cursor.style.top.replace("px", "") or 0)

    # Apply movement offsets
    new_x = current_x + offset_x
    new_y = current_y + offset_y

    # Clamp inside screen
    max_x = window.innerWidth - cursor.offsetWidth
    max_y = window.innerHeight - cursor.offsetHeight
    new_x = max(0, min(new_x, max_x))
    new_y = max(0, min(new_y, max_y))

    # Update fake cursor position
    cursor.style.left = f"{new_x}px"
    cursor.style.top = f"{new_y}px"

    # Highlight & copy text inside drag rectangle
    text = get_and_highlight_text_in_rect(current_x, current_y, new_x, new_y)
    send_text(text)

    console.log(new_x, new_y)


def fetch_coordinates(data_x: float, data_y: float, fingers: int, data_type: str, click: int):
    """
    Handle new coordinate data from the WebSocket (touch/mouse gestures).
    Decides whether to move, click, drag, or scroll.
    """
    global LAST_X, LAST_Y, LAST_CLICK, NEXT_SCROLL_VALUE, LAST_SCROLL_VALUE

    # Scale normalized coordinates into pixel values
    data_x = data_x * BROWSER_WIDTH
    data_y = data_y * BROWSER_HEIGHT

    try:
        console.log("New Data", data_x, data_y, fingers, data_type, click)
        if isinstance(data_x, (int, float)) and isinstance(data_y, (int, float)):
            if fingers == 1:
                # Single-finger gestures
                if data_type in {"scroll", "touch"} and (data_x != LAST_X or data_y != LAST_Y or click != LAST_CLICK):
                    move_and_maybe_click(fake_cursor, -data_x, -data_y, bool(click))
                    LAST_X, LAST_Y, LAST_CLICK = data_x, data_y, click

                elif data_type == "drag" and (data_x != LAST_X or data_y != LAST_Y or click != LAST_CLICK):
                    drag_and_copy(fake_cursor, data_x, data_y)
                    console.log(f"from [{LAST_X},{LAST_Y}] to [{data_x},{data_y}]")
                    LAST_X, LAST_Y, LAST_CLICK = data_x, data_y, click
            else:
                # Multi-finger gestures → scrolling
                if data_y != 0:
                    NEXT_SCROLL_VALUE = window.scrollY + data_y
                    console.log(f"scroll to {NEXT_SCROLL_VALUE}")
                    window.scrollTo(0, NEXT_SCROLL_VALUE)

    except Exception as err:
        console.error("Error fetching coordinates:", str(err))
        console.error(traceback.format_exc())


# Start idle tracking immediately
reset_inactivity_timer()


# WebSocket event handlers
def onopen(event):  # noqa: ARG001
    """
    When connection is established
    """
    console.log("✅ Connection opened from extension")


def onmessage(event):  # noqa: ARG001
    """
    When message is received
    """
    data = json.loads(event.data)
    console.log("Received coordinates", data)
    reset_inactivity_timer()  # reset idle timer on activity
    fetch_coordinates(data["x"], data["y"], data["fingers"], data["type"], data["click"])


def onclose(event):  # noqa: ARG001
    """
    When connection is closed
    """
    console.log("❌ Connection closed")


# Initialize fake cursor element
fake_cursor = create_fake_cursor()

# Attach WebSocket event listeners
ws.addEventListener("open", create_proxy(onopen))
ws.addEventListener("message", create_proxy(onmessage))
ws.addEventListener("close", create_proxy(onclose))
