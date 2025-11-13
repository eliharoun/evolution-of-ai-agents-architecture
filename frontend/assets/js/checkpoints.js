/**
 * Checkpoint Management - Handles debugging and time-travel
 */
import CONFIG from './config.js';
import appState from './state.js';
import { showNotification } from './utils.js';

/**
 * Get current checkpointing status
 */
export async function getCheckpointingStatus() {
    try {
        const response = await fetch(`${CONFIG.API_URL}/checkpointing/status`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📋 Checkpointing status:', data);
        
        updateCheckpointingUI(data);
        
    } catch (error) {
        console.error('Error fetching checkpointing status:', error);
        document.getElementById('checkpointingStatus').textContent = 'Error loading checkpointing status';
    }
}

/**
 * Update checkpointing UI elements
 * @param {Object} status - Checkpointing status object
 */
function updateCheckpointingUI(status) {
    const toggle = document.getElementById('checkpointingToggle');
    const statusDiv = document.getElementById('checkpointingStatus');
    const toggleSlider = toggle.nextElementSibling;
    const sliderButton = toggleSlider.querySelector('span');
    
    toggle.checked = status.checkpointing_enabled;
    
    if (status.checkpointing_enabled) {
        toggleSlider.style.backgroundColor = '#667eea';
        sliderButton.style.transform = 'translateX(26px)';
    } else {
        toggleSlider.style.backgroundColor = '#ccc';
        sliderButton.style.transform = 'translateX(0px)';
    }
    
    let statusText = `Status: ${status.checkpointing_enabled ? 'Enabled' : 'Disabled'}`;
    if (status.workflow_has_checkpointer) {
        statusText += ' • Checkpointer Active';
    }
    if (status.workflow_supports_checkpointing) {
        statusText += ' • Workflow Compatible';
    }
    
    statusDiv.textContent = statusText;
}

/**
 * Toggle checkpointing on/off
 */
export async function toggleCheckpointing() {
    const toggle = document.getElementById('checkpointingToggle');
    const enabled = toggle.checked;
    
    try {
        console.log(`🔧 ${enabled ? 'Enabling' : 'Disabling'} checkpointing...`);
        
        const response = await fetch(`${CONFIG.API_URL}/checkpointing/${enabled}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Checkpointing toggled:', data);
        
        updateCheckpointingUI({
            checkpointing_enabled: data.checkpointing_enabled,
            workflow_has_checkpointer: data.has_checkpointer,
            workflow_supports_checkpointing: data.workflow_reloaded
        });
        
        showNotification(data.message, 'success');
        
    } catch (error) {
        console.error('Error toggling checkpointing:', error);
        showNotification(`Error toggling checkpointing: ${error.message}`, 'error');
        
        toggle.checked = !enabled;
        updateCheckpointingUI({
            checkpointing_enabled: !enabled,
            workflow_has_checkpointer: false,
            workflow_supports_checkpointing: false
        });
    }
}

/**
 * Load checkpoints from backend
 */
export async function loadCheckpoints() {
    const threadId = document.getElementById('threadIdInput').value.trim();
    if (!threadId) {
        alert('Please enter a thread ID');
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/checkpoint/history/${threadId}?limit=${CONFIG.MAX_CHECKPOINT_LIMIT}`);
        const data = await response.json();
        
        if (!response.ok) {
            alert(`Error: ${data.detail || 'Failed to load checkpoints'}`);
            return;
        }
        
        appState.setCheckpoints(data.checkpoints);
        displayCheckpointTimeline(data);
        
    } catch (error) {
        alert(`Error loading checkpoints: ${error.message}`);
    }
}

/**
 * Display checkpoint timeline
 * @param {Object} data - Checkpoint data
 */
function displayCheckpointTimeline(data) {
    const timeline = document.getElementById('checkpointTimeline');
    
    if (data.checkpoint_count === 0) {
        timeline.innerHTML = '<div class="empty-state"><div>No checkpoints found for this thread</div></div>';
        return;
    }
    
    let html = `<div class="checkpoint-timeline"><h3>Checkpoint Timeline (${data.checkpoint_count} points)</h3>`;
    
    data.checkpoints.forEach((cp, idx) => {
        const time = new Date(cp.created_at).toLocaleTimeString();
        html += `
            <div class="checkpoint-item" onclick="window.selectCheckpoint(${idx})" id="cp-${idx}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>Step ${cp.step}</strong> - ${time}
                    </div>
                    <div style="font-size: 11px; color: #666;">
                        ${cp.evidence_count} evidence | ${cp.message_count} msgs
                    </div>
                </div>
                <div style="font-size: 12px; margin-top: 4px; color: #666;">
                    Next: ${cp.next_nodes.join(', ') || 'END'}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    timeline.innerHTML = html;
}

/**
 * Select a checkpoint to view details
 * @param {number} index - Checkpoint index
 */
export function selectCheckpoint(index) {
    appState.setSelectedCheckpoint(index);
    
    document.querySelectorAll('.checkpoint-item').forEach((el, i) => {
        if (i === index) {
            el.classList.add('selected');
        } else {
            el.classList.remove('selected');
        }
    });
    
    displayCheckpointDetails(appState.checkpointsData[index]);
    
    if (index < appState.checkpointsData.length - 1) {
        showCheckpointDiff(appState.checkpointsData[index], appState.checkpointsData[index + 1]);
    }
}

/**
 * Display checkpoint details
 * @param {Object} checkpoint - Checkpoint object
 */
function displayCheckpointDetails(checkpoint) {
    const details = document.getElementById('checkpointDetails');
    
    let html = `
        <div style="margin-bottom: 20px;">
            <h3>Checkpoint Details</h3>
            <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin-top: 10px;">
                <div><strong>Checkpoint ID:</strong> ${checkpoint.checkpoint_id}</div>
                <div><strong>Step:</strong> ${checkpoint.step}</div>
                <div><strong>Next Nodes:</strong> ${checkpoint.next_nodes.join(', ') || 'END'}</div>
                <div><strong>Evidence Count:</strong> ${checkpoint.evidence_count}</div>
                <div><strong>Message Count:</strong> ${checkpoint.message_count}</div>
                <div><strong>Created:</strong> ${new Date(checkpoint.created_at).toLocaleString()}</div>
            </div>
        </div>
        
        <div style="margin-bottom: 20px;">
            <button onclick="window.timeTravel('${checkpoint.checkpoint_id}')" 
                    style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer;">
                ⏮️ Jump to This Checkpoint
            </button>
            <p style="font-size: 12px; color: #666; margin-top: 8px;">
                Loads this checkpoint's state. Note: Checkpoint history is preserved.
            </p>
        </div>
        
        <div id="checkpointDiff"></div>
    `;
    
    details.innerHTML = html;
}

/**
 * Show visual diff between checkpoints
 * @param {Object} current - Current checkpoint
 * @param {Object} previous - Previous checkpoint
 */
function showCheckpointDiff(current, previous) {
    const diffDiv = document.getElementById('checkpointDiff');
    
    let html = '<h4>Changes from Previous Checkpoint</h4><div style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin-top: 10px;">';
    
    const evidenceDiff = current.evidence_count - previous.evidence_count;
    if (evidenceDiff > 0) {
        html += `<div style="color: #28a745;">✓ +${evidenceDiff} evidence gathered</div>`;
    }
    
    const messageDiff = current.message_count - previous.message_count;
    if (messageDiff > 0) {
        html += `<div style="color: #667eea;">✓ +${messageDiff} messages</div>`;
    }
    
    html += `<div>Step: ${previous.step} → ${current.step}</div>`;
    
    if (JSON.stringify(current.next_nodes) !== JSON.stringify(previous.next_nodes)) {
        html += `<div>Next: ${previous.next_nodes.join(', ') || 'none'} → ${current.next_nodes.join(', ') || 'END'}</div>`;
    }
    
    html += '</div>';
    diffDiv.innerHTML = html;
}

/**
 * Time travel: jump to checkpoint state
 * @param {string} checkpointId - Checkpoint ID
 */
export async function timeTravel(checkpointId) {
    const threadId = document.getElementById('threadIdInput').value.trim();
    
    if (!confirm('This will load the selected checkpoint state. Checkpoint history is preserved. Continue?')) {
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/checkpoint/reset/${threadId}/${checkpointId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            alert(`Error: ${data.detail || 'Failed to jump to checkpoint'}`);
            return;
        }
        
        alert(`Successfully jumped to checkpoint at step ${data.step}. Agent will continue from this state.`);
        loadCheckpoints();
        
    } catch (error) {
        alert(`Error jumping to checkpoint: ${error.message}`);
    }
}

// Make functions available globally
window.toggleCheckpointing = toggleCheckpointing;
window.loadCheckpoints = loadCheckpoints;
window.selectCheckpoint = selectCheckpoint;
window.timeTravel = timeTravel;
