/**
 * Utility functions
 */
import CONFIG from './config.js';

/**
 * Estimate token count from text
 * @param {string} text - Text to estimate tokens for
 * @returns {number} Estimated token count
 */
export function estimateTokens(text) {
    return Math.ceil(text.length / CONFIG.TOKENS_PER_CHARACTER);
}

/**
 * Scroll element to bottom
 * @param {HTMLElement} element - Element to scroll
 */
export function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
}

/**
 * Clear empty state messages
 */
export function clearEmptyStates() {
    const chatMessages = document.getElementById('chatMessages');
    const processContent = document.getElementById('processContent');
    
    if (chatMessages && chatMessages.querySelector('.empty-state')) {
        chatMessages.innerHTML = '';
    }
    if (processContent && processContent.querySelector('.empty-state')) {
        processContent.innerHTML = '';
    }
}

/**
 * Format message with markdown-style formatting
 * @param {string} text - Text to format
 * @returns {string} Formatted HTML
 */
export function formatMessage(text) {
    if (!text) return '';
    
    console.log('Formatting text length:', text.length, 'Preview:', text.substring(0, 100));
    
    let formatted = text;
    
    // Bold text: **text** -> <strong>text</strong>
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Headers: ### text -> <h3>text</h3>
    formatted = formatted.replace(/^### (.+)$/gm, '<h3 style="margin: 12px 0 8px 0; color: #333;">$1</h3>');
    
    // Line breaks
    formatted = formatted.replace(/\n\n/g, '<br><br>');
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Bullet points
    formatted = formatted.replace(/^- (.+)$/gm, '<div style="margin: 4px 0; padding-left: 16px;">• $1</div>');
    
    // Numbered lists
    formatted = formatted.replace(/(\d+)\.\s+\*\*([^*]+)\*\*:/g, '<div style="margin: 8px 0; font-weight: 600;"><strong>$1. $2:</strong></div>');
    
    console.log('Formatted result length:', formatted.length, 'Has bold:', formatted.includes('<strong>'));
    
    return formatted;
}

/**
 * Show notification message
 * @param {string} message - Message to display
 * @param {string} type - Notification type ('success' or 'error')
 */
export function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'error' ? '#f44336' : '#4caf50'};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 2000;
        font-size: 13px;
        font-weight: 600;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @param {HTMLElement} element - Element to show feedback on
 */
export function copyToClipboard(text, element) {
    if (!text) return;
    
    navigator.clipboard.writeText(text).then(() => {
        if (element) {
            const originalText = element.textContent;
            element.textContent = '✓ Copied!';
            setTimeout(() => {
                element.textContent = originalText;
            }, 2000);
        }
    });
}

/**
 * Check if current stage is Stage 4
 * @param {number} stage - Current stage number
 * @returns {boolean}
 */
export function isStage4(stage) {
    return stage === 4.1 || stage === 4.11 || stage === 4.12;
}

/**
 * Check if tool is a specialist consultation
 * @param {Object} toolInfo - Tool information object
 * @returns {boolean}
 */
export function isSpecialistConsultation(toolInfo) {
    if (!toolInfo || !toolInfo.name) return false;
    
    const specialistTools = [
        'transfer_to_order_operations',
        'transfer_to_product_inventory', 
        'transfer_to_customer_account',
        'specialist_order_operations',
        'specialist_product_inventory',
        'specialist_customer_account'
    ];
    
    return specialistTools.includes(toolInfo.name);
}

/**
 * Get specialist info from tool name
 * @param {string} toolName - Tool name
 * @returns {Object} Specialist information
 */
export function getSpecialistInfo(toolName) {
    const specialists = {
        'transfer_to_order_operations': { name: 'Order Operations', emoji: '📦', color: '#ff9800' },
        'specialist_order_operations': { name: 'Order Operations', emoji: '📦', color: '#ff9800' },
        'transfer_to_product_inventory': { name: 'Product & Inventory', emoji: '🛍️', color: '#9c27b0' },
        'specialist_product_inventory': { name: 'Product & Inventory', emoji: '🛍️', color: '#9c27b0' },
        'transfer_to_customer_account': { name: 'Customer Account', emoji: '👤', color: '#2196f3' },
        'specialist_customer_account': { name: 'Customer Account', emoji: '👤', color: '#2196f3' }
    };
    
    return specialists[toolName] || { name: 'Unknown Specialist', emoji: '🤖', color: '#666' };
}
