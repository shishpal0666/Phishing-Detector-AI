// This function runs INSIDE the web page (Gmail/Outlook) to find text
function extractEmailBody() {
    // 1. Try Gmail message body selector (class .a3s)
    const gmailBody = document.querySelector('.a3s.aiL');
    if (gmailBody && gmailBody.innerText.trim().length > 0) {
        return gmailBody.innerText;
    }

    // 2. Try Outlook/Hotmail message body selector
    // Outlook often uses ARIA labels or specific classes like .READINGPANE
    const outlookBody = document.querySelector('[aria-label="Message body"]');
    if (outlookBody && outlookBody.innerText.trim().length > 0) {
        return outlookBody.innerText;
    }
    
    // 3. Fallback: If user has highlighted text, use that
    const selection = window.getSelection().toString();
    if (selection.trim().length > 0) {
        return selection;
    }

    // 4. Final Fallback: Grab the whole visible page text (can be noisy)
    return document.body.innerText;
}

// Main Logic
document.addEventListener('DOMContentLoaded', async () => {
    const statusDiv = document.getElementById('status');
    const previewDiv = document.getElementById('preview');

    // 1. Get the active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab) {
        statusDiv.innerText = "Error: No active tab found.";
        return;
    }

    // 2. Inject the extraction script into the page
    try {
        const injectionResults = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: extractEmailBody,
        });

        // The result is an array (one per frame), we usually want the main frame (index 0)
        const emailText = injectionResults[0].result;

        if (!emailText || emailText.length < 5) {
            statusDiv.innerText = "⚠️ No email text found.";
            previewDiv.innerText = "Could not detect email body. Try highlighting the text manually and reopening this popup.";
            return;
        }

        // Show preview of text (first 200 chars)
        previewDiv.innerText = emailText.substring(0, 200) + "...";
        statusDiv.innerHTML = '<span class="loading">Analyzed by AI...</span>';

        // 3. Send to Python Backend
        const response = await fetch('http://127.0.0.1:5000/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: emailText })
        });

        const data = await response.json();

        // 4. Display Result
        if (data.is_phishing) {
            statusDiv.className = 'danger';
            statusDiv.innerHTML = `⚠️ PHISHING DETECTED<br><small>Confidence: ${data.confidence_score}%</small>`;
        } else {
            statusDiv.className = 'safe';
            statusDiv.innerHTML = `✅ LOOKS SAFE<br><small>Phishing Prob: ${data.confidence_score}%</small>`;
        }

    } catch (error) {
        console.error(error);
        statusDiv.className = 'neutral';
        statusDiv.innerText = "Connection Error.";
        previewDiv.innerText = "Is app.py running? \nError: " + error.message;
    }
});