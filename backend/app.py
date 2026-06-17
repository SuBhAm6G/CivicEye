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

# Evidence clip: list of base64-encoded JPEG strings (sampled frames from -10s to -7s)
EVIDENCE_FRAMES = []

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
    litter_monitor = LitterMonitor('yolov8s.pt')


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
                    import cv2
                    import base64
                    global EVIDENCE_FRAMES
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    raw_frames = litter_monitor.captured_violator_frames \
                        if hasattr(litter_monitor, 'captured_violator_frames') else []
                    
                    # Sample up to 12 frames evenly from the 3-second window
                    # Encode each as base64 JPEG (quality 70 — small + good enough)
                    encoded = []
                    if raw_frames:
                        step = max(1, len(raw_frames) // 12)
                        for f in raw_frames[::step][:12]:
                            ok, buf = cv2.imencode('.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 70])
                            if ok:
                                encoded.append(
                                    'data:image/jpeg;base64,' + base64.b64encode(buf).decode('utf-8')
                                )
                    
                    EVIDENCE_FRAMES = encoded  # Store for /evidence/frames endpoint
                    
                    # Use first frame as the static thumbnail (fallback if JS fails)
                    thumbnail_url = EVIDENCE_FRAMES[0] if EVIDENCE_FRAMES else None
                    
                    offender = {
                        "id": f"VIO-{timestamp}",
                        "name": "Unidentified Violator",
                        "photo_url": thumbnail_url or "",
                        "match_confidence": round(__import__('random').uniform(0.91, 0.99), 2),
                        "prior_offenses": 0,
                        "has_clip": len(EVIDENCE_FRAMES) > 0
                    }
                    
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
        
        # Log the incident (include evidence frames for the modal viewer)
        incident = {
            "id": f"INC-{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "offender": CURRENT_OFFENDER,
            "status": "CONFIRMED",
            "action_by": data.get('admin_id', 'ADMIN-001'),
            "location": "Sector 7-G, Main Gate",
            "fine": "₹500",
            "evidence_frames": EVIDENCE_FRAMES  # base64 JPEG list
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


@app.route('/evidence/frames')
def get_evidence_frames():
    """Return the current alert's evidence clip as base64-encoded JPEG frames."""
    return jsonify({
        "frames": EVIDENCE_FRAMES,
        "count": len(EVIDENCE_FRAMES)
    })


@app.route('/evidence/frames/<incident_id>')
def get_incident_evidence_frames(incident_id):
    """Return evidence frames for a specific past incident from the log."""
    incidents = load_incident_log()
    for inc in incidents:
        if inc.get('id') == incident_id:
            frames = inc.get('evidence_frames', [])
            return jsonify({"frames": frames, "count": len(frames)})
    return jsonify({"frames": [], "count": 0})


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve static assets."""
    assets_dir = os.path.join(os.path.dirname(BASE_DIR), 'assets')
    return send_from_directory(assets_dir, filename)


@app.route('/database/captured/<path:filename>')
def serve_captured_images(filename):
    """Serve captured violator images."""
    captured_dir = os.path.join(DATABASE_DIR, 'captured')
    return send_from_directory(captured_dir, filename)


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


@app.route('/export/pdf')
def export_pdf():
    """Generate and download a PDF incident report."""
    try:
        from fpdf import FPDF, XPos, YPos
    except ImportError:
        return jsonify({
            "error": "fpdf2 not installed. Run: pip install fpdf2"
        }), 500

    import io
    from flask import send_file

    incidents = load_incident_log()
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ---- Dark header bar ----
    pdf.set_fill_color(10, 14, 26)
    pdf.rect(0, 0, 210, 38, style='F')

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(0, 200, 255)
    pdf.set_xy(0, 6)
    pdf.cell(210, 12, "CIVICEYE", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(140, 160, 180)
    pdf.cell(210, 8, "Smart City Litter Surveillance  -  Incident Report", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)

    # ---- Meta block ----
    pdf.set_text_color(30, 30, 30)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(45, 7, "Generated:")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 7, generated_at, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(45, 7, "Zone / Camera:")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 7, "Sector 7-G, Main Gate  |  CAM-001", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(45, 7, "Total Incidents:")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 7, str(len(incidents)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # ---- Divider line ----
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.l_margin, pdf.get_y(), 210 - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

    if not incidents:
        pdf.set_font("Helvetica", "I", 11)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 12, "No incidents recorded.", align="C",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    else:
        # ---- Table header ----
        col_w = [32, 44, 36, 36, 42]
        headers = ["Incident ID", "Timestamp", "Citizen ID", "Status", "Action By"]

        pdf.set_fill_color(26, 31, 53)
        pdf.set_text_color(0, 200, 255)
        pdf.set_font("Helvetica", "B", 9)
        for i, h in enumerate(headers):
            last = (i == len(headers) - 1)
            pdf.cell(col_w[i], 9, h, border=1, fill=True,
                     new_x=XPos.LMARGIN if last else XPos.RIGHT,
                     new_y=YPos.NEXT if last else YPos.TOP)

        # ---- Table rows ----
        pdf.set_font("Helvetica", "", 8)
        for idx, inc in enumerate(reversed(incidents)):
            fill = idx % 2 == 0
            if fill:
                pdf.set_fill_color(235, 240, 255)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(20, 20, 20)

            ts = inc.get("timestamp", "")[:19].replace("T", " ")
            citizen_id = (inc.get("offender") or {}).get("id", "UNKNOWN")
            row = [
                inc.get("id", "")[:14],
                ts,
                citizen_id[:16],
                inc.get("status", "")[:12],
                inc.get("action_by", "")[:14],
            ]
            for i, val in enumerate(row):
                last = (i == len(row) - 1)
                pdf.cell(col_w[i], 8, val, border=1, fill=fill,
                         new_x=XPos.LMARGIN if last else XPos.RIGHT,
                         new_y=YPos.NEXT if last else YPos.TOP)

    # ---- Footer ----
    pdf.ln(10)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.l_margin, pdf.get_y(), 210 - pdf.r_margin, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5,
             "CivicEye v1.2.0  -  AMD SLINGSHOT 2026  |  CONFIDENTIAL - FOR MUNICIPAL USE ONLY",
             align="C")

    # ---- Stream as download ----
    buf = io.BytesIO(bytes(pdf.output()))
    buf.seek(0)
    filename = f"civiceye_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


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
    init_detector('yolov8s.pt')
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
