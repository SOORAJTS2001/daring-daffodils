
// Background script for WebSocket Mouse Controller
// Handles WebSocket connections since content scripts have limitations

const WEBSOCKET_URL = "ws://localhost:8765";
const HTTP_POLLING_URL = "http://localhost:8766/data";

let websocket = null;
let isWebSocketEnabled = true;
let pollingInterval = null;

chrome.runtime.onInstalled.addListener(() => {
    console.log("WebSocket Mouse Controller installed and ready.");
    // Start with HTTP polling for better compatibility with service workers
    console.log("Background: Starting with HTTP polling (service worker compatibility)");
    startHttpPolling();
});

function initWebSocket() {
    // Note: Service workers may have limitations with WebSocket connections
    // This is kept for manual testing but HTTP polling is preferred
    if (!isWebSocketEnabled) return;
    
    try {
        websocket = new WebSocket(WEBSOCKET_URL);
        
        websocket.onopen = function(event) {
            console.log("Background: WebSocket connected to mobile app");
            // Stop HTTP polling if WebSocket works
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        };
        
        websocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log("Background: Received data via WebSocket:", data);
                
                // Send data to all content scripts
                chrome.tabs.query({}, (tabs) => {
                    tabs.forEach(tab => {
                        chrome.tabs.sendMessage(tab.id, {
                            type: "coordinate_data",
                            data: data
                        }).catch(() => {
                            // Ignore errors for tabs that don't have content script
                        });
                    });
                });
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
            console.error("Background: WebSocket error (service worker limitation):", error);
            console.log("Background: Using HTTP polling instead...");
            isWebSocketEnabled = false;
            startHttpPolling();
        };
        
    } catch (error) {
        console.error("Background: Failed to create WebSocket (using HTTP polling):", error);
        isWebSocketEnabled = false;
        startHttpPolling();
    }
}
                        });
                    });
                });
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
            console.log("Background: Switching to HTTP polling...");
            isWebSocketEnabled = false;
            startHttpPolling();
        };
        
    } catch (error) {
        console.error("Background: Failed to create WebSocket:", error);
        isWebSocketEnabled = false;
        startHttpPolling();
    }
}

function startHttpPolling() {
    console.log("Background: Starting HTTP polling mode");
    
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(HTTP_POLLING_URL);
            if (response.ok) {
                const data = await response.json();
                if (data && Object.keys(data).length > 0) {
                    // Send data to all content scripts
                    chrome.tabs.query({}, (tabs) => {
                        tabs.forEach(tab => {
                            chrome.tabs.sendMessage(tab.id, {
                                type: "coordinate_data", 
                                data: data
                            }).catch(() => {
                                // Ignore errors for tabs that don't have content script
                            });
                        });
                    });
                }
            }
        } catch (error) {
            console.error("Background: HTTP polling error:", error);
        }
    }, 50);
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
    }
    
    return true; // Keep message channel open for async response
});
