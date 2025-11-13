/**
 * UI Management - Context monitoring and UI updates
 */
import appState from './state.js';

/**
 * Update context monitor widget
 */
export function updateContextMonitor() {
    document.getElementById('messageCount').textContent = appState.messageCount;
    document.getElementById('tokenCount').textContent = `~${appState.totalTokens.toLocaleString()}`;
    document.getElementById('toolCallCount').textContent = appState.toolCallCount;
    document.getElementById('currentStage').textContent = appState.currentStage;
    
    updateStageSubtitle();
    
    // Add warning/danger classes based on thresholds
    const tokenElement = document.getElementById('tokenCount');
    tokenElement.classList.remove('warning', 'danger');
    if (appState.totalTokens > 50000) {
        tokenElement.classList.add('danger');
    } else if (appState.totalTokens > 30000) {
        tokenElement.classList.add('warning');
    }
}

/**
 * Update stage subtitle in panel header
 */
export function updateStageSubtitle() {
    const subtitle = document.getElementById('stageSubtitle');
    const processSubtitle = document.querySelector('.process-panel .subtitle');
    
    const stage = appState.currentStage;
    
    if (stage === 1) {
        subtitle.textContent = 'Stage 1: Simple ReAct Agent';
        if (processSubtitle) processSubtitle.textContent = 'ReAct: Reasoning & Actions';
    } else if (stage === 2) {
        subtitle.textContent = 'Stage 2: Advanced ReAct Agent';
        if (processSubtitle) processSubtitle.textContent = 'ReAct: Reasoning & Actions';
    } else if (stage === 3.1) {
        subtitle.textContent = 'Stage 3.1: ReWOO Pattern';
        if (processSubtitle) processSubtitle.textContent = 'ReWOO: Plan → Execute → Solve';
    } else if (stage === 3.2) {
        subtitle.textContent = 'Stage 3.2: Reflection Pattern';
        if (processSubtitle) processSubtitle.textContent = 'Reflection: Generate → Critique → Refine';
    } else if (stage === 3.3) {
        subtitle.textContent = 'Stage 3.3: Plan-and-Execute';
        if (processSubtitle) processSubtitle.textContent = 'Plan-Execute: Plan → Execute → Replan';
    } else if (stage === 4.1 || stage === 4.11) {
        subtitle.textContent = 'Stage 4.1.1: Supervisor (Built-in)';
        if (processSubtitle) processSubtitle.textContent = 'Supervisor: Delegate → Coordinate → Synthesize';
    } else if (stage === 4.12) {
        subtitle.textContent = 'Stage 4.1.2: Supervisor (Custom)';
        if (processSubtitle) processSubtitle.textContent = 'Supervisor: Delegate → Coordinate → Synthesize';
    } else {
        subtitle.textContent = `Stage ${stage}`;
    }
}

/**
 * Toggle process panel visibility
 */
export function toggleProcessPanel() {
    const container = document.querySelector('.container');
    const panel = document.querySelector('.process-panel');
    const icon = document.getElementById('toggleIcon');
    
    container.classList.toggle('panel-collapsed');
    panel.classList.toggle('collapsed');
    
    if (panel.classList.contains('collapsed')) {
        icon.textContent = '▶';
    } else {
        icon.textContent = '−';
    }
}

/**
 * Switch between Chat and Debug tabs
 * @param {string} tabName - 'chat' or 'debug'
 */
export function switchTab(tabName) {
    const chatTab = document.getElementById('chatTab');
    const debugTab = document.getElementById('debugTab');
    const chatContainer = document.getElementById('chatContainer');
    const debugContainer = document.getElementById('debugContainer');
    
    if (tabName === 'chat') {
        chatTab.classList.add('active');
        debugTab.classList.remove('active');
        chatContainer.style.display = 'grid';
        debugContainer.classList.remove('active');
    } else {
        chatTab.classList.remove('active');
        debugTab.classList.add('active');
        chatContainer.style.display = 'none';
        debugContainer.classList.add('active');
        
        // Import and initialize checkpointing status when debug tab is opened
        import('./checkpoints.js').then(module => {
            module.getCheckpointingStatus();
        });
    }
}

/**
 * Update thread ID display
 * @param {string} threadId - Thread ID to display
 */
export function updateThreadIdDisplay(threadId) {
    const threadIdStat = document.getElementById('threadIdStat');
    const threadIdDisplay = document.getElementById('threadIdDisplay');
    threadIdStat.style.display = 'flex';
    threadIdDisplay.textContent = threadId.substring(0, 8) + '...';
    threadIdDisplay.title = `Click to copy: ${threadId}`;
    
    // Auto-populate debug tab
    document.getElementById('threadIdInput').value = threadId;
}

// Make functions available globally for onclick handlers
window.toggleProcessPanel = toggleProcessPanel;
window.switchTab = switchTab;
