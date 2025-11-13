/**
 * Application state management
 */
class AppState {
    constructor() {
        this.isProcessing = false;
        this.messageCount = 0;
        this.totalTokens = 0;
        this.toolCallCount = 0;
        this.currentStage = 1;
        this.responseCount = 0;
        this.currentResponseCard = null;
        this.currentResponseProcessItems = [];
        this.sessionId = null;
        this.currentThreadId = null;
        this.stagesData = [];
        this.currentStageInfo = null;
        this.checkpointsData = [];
        this.selectedCheckpointIndex = null;
        this.currentDelegationTools = [];
        this.delegationTimeout = null;
    }

    // Session management
    getSessionId() {
        if (!this.sessionId) {
            this.sessionId = localStorage.getItem('agent_session_id');
            if (!this.sessionId) {
                this.sessionId = 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('agent_session_id', this.sessionId);
                console.log('Generated new session ID:', this.sessionId);
            } else {
                console.log('Reusing session ID:', this.sessionId);
            }
        }
        return this.sessionId;
    }

    // Reset state for new interaction
    resetInteraction() {
        this.isProcessing = false;
        this.currentResponseCard = null;
        this.currentResponseProcessItems = [];
    }

    // Increment counters
    incrementMessages() {
        this.messageCount++;
    }

    incrementTools() {
        this.toolCallCount++;
    }

    incrementResponses() {
        this.responseCount++;
    }

    addTokens(count) {
        this.totalTokens += count;
    }

    // Stage management
    setStage(stage) {
        this.currentStage = stage;
    }

    setStagesData(data) {
        this.stagesData = data;
    }

    setCurrentStageInfo(info) {
        this.currentStageInfo = info;
    }

    // Thread management
    setThreadId(threadId) {
        this.currentThreadId = threadId;
    }

    // Checkpoint management
    setCheckpoints(checkpoints) {
        this.checkpointsData = checkpoints;
    }

    setSelectedCheckpoint(index) {
        this.selectedCheckpointIndex = index;
    }
}

// Create singleton instance
const appState = new AppState();

export default appState;
