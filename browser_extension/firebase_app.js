const FIREBASE_DB_URL = "<PROJECT_FIREBASE_URL>";

function createFakeCursor() {
    const cursor = document.createElement('div');
    cursor.id = 'fake-cursor';
    cursor.style.position = 'fixed';
    cursor.style.width = '10px';
    cursor.style.height = '10px';
    cursor.style.background = 'red';
    cursor.style.borderRadius = '50%';
    cursor.style.pointerEvents = 'none';
    cursor.style.zIndex = 999999;
    cursor.style.left = '0px';
    cursor.style.top = '0px';
    document.body.appendChild(cursor);
    document.body.style.cursor = 'none';
    return cursor;
}

function triggerClick(el) {
    ["mousedown", "mouseup", "click"].forEach(type => {
        el.dispatchEvent(new MouseEvent(type, {bubbles: true, cancelable: true, view: window}));
    });
}

function moveAndMaybeClick(cursor, offsetX, offsetY, shouldClick) {
    let currentX = parseFloat(cursor.style.left) || 0;
    let currentY = parseFloat(cursor.style.top) || 0;

    let newX = currentX + offsetX;
    let newY = currentY + offsetY;

    // Clamp coordinates so they stay inside viewport
    const maxX = window.innerWidth - cursor.offsetWidth;
    const maxY = window.innerHeight - cursor.offsetHeight;

    newX = Math.max(0, Math.min(newX, maxX));
    newY = Math.max(0, Math.min(newY, maxY));

    cursor.style.left = `${newX}px`;
    cursor.style.top = `${newY}px`;

    console.log(newX, newY)

    const el = document.elementFromPoint(newX, newY);
    if (shouldClick && el) {
        const tag = el.tagName.toLowerCase();
        const clickable = ["button", "a", "input", "select"].includes(tag) ||
            el.onclick ||
            getComputedStyle(el).cursor === "pointer";
        if (clickable) {
            console.log("Clicking:", el);
            triggerClick(el);
        }
    }
}

let lastX = null;
let lastY = null;
let lastClick = null;
let scrollValue = null

async function fetchCoordinates() {
    try {
        const res = await fetch(FIREBASE_DB_URL);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (data && typeof data.x === 'number' && typeof data.y === 'number') {
            if (data.fingers === 1) {
                if (data.x !== lastX || data.y !== lastY || data.click !== lastClick) {
                    moveAndMaybeClick(fakeCursor, data.x, data.y, !!data.click);
                    lastX = data.x;
                    lastY = data.y;
                    lastClick = data.click;
                }
            } else {
                if (data.x !== scrollValue) {
                    console.log(data.x+scrollValue)
                    window.scrollTo({
                        top: data.x+scrollValue, // 250 + 100
                        behavior: "smooth"
                    });
                    scrollValue = data.x;

                }
            }
        }
    } catch (err) {
        console.error("Error fetching coordinates:", err);
    }
}

const fakeCursor = createFakeCursor();
setInterval(fetchCoordinates, 100);
