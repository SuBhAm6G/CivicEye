
# 👁️ CIVIC**EYE** — Smart City Surveillance System

> **Making our cities cleaner, safer, and smarter, one detection at a time.**

---

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-black?style=for-the-badge&logo=flask&logoColor=white)
![YOLOv8](https://img.shields.io/badge/AI-YOLOv8-ff69b4?style=for-the-badge&logo=ultralytics&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## 📖 Table of Contents
- [About the Project](#-about-the-project)
- [Key Features](#-key-features)
- [Dashboard Tour](#-dashboard-tour)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [Future Roadmap](#-future-roadmap)

---

## 🏙️ About the Project

**CivicEye** is an advanced AI-powered surveillance system designed for smart cities. It tackles the issue of public littering by detecting incidents in real-time, identifying offenders via facial recognition (simulated), and managing the enforcement workflow through a unified control center.

Unlike traditional CCTV that requires constant human monitoring, **CivicEye** is proactive:
1.  **Observes**: Continuously scans video feeds for litter items (bottles, wrappers, etc.).
2.  **Detects**: Uses YOLOv8 to identify the act of littering and the person responsible.
3.  **Acts**: Automatically triggers public warnings on display screens.
4.  **Enforces**: Logs the incident and dispatches alerts to security personnel via WhatsApp integration.

---

## ✨ Key Features

### 🧠 Intelligent Detection
-   **Real-Time Object Detection**: Powered by **YOLOv8**, capable of spotting small litter items like cups, bottles, and food wrappers.
-   **Person Association**: Associates the litter with the nearest person to identify the "Offender".
-   **Grace Period Logic**: Allows a 5-second window for the person to pick up the trash before escalating the alert.

### 🎮 Unified Control Dashboard
-   **Live Monitoring**: View the real-time feed with AI bounding boxes and annotations.
-   **Public Display Control**: Toggle the public-facing screen and customize warning messages instantly.
-   **Security Alerts**: Review recent incidents with captured evidence.
-   **Surveillance Control**: Pause and resume AI detection with a single click.

### 📤 **NEW!** Automated Dispatch System
-   **WhatsApp Integration**: Automatically dispatches incident details to security personnel upon violation confirmation.
-   **Visual Logs**: View a history of sent messages in the **"Sent Messages"** tab, styled like a WhatsApp chat for easy tracking.
-   **Multi-Guard Coordination**: Alerts are sent simultaneously to the Security Head and Patrol Units.

---

## 🖥️ Dashboard Tour

### 1. Live Monitoring Tab 🎥
The command center. Watch the live feed, see real-time system metrics (Active Cameras, Alerts Today), and handle incoming violation alerts.
-   **Action**: Approve or Ignore violations with a single click.

### 2. Public Display Tab 📺
Controls what the public sees on the large street-side screens.
-   **Modes**: 
    -   *Idle* (City Branding), 
    -   *Warning* ("Please pick up your trash"), 
    -   *Shaming* (Displays offender's face and fine amount).
-   **Customization**: Edit the warning text and fine details on the fly.

### 3. Security Alerts Tab 🚨
A historical log of all detected incidents.
-   **Evidence**: Time-stamped logs with offender ID and status.

### 4. Sent Messages Log 📤
**[NEW FEATURE]** 
A dedicated view for tracking outbound communications.
-   **Visuals**: Cards styled to look like WhatsApp messages.
-   **Details**: Shows the photo, location, and time sent to each guard.
-   **Status**: Indicates successful delivery with "Blue Ticks".

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | Python, Flask | REST API and Video Streaming Server |
| **AI Engine** | YOLOv8 (Ultralytics), OpenCV | Real-time object detection and image processing |
| **Frontend** | HTML5, CSS3, JavaScript | Responsive Admin Dashboard and Public Display |
| **Styling** | Custom CSS (Cyberpunk/Sci-Fi) | Futuristic UI with Orbitron & Rajdhani fonts |
| **Data** | JSON (Local) | Lightweight structured logging for incidents |

---

## 🚀 Getting Started

### Prerequisites
Ensure you have Python 3.9+ installed.

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/SuBhAm6G/CivicEye.git
    cd CivicEye
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *(If `requirements.txt` is missing, install manually: `pip install opencv-python ultralytics flask flask-cors numpy`)*

3.  **Download Model Weights**
    Ensure `yolov8n.pt` is in the root directory (it will download automatically on first run).

### Running the System

1.  **Start the Application**
    ```bash
    python main.py
    ```

2.  **Access the Dashboard**
    The system will automatically open the dashboard in your default browser.
    -   **Admin Panel**: `http://localhost:5000/frontend/admin_dashboard/index.html` (served via file or mapped route)
    -   **API Root**: `http://localhost:5000/`

---

## 📂 Project Structure

```bash
CivicEye/
├── ai_engine/          # YOLOv8 logic and Face Recognition modules
├── assets/             # Demo videos and sound effects
├── backend/            # Flask API routes and state management
├── database/           # JSON logs and captured offender images
├── frontend/           # Web Interface
│   ├── admin_dashboard/    # The main control center
│   └── public_display/     # The screen shown to the public
├── main.py             # Entry point script
└── README.md           # You are here!
```

---

## 🔮 Future Roadmap

-   [ ] **Cloud Integration**: Upload incident logs to a cloud database (Firebase/AWS).
-   [ ] **Mobile App**: A dedicated app for security guards to receive push notifications.
-   [ ] **Fine Automation**: Integration with payment gateways to auto-issue fines via SMS.
-   [ ] **Drone Support**: Extend surveillance to autonomous drones.
-   [ ] **Multi-Panel CCTV**: Support for simultaneous monitoring and processing of multiple camera feeds in a unified grid view.


---

> **Built for AMD SLINGSHOT 2026 Hackathon**  
> *Innovating for a cleaner tomorrow.*

