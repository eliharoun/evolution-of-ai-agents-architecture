/**
 * Stage Management - Handles stage selection and switching
 */
import CONFIG from './config.js';
import appState from './state.js';
import { showNotification } from './utils.js';
import { updateContextMonitor } from './ui.js';

/**
 * Fetch available stages from backend
 */
export async function fetchStages() {
    try {
        const response = await fetch(`${CONFIG.API_URL}/stages`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Convert backend format to array
        const stages = [];
        if (data.available_stages) {
            Object.entries(data.available_stages).forEach(([stageNum, stageInfo]) => {
                stages.push({
                    stage_num: parseFloat(stageNum),
                    name: stageInfo.name,
                    description: stageInfo.description,
                    tools_count: stageInfo.tools_count
                });
            });
        }
        
        appState.setStagesData(stages);
        console.log('📋 Available stages:', stages);
        populateStageDropdown();
        
    } catch (error) {
        console.error('Error fetching stages:', error);
        const dropdown = document.getElementById('stageDropdown');
        dropdown.innerHTML = '<option value="">Error loading stages</option>';
    }
}

/**
 * Populate stage dropdown with available stages
 */
function populateStageDropdown() {
    const dropdowns = ['stageDropdown', 'stageDropdownDebug'];
    
    dropdowns.forEach(dropdownId => {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return;
        
        dropdown.innerHTML = '';
        
        if (appState.stagesData.length === 0) {
            dropdown.innerHTML = '<option value="">No stages available</option>';
            return;
        }
        
        dropdown.innerHTML = '<option value="">Select a stage...</option>';
        
        appState.stagesData.forEach(stage => {
            const option = document.createElement('option');
            option.value = stage.stage_num;
            option.textContent = `Stage ${stage.stage_num}: ${stage.name}`;
            
            if (stage.stage_num === appState.currentStage) {
                option.selected = true;
            }
            
            dropdown.appendChild(option);
        });
    });
    
    if (appState.currentStage) {
        updateStageInfo(appState.currentStage);
        fetchStageTools(appState.currentStage);
    }
}

/**
 * Switch to selected stage
 */
export async function switchStage() {
    const mainDropdown = document.getElementById('stageDropdown');
    const debugDropdown = document.getElementById('stageDropdownDebug');
    
    let selectedStageNum;
    if (event && event.target) {
        selectedStageNum = event.target.value;
        if (event.target.id === 'stageDropdown') {
            debugDropdown.value = selectedStageNum;
        } else if (event.target.id === 'stageDropdownDebug') {
            mainDropdown.value = selectedStageNum;
        }
    } else {
        selectedStageNum = mainDropdown.value;
    }
    
    if (!selectedStageNum) return;
    
    try {
        console.log(`🔄 Switching to stage ${selectedStageNum}`);
        
        const response = await fetch(`${CONFIG.API_URL}/stage/${selectedStageNum}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Stage switched successfully:', data);
        
        appState.setStage(parseFloat(selectedStageNum));
        updateContextMonitor();
        
        updateStageInfo(selectedStageNum);
        fetchStageTools(selectedStageNum);
        
        showNotification(`Switched to Stage ${selectedStageNum}: ${data.message || 'Unknown'}`);
        
    } catch (error) {
        console.error('Error switching stage:', error);
        showNotification(`Error switching to stage: ${error.message}`, 'error');
        
        mainDropdown.value = appState.currentStage.toString();
        debugDropdown.value = appState.currentStage.toString();
    }
}

/**
 * Update stage info display in both sidebars
 * @param {string|number} stageNum - Stage number
 */
function updateStageInfo(stageNum) {
    const stageInfos = ['stageInfo', 'stageInfoDebug'];
    const stage = appState.stagesData.find(s => s.stage_num.toString() === stageNum.toString());
    
    stageInfos.forEach(infoId => {
        const stageInfo = document.getElementById(infoId);
        if (!stageInfo) return;
        
        if (stage) {
            appState.setCurrentStageInfo(stage);
            stageInfo.innerHTML = `
                <div style="font-weight: 600; color: #333; margin-bottom: 4px;">${stage.name}</div>
                <div style="font-size: 11px; color: #666;">${stage.description}</div>
            `;
        } else {
            stageInfo.textContent = `Stage ${stageNum} - Loading info...`;
        }
    });
}

/**
 * Fetch and display tools for selected stage
 * @param {string|number} stageNum - Stage number
 */
async function fetchStageTools(stageNum) {
    try {
        const response = await fetch(`${CONFIG.API_URL}/tools?stage=${stageNum}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`🛠️ Tools for stage ${stageNum}:`, data.tools);
        
        displayTools(data.tools || []);
        
    } catch (error) {
        console.error('Error fetching tools:', error);
        const toolsLists = ['toolsList', 'toolsListDebug'];
        toolsLists.forEach(listId => {
            const toolsList = document.getElementById(listId);
            if (toolsList) {
                toolsList.innerHTML = '<div style="color: #f44336; font-size: 11px;">Error loading tools</div>';
            }
        });
    }
}

/**
 * Display tools in both tools lists
 * @param {Array} tools - Array of tool objects
 */
function displayTools(tools) {
    const toolsLists = ['toolsList', 'toolsListDebug'];
    
    toolsLists.forEach(listId => {
        const toolsList = document.getElementById(listId);
        if (!toolsList) return;
        
        if (!tools || tools.length === 0) {
            toolsList.innerHTML = '<div style="color: #666; font-size: 11px; padding: 8px;">No tools available</div>';
            return;
        }
        
        let toolsHtml = '<div class="tools-list-title">Available Tools:</div>';
        
        tools.forEach(tool => {
            toolsHtml += `
                <div class="tool-item">
                    <div class="tool-item-name">${tool.name}</div>
                </div>
            `;
        });
        
        toolsList.innerHTML = toolsHtml;
    });
}

/**
 * Initialize stage selector on page load
 */
export function initializeStageSelector() {
    console.log('🎯 Initializing stage selector...');
    fetchStages();
}

// Make function available globally for onchange handler
window.switchStage = switchStage;
