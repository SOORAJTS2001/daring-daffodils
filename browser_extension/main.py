# ruff : noqa
import json
import random
import traceback

from js import MouseEvent, WebSocket, console, document, window
from pyodide.ffi import create_proxy

ws = WebSocket.new("ws://localhost:8000/ws")
browser_height = window.innerHeight
browser_width = window.innerWidth
easter_eggs_coordinates = []
inactivity_timer = None
wandering = False
wandering_proxy = None
# State tracking
last_x = None
last_y = None
last_click = 0
last_scroll_value = None
scroll_value = 0

WANDERING_STEP_X = 100
WANDERING_STEP_Y = 100
WANDERING_STEP_TIME = 500  # ms
INACTIVITY_TIME = 60000
WANDERING_TIME_MAX_LIMIT = 60000
WANDERING_TIME_MIN_LIMIT = 10000
PROBABILITY_FOR_EASTER_EGG = 0.1
PROBABILITY_FOR_SHADOW_MODE = 0.3


def fetch_easter_eggs():  # Find the element by ID
    global easter_eggs_coordinates
    easter_eggs_coordinates = []
    el = document.getElementById("pyscript-hidden-easter-eggs")

    if el:
        rect = el.getBoundingClientRect()
        easter_eggs_coordinates.append([rect.x, rect.y])
    return easter_eggs_coordinates


def create_fake_cursor():
    cursor = document.createElement("div")
    cursor.id = "fake-cursor"
    style = cursor.style
    style.position = "fixed"
    style.width = "50px"
    style.height = "50px"
    style.pointerEvents = "none"
    style.zIndex = 999999
    style.left = "0px"
    style.top = "0px"
    style.backgroundSize = "cover"
    style.backgroundImage = "url('http://127.0.0.1:8000/static/img.png')"
    document.body.appendChild(cursor)
    document.body.style.cursor = "none"
    return cursor


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


def show_toast(msg="Hello from PyScript 🎉"):
    toast = document.getElementById("toast")
    if toast is None:  # if not created yet
        toast = create_toast(msg)
    else:
        toast.innerText = msg

    # Show
    toast.style.opacity = "1"
    toast.style.bottom = "50px"

    # Hide after 3s
    def hide_toast():
        toast.style.opacity = "0"
        toast.style.bottom = "30px"

        def remove():
            toast.remove()

        rm_cb = create_proxy(remove)
        window.setTimeout(rm_cb, 500)  # remove after fade out

    cb = create_proxy(hide_toast)
    window.setTimeout(cb, 3000)


def random_mode(modes: list):
    # choose a random number of items (between 1 and len(modes))
    k = random.randint(1, len(modes))
    # pick k items randomly without replacement
    return random.sample(modes, k)


def start_wandering():
    global wandering, wandering_proxy
    if wandering:
        return  # already wandering
    wandering = True
    console.log("⚠️ No WebSocket messages — starting wandering mode")
    modes = ["wandering", "rage", "shadow"]
    mode = random_mode(modes)
    if len(mode) == 1:
        show_toast(f"You have activated {mode[0]} mode")
    else:
        show_toast(f"You have activated {(','.join(mode))} mode")

    def wander_step(*args):
        if not wandering:
            return  # stop if deactivated

        x = random.randint(0, browser_width - 50)  # subtract cursor size
        y = random.randint(0, browser_height - 50)

        # Occasionally snap to one of our diagonal anchor coords
        if easter_eggs_coordinates and random.random() < PROBABILITY_FOR_EASTER_EGG:  # 30% chance
            dx, dy = random.choice(easter_eggs_coordinates)
        else:
            dx, dy = x, y

        if "shadow" in mode and random.random() < PROBABILITY_FOR_SHADOW_MODE:
            console.log("Shadow enabled")
            fake_cursor.style.visibility = "visible" if fake_cursor.style.visibility == "hidden" else "hidden"

        if "rage" in mode:
            console.log("Rage enabled")
            dx *= 2
            dy *= 2
        fake_cursor.style.left = f"{dx}px"
        fake_cursor.style.top = f"{dy}px"
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

        window.setTimeout(wandering_proxy, WANDERING_STEP_TIME)

    # proxy wrapper for JS callbacks
    wandering_proxy = create_proxy(wander_step)
    wander_step()  # kick off wandering

    # stop wandering after random duration
    def stop_wandering(*args):
        global wandering
        wandering = False
        fake_cursor.style.visibility = "visible"  # ensure visible at the end
        console.log("✅ Wandering mode ended — control back to user")

    duration = random.randint(WANDERING_TIME_MIN_LIMIT, WANDERING_TIME_MAX_LIMIT)  # 10s–60s
    window.setTimeout(create_proxy(stop_wandering), duration)
    fake_cursor.style.visibility = "visible"


def reset_inactivity_timer():
    global inactivity_timer
    if inactivity_timer is not None:
        window.clearTimeout(inactivity_timer)

    def on_timeout(*args):
        start_wandering()

    inactivity_timer = window.setTimeout(create_proxy(on_timeout), INACTIVITY_TIME)
    console.log("finished_all")


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


reset_inactivity_timer()


def onopen(event):
    console.log("✅ Connection opened from extension")


def onmessage(event):
    data = json.loads(event.data)
    console.log("Received coordinates", data)
    reset_inactivity_timer()
    fetch_coordinates(data["x"], data["y"], data["fingers"], data["type"], data["click"])


def onclose(event):
    console.log("❌ Connection closed")


fetch_easter_eggs()
# Attach event listeners
ws.addEventListener("open", create_proxy(onopen))
ws.addEventListener("message", create_proxy(onmessage))
ws.addEventListener("close", create_proxy(onclose))

# Init
fake_cursor = create_fake_cursor()
