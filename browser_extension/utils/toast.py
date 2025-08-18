from js import document
from js import window
from pyodide.ffi import create_proxy


def create_toast(message="Hello from PyScript 🎉"):
    """
    Create a toast notification element and insert it into the DOM.

    The toast is styled as a fixed-position notification centered near the bottom
    of the screen. It is initially invisible (opacity 0) and ready for animation.

    Args:
        message (str, optional): The text content of the toast. Defaults to "Hello from PyScript 🎉".

    Returns:
        js.Element: The created <div> element representing the toast notification.
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


def show_toast(msg="Hello from PyScript 🎉"):
    """
    Display a toast notification with the given message, then fade it out.

    If no toast currently exists, one is created via `create_toast`. Otherwise,
    the existing toast is reused and its text updated. The toast fades in,
    stays visible for 3 seconds, and then fades out smoothly before being
    removed from the DOM.

    Args:
        msg (str, optional): The message text to display. Defaults to "Hello from PyScript 🎉".
    """
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
