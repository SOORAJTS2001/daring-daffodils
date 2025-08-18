from .easter_eggs import fetch_easter_eggs
from .fake_cursor import create_fake_cursor
from .make_highlights import get_and_highlight_text_in_rect
from .move_and_click import move_and_maybe_click
from .move_and_click import trigger_click
from .toast import create_toast
from .toast import show_toast

__all__ = [
    "fetch_easter_eggs",
    "create_fake_cursor",
    "get_and_highlight_text_in_rect",
    "move_and_maybe_click",
    "trigger_click",
    "create_toast",
    "show_toast",
]
