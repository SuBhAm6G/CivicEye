/**
 * CivicEye Unified Dashboard - JavaScript Controller
 * Handles tab navigation, monitoring, display control, and security alerts
 */

// =============================================================================
//CONFIG
// =============================================================================

const CONFIG = {
    API_BASE: 'http://localhost:5000',
    POLL_INTERVAL: 500,  // ms
    LOG_REFRESH_INTERVAL: 5000  // ms
};

// =============================================================================
// STATE MANAGEMENT
// =============================================================================

let currentState = null;
let pollInterval = null;
let logRefreshInterval = null;
let currentTab = 'monitoring';

// =============================================================================
// DOM ELEMENTS
// =============================================================================

const elements = {
    // Navigation
    navItems: document.querySelectorAll('.nav-item'),
    pageTitle: document.getElementById('page-title'),

    // Tabs
    tabs: {
        monitoring: document.getElementById('tab-monitoring'),
        display: document.getElementById('tab-display'),
        alerts: document.getElementById('tab-alerts')
    },

    // Status
    statusIndicator: document.getElementById('status-indicator'),
    statusText: document.getElementById('status-text'),
    currentTime: document.getElementById('current-time'),
    currentDate: document.getElementById('current-date'),

    // Video
    videoFeed: document.getElementById('video-feed'),

    // Stats
    activeCameras: document.getElementById('active-cameras'),
    alertsToday: document.getElementById('alerts-today'),
    confirmedViolations: document.getElementById('confirmed-violations'),
    pendingReview: document.getElementById('pending-review'),

    // Alert Panel
    alertPanel: document.getElementById('alert-panel'),
    noAlerts: document.getElementById('no-alerts'),
    activeAlert: document.getElementById('active-alert'),
    alertTime: document.getElementById('alert-time'),
    alertTimeout: document.getElementById('alert-timeout'),
    suspectPhoto: document.getElementById('suspect-photo'),
    suspectId: document.getElementById('suspect-id'),
    suspectName: document.getElementById('suspect-name'),

    // Buttons
    confirmBtn: document.getElementById('confirm-btn'),
    ignoreBtn: document.getElementById('ignore-btn'),
    pauseSurveillanceBtn: document.getElementById('pause-surveillance-btn'),

    // Display Control
    displayToggle: document.getElementById('display-toggle'),
    displayStatus: document.getElementById('display-status'),
    displayIdle: document.getElementById('display-idle'),
    displayWarning: document.getElementById('display-warning'),
    displayShaming: document.getElementById('display-shaming'),
    previewCountdown: document.getElementById('preview-countdown'),
    previewWarningText: document.getElementById('preview-warning-text'),
    previewShamingText: document.getElementById('preview-shaming-text'),
    previewFineText: document.getElementById('preview-fine-text'),
    previewOffenderPhoto: document.getElementById('preview-offender-photo'),
    messageWarning: document.getElementById('message-warning'),
    messageShaming: document.getElementById('message-shaming'),
    messageFine: document.getElementById('message-fine'),
    saveMessagesBtn: document.getElementById('save-messages-btn'),
    demoTrigger: document.getElementById('demo-trigger'),
    demoReset: document.getElementById('demo-reset'),

    // Security Alerts
    recentAlertsList: document.getElementById('recent-alerts-list'),
    refreshLogs: document.getElementById('refresh-logs'),
    logEntries: document.getElementById('log-entries'),

    // Audio
    alertSound: document.getElementById('alert-sound')
};

// =============================================================================
// INITIALIZATION
// =============================================================================

function init() {
    console.log('CivicEye Unified Dashboard initializing...');

    // Start clock
    updateClock();
    setInterval(updateClock, 1000);

    // Start status polling
    pollInterval = setInterval(fetchStatus, CONFIG.POLL_INTERVAL);
    fetchStatus();

    // Start log refresh
    logRefreshInterval = setInterval(fetchLogs, CONFIG.LOG_REFRESH_INTERVAL);
    fetchLogs();

    // Set up event listeners
    setupEventListeners();

    console.log('Unified Dashboard initialized');
}

function setupEventListeners() {
    // Tab navigation
    elements.navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tab = item.dataset.tab;
            switchTab(tab);
        });
    });

    // Alert actions
    if (elements.confirmBtn) {
        elements.confirmBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Confirm button clicked');
            sendAction('CONFIRM');
        });
    }

    if (elements.ignoreBtn) {
        elements.ignoreBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Ignore button clicked');
            sendAction('IGNORE');
        });
    }

    // Pause/Resume Surveillance
    if (elements.pauseSurveillanceBtn) {
        elements.pauseSurveillanceBtn.addEventListener('click', toggleSurveillance);
    }

    // Display controls
    if (elements.displayToggle) {
        elements.displayToggle.addEventListener('change', toggleDisplay);
    }

    if (elements.saveMessagesBtn) {
        elements.saveMessagesBtn.addEventListener('click', saveMessages);
    }

    if (elements.demoTrigger) {
        elements.demoTrigger.addEventListener('click', triggerDemoAlert);
    }

    if (elements.demoReset) {
        elements.demoReset.addEventListener('click', resetDemo);
    }

    // Refresh logs
    if (elements.refreshLogs) {
        elements.refreshLogs.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Refresh logs clicked');
            fetchLogs();
        });
    }
}

// =============================================================================
// TAB NAVIGATION
// =============================================================================

function switchTab(tabName) {
    console.log(`Switching to tab: ${tabName}`);
    currentTab = tabName;

    // Update nav items
    elements.navItems.forEach(item => {
        if (item.dataset.tab === tabName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Update tab content
    Object.keys(elements.tabs).forEach(key => {
        if (key === tabName) {
            elements.tabs[key].classList.add('active');
        } else {
            elements.tabs[key].classList.remove('active');
        }
    });

    // Update page title
    const titles = {
        monitoring: 'Live Monitoring',
        display: 'Public Display Control',
        alerts: 'Security Alerts'
    };
    elements.pageTitle.textContent = titles[tabName] || tabName;
}

// =============================================================================
// CLOCK
// =============================================================================

function updateClock() {
    const now = new Date();

    // Time
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    elements.currentTime.textContent = `${hours}:${minutes}:${seconds}`;

    // Date
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
        'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
    const day = String(now.getDate()).padStart(2, '0');
    const month = months[now.getMonth()];
    const year = now.getFullYear();
    elements.currentDate.textContent = `${day} ${month} ${year}`;
}

// =============================================================================
// API COMMUNICATION
// =============================================================================

async function fetchStatus() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/status`);
        const data = await response.json();

        updateStatusDisplay(data);
        updateDisplayPreview(data);

        if (data.state !== currentState) {
            handleStateChange(data.state, data.offender_details);
        }

        // Update timeout display
        if (data.timeout_remaining !== null) {
            elements.alertTimeout.textContent = `${Math.ceil(data.timeout_remaining)}s`;
            if (elements.previewCountdown) {
                elements.previewCountdown.textContent = Math.ceil(data.timeout_remaining);
            }
        }

        // Update custom messages in textareas
        if (data.custom_messages) {
            if (elements.messageWarning.value === '' || !elements.messageWarning.dataset.edited) {
                elements.messageWarning.value = data.custom_messages.warning;
            }
            if (elements.messageShaming.value === '' || !elements.messageShaming.dataset.edited) {
                elements.messageShaming.value = data.custom_messages.shaming;
            }
            if (elements.messageFine.value === '' || !elements.messageFine.dataset.edited) {
                elements.messageFine.value = data.custom_messages.fine;
            }
        }

    } catch (error) {
        console.error('Status fetch error:', error);
        elements.statusText.textContent = 'CONNECTION ERROR';
        elements.statusIndicator.className = 'status-dot';
        elements.statusIndicator.style.background = '#ff3366';
    }
}

async function fetchLogs() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/get_logs`);
        const data = await response.json();

        updateLogDisplay(data.incidents);
        updateRecentAlerts(data.incidents);
        updateStats(data.incidents);

    } catch (error) {
        console.error('Log fetch error:', error);
    }
}

async function sendAction(action) {
    console.log(`Sending action: ${action}`);

    try {
        const response = await fetch(`${CONFIG.API_BASE}/admin/action`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: action,
                admin_id: 'ADMIN-001'
            })
        });

        const data = await response.json();
        console.log('Action response:', data);

        if (data.success) {
            // Force immediate UI update
            if (action === 'IGNORE') {
                currentState = 'IDLE';
                hideAlert();
                console.log('Alert dismissed - UI updated');
            }

            // Refresh status immediately
            fetchStatus();

            // Refresh logs if confirmed
            if (action === 'CONFIRM') {
                setTimeout(fetchLogs, 500);
            }
        } else {
            console.error('Action failed:', data.message);
            alert('Action failed: ' + data.message);
        }

    } catch (error) {
        console.error('Action error:', error);
        alert('Failed to send action. Is the server running? Check console for details.');
    }
}

async function triggerDemoAlert() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/demo/trigger_warning`, {
            method: 'POST'
        });
        const data = await response.json();
        console.log('Demo trigger response:', data);
    } catch (error) {
        console.error('Demo trigger error:', error);
    }
}

async function resetDemo() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/demo/reset`, {
            method: 'POST'
        });
        const data = await response.json();
        console.log('Demo reset response:', data);
    } catch (error) {
        console.error('Demo reset error:', error);
    }
}

async function toggleDisplay() {
    const enabled = elements.displayToggle.checked;
    elements.displayStatus.textContent = enabled ? 'ON' : 'OFF';
    elements.displayStatus.style.color = enabled ? 'var(--accent-green)' : 'var(--accent-red)';

    try {
        const response = await fetch(`${CONFIG.API_BASE}/display/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled })
        });
        const data = await response.json();
        console.log('Display toggle response:', data);
    } catch (error) {
        console.error('Display toggle error:', error);
    }
}

async function saveMessages() {
    const messages = {
        warning: elements.messageWarning.value,
        shaming: elements.messageShaming.value,
        fine: elements.messageFine.value
    };

    try {
        const response = await fetch(`${CONFIG.API_BASE}/display/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(messages)
        });
        const data = await response.json();
        console.log('Messages saved:', data);

        // Update preview
        elements.previewWarningText.textContent = messages.warning;
        elements.previewShamingText.textContent = messages.shaming;
        elements.previewFineText.textContent = messages.fine;

        alert('Messages saved successfully!');
    } catch (error) {
        console.error('Save messages error:', error);
        alert('Failed to save messages');
    }
}

async function toggleSurveillance() {
    const btn = elements.pauseSurveillanceBtn;
    const isPaused = btn.classList.contains('paused');
    const newState = !isPaused; // true = active, false = paused

    try {
        const response = await fetch(`${CONFIG.API_BASE}/surveillance/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ active: newState })
        });
        const data = await response.json();
        console.log('Surveillance toggle response:', data);

        if (data.success) {
            if (newState) {
                // Resuming
                btn.classList.remove('paused');
                btn.querySelector('.btn-icon').textContent = '⏸️';
                btn.querySelector('.btn-text').textContent = 'PAUSE';
            } else {
                // Pausing
                btn.classList.add('paused');
                btn.querySelector('.btn-icon').textContent = '▶️';
                btn.querySelector('.btn-text').textContent = 'RESUME';
            }
        }
    } catch (error) {
        console.error('Surveillance toggle error:', error);
        alert('Failed to toggle surveillance');
    }
}

// =============================================================================
// STATE HANDLING
// =============================================================================

function handleStateChange(newState, offenderDetails) {
    console.log(`State change: ${currentState} -> ${newState}`);
    currentState = newState;

    switch (newState) {
        case 'IDLE':
            hideAlert();
            break;
        case 'WARNING':
        case 'PENDING_REVIEW':
            showAlert(offenderDetails);
            break;
        case 'SHAMING':
            showShamingState(offenderDetails);
            break;
    }
}

function updateStatusDisplay(data) {
    const state = data.state;

    // Update indicator
    elements.statusIndicator.className = 'status-dot';

    switch (state) {
        case 'IDLE':
            elements.statusIndicator.style.background = '#00ff88';
            elements.statusText.textContent = 'SYSTEM ONLINE';
            break;
        case 'WARNING':
        case 'PENDING_REVIEW':
            elements.statusIndicator.classList.add('warning');
            elements.statusText.textContent = 'ALERT ACTIVE';
            break;
        case 'SHAMING':
            elements.statusIndicator.classList.add('shaming');
            elements.statusText.textContent = 'VIOLATION CONFIRMED';
            break;
    }
}

function showAlert(offenderDetails) {
    elements.alertPanel.classList.add('has-alert');
    elements.noAlerts.classList.add('hidden');
    elements.activeAlert.classList.remove('hidden');

    // Update alert time
    const now = new Date();
    elements.alertTime.textContent = now.toLocaleTimeString();

    // Update suspect info
    if (offenderDetails) {
        elements.suspectPhoto.src = offenderDetails.photo_url || 'https://via.placeholder.com/70?text=?';
        elements.suspectId.textContent = offenderDetails.id || 'UNKNOWN';
        elements.suspectName.textContent = offenderDetails.name || 'Unknown Citizen';
    }

    // Update pending count
    elements.pendingReview.textContent = '1';

    // Play alert sound
    playAlertSound();
}

function hideAlert() {
    elements.alertPanel.classList.remove('has-alert');
    elements.noAlerts.classList.remove('hidden');
    elements.activeAlert.classList.add('hidden');

    // Update pending count
    elements.pendingReview.textContent = '0';

    // Stop alert sound
    stopAlertSound();
}

function showShamingState(offenderDetails) {
    // Keep showing alert panel but in confirmed state
    elements.alertPanel.classList.remove('has-alert');
    elements.noAlerts.classList.remove('hidden');
    elements.activeAlert.classList.add('hidden');

    // Update pending count
    elements.pendingReview.textContent = '0';

    // Stop alert sound
    stopAlertSound();
}

// =============================================================================
// DISPLAY PREVIEW
// =============================================================================

function updateDisplayPreview(data) {
    const state = data.state;

    // Hide all screens
    elements.displayIdle.classList.remove('active');
    elements.displayWarning.classList.remove('active');
    elements.displayShaming.classList.remove('active');

    // Show appropriate screen
    switch (state) {
        case 'IDLE':
            elements.displayIdle.classList.add('active');
            break;
        case 'WARNING':
        case 'PENDING_REVIEW':
            elements.displayWarning.classList.add('active');
            if (data.custom_messages) {
                elements.previewWarningText.textContent = data.custom_messages.warning;
            }
            break;
        case 'SHAMING':
            elements.displayShaming.classList.add('active');
            if (data.offender_details) {
                elements.previewOffenderPhoto.src = data.offender_details.photo_url || 'https://via.placeholder.com/150?text=?';
            }
            if (data.custom_messages) {
                elements.previewShamingText.textContent = data.custom_messages.shaming;
                elements.previewFineText.textContent = data.custom_messages.fine;
            }
            break;
    }
}

// =============================================================================
// SECURITY ALERTS
// =============================================================================

function updateRecentAlerts(incidents) {
    if (!incidents || incidents.length === 0) {
        elements.recentAlertsList.innerHTML = '<div class="alert-empty">No recent alerts</div>';
        return;
    }

    // Sort by timestamp (newest first) and take last 5
    const sorted = [...incidents].sort((a, b) =>
        new Date(b.timestamp) - new Date(a.timestamp)
    ).slice(0, 5);

    let html = '';
    for (const incident of sorted) {
        const time = new Date(incident.timestamp).toLocaleTimeString();
        const citizenId = incident.offender?.id || 'UNKNOWN';
        const photoUrl = incident.offender?.photo_url || 'https://via.placeholder.com/60?text=?';

        html += `
            <div class="alert-card">
                <img src="${photoUrl}" alt="Offender">
                <div class="alert-card-info">
                    <div class="alert-card-header">
                        <span class="alert-card-id">${citizenId}</span>
                        <span class="alert-card-time">${time}</span>
                    </div>
                    <div class="alert-card-type">Littering Incident</div>
                </div>
            </div>
        `;
    }

    elements.recentAlertsList.innerHTML = html;
}

function updateLogDisplay(incidents) {
    if (!incidents || incidents.length === 0) {
        elements.logEntries.innerHTML = '<div class="log-empty">No incidents recorded</div>';
        return;
    }

    // Sort by timestamp (newest first)
    const sortedIncidents = [...incidents].sort((a, b) =>
        new Date(b.timestamp) - new Date(a.timestamp)
    );

    let html = '';
    for (const incident of sortedIncidents.slice(0, 10)) {
        const time = new Date(incident.timestamp).toLocaleTimeString();
        const citizenId = incident.offender?.id || 'UNKNOWN';
        const status = incident.status || 'CONFIRMED';

        html += `
            <div class="log-entry">
                <span>${time}</span>
                <span>${citizenId}</span>
                <span class="status">${status}</span>
                <span>${incident.action_by}</span>
            </div>
        `;
    }

    elements.logEntries.innerHTML = html;
}

function updateStats(incidents) {
    if (!incidents) return;

    // Count today's incidents
    const today = new Date().toDateString();
    const todayIncidents = incidents.filter(inc => {
        const incDate = new Date(inc.timestamp).toDateString();
        return incDate === today;
    });

    elements.alertsToday.textContent = todayIncidents.length;
    elements.confirmedViolations.textContent = incidents.length;
}

// =============================================================================
// AUDIO
// =============================================================================

function playAlertSound() {
    if (elements.alertSound) {
        elements.alertSound.currentTime = 0;
        elements.alertSound.loop = true;
        elements.alertSound.play().catch(err => {
            console.log('Alert sound autoplay blocked:', err);
        });
    }
}

function stopAlertSound() {
    if (elements.alertSound) {
        elements.alertSound.pause();
        elements.alertSound.currentTime = 0;
    }
}

// =============================================================================
// INITIALIZE ON DOM LOAD
// =============================================================================

document.addEventListener('DOMContentLoaded', init);

// Mark textareas as edited when user types
document.addEventListener('DOMContentLoaded', () => {
    [elements.messageWarning, elements.messageShaming, elements.messageFine].forEach(el => {
        if (el) {
            el.addEventListener('input', () => {
                el.dataset.edited = 'true';
            });
        }
    });
});
