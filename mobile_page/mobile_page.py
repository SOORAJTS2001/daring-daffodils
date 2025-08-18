# ruff : noqa

import json

from js import WebSocket, clearTimeout, console, document, setTimeout, window, navigator
from pyodide.ffi import create_proxy

ws_url = f"ws://{window.location.hostname}:{window.location.port}/ws"
console.log(f"{ws_url}")
ws = WebSocket.new(ws_url)

startX = 0
startY = 0
browser_height = window.innerHeight
browser_width = window.innerWidth
fingers = 1

pressTimer = None
isDragging = False
dragCancelled = False
LONG_PRESS_TIME = 300  # ms
MOVE_THRESHOLD = 5  # px


def create_toast(message="Hello from PyScript 🎉"):
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
    payload = {
        "x": x,
        "y": y,
        "click": 1 if click else 0,
        "fingers": fingers,
        "browser_width": browser_width,
        "browser_height": browser_height,
        "type": type_,
    }
    console.log(x, y, click, fingers, type_)
    console.log("Sending coordinates", payload)
    ws.send(json.dumps(payload))


async def touch_start(event):
    global startX, startY, fingers, isDragging, dragCancelled, pressTimer
    touch = event.touches.item(0)  # ✅ JS method to access first touch
    startX = touch.clientX
    startY = touch.clientY
    fingers = event.touches.length
    isDragging = False
    dragCancelled = False

    def enable_drag():
        global isDragging
        if not dragCancelled:
            isDragging = True
            console.log("Long press → drag mode enabled")

    pressTimer = setTimeout(create_proxy(enable_drag), LONG_PRESS_TIME)


async def touch_move(event):
    global dragCancelled
    touch = event.touches.item(0)
    dx = abs(touch.clientX - startX)
    dy = abs(touch.clientY - startY)

    if not isDragging and (dx > MOVE_THRESHOLD or dy > MOVE_THRESHOLD):
        dragCancelled = True
        clearTimeout(pressTimer)


async def touch_end(event):
    global pressTimer
    clearTimeout(pressTimer)

    # ✅ Access first changed touch via .item(0)
    touch = event.changedTouches.item(0)
    endX = touch.clientX
    endY = touch.clientY

    deltaX = (endX - startX) / browser_width
    deltaY = (endY - startY) / browser_height

    click = False
    if isDragging:
        type_ = "drag"
    elif dragCancelled:
        type_ = "scroll"
    else:
        type_ = "touch"
        click = True

    console.log(f"Type: {type_}, End coords: ({endX}, {endY})")
    await sendCoords(deltaX, deltaY, click, fingers, type_)


def update_textarea(text):
    console.log("Update textarea")
    doc = document.getElementById("copiedText")
    doc.value = text if text else ""


touch_area = document.getElementById("touchArea")
touch_area.addEventListener("touchstart", create_proxy(touch_start), {"passive": True})
touch_area.addEventListener("touchmove", create_proxy(touch_move), {"passive": True})
touch_area.addEventListener("touchend", create_proxy(touch_end), {"passive": True})


def onopen(event):  # <-- accept event arg
    console.log("Connection opened from page")


def onmessage(event):
    data = json.loads(event.data)
    console.log(data)
    if data and data.get("copied_text"):
        update_textarea(data["copied_text"])


def onclose(event):
    console.log("Connection closed")


# Add event listeners
ws.addEventListener("open", create_proxy(onopen))
ws.addEventListener("message", create_proxy(onmessage))
ws.addEventListener("close", create_proxy(onclose))
