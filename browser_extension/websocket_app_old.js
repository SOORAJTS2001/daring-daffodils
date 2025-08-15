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

function initWebSocket() {
    // Content scripts in browser extensions have WebSocket limitations
    // Try WebSocket but expect it might fail due to security restrictions
    if (!isWebSocketEnabled) {
        console.log("WebSocket disabled, using HTTP polling instead");
        startHttpPolling();
        return;
    }
    
    try {
        websocket = new WebSocket(WEBSOCKET_URL);
        
        websocket.onopen = function(event) {
            console.log("WebSocket connected to mobile app");
        };
        
        websocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log("Received data via WebSocket:", data);
                processCoordinateData(data);
            } catch (error) {
                console.error("Error parsing WebSocket message:", error);
            }
        };
        
        websocket.onclose = function(event) {
            console.log("WebSocket connection closed, switching to HTTP polling...");
            isWebSocketEnabled = false;
            startHttpPolling();
        };
        
        websocket.onerror = function(error) {
            console.error("WebSocket error (this is expected in browser extensions):", error);
            console.log("Switching to HTTP polling for better extension compatibility...");
            isWebSocketEnabled = false;
            startHttpPolling();
        };
        
    } catch (error) {
        console.error("Failed to create WebSocket (using HTTP polling instead):", error);
        isWebSocketEnabled = false;
        startHttpPolling();
    }
}

// HTTP polling as alternative to WebSocket for extension compatibility
function startHttpPolling() {
    console.log("Starting HTTP polling mode for extension compatibility");
    
    // Clear any existing polling
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Try to fetch from our local HTTP server first, then fallback to Firebase
    pollingInterval = setInterval(async () => {
        try {
            // Try local HTTP server first
            const response = await fetch(HTTP_POLLING_URL);
            if (response.ok) {
                const data = await response.json();
                if (data && Object.keys(data).length > 0) {
                    processCoordinateData(data);
                    return;
                }
            }
        } catch (error) {
            // HTTP server not available, fallback to Firebase
        }
        
        // Fallback to Firebase
        try {
            const res = await fetch(FIREBASE_DB_URL);
            if (res.ok) {
                const data = await res.json();
                processCoordinateData(data);
            }
        } catch (err) {
            console.error("Error fetching from Firebase:", err);
        }
    }, 50); // Faster polling for better responsiveness
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

// Firebase fallback function (kept for compatibility)
async function fetchCoordinates() {
    try {
        const res = await fetch(FIREBASE_DB_URL);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        processCoordinateData(data);
    } catch (err) {
        console.error("Error fetching coordinates:", err);
    }
}

function startFirebasePolling() {
    console.log("Starting Firebase polling mode");
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    pollingInterval = setInterval(fetchCoordinates, 100);
}

// Initialize the system
const fakeCursor = createFakeCursor();

// Start with HTTP polling (better extension compatibility)
console.log("WebSocket Mouse Controller loaded");
console.log("Starting with HTTP polling due to browser extension security restrictions");
startHttpPolling();

// Add a way to toggle between connection modes for testing
window.toggleConnectionMode = function() {
    isWebSocketEnabled = !isWebSocketEnabled;
    
    // Clear existing polling
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
    
    if (isWebSocketEnabled) {
        console.log("Switching to WebSocket mode");
        if (websocket) websocket.close();
        initWebSocket();
    } else {
        console.log("Switching to HTTP polling mode");
        if (websocket) websocket.close();
        startHttpPolling();
    }
};

console.log("Use toggleConnectionMode() to switch between WebSocket and HTTP polling modes.");
