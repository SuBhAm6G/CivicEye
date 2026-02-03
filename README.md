# 👁️ CivicEye - AI-Powered Litter Surveillance System

**Version 1.2.0**

CivicEye is an intelligent surveillance system that uses AI to detect littering incidents in real-time, identify offenders, and manage the enforcement workflow through an intuitive unified dashboard.

---

## 🎯 Features

### Core Functionality
- **Real-Time Litter Detection** - YOLOv8-powered object detection for bottles, cups, phones, food waste, and more
- **Face Recognition** - Automated offender identification with citizen database matching
- **Multi-State Workflow** - IDLE → WARNING → PENDING_REVIEW → SHAMING states with grace periods
- **Unified Admin Dashboard** - Single interface for monitoring, control, and alerts
- **Public Display Control** - Customizable warning/shaming messages with ON/OFF toggle
- **Incident Logging** - Comprehensive JSON-based logging with timestamps and evidence

### Version 1.2.0 - New Features ✨
- **🎮 Surveillance Pause/Resume** - Control AI detection without stopping the video feed
  - Click pause button in dashboard header
  - Visual overlay shows when paused
  - Automatic IDLE state reset on resume

### Admin Dashboard
- **Live Monitoring Tab** - Real-time video feed with AI annotations, alert popups, and system metrics
- **Public Display Tab** - Live preview, message editor, display toggle, and manual triggers
- **Security Alerts Tab** - Last 5 alerts with perpetrator photos + full incident log

---

## 🚀 Quick Start

### Prerequisites
```bash
pip install opencv-python ultralytics flask flask-cors numpy
```

### Installation
1. Clone the repository
2. Navigate to project directory
3. Install dependencies (see above)

### Running the System
```bash
python main.py
```

The system will:
- Start Flask backend on `http://localhost:5000`
- Initialize YOLOv8 detection model
- Launch video processing from `assets/test_littering.mp4`

### Accessing the Dashboard
Open `frontend/admin_dashboard/index.html` in your browser.

---

## 📂 Project Structure

```
Project/
├── ai_engine/          # AI detection & face recognition
│   ├── detector.py     # YOLOv8 litter detection
│   ├── face_recog.py   # Face matching system
│   └── __init__.py
├── backend/            # Flask API server
│   ├── app.py         # Main Flask application
│   └── database/      # Incident logs & data
├── frontend/
│   └── admin_dashboard/  # Unified control center
│       ├── index.html    # Main UI
│       ├── style.css     # Styling
│       └── script.js     # Controller logic
├── assets/            # Media assets
│   ├── test_littering.mp4
│   └── siren.mp3
├── main.py           # Application entry point
└── CHANGELOG.md      # Version history
```

---

## 🎮 Usage Guide

### Live Monitoring
1. **View Feed** - Live surveillance with AI detection overlay
2. **Handle Alerts** - When litter detected:
   - Review incident details
   - Click "CONFIRM VIOLATION" or "FALSE ALARM"
3. **Monitor Stats** - Track cameras, alerts, and pending reviews

### Public Display Control
1. **Toggle Display** - Turn public screen ON/OFF
2. **Edit Messages** - Customize warning/shaming/penalty text
3. **Save Changes** - Update messages instantly
4. **Manual Triggers** - Test warning/reset for demos

### Security Alerts
1. **Recent Alerts** - View last 5 incidents with photos
2. **Incident Log** - Full history of all events
3. **Refresh** - Update logs in real-time

### Surveillance Control (NEW in v1.2.0)
1. **Pause** - Click pause button to stop AI detection
   - Video continues, but no new alerts triggered
   - "SURVEILLANCE PAUSED" overlay shown
2. **Resume** - Click resume to restart detection
   - System resets to IDLE state
   - AI processing resumes normally

---

## 🔧 API Endpoints

### Status & Monitoring
- `GET /status` - System state, offender details, display settings, surveillance state
- `GET /video_feed` - Live video stream with AI annotations

### Admin Actions
- `POST /admin/action` - Handle alerts (CONFIRM/IGNORE)
- `POST /surveillance/toggle` - Pause/resume AI detection

### Display Control
- `POST /display/toggle` - Toggle public display ON/OFF
- `POST /display/messages` - Update custom messages

### Logs
- `GET /get_logs` - Retrieve incident history

### Demo/Testing
- `POST /demo/trigger_warning` - Manually trigger alert
- `POST /demo/reset` - Reset to IDLE state

---

## 🤖 AI Detection Details

### Detected Objects (Litter Classes)
- Bottles, cups, bowls
- Utensils (fork, knife, spoon)
- Food items (banana, apple, sandwich)
- Electronics (cell phone)
- Miscellaneous (book, scissors, teddy bear)

### Detection Parameters
- **Confidence Threshold**: 30% (adjusted for sensitivity)
- **Distance Threshold**: 150px from nearest person
- **Static Object Frames**: 10 frames (reduced for faster detection)
- **Grace Period**: 5 seconds before escalation

### Debug Overlay
- Person count
- Litter objects detected
- Static object tracker
- Distance to nearest person
- Grace timer (when active)

---

## 📊 System States

1. **IDLE** - Normal surveillance, no incidents
2. **WARNING** - Litter detected, grace period active
3. **PENDING_REVIEW** - Awaiting admin decision
4. **SHAMING** - Violation confirmed, public display active

---

## 🎨 Tech Stack

- **Backend**: Flask, OpenCV, Python
- **AI/ML**: YOLOv8 (Ultralytics), NumPy
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Fonts**: Orbitron, Rajdhani, Share Tech Mono
- **Video**: MJPEG streaming via Flask

---

## 📝 Version History

See [CHANGELOG.md](./CHANGELOG.md) for detailed version history.

**Current Version**: 1.2.0 - Added surveillance pause/resume functionality

---

## 🔐 Security Notes

- Admin actions require admin_id validation
- Incident logs stored in JSON format
- Face recognition uses mock data (placeholder for real database)
- All state changes are timestamped and logged

---

## 🛠️ Development

### Modifying Detection Logic
Edit `ai_engine/detector.py`:
- Adjust `LITTER_CLASSES` to add/remove object types
- Tune `CONFIDENCE_THRESHOLD`, `DISTANCE_THRESHOLD`, `STATIC_FRAMES`

### Customizing UI
Edit `frontend/admin_dashboard/`:
- `style.css` - Colors, fonts, layouts
- `script.js` - Polling intervals, API calls
- `index.html` - Structure, content

### Adding Features
1. Backend: Add route in `backend/app.py`
2. Frontend: Update HTML/CSS/JS
3. Test with demo triggers
4. Update version in sidebar and CHANGELOG

---

## 📞 Support

For issues, feature requests, or questions, please refer to the code documentation or contact the development team.

---

**Built for AMD SLINGSHOT 2026 Hackathon**

*Making our cities cleaner, one detection at a time.* 👁️
