// Content script for WebSocket Mouse Controller
// Works with background script for WebSocket/HTTP communication

const FIREBASE_DB_URL = "https://fake-mouse-706a0-default-rtdb.firebaseio.com/coordinates.json";

let pollingInterval = null;

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

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "coordinate_data") {
        console.log("Content: Received data from background script:", message.data);
        processCoordinateData(message.data);
    }
});

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
                collectedText.push(node.textContent.trim());
                break;
            }
        }
    }

    const textContent = [...new Set(collectedText)].join(' ').trim();
    
    if (textContent) {
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.left = `${rect.left}px`;
        overlay.style.top = `${rect.top}px`;
        overlay.style.width = `${rect.right - rect.left}px`;
        overlay.style.height = `${rect.bottom - rect.top}px`;
        overlay.style.backgroundColor = 'rgba(255, 255, 0, 0.3)';
        overlay.style.border = '2px solid yellow';
        overlay.style.pointerEvents = 'none';
        overlay.style.zIndex = '999998';
        overlay.id = 'text-highlight-overlay';
        
        const existingOverlay = document.getElementById('text-highlight-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }
        
        document.body.appendChild(overlay);
        
        setTimeout(() => {
            overlay.remove();
        }, 2000);
    }
    
    return textContent;
}

function triggerClick(element) {
    const rect = element.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    ['mousedown', 'mouseup', 'click'].forEach(eventType => {
        const event = new MouseEvent(eventType, {
            view: window,
            bubbles: true,
            cancelable: true,
            clientX: centerX,
            clientY: centerY
        });
        element.dispatchEvent(event);
    });
}

function moveAndMaybeClick(cursor, offsetX, offsetY, shouldClick) {
    let currentX = parseFloat(cursor.style.left) || 0;
    let currentY = parseFloat(cursor.style.top) || 0;

    let newX = currentX + offsetX;
    let newY = currentY + offsetY;

    const maxX = window.innerWidth - cursor.offsetWidth;
    const maxY = window.innerHeight - cursor.offsetHeight;

    newX = Math.max(0, Math.min(newX, maxX));
    newY = Math.max(0, Math.min(newY, maxY));

    cursor.style.left = `${newX}px`;
    cursor.style.top = `${newY}px`;

    console.log(newX, newY);

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

    const maxX = window.innerWidth - cursor.offsetWidth;
    const maxY = window.innerHeight - cursor.offsetHeight;

    newX = Math.max(0, Math.min(newX, maxX));
    newY = Math.max(0, Math.min(newY, maxY));

    cursor.style.left = `${newX}px`;
    cursor.style.top = `${newY}px`;

    let text = getAndHighlightTextInRect(currentX, currentY, newX, newY);
    sendText(text);

    console.log(newX, newY);
}

let lastX = null;
let lastY = null;
let lastClick = null;
let scrollValue = 0;
let lastScrollValue = null;

function processCoordinateData(data) {
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
                console.log(`from [${lastX},${lastY}] to [${data.x},${data.y}]`);
                lastX = data.x;
                lastY = data.y;
                lastClick = data.click;
            }
        } else {
            if (data.y !== lastScrollValue) {
                console.log(`scroll down to ${data.y}`);
                scrollValue += data.y;
                window.scrollTo({
                    top: scrollValue,
                    behavior: "smooth"
                });
                lastScrollValue = data.y;
            }
        }
    }
}

// Firebase fallback function (for emergency use)
async function fetchCoordinates() {
    try {
        const res = await fetch(FIREBASE_DB_URL);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        processCoordinateData(data);
    } catch (err) {
        console.error("Error fetching coordinates from Firebase:", err);
    }
}

function startFirebasePolling() {
    console.log("Content: Starting Firebase polling mode (emergency fallback)");
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    pollingInterval = setInterval(fetchCoordinates, 100);
}

// Initialize the system
const fakeCursor = createFakeCursor();

// The background script will handle connections and send us data
console.log("Content: WebSocket Mouse Controller loaded");
console.log("Content: Waiting for coordinate data from background script...");

// Add a toggle function for testing (accessible from browser console)
window.toggleConnectionMode = function() {
    chrome.runtime.sendMessage({type: "toggle_connection"}, (response) => {
        console.log("Content: Connection mode toggled to:", response.mode);
    });
};

window.startFirebaseFallback = function() {
    console.log("Content: Manually starting Firebase fallback");
    startFirebasePolling();
};

console.log("Content: Use toggleConnectionMode() to switch connection modes or startFirebaseFallback() for emergency Firebase mode.");
