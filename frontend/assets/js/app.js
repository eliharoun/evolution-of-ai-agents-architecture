/**
 * Main Application Entry Point
 * Initializes all modules and sets up event handlers
 */
import CONFIG from './config.js';
import appState from './state.js';
import { sendMessage } from './chat.js';
import { updateContextMonitor, updateStageSubtitle } from './ui.js';
import { initializeStageSelector } from './stages.js';
import { copyToClipboard } from './utils.js';

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('🚀 Initializing Customer Support Agent...');
    
    // Initialize session ID
    appState.getSessionId();
    
    // Initialize stage selector
    initializeStageSelector();
    
    // Setup event listeners
    setupEventListeners();
    
    // Check backend health
    checkBackendHealth();
    
    // Focus on input
    const userInput = document.getElementById('userInput');
    if (userInput) {
        userInput.focus();
    }
    
    console.log('✅ Application initialized successfully');
}

/**
 * Setup event listeners for UI interactions
 */
function setupEventListeners() {
    const sendButton = document.getElementById('sendButton');
    const userInput = document.getElementById('userInput');
    
    // Send button click
    if (sendButton) {
        sendButton.addEventListener('click', () => {
            const message = userInput.value.trim();
            if (message) {
                sendMessage(message);
                userInput.value = '';
            }
        });
    }
    
    // Enter key to send message
    if (userInput) {
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const message = userInput.value.trim();
                if (message) {
                    sendMessage(message);
                    userInput.value = '';
                }
            }
        });
    }
    
    // Thread ID copy functionality
    const threadIdDisplay = document.getElementById('threadIdDisplay');
    if (threadIdDisplay) {
        threadIdDisplay.addEventListener('click', () => {
            copyToClipboard(appState.currentThreadId, threadIdDisplay);
        });
    }
}

/**
 * Check backend health and initialize stage
 */
async function checkBackendHealth() {
    try {
        const response = await fetch(`${CONFIG.API_URL}/health`);
        const data = await response.json();
        console.log('Backend status:', data);
        
        if (data.stage) {
            appState.setStage(data.stage);
            updateContextMonitor();
        }
    } catch (error) {
        console.error('Backend not reachable:', error);
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            const warningDiv = document.createElement('div');
            warningDiv.className = 'message agent';
            warningDiv.textContent = '⚠️ Backend not connected. Please ensure the server is running on http://localhost:8000';
            chatMessages.appendChild(warningDiv);
        }
        document.getElementById('stageSubtitle').textContent = 'Backend Disconnected';
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

// Also handle window load event
window.addEventListener('load', () => {
    console.log('Window loaded - ensuring initialization...');
});

// Make copyThreadId available globally (for inline onclick)
window.copyThreadId = function() {
    if (appState.currentThreadId) {
        copyToClipboard(appState.currentThreadId, document.getElementById('threadIdDisplay'));
    }
};
