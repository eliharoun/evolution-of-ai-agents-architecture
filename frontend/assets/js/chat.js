/**
 * Chat Management - Handles chat interactions and messaging
 */
import CONFIG from './config.js';
import appState from './state.js';
import { estimateTokens, scrollToBottom, clearEmptyStates, formatMessage, isStage4, isSpecialistConsultation, getSpecialistInfo } from './utils.js';
import { updateContextMonitor, updateThreadIdDisplay } from './ui.js';

const chatMessages = document.getElementById('chatMessages');
const processContent = document.getElementById('processContent');

/**
 * Add user message to chat
 * @param {string} message - User message text
 */
export function addUserMessage(message) {
    clearEmptyStates();
    appState.incrementMessages();
    appState.addTokens(estimateTokens(message));
    updateContextMonitor();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.textContent = message;
    chatMessages.appendChild(messageDiv);
    scrollToBottom(chatMessages);
}

/**
 * Add agent message to chat
 * @param {string} message - Agent message text
 * @param {boolean} isThinking - Whether this is a thinking state
 * @returns {HTMLElement} Message element
 */
export function addAgentMessage(message, isThinking = false) {
    if (!isThinking) {
        appState.incrementMessages();
        appState.addTokens(estimateTokens(message));
        updateContextMonitor();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message agent ${isThinking ? 'thinking' : ''}`;
    
    if (isThinking) {
        messageDiv.textContent = message;
    } else {
        messageDiv.innerHTML = formatMessage(message);
    }
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom(chatMessages);
    return messageDiv;
}

/**
 * Create response card for grouping process items
 * @returns {HTMLElement} Response card element
 */
export function createResponseCard() {
    appState.incrementResponses();
    const cardDiv = document.createElement('div');
    cardDiv.className = 'response-card';
    cardDiv.innerHTML = `
        <div class="response-card-header">
            <div class="response-card-title">
                🤖 Agent Response #${appState.responseCount}
                <span class="struggle-badge" id="struggleBadge${appState.responseCount}">⚠️ 0 Struggles</span>
            </div>
            <div class="response-card-toggle">▼</div>
        </div>
        <div class="response-card-content"></div>
    `;
    
    // Add click handler for collapse/expand
    const header = cardDiv.querySelector('.response-card-header');
    header.addEventListener('click', () => {
        cardDiv.classList.toggle('collapsed');
    });
    
    processContent.appendChild(cardDiv);
    scrollToBottom(processContent);
    return cardDiv;
}

/**
 * Update struggle badge with count
 * @param {Object} stats - Struggle statistics
 */
export function updateStruggleBadge(stats) {
    if (!appState.currentResponseCard) return;
    
    let struggleCount = 0;
    if (stats.high_iterations) struggleCount++;
    if (stats.tool_confusion) struggleCount++;
    if (stats.context_loss) struggleCount++;
    
    const badge = appState.currentResponseCard.querySelector('.struggle-badge');
    if (badge && struggleCount > 0) {
        badge.textContent = `⚠️ ${struggleCount} Struggle${struggleCount > 1 ? 's' : ''}`;
        badge.classList.add('visible');
    }
}

/**
 * Add struggle summary panel
 * @param {Object} stats - Struggle statistics
 */
export function addStruggleSummary(stats) {
    if (!appState.currentResponseCard) return;
    
    const hasStruggles = stats.high_iterations || stats.tool_confusion || stats.context_loss;
    if (!hasStruggles) return;
    
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'struggle-summary';
    
    let summaryHtml = `<div class="struggle-summary-title">⚠️ Agent Struggle Analysis</div>`;
    
    if (stats.high_iterations) {
        summaryHtml += `
            <div class="struggle-stat">
                <div class="struggle-stat-icon">🔄</div>
                <div class="struggle-stat-detail">
                    <strong>High Iterations:</strong> Agent took ${stats.iteration_count} iterations to complete the task.
                </div>
            </div>
        `;
    }
    
    if (stats.tool_confusion) {
        summaryHtml += `
            <div class="struggle-stat">
                <div class="struggle-stat-icon">🤔</div>
                <div class="struggle-stat-detail">
                    <strong>Tool Confusion:</strong> Agent used ${stats.unique_tools} different tools, suggesting uncertainty.
                </div>
            </div>
        `;
    }
    
    if (stats.context_loss) {
        summaryHtml += `
            <div class="struggle-stat">
                <div class="struggle-stat-icon">📉</div>
                <div class="struggle-stat-detail">
                    <strong>Context Loss:</strong> Agent repeatedly called the same tools, indicating possible memory issues.
                </div>
            </div>
        `;
    }
    
    summaryDiv.innerHTML = summaryHtml;
    
    const cardContent = appState.currentResponseCard.querySelector('.response-card-content');
    cardContent.appendChild(summaryDiv);
}

/**
 * Add thought process item
 * @param {string} type - Item type ('thought', 'observation', 'response')
 * @param {string} content - Item content
 * @param {Object} toolInfo - Tool information (optional)
 * @param {Object} data - Additional data (optional)
 */
export function addProcessItem(type, content, toolInfo = null, data = null) {
    clearEmptyStates();
    
    if (toolInfo) {
        appState.incrementTools();
        updateContextMonitor();
    }
    
    // For Stage 3, use specialized handlers
    if (appState.currentStage >= 3 && appState.currentStage < 4 && data) {
        if (data.node === 'plan') {
            addReWOOPlan(data);
            return;
        } else if (data.node === 'tool') {
            addReWOOEvidence(data);
            return;
        }
    }
    
    // For Stage 4, handle supervisor-specialist interactions
    if (isStage4(appState.currentStage) && toolInfo && isSpecialistConsultation(toolInfo)) {
        addSupervisorDelegation(toolInfo, content);
        return;
    }
    
    const itemDiv = document.createElement('div');
    itemDiv.className = `process-item ${type}`;
    
    let typeLabel = type.charAt(0).toUpperCase() + type.slice(1);
    if (type === 'thought') typeLabel = '💭 Thought';
    if (type === 'observation') typeLabel = '🔍 Observation';
    if (type === 'response') typeLabel = '💬 Response';
    
    let contentHtml = `<div class="process-item-type">${typeLabel}</div>`;
    contentHtml += `<div class="process-item-content">${content}`;
    
    if (toolInfo) {
        contentHtml += `<span class="tool-badge">${toolInfo.name}</span>`;
        if (Object.keys(toolInfo.args).length > 0) {
            contentHtml += `<pre>${JSON.stringify(toolInfo.args, null, 2)}</pre>`;
        }
    }
    
    contentHtml += `</div>`;
    itemDiv.innerHTML = contentHtml;
    
    // Add to current response card if exists
    if (appState.currentResponseCard) {
        const cardContent = appState.currentResponseCard.querySelector('.response-card-content');
        cardContent.appendChild(itemDiv);
        appState.currentResponseProcessItems.push(itemDiv);
    } else {
        processContent.appendChild(itemDiv);
    }
    
    scrollToBottom(processContent);
}

/**
 * Add ReWOO Plan display
 * @param {Object} data - Plan data
 */
function addReWOOPlan(data) {
    const itemDiv = document.createElement('div');
    itemDiv.className = 'process-item thought';
    
    const planText = data.plan || '';
    const stepCount = data.content.match(/Planning complete: (\d+) steps/)?.[1] || '?';
    
    const planLines = planText.split('\n').filter(line => line.trim());
    let stepsHtml = '';
    let stepNumber = 0;
    
    planLines.forEach((line) => {
        if (line.trim().startsWith('Plan:')) {
            stepNumber++;
            const evidenceMatch = line.match(/(#E\d+)\s*=\s*(\w+)\[([^\]]+)\]/);
            
            if (evidenceMatch) {
                const [, evidenceVar, tool, args] = evidenceMatch;
                const description = line.substring(0, line.indexOf(evidenceVar)).replace(/Plan:\s*/, '').trim();
                
                stepsHtml += `
                    <div class="plan-step">
                        <div style="margin-bottom: 6px;">
                            <span style="display: inline-block; background: #667eea; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; margin-right: 8px;">Step ${stepNumber}</span>
                            ${description}
                        </div>
                        <div style="margin-left: 12px; padding: 6px 10px; background: white; border-radius: 4px;">
                            <span class="evidence-var">${evidenceVar}</span> = ${tool}[${args}]
                        </div>
                    </div>
                `;
            }
        }
    });
    
    itemDiv.innerHTML = `
        <div class="process-item-type">📋 REWOO PLAN</div>
        <div class="process-item-content">
            <strong>Generated ${stepCount}-step execution plan</strong>
            <div class="expandable-content">${stepsHtml}</div>
        </div>
    `;
    
    if (appState.currentResponseCard) {
        const cardContent = appState.currentResponseCard.querySelector('.response-card-content');
        cardContent.appendChild(itemDiv);
    } else {
        processContent.appendChild(itemDiv);
    }
    
    scrollToBottom(processContent);
}

/**
 * Add ReWOO Evidence display
 * @param {Object} data - Evidence data
 */
function addReWOOEvidence(data) {
    appState.incrementTools();
    updateContextMonitor();
    
    const itemDiv = document.createElement('div');
    itemDiv.className = 'process-item observation';
    
    const content = data.content;
    const match = content.match(/^(#E\d+):\s*(.+)$/);
    
    let contentHtml = '';
    if (match) {
        const [, evidenceVar, evidenceResult] = match;
        contentHtml = `
            <div class="process-item-type">🔍 EVIDENCE GATHERED</div>
            <div class="process-item-content">
                <strong>${evidenceVar}</strong>
                <div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                    ${evidenceResult}
                </div>
            </div>
        `;
    } else {
        contentHtml = `
            <div class="process-item-type">🔍 EVIDENCE GATHERED</div>
            <div class="process-item-content">${content}</div>
        `;
    }
    
    itemDiv.innerHTML = contentHtml;
    
    if (appState.currentResponseCard) {
        const cardContent = appState.currentResponseCard.querySelector('.response-card-content');
        cardContent.appendChild(itemDiv);
    } else {
        processContent.appendChild(itemDiv);
    }
    
    scrollToBottom(processContent);
}

/**
 * Add supervisor delegation visualization
 * @param {Object} toolInfo - Tool information
 * @param {string} content - Content
 */
function addSupervisorDelegation(toolInfo, content) {
    const specialist = getSpecialistInfo(toolInfo.name);
    const isParallel = appState.currentDelegationTools && appState.currentDelegationTools.length > 1;
    
    const itemDiv = document.createElement('div');
    itemDiv.className = 'supervisor-delegation';
    
    let executionType = '';
    let executionExplanation = '';
    
    if (isParallel) {
        executionType = '<span class="parallel-indicator">PARALLEL</span>';
        executionExplanation = 'Multiple specialists working simultaneously';
    } else {
        executionType = '<span class="sequential-indicator">SEQUENTIAL</span>';
        executionExplanation = 'Single specialist or dependent operations';
    }
    
    const request = toolInfo.args ? toolInfo.args.request || JSON.stringify(toolInfo.args) : '';
    
    itemDiv.innerHTML = `
        <div class="supervisor-delegation-title">
            🎯 Supervisor Delegation ${executionType}
        </div>
        <div class="specialist-consultation">
            <div class="specialist-name">
                ${specialist.emoji} ${specialist.name}
            </div>
            <div class="specialist-request">
                Request: "${request}"
            </div>
            <div style="font-size: 11px; color: #999; margin-top: 4px;">
                ${executionExplanation}
            </div>
        </div>
    `;
    
    itemDiv.dataset.toolName = toolInfo.name;
    itemDiv.dataset.specialistEmoji = specialist.emoji;
    
    if (appState.currentResponseCard) {
        const cardContent = appState.currentResponseCard.querySelector('.response-card-content');
        cardContent.appendChild(itemDiv);
        appState.currentResponseProcessItems.push(itemDiv);
    } else {
        processContent.appendChild(itemDiv);
    }
    
    scrollToBottom(processContent);
}

/**
 * Send message to backend
 * @param {string} message - Message to send
 */
export async function sendMessage(message) {
    if (!message || appState.isProcessing) return;

    addUserMessage(message);
    
    const thinkingMsg = addAgentMessage('Agent is thinking...', true);
    appState.isProcessing = true;
    
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    sendButton.innerHTML = '<span class="spinner"></span>';
    
    appState.currentResponseCard = createResponseCard();
    appState.currentResponseProcessItems = [];

    try {
        const response = await fetch(`${CONFIG.API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                stream: true,
                session_id: appState.getSessionId()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        thinkingMsg.remove();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let agentResponseDiv = null;
        let agentResponse = '';
        let struggleSummaryAdded = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'thread_id') {
                            appState.setThreadId(data.thread_id);
                            console.log('🔗 Thread ID:', data.thread_id);
                            updateThreadIdDisplay(data.thread_id);
                        }
                        else if (data.type === 'thought') {
                            addProcessItem('thought', data.content, data.tool_call, data);
                        }
                        else if (data.type === 'observation') {
                            addProcessItem('observation', data.content, null, data);
                        }
                        else if (data.type === 'response_start') {
                            if (!agentResponseDiv) {
                                agentResponseDiv = addAgentMessage('');
                                agentResponseDiv.classList.add('typing');
                                agentResponseDiv.textNode = document.createTextNode('');
                                agentResponseDiv.appendChild(agentResponseDiv.textNode);
                            }
                            agentResponse = '';
                        }
                        else if (data.type === 'response_chunk') {
                            if (agentResponseDiv && agentResponseDiv.textNode) {
                                agentResponseDiv.textNode.appendData(data.content);
                                agentResponse += data.content;
                                scrollToBottom(chatMessages);
                            }
                        }
                        else if (data.type === 'response_complete') {
                            if (agentResponseDiv) {
                                agentResponseDiv.classList.remove('typing');
                                agentResponseDiv.innerHTML = '';
                                agentResponseDiv.innerHTML = formatMessage(agentResponse);
                                addProcessItem('response', 'Generated final response');
                            }
                            
                            if (data.struggle_stats && !struggleSummaryAdded) {
                                updateStruggleBadge(data.struggle_stats);
                                addStruggleSummary(data.struggle_stats);
                                struggleSummaryAdded = true;
                            }
                            
                            if (data.stage) {
                                appState.setStage(data.stage);
                                updateContextMonitor();
                            }
                        }
                        else if (data.type === 'done') {
                            if (!agentResponseDiv && agentResponse) {
                                const finalMsg = addAgentMessage('');
                                finalMsg.innerHTML = formatMessage(agentResponse);
                            }
                            
                            if (data.struggle_stats && !struggleSummaryAdded) {
                                updateStruggleBadge(data.struggle_stats);
                                addStruggleSummary(data.struggle_stats);
                                struggleSummaryAdded = true;
                            }
                            
                            appState.currentResponseCard = null;
                            appState.currentResponseProcessItems = [];
                        }
                        else if (data.type === 'error') {
                            addAgentMessage(`Error: ${data.content}`);
                        }
                    } catch (e) {
                        console.error('Parse error:', e);
                    }
                }
            }
        }

    } catch (error) {
        console.error('Error:', error);
        addAgentMessage(`Sorry, an error occurred: ${error.message}`);
    } finally {
        appState.resetInteraction();
        sendButton.disabled = false;
        sendButton.textContent = 'Send';
    }
}
