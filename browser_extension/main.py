# ruff : noqa


import json
import traceback

from js import MouseEvent, WebSocket, console, document, window
from pyodide.ffi import create_proxy

# FIREBASE_DB_URL = "https://fake-mouse-706a0-default-rtdb.firebaseio.com/coordinates.json"

ws = WebSocket.new("ws://localhost:8000/ws")

browser_height = window.innerHeight
browser_width = window.innerWidth


def create_fake_cursor():
    cursor = document.createElement("div")
    cursor.id = "fake-cursor"
    style = cursor.style
    style.position = "fixed"
    style.width = "10px"
    style.height = "10px"
    style.background = "red"
    style.borderRadius = "50%"
    style.pointerEvents = "none"
    style.zIndex = 999999
    style.left = "0px"
    style.top = "0px"
    document.body.appendChild(cursor)
    document.body.style.cursor = "none"
    return cursor


def send_text(text):
    console.log("Sending copied text")
    ws.send(json.dumps({"copied_text": text}))


HIGHLIGHT_CLASS = "pyodide-temp-highlight"


def _schedule_auto_remove(el, timeout=2000):
    holder = {"cb": None}  # so we can destroy once

    def _remove(el=el, holder=holder):
        try:
            el.remove()
        finally:
            cb = holder.pop("cb", None)
            if cb is not None:
                cb.destroy()

    cb = create_proxy(_remove)  # persistent JS callback
    holder["cb"] = cb
    window.setTimeout(cb, timeout)


def get_and_highlight_text_in_rect(x1, y1, x2, y2):
    rect = {
        "left": min(x1, x2),
        "top": min(y1, y2),
        "right": max(x1, x2),
        "bottom": max(y1, y2),
    }

    walker = document.createTreeWalker(document.body, window.NodeFilter.SHOW_TEXT, None, False)
    collected_text = []

    node = walker.nextNode()
    while node:
        range_ = document.createRange()
        range_.selectNodeContents(node)
        rects = range_.getClientRects()

        for r in rects:
            if not (
                r.right < rect["left"] or r.left > rect["right"] or r.bottom < rect["top"] or r.top > rect["bottom"]
            ):
                txt = node.textContent.strip()
                if txt:
                    collected_text.append(txt)

                highlight = document.createElement("div")
                highlight.classList.add(HIGHLIGHT_CLASS)
                s = highlight.style
                s.position = "fixed"
                s.left = f"{r.left}px"
                s.top = f"{r.top}px"
                s.width = f"{r.width}px"
                s.height = f"{r.height}px"
                s.border = "1px solid blue"
                s.backgroundColor = "rgba(0, 0, 255, 0.1)"
                s.pointerEvents = "none"
                s.zIndex = 999999
                document.body.appendChild(highlight)

                _schedule_auto_remove(highlight, 2000)  # ← each box self-destructs in 2s
                break

        node = walker.nextNode()

    return " ".join(collected_text)


def trigger_click(el):
    for evt_type in ["mousedown", "mouseup", "click"]:
        event = MouseEvent.new(evt_type, {"bubbles": True, "cancelable": True, "view": window})
        el.dispatchEvent(event)


def move_and_maybe_click(cursor, offset_x, offset_y, should_click):
    current_x = float(cursor.style.left.replace("px", "") or 0)
    current_y = float(cursor.style.top.replace("px", "") or 0)

    new_x = current_x + offset_x
    new_y = current_y + offset_y

    max_x = window.innerWidth - cursor.offsetWidth
    max_y = window.innerHeight - cursor.offsetHeight
    new_x = max(0, min(new_x, max_x))
    new_y = max(0, min(new_y, max_y))

    cursor.style.left = f"{new_x}px"
    cursor.style.top = f"{new_y}px"

    console.log(new_x, new_y)

    el = document.elementFromPoint(new_x, new_y)
    if should_click and el:
        tag = el.tagName.lower()
        clickable = (
            tag in ["button", "a", "input", "select"] or el.onclick or window.getComputedStyle(el).cursor == "pointer"
        )
        if clickable:
            console.log("Clicking:", el)
            trigger_click(el)


def drag_and_copy(cursor, offset_x, offset_y):
    current_x = float(cursor.style.left.replace("px", "") or 0)
    current_y = float(cursor.style.top.replace("px", "") or 0)

    new_x = current_x + offset_x
    new_y = current_y + offset_y

    max_x = window.innerWidth - cursor.offsetWidth
    max_y = window.innerHeight - cursor.offsetHeight
    new_x = max(0, min(new_x, max_x))
    new_y = max(0, min(new_y, max_y))

    cursor.style.left = f"{new_x}px"
    cursor.style.top = f"{new_y}px"

    text = get_and_highlight_text_in_rect(current_x, current_y, new_x, new_y)
    send_text(text)

    console.log(new_x, new_y)


# State tracking
last_x = None
last_y = None
last_click = 0
last_scroll_value = None
scroll_value = 0


def fetch_coordinates(data_x, data_y, fingers, data_type, click):
    global last_x, last_y, last_click, scroll_value, last_scroll_value
    data_x = data_x * browser_width
    data_y = data_y * browser_height
    try:
        console.log("New Data", data_x, data_y, fingers, data_type, click)
        if isinstance(data_x, (int, float)) and isinstance(data_y, (int, float)):
            if fingers == 1:
                if data_type in {"scroll", "touch"} and (data_x != last_x or data_y != last_y or click != last_click):
                    move_and_maybe_click(fake_cursor, -data_x, -data_y, bool(click))
                    last_x, last_y, last_click = data_x, data_y, click
                elif data_type == "drag" and (data_x != last_x or data_y != last_y or click != last_click):
                    drag_and_copy(fake_cursor, data_x, data_y)
                    console.log(f"from [{last_x},{last_y}] to [{data_x},{data_y}]")
                    last_x, last_y, last_click = data_x, data_y, click
            elif data_y != 0:
                scroll_value = window.scrollY + data_y
                console.log(f"scroll to {scroll_value}")
                window.scrollTo(0, scroll_value)  # no smooth first, test it works

    except Exception as err:
        console.error("Error fetching coordinates:", str(err))

        console.error(traceback.format_exc())


def onopen(event):
    console.log("✅ Connection opened from extension")


def onmessage(event):
    data = json.loads(event.data)
    console.log("Received coordinates", data)
    fetch_coordinates(data["x"], data["y"], data["fingers"], data["type"], data["click"])


def onclose(event):
    console.log("❌ Connection closed")


# Attach event listeners
ws.addEventListener("open", create_proxy(onopen))
ws.addEventListener("message", create_proxy(onmessage))
ws.addEventListener("close", create_proxy(onclose))

# Init
fake_cursor = create_fake_cursor()
