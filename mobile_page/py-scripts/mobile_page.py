# ruff: noqa
import json
from js import WebSocket, console, document, window
from pyodide.ffi import create_proxy

# ----------------------------
# Setup
# ----------------------------
# Use WSS (secure websocket) if page is loaded over HTTPS, otherwise use WS
protocol = "wss" if window.location.protocol == "https:" else "ws"
ws_url = f"{protocol}://{window.location.hostname}:{window.location.port}/ws"
console.log("WS URL:", ws_url)
ws = WebSocket.new(ws_url)

browser_height = window.innerHeight
browser_width = window.innerWidth

# Touch state
startX = 0
startY = 0
fingers = 1
pressTimer = None
isDragging = False
dragCancelled = False
LONG_PRESS_TIME = 300  # ms
MOVE_THRESHOLD = 5  # px

# Throttle (ms) for sensor -> WS
THROTTLE_MS = 50
last_send_orientation = 0.0
last_send_motion = 0.0


# ----------------------------
# WS helpers (sync)
# ----------------------------
def send_coords(x, y, click, fingers, type_):
    payload = {
        "x": x,
        "y": y,
        "click": 1 if click else 0,
        "fingers": fingers,
        "browser_width": browser_width,
        "browser_height": browser_height,
        "type": type_,
    }
    console.log("Sending coordinates", payload)
    ws.send(json.dumps(payload))


def send_orientation(alpha, beta, gamma):
    payload = {
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "type": "orientation",
        "browser_width": browser_width,
        "browser_height": browser_height,
    }
    ws.send(json.dumps(payload))


def send_motion(ax, ay, az, ra, rb, rg):
    payload = {
        "acceleration": {"x": ax, "y": ay, "z": az},
        "rotation_rate": {"alpha": ra, "beta": rb, "gamma": rg},
        "type": "motion",
        "browser_width": browser_width,
        "browser_height": browser_height,
    }
    ws.send(json.dumps(payload))


# ----------------------------
# UI helpers
# ----------------------------
def set_text(id_, text):
    el = document.getElementById(id_)
    if el is not None:
        el.textContent = text


def update_textarea(text):
    doc = document.getElementById("copiedText")
    if doc is not None:
        doc.value = text if text else ""


# ----------------------------
# Touch handling
# ----------------------------
def touch_start(event):
    global startX, startY, fingers, isDragging, dragCancelled, pressTimer
    touch = event.touches.item(0)
    startX = touch.clientX
    startY = touch.clientY
    fingers = event.touches.length
    isDragging = False
    dragCancelled = False

    def enable_drag(_=None):
        global isDragging
        if not dragCancelled:
            isDragging = True
            console.log("Long press → drag mode enabled")

    # Use JS setTimeout directly so it’s truly async
    pressTimer = window.setTimeout(create_proxy(enable_drag), LONG_PRESS_TIME)


def touch_move(event):
    global dragCancelled, pressTimer
    touch = event.touches.item(0)
    dx = abs(touch.clientX - startX)
    dy = abs(touch.clientY - startY)

    # If moved beyond threshold before long-press → cancel drag
    if not isDragging and (dx > MOVE_THRESHOLD or dy > MOVE_THRESHOLD):
        dragCancelled = True
        if pressTimer:
            window.clearTimeout(pressTimer)


def touch_end(event):
    global pressTimer
    if pressTimer:
        window.clearTimeout(pressTimer)

    changed = event.changedTouches.item(0)
    endX = changed.clientX
    endY = changed.clientY

    deltaX = (endX - startX) / browser_width
    deltaY = (endY - startY) / browser_height

    if isDragging:
        type_ = "drag"
        click = False
    elif dragCancelled:
        type_ = "scroll"
        click = False
    else:
        type_ = "touch"
        click = True

    console.log(f"TouchEnd → {type_} ({endX}, {endY})")
    send_coords(deltaX, deltaY, click, fingers, type_)


# Bind touch events
touch_area = document.getElementById("touchArea")
if touch_area is not None:
    touch_area.addEventListener("touchstart", create_proxy(touch_start), {"passive": True})
    touch_area.addEventListener("touchmove", create_proxy(touch_move), {"passive": True})
    touch_area.addEventListener("touchend", create_proxy(touch_end), {"passive": True})


# ----------------------------
# Sensor handlers (no await; throttled)
# ----------------------------
def device_orientation(event):
    global last_send_orientation
    alpha, beta, gamma = event.alpha, event.beta, event.gamma

    # Quick visual to prove events are firing
    if alpha is not None:
        set_text("alpha", f"{alpha:.1f}")
    if beta is not None:
        set_text("beta", f"{beta:.1f}")
    if gamma is not None:
        set_text("gamma", f"{gamma:.1f}")

    if alpha is None or beta is None or gamma is None:
        return

    now = window.performance.now()
    if now - last_send_orientation >= THROTTLE_MS:
        send_orientation(alpha, beta, gamma)
        last_send_orientation = now


def device_motion(event):
    global last_send_motion
    acc = event.acceleration
    rot = event.rotationRate

    ax = acc.x if acc else None
    ay = acc.y if acc else None
    az = acc.z if acc else None
    ra = rot.alpha if rot else None
    rb = rot.beta if rot else None
    rg = rot.gamma if rot else None

    # Visual feedback
    if ax is not None:
        set_text("accel-x", f"{ax:.2f}")
    if ay is not None:
        set_text("accel-y", f"{ay:.2f}")
    if az is not None:
        set_text("accel-z", f"{az:.2f}")
    if ra is not None:
        set_text("rot-alpha", f"{ra:.1f}")
    if rb is not None:
        set_text("rot-beta", f"{rb:.1f}")
    if rg is not None:
        set_text("rot-gamma", f"{rg:.1f}")

    if None in (ax, ay, az, ra, rb, rg):
        return

    now = window.performance.now()
    if now - last_send_motion >= THROTTLE_MS:
        send_motion(ax, ay, az, ra, rb, rg)
        last_send_motion = now


# ----------------------------
# Permission flow & listener attach
# ----------------------------
def attach_listeners():
    # No {passive: True} here; not needed and can be quirky on Safari
    window.addEventListener("deviceorientation", create_proxy(device_orientation))
    window.addEventListener("devicemotion", create_proxy(device_motion))
    console.log("Device listeners attached")


async def permission_button_click(_event):
    # iOS requires explicit user gesture + request
    try:
        if hasattr(window, "DeviceOrientationEvent") and hasattr(window.DeviceOrientationEvent, "requestPermission"):
            perm_o = await window.DeviceOrientationEvent.requestPermission()
            console.log("Orientation permission:", perm_o)
        if hasattr(window, "DeviceMotionEvent") and hasattr(window.DeviceMotionEvent, "requestPermission"):
            perm_m = await window.DeviceMotionEvent.requestPermission()
            console.log("Motion permission:", perm_m)
    except Exception as e:
        console.log("Permission request failed:", e)

    attach_listeners()
    btn = document.getElementById("requestPermission")
    if btn:
        btn.style.display = "none"


# Button wiring
permission_button = document.getElementById("requestPermission")
if permission_button is not None:
    permission_button.addEventListener("click", create_proxy(permission_button_click))

# Decide path: iOS vs Android/desktop
if hasattr(window, "DeviceOrientationEvent") and hasattr(window, "DeviceMotionEvent"):
    if hasattr(window.DeviceOrientationEvent, "requestPermission"):
        # iOS path → show button, wait for click
        console.log("iOS detected → waiting for user to enable sensors")
        if permission_button:
            permission_button.style.display = "block"
    else:
        # Android/desktop → attach immediately
        console.log("Android/desktop detected → attaching listeners now")
        if permission_button:
            permission_button.style.display = "none"
        attach_listeners()
else:
    console.log("Device orientation/motion APIs not supported")
    if permission_button:
        permission_button.style.display = "none"


# ----------------------------
# WebSocket events
# ----------------------------
def onopen(event):
    console.log("WS: Connection opened")


def onmessage(event):
    try:
        data = json.loads(event.data)
        if data and "copied_text" in data:
            update_textarea(data["copied_text"])
    except Exception as e:
        console.log("WS message parse error:", e)


def onclose(event):
    console.log("WS: Connection closed")


ws.addEventListener("open", create_proxy(onopen))
ws.addEventListener("message", create_proxy(onmessage))
ws.addEventListener("close", create_proxy(onclose))
