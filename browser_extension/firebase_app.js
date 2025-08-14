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

function sendText(text) {
    fetch(FIREBASE_DB_URL, {
        method: "PATCH",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text})
    });
}

function getAndHighlightTextInRect(x1, y1, x2, y2) {
    const rect = {
        left: Math.min(x1, x2),
        top: Math.min(y1, y2),
        right: Math.max(x1, x2),
        bottom: Math.max(y1, y2)
    };

    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    let node;
    let collectedText = [];

    while ((node = walker.nextNode())) {
        const range = document.createRange();
        range.selectNodeContents(node);
        const rects = range.getClientRects();

        for (let r of rects) {
            if (!(r.right < rect.left ||
                r.left > rect.right ||
                r.bottom < rect.top ||
                r.top > rect.bottom)) {

                // Add to text list
                if (node.textContent.trim().length > 0) {
                    collectedText.push(node.textContent.trim());
                }

                // Create overlay highlight
                const highlight = document.createElement("div");
                highlight.style.position = "fixed";
                highlight.style.left = `${r.left}px`;
                highlight.style.top = `${r.top}px`;
                highlight.style.width = `${r.width}px`;
                highlight.style.height = `${r.height}px`;
                highlight.style.border = "1px solid blue";
                highlight.style.backgroundColor = "rgba(0, 0, 255, 0.1)";
                highlight.style.pointerEvents = "none";
                highlight.style.zIndex = 999999;
                document.body.appendChild(highlight);

                // Remove after 2 seconds
                setTimeout(() => highlight.remove(), 2000);

                break; // no need to check other rects for same node
            }
        }
    }

    return collectedText.join(" ");
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

function dragAndCopy(cursor, offsetX, offsetY) {
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

    let text = getAndHighlightTextInRect(currentX, currentY, newX, newY)
    sendText(text)

    console.log(newX, newY)
}

let lastX = null;
let lastY = null;
let lastClick = null;
let scrollValue = null;
let lastScrollValue = null;
let lastText = null;

async function fetchCoordinates() {
    try {
        const res = await fetch(FIREBASE_DB_URL);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (data && typeof data.x === 'number' && typeof data.y === 'number') {
            if (data.fingers === 1) {
                if (['scroll', 'touch'].includes(data.type) && (data.x !== lastX || data.y !== lastY || data.click !== lastClick)) {
                    moveAndMaybeClick(fakeCursor, -data.x, -data.y, !!data.click);
                    lastX = data.x;
                    lastY = data.y;
                    lastClick = data.click;
                }
                if (['drag'].includes(data.type) && (data.x !== lastX || data.y !== lastY || data.click !== lastClick)) {
                    dragAndCopy(fakeCursor, data.x, data.y);
                    console.log(`from [${lastX},${lastY}] to [${data.x},${data.y}]`)
                    lastX = data.x;
                    lastY = data.y;
                    lastClick = data.click;
                }
            } else {
                if (data.y !== lastScrollValue) {
                    console.log(`scroll down to ${data.y}`)
                    scrollValue += data.y;
                    window.scrollTo({
                        top: scrollValue, // 250 + 100
                        behavior: "smooth"
                    });
                    lastScrollValue = data.y;

                }
            }
        }
    } catch
        (err) {
        console.error("Error fetching coordinates:", err);
    }
}

const fakeCursor = createFakeCursor();
setInterval(fetchCoordinates, 100);
