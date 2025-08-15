// Background script for WebSocket Mouse Controller
// Uses HTTP polling for better service worker compatibility

const WEBSOCKET_URL = "ws://localhost:8765";
const HTTP_POLLING_URL = "http://localhost:8766/data";

let websocket = null;
let isWebSocketEnabled = false; // Start with HTTP polling
let pollingInterval = null;

chrome.runtime.onInstalled.addListener(() => {
    console.log("Background: WebSocket Mouse Controller installed and ready.");
    console.log("Background: Starting with HTTP polling (service worker compatibility)");
    startHttpPolling();
});

chrome.runtime.onStartup.addListener(() => {
    console.log("Background: Extension startup, starting HTTP polling");
    startHttpPolling();
});

function initWebSocket() {
    // Note: Service workers may have limitations with WebSocket connections
    if (!isWebSocketEnabled) return;
    
    try {
        websocket = new WebSocket(WEBSOCKET_URL);
        
        websocket.onopen = function(event) {
            console.log("Background: WebSocket connected to mobile app");
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        };
        
        websocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log("Background: Received data via WebSocket:", data);
                sendDataToContentScripts(data);
            } catch (error) {
                console.error("Background: Error parsing WebSocket message:", error);
            }
        };
        
        websocket.onclose = function(event) {
            console.log("Background: WebSocket connection closed, switching to HTTP polling...");
            isWebSocketEnabled = false;
            startHttpPolling();
        };
        
        websocket.onerror = function(error) {
            console.error("Background: WebSocket error:", error);
            console.log("Background: Using HTTP polling instead...");
            isWebSocketEnabled = false;
            startHttpPolling();
        };
        
    } catch (error) {
        console.error("Background: Failed to create WebSocket:", error);
        isWebSocketEnabled = false;
        startHttpPolling();
    }
}

function sendDataToContentScripts(data) {
    console.log("Background: Sending data to content scripts:", data);
    chrome.tabs.query({active: true}, (tabs) => {
        if (tabs.length > 0) {
            tabs.forEach(tab => {
                chrome.tabs.sendMessage(tab.id, {
                    type: "coordinate_data",
                    data: data
                }).catch((error) => {
                    console.log("Background: Error sending to tab", tab.id, ":", error.message);
                });
            });
        } else {
            console.log("Background: No active tabs found");
        }
    });
}

function startHttpPolling() {
    console.log("Background: Starting HTTP polling mode");
    
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
    
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(HTTP_POLLING_URL);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data && Object.keys(data).length > 0) {
                    console.log("Background: Received data from HTTP:", data);
                    sendDataToContentScripts(data);
                }
                // Don't log empty responses to avoid spam
            } else {
                console.error("Background: HTTP response not OK:", response.status);
            }
        } catch (error) {
            console.error("Background: HTTP polling error:", error);
        }
    }, 100); // Back to fast polling
}

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "log") {
        console.log("Background: Message from content script:", message.data);
    } else if (message.type === "toggle_connection") {
        // Toggle between WebSocket and HTTP polling
        isWebSocketEnabled = !isWebSocketEnabled;
        
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        
        if (isWebSocketEnabled) {
            console.log("Background: Switching to WebSocket mode");
            if (websocket) websocket.close();
            initWebSocket();
        } else {
            console.log("Background: Switching to HTTP polling mode");
            if (websocket) websocket.close();
            startHttpPolling();
        }
        
        sendResponse({status: "toggled", mode: isWebSocketEnabled ? "websocket" : "http"});
    } else if (message.type === "get_status") {
        sendResponse({
            mode: isWebSocketEnabled ? "websocket" : "http",
            polling: pollingInterval !== null,
            websocket_connected: websocket && websocket.readyState === WebSocket.OPEN
        });
    }
    
    return true; // Keep message channel open for async response
});
