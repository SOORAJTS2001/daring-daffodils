from js import document


def fetch_easter_eggs():  # Find the element by ID
    """
    Locate and return the screen coordinates of the hidden Easter egg element in the DOM.

    This function searches for an HTML element with the ID "pyscript-hidden-easter-eggs".
    If found, it retrieves its bounding rectangle using `getBoundingClientRect()` and
    returns the top-left (x, y) coordinates.

    Returns:
        list[list[float]]: A list containing one [x, y] coordinate pair if the element exists,
        otherwise an empty list.
    """
    easter_eggs_coordinates = []
    el = document.getElementById("pyscript-hidden-easter-eggs")

    if el:
        rect = el.getBoundingClientRect()
        easter_eggs_coordinates.append([rect.x, rect.y])
    return easter_eggs_coordinates
