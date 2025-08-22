from js import document
from js import window
from pyodide.ffi import create_proxy

HIGHLIGHT_CLASS = "pyodide-temp-highlight"


def _schedule_auto_remove(el, timeout=2000):
    """
    Schedule automatic removal of a DOM element after a given timeout.

    This helper creates a persistent JavaScript callback using Pyodide's
    `create_proxy`, then registers it with `window.setTimeout`. Once the
    timeout expires, the element is removed from the DOM and the callback
    is destroyed to avoid memory leaks.

    Args:
        el (js.Element): The DOM element to remove.
        timeout (int, optional): Delay in milliseconds before removal. Defaults to 2000.
    """
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
    """
    Extract visible text within a rectangular region of the webpage and temporarily highlight it.

    This function:
      1. Defines a rectangle using the given screen coordinates (x1, y1) and (x2, y2).
      2. Walks through all text nodes in the document body.
      3. For each text node, checks whether any part of its bounding client rect
         intersects with the defined rectangle.
      4. If overlapping text is found:
         - Collects and returns the text content (whitespace-trimmed).
         - Visually highlights the region by overlaying a semi-transparent blue box.
         - The highlight box automatically disappears after 2 seconds.

    Args:
        x1 (float): X-coordinate of the first corner of the rectangle.
        y1 (float): Y-coordinate of the first corner of the rectangle.
        x2 (float): X-coordinate of the opposite corner of the rectangle.
        y2 (float): Y-coordinate of the opposite corner of the rectangle.

    Returns:
        str: A concatenated string of all text snippets found within the rectangle.
    """
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
