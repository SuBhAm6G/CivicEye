/**
 * CivicEye Public Display - JavaScript Controller
 * Handles state polling, audio management, and UI updates
 */

// =============================================================================
// Configuration
// =============================================================================

const CONFIG = {
    API_BASE: 'http://localhost:5000',
    POLL_INTERVAL: 500,  // ms
    WARNING_DURATION: 30  // seconds
};

// =============================================================================
// State Management
// =============================================================================

let currentState = 'IDLE';
let audioContext = null;
let sirenAudio = null;
let pollInterval = null;
let warningCountdown = CONFIG.WARNING_DURATION;
let countdownInterval = null;

// =============================================================================
// DOM Elements
// =============================================================================

const elements = {
    initOverlay: document.getElementById('init-overlay'),
    initBtn: document.getElementById('init-btn'),
    mainDisplay: document.getElementById('main-display'),
    statusIndicator: document.getElementById('status-indicator'),
    statusText: document.getElementById('status-text'),
    currentTime: document.getElementById('current-time'),
    currentDate: document.getElementById('current-date'),
    idleContent: document.getElementById('idle-content'),
    warningContent: document.getElementById('warning-content'),
    shamingContent: document.getElementById('shaming-content'),
    warningCountdown: document.getElementById('warning-countdown'),
    offenderPhoto: document.getElementById('offender-photo'),
    offenderId: document.getElementById('offender-id'),
    sirenAudio: document.getElementById('siren-audio')
};

// =============================================================================
// Initialization
// =============================================================================

function init() {
    // Set up init button click handler
    elements.initBtn.addEventListener('click', initializeSystem);

    // Start clock
    updateClock();
    setInterval(updateClock, 1000);
}

function initializeSystem() {
    // Initialize audio context (required for browser autoplay policy)
    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();

        // Pre-load siren audio
        sirenAudio = elements.sirenAudio;
        sirenAudio.load();

        // Test audio context by playing silent audio
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        gainNode.gain.value = 0;
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.start();
        oscillator.stop(audioContext.currentTime + 0.1);

        console.log('Audio context initialized successfully');
    } catch (error) {
        console.error('Audio initialization failed:', error);
    }

    // Hide overlay, show main display
    elements.initOverlay.classList.add('hidden');
    elements.mainDisplay.classList.remove('hidden');

    // Start polling for status
    startPolling();

    console.log('CivicEye Public Display initialized');
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
// Status Polling
// =============================================================================

function startPolling() {
    pollInterval = setInterval(fetchStatus, CONFIG.POLL_INTERVAL);
    fetchStatus(); // Initial fetch
}

async function fetchStatus() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/status`);
        const data = await response.json();

        if (data.state !== currentState) {
            handleStateChange(data.state, data.offender_details);
        }

        // Update timeout countdown if in WARNING
        if (data.state === 'WARNING' && data.timeout_remaining !== null) {
            warningCountdown = Math.ceil(data.timeout_remaining);
            elements.warningCountdown.textContent = warningCountdown;
        }

    } catch (error) {
        console.error('Status fetch error:', error);
        // Continue polling even on error
    }
}

// =============================================================================
// State Handling
// =============================================================================

function handleStateChange(newState, offenderDetails) {
    console.log(`State change: ${currentState} -> ${newState}`);

    // Clean up previous state
    cleanupState(currentState);

    // Update state
    currentState = newState;

    // Apply new state
    switch (newState) {
        case 'IDLE':
            activateIdleMode();
            break;
        case 'WARNING':
        case 'PENDING_REVIEW':
            activateWarningMode();
            break;
        case 'SHAMING':
            activateShamingMode(offenderDetails);
            break;
    }
}

function cleanupState(state) {
    // Stop audio
    stopSiren();

    // Remove body classes
    document.body.classList.remove('shaming-mode');

    // Clear countdown interval
    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }

    // Hide all content states
    elements.idleContent.classList.remove('active');
    elements.warningContent.classList.remove('active');
    elements.shamingContent.classList.remove('active');
}

function activateIdleMode() {
    // Update status indicator
    elements.statusIndicator.className = 'status-dot idle';
    elements.statusText.textContent = 'SYSTEM ONLINE';

    // Show idle content
    elements.idleContent.classList.add('active');

    console.log('IDLE mode activated');
}

function activateWarningMode() {
    // Update status indicator
    elements.statusIndicator.className = 'status-dot warning';
    elements.statusText.textContent = 'ALERT DETECTED';

    // Show warning content
    elements.warningContent.classList.add('active');

    // Start countdown
    warningCountdown = CONFIG.WARNING_DURATION;
    elements.warningCountdown.textContent = warningCountdown;

    // Play siren
    playSiren();

    console.log('WARNING mode activated');
}

function activateShamingMode(offenderDetails) {
    // Update status indicator
    elements.statusIndicator.className = 'status-dot shaming';
    elements.statusText.textContent = 'VIOLATION CONFIRMED';

    // Add body class for red flash effect
    document.body.classList.add('shaming-mode');

    // Update offender details
    if (offenderDetails) {
        elements.offenderPhoto.src = offenderDetails.photo_url || 'https://via.placeholder.com/150?text=OFFENDER';
        elements.offenderId.textContent = offenderDetails.id || 'CIV-XXX';
    }

    // Show shaming content
    elements.shamingContent.classList.add('active');

    // Stop siren for shaming (or play different sound)
    stopSiren();

    console.log('SHAMING mode activated', offenderDetails);
}

// =============================================================================
// Audio Management
// =============================================================================

function playSiren() {
    if (sirenAudio) {
        sirenAudio.currentTime = 0;
        sirenAudio.loop = true;

        const playPromise = sirenAudio.play();

        if (playPromise !== undefined) {
            playPromise.catch(error => {
                console.error('Siren playback failed:', error);
                // Try using Web Audio API as fallback
                playFallbackSiren();
            });
        }
    } else {
        playFallbackSiren();
    }
}

function stopSiren() {
    if (sirenAudio) {
        sirenAudio.pause();
        sirenAudio.currentTime = 0;
    }
}

function playFallbackSiren() {
    // Generate siren sound using Web Audio API
    if (!audioContext) return;

    try {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.type = 'sawtooth';
        oscillator.frequency.setValueAtTime(440, audioContext.currentTime);
        oscillator.frequency.linearRampToValueAtTime(880, audioContext.currentTime + 0.5);
        oscillator.frequency.linearRampToValueAtTime(440, audioContext.currentTime + 1);

        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.start();
        oscillator.stop(audioContext.currentTime + 1);

        // Repeat if still in warning mode
        setTimeout(() => {
            if (currentState === 'WARNING' || currentState === 'PENDING_REVIEW') {
                playFallbackSiren();
            }
        }, 1000);

    } catch (error) {
        console.error('Fallback siren failed:', error);
    }
}

// =============================================================================
// Initialize on DOM Load
// =============================================================================

document.addEventListener('DOMContentLoaded', init);
