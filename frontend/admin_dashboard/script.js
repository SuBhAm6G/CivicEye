/**
 * CivicEye Admin Dashboard - JavaScript Controller
 * Handles live feed, status polling, alert management, and admin actions
 */

// =============================================================================
// Configuration
// =============================================================================

const CONFIG = {
    API_BASE: 'http://localhost:5000',
    POLL_INTERVAL: 500,  // ms
    LOG_REFRESH_INTERVAL: 5000  // ms
};

// =============================================================================
// State Management
// =============================================================================

let currentState = null;
let pollInterval = null;
let logRefreshInterval = null;

// =============================================================================
// DOM Elements
// =============================================================================

const elements = {
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
    refreshLogs: document.getElementById('refresh-logs'),
    demoTrigger: document.getElementById('demo-trigger'),
    demoReset: document.getElementById('demo-reset'),

    // Logs
    logEntries: document.getElementById('log-entries'),

    // Audio
    alertSound: document.getElementById('alert-sound')
};

// =============================================================================
// Initialization
// =============================================================================

function init() {
    console.log('CivicEye Admin Dashboard initializing...');

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

    console.log('Admin Dashboard initialized');
}

function setupEventListeners() {
    // Confirm violation
    if (elements.confirmBtn) {
        elements.confirmBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Confirm button clicked');
            sendAction('CONFIRM');
        });
    } else {
        console.error('Confirm button not found!');
    }

    // Ignore/False alarm
    if (elements.ignoreBtn) {
        elements.ignoreBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Ignore button clicked');
            sendAction('IGNORE');
        });
    } else {
        console.error('Ignore button not found!');
    }

    // Refresh logs
    if (elements.refreshLogs) {
        elements.refreshLogs.addEventListener('click', fetchLogs);
    }

    // Demo buttons
    if (elements.demoTrigger) {
        elements.demoTrigger.addEventListener('click', triggerDemoAlert);
    }
    if (elements.demoReset) {
        elements.demoReset.addEventListener('click', resetDemo);
    }
}

// =============================================================================
// Clock
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
// API Communication
// =============================================================================

async function fetchStatus() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/status`);
        const data = await response.json();

        updateStatusDisplay(data);

        if (data.state !== currentState) {
            handleStateChange(data.state, data.offender_details);
        }

        // Update timeout display
        if (data.timeout_remaining !== null) {
            elements.alertTimeout.textContent = `${Math.ceil(data.timeout_remaining)}s`;
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

// =============================================================================
// State Handling
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
            elements.statusIndicator.classList.add('');
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
// Log Display
// =============================================================================

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
// Audio
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
// Initialize on DOM Load
// =============================================================================

document.addEventListener('DOMContentLoaded', init);
