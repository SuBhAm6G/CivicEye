"""
CivicEye Backend - Flask Application
Main server handling video streaming, status updates, and admin actions.
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.detector import LitterMonitor
from ai_engine.face_recog import FaceMatcher

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# =============================================================================
# GLOBAL STATE
# =============================================================================

SYSTEM_STATE = "IDLE"  # IDLE, WARNING, PENDING_REVIEW, SHAMING
STATE_TIMESTAMP = time.time()
STATE_TIMEOUT = 30.0  # Auto-reset after 30 seconds
CURRENT_OFFENDER = None
FRAME_LOCK = threading.Lock()
CURRENT_FRAME = None

# Public Display Control
DISPLAY_ENABLED = True
CUSTOM_MESSAGES = {
    "warning": "PLEASE PICK UP YOUR TRASH",
    "shaming": "LITTERING IS A CIVIC OFFENSE",
    "fine": "FINE: ₹500 | PRIOR OFFENSES LOGGED"
}

# Surveillance Control
SURVEILLANCE_ACTIVE = True

# Initialize AI components
litter_monitor = None
face_matcher = FaceMatcher()

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
INCIDENT_LOG_PATH = os.path.join(DATABASE_DIR, 'incident_log.json')

# Video source (will be set by main.py)
video_source = None


def init_detector(model_path='yolov8n.pt'):
    """Initialize the litter detector."""
    global litter_monitor
    litter_monitor = LitterMonitor(model_path)


def set_video_source(source):
    """Set the video source (camera index or file path)."""
    global video_source
    video_source = source


# =============================================================================
# STATE MANAGEMENT
# =============================================================================

def set_state(new_state, offender=None):
    """Set the system state with timestamp tracking."""
    global SYSTEM_STATE, STATE_TIMESTAMP, CURRENT_OFFENDER
    SYSTEM_STATE = new_state
    STATE_TIMESTAMP = time.time()
    if offender is not None:
        CURRENT_OFFENDER = offender
    if litter_monitor:
        litter_monitor.set_state(new_state)


def check_state_timeout():
    """Check if current state has timed out and reset if needed."""
    global SYSTEM_STATE
    if SYSTEM_STATE in ["WARNING", "PENDING_REVIEW"]:
        if time.time() - STATE_TIMESTAMP > STATE_TIMEOUT:
            set_state("IDLE")
            return True
    return False


def load_incident_log():
    """Load incident log from JSON file."""
    try:
        with open(INCIDENT_LOG_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_incident(incident):
    """Save an incident to the log."""
    incidents = load_incident_log()
    incidents.append(incident)
    with open(INCIDENT_LOG_PATH, 'w') as f:
        json.dump(incidents, f, indent=2)


# =============================================================================
# VIDEO STREAMING
# =============================================================================

def generate_frames():
    """Generate video frames for streaming."""
    global CURRENT_FRAME, SYSTEM_STATE
    
    import cv2
    
    # Try to open video source
    cap = None
    if video_source is not None:
        cap = cv2.VideoCapture(video_source)
    else:
        # Try webcam
        cap = cv2.VideoCapture(0)
    
    if not cap or not cap.isOpened():
        # Generate placeholder frame
        while True:
            frame = create_placeholder_frame("NO VIDEO SOURCE")
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.1)
    
    while True:
        ret, frame = cap.read()
        
        # Loop video if end reached
        if not ret or frame is None:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                continue
        
        # Check if surveillance is active
        if SURVEILLANCE_ACTIVE:
            # Check for state timeout
            check_state_timeout()
            
            # Process frame with AI detector
            if litter_monitor:
                annotated_frame, detected_state = litter_monitor.detect_frame(frame)
                
                # Update state based on detection
                if detected_state == "WARNING" and SYSTEM_STATE == "IDLE":
                    # Generate mock offender data
                    offender = face_matcher.match_face()
                    set_state("WARNING", offender)
                
                frame = annotated_frame if annotated_frame is not None else frame
        else:
            # Surveillance paused - show overlay
            import cv2
            import numpy as np
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)
            
            # Add "PAUSED" text
            text = "SURVEILLANCE PAUSED"
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_size = cv2.getTextSize(text, font, 2, 3)[0]
            text_x = (frame.shape[1] - text_size[0]) // 2
            text_y = (frame.shape[0] + text_size[1]) // 2
            cv2.putText(frame, text, (text_x, text_y), font, 2, (0, 165, 255), 3)
        
        with FRAME_LOCK:
            CURRENT_FRAME = frame.copy()
        
        # Encode and yield frame
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Control frame rate
        time.sleep(0.033)  # ~30 FPS


def create_placeholder_frame(message="CivicEye"):
    """Create a placeholder frame when no video is available."""
    import cv2
    import numpy as np
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add gradient background
    for i in range(480):
        frame[i, :] = [int(20 + i * 0.05), int(10 + i * 0.02), int(30 + i * 0.08)]
    
    # Add text
    cv2.putText(frame, message, (120, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 2)
    cv2.putText(frame, "Waiting for video source...", (150, 300),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 1)
    
    return frame


# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/')
def index():
    """Root endpoint."""
    return jsonify({
        "name": "CivicEye API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/video_feed",
            "/status",
            "/admin/action",
            "/get_logs"
        ]
    })


@app.route('/video_feed')
def video_feed():
    """Video streaming endpoint."""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/status')
def get_status():
    """Get current system status."""
    check_state_timeout()  # Check for timeout on each status request
    
    return jsonify({
        "state": SYSTEM_STATE,
        "timestamp": STATE_TIMESTAMP,
        "offender_details": CURRENT_OFFENDER,
        "timeout_remaining": max(0, STATE_TIMEOUT - (time.time() - STATE_TIMESTAMP)) 
                            if SYSTEM_STATE in ["WARNING", "PENDING_REVIEW"] else None,
        "display_enabled": DISPLAY_ENABLED,
        "custom_messages": CUSTOM_MESSAGES,
        "surveillance_active": SURVEILLANCE_ACTIVE
    })


@app.route('/admin/action', methods=['POST'])
def admin_action():
    """Handle admin actions (CONFIRM or IGNORE)."""
    global SYSTEM_STATE, CURRENT_OFFENDER
    
    data = request.get_json()
    action = data.get('action', '').upper()
    
    if action == 'CONFIRM':
        # Set to SHAMING state
        set_state("SHAMING")
        
        # Log the incident
        incident = {
            "id": f"INC-{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "offender": CURRENT_OFFENDER,
            "status": "CONFIRMED",
            "action_by": data.get('admin_id', 'ADMIN-001')
        }
        save_incident(incident)
        
        # Schedule auto-reset after 10 seconds of shaming
        def reset_after_shaming():
            time.sleep(10)
            set_state("IDLE")
        threading.Thread(target=reset_after_shaming, daemon=True).start()
        
        return jsonify({
            "success": True,
            "message": "Violation confirmed. Shaming mode activated.",
            "incident_id": incident["id"]
        })
    
    elif action == 'IGNORE':
        # Reset to IDLE
        set_state("IDLE")
        CURRENT_OFFENDER = None
        
        return jsonify({
            "success": True,
            "message": "Alert dismissed. System reset to IDLE."
        })
    
    else:
        return jsonify({
            "success": False,
            "message": f"Unknown action: {action}"
        }), 400


@app.route('/get_logs')
def get_logs():
    """Get incident log history."""
    incidents = load_incident_log()
    return jsonify({
        "count": len(incidents),
        "incidents": incidents
    })


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve static assets."""
    assets_dir = os.path.join(os.path.dirname(BASE_DIR), 'assets')
    return send_from_directory(assets_dir, filename)


@app.route('/display/toggle', methods=['POST'])
def toggle_display():
    """Toggle public display on/off."""
    global DISPLAY_ENABLED
    data = request.get_json()
    DISPLAY_ENABLED = data.get('enabled', True)
    return jsonify({
        "success": True,
        "display_enabled": DISPLAY_ENABLED
    })


@app.route('/display/messages', methods=['POST'])
def update_messages():
    """Update custom display messages."""
    global CUSTOM_MESSAGES
    data = request.get_json()
    
    if 'warning' in data:
        CUSTOM_MESSAGES['warning'] = data['warning']
    if 'shaming' in data:
        CUSTOM_MESSAGES['shaming'] = data['shaming']
    if 'fine' in data:
        CUSTOM_MESSAGES['fine'] = data['fine']
    
    return jsonify({
        "success": True,
        "custom_messages": CUSTOM_MESSAGES
    })


@app.route('/surveillance/toggle', methods=['POST'])
def toggle_surveillance():
    """Toggle surveillance on/off."""
    global SURVEILLANCE_ACTIVE
    data = request.get_json()
    SURVEILLANCE_ACTIVE = data.get('active', True)
    
    # If resuming, reset to IDLE state
    if SURVEILLANCE_ACTIVE:
        set_state("IDLE")
    
    return jsonify({
        "success": True,
        "surveillance_active": SURVEILLANCE_ACTIVE
    })


# =============================================================================
# DEBUG/DEMO ROUTES
# =============================================================================

@app.route('/demo/trigger_warning', methods=['POST'])
def demo_trigger_warning():
    """Demo endpoint to manually trigger WARNING state."""
    offender = face_matcher.match_face()
    set_state("WARNING", offender)
    return jsonify({
        "success": True,
        "message": "WARNING state triggered",
        "offender": offender
    })


@app.route('/demo/reset', methods=['POST'])
def demo_reset():
    """Demo endpoint to reset system state."""
    set_state("IDLE")
    return jsonify({
        "success": True,
        "message": "System reset to IDLE"
    })


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    init_detector()
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
