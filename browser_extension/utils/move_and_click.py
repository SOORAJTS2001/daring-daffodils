from js import MouseEvent
from js import console
from js import document
from js import window


def trigger_click(el):
    """
    Programmatically simulate a full mouse click sequence on a DOM element.

    This dispatches three mouse events in order: "mousedown", "mouseup", and "click".
    The events bubble, are cancelable, and are associated with the global `window`.

    Args:
        el (js.Element): The DOM element to trigger the click on.
    """
    for evt_type in ["mousedown", "mouseup", "click"]:
        event = MouseEvent.new(evt_type, {"bubbles": True, "cancelable": True, "view": window})
        el.dispatchEvent(event)


def move_and_maybe_click(cursor, offset_x, offset_y, should_click):
    """
    Move a fake cursor element across the screen and optionally simulate a click.

    The cursor's new position is calculated relative to its current position,
    constrained within the visible window boundaries. After moving, the function
    checks which element lies beneath the cursor, and if `should_click` is True,
    simulates a click on that element if it appears to be interactive.

    Args:
        cursor (js.Element): The fake cursor <div> element to move.
        offset_x (float): Horizontal offset (in pixels) to move the cursor.
        offset_y (float): Vertical offset (in pixels) to move the cursor.
        should_click (bool): Whether to attempt a click on the element under the cursor.

    Behavior:
        - Updates the cursor's `style.left` and `style.top` positions.
        - Logs the new coordinates to the console.
        - If `should_click` is True and the underlying element is considered clickable
          (button, link, input, select, or styled with `cursor: pointer`), triggers
          a synthetic mouse click sequence on that element.
    """
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
