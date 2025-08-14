# ruff: noqa

import asyncio
import json
from typing import Any

from js import clearTimeout, console, document, setInterval, setTimeout, window
from pyodide.ffi import create_proxy
from pyodide.http import pyfetch

FIREBASE_DB_URL = "<DATABASE_URL>"

START_X = 0
START_Y = 0
BROWSER_HEIGHT = window.innerHeight
BROWSER_WIDTH = window.innerWidth
FINGERS = 1

PRESS_TIMER = None
IS_DRAGGING = False
DRAG_CANCELLED = False
LONG_PRESS_TIME = 300  # ms
MOVE_THRESHOLD = 5  # px

console.log("Loaded main.py!")


async def get_text() -> None:
    """:return:"""
    resp = await pyfetch(
        url=FIREBASE_DB_URL,
        method="GET",
    )
    response = await resp.json()
    text_value = response.get("text")
    console.log(f"Fetched text from Firebase: {text_value}")
    return text_value


async def send_coords(x: float, y: float, click: bool, fingers: int, type_: str) -> None:
    """:param x:
    :param y:
    :param click:
    :param fingers:
    :param type_:
    :return:
    """
    payload = {
        "x": x,
        "y": y,
        "click": click,
        "fingers": fingers,
        "browser_width": BROWSER_WIDTH,
        "browser_height": BROWSER_HEIGHT,
        "type": type_,
    }
    await pyfetch(
        url=FIREBASE_DB_URL,
        method="PATCH",
        headers={"Content-Type": "application/json"},
        body=json.dumps(payload),
    )


async def touch_start(event: Any) -> None:
    """:param event:
    :return:
    """
    global START_X, START_Y, FINGERS, IS_DRAGGING, DRAG_CANCELLED, PRESS_TIMER
    touch = event.touches.item(0)  # ✅ JS method to access first touch
    START_X = touch.clientX
    START_Y = touch.clientY
    FINGERS = event.touches.length
    IS_DRAGGING = False
    DRAG_CANCELLED = False

    def enable_drag() -> None:
        global IS_DRAGGING
        if not DRAG_CANCELLED:
            IS_DRAGGING = True
            console.log("Long press → drag mode enabled")

    PRESS_TIMER = setTimeout(create_proxy(enable_drag), LONG_PRESS_TIME)


async def touch_move(event: Any) -> None:
    """:param event:
    :return:
    """
    global DRAG_CANCELLED
    touch = event.touches.item(0)
    dx = abs(touch.clientX - START_X)
    dy = abs(touch.clientY - START_Y)

    if not IS_DRAGGING and (dx > MOVE_THRESHOLD or dy > MOVE_THRESHOLD):
        DRAG_CANCELLED = True
        clearTimeout(PRESS_TIMER)


async def touch_end(event: Any) -> None:
    """:param event:
    :return:
    """
    global PRESS_TIMER
    clearTimeout(PRESS_TIMER)

    # ✅ Access first changed touch via .item(0)
    touch = event.changedTouches.item(0)
    end_x = touch.clientX
    end_y = touch.clientY

    delta_x = (end_x - START_X) * (1719 / BROWSER_WIDTH)
    delta_y = (end_y - START_Y) * (865 / BROWSER_HEIGHT)

    click = False
    if IS_DRAGGING:
        type_ = "drag"
    elif DRAG_CANCELLED:
        type_ = "scroll"
    else:
        type_ = "touch"
        click = True

    console.log(f"Type: {type_}, End coords: ({end_x}, {end_y})")
    await send_coords(delta_x, delta_y, click, FINGERS, type_)


async def update_textarea() -> None:
    """:return:"""
    console.log("Update textarea")
    text = await get_text()
    doc = document.getElementById("copiedText")
    doc.value = text if text else ""


def update_wrapper() -> None:
    """:return:"""
    _ = asyncio.ensure_future(update_textarea())


def start_interval() -> None:
    """:return:"""
    proxy_fn = create_proxy(update_wrapper)
    setInterval(proxy_fn, 1000)  # Run every second


start_interval()
touch_area = document.getElementById("touchArea")
touch_area.addEventListener("touchstart", create_proxy(touch_start), {"passive": True})
touch_area.addEventListener("touchmove", create_proxy(touch_move), {"passive": True})
touch_area.addEventListener("touchend", create_proxy(touch_end), {"passive": True})
