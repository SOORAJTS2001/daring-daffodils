from js import document


def create_fake_cursor():
    """
    Create and display a custom fake mouse cursor on the webpage.

    This function injects a fixed-position <div> element styled to look like a cursor
    using a custom image. It replaces the default browser cursor with this fake cursor
    by setting `document.body.style.cursor` to "none".

    The cursor is initialized at the top-left corner of the screen (0,0), with fixed
    dimensions of 70x50 pixels, and rendered above all other elements using a very
    high z-index.

    Returns:
        js.Element: The created <div> element representing the fake cursor.
    """
    cursor = document.createElement("div")
    cursor.id = "fake-cursor"
    style = cursor.style
    style.position = "fixed"
    style.width = "70px"
    style.height = "50px"
    style.pointerEvents = "none"
    style.zIndex = 999999
    style.left = "0px"
    style.top = "0px"
    style.backgroundSize = "cover"
    style.backgroundImage = "url('http://127.0.0.1:8000/resource/static/mouse_pointer.png')"
    document.body.appendChild(cursor)
    document.body.style.cursor = "none"
    return cursor
