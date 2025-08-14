
chrome.runtime.onInstalled.addListener(() => {
    console.log("Firebase Mouse Controller installed and ready.");
});

// Example: listen for messages from firebase_app.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "log") {
        console.log("Message from content script:", message.data);
    }
});
