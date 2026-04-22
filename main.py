"""
CivicEye - Main Entry Point
Single script to run the entire surveillance system
"""

import os
import sys
import time
import threading
import webbrowser

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def print_banner():
    """Print the CivicEye startup banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║      ██████╗██╗██╗   ██╗██╗ ██████╗███████╗██╗   ██╗███████╗  ║
    ║     ██╔════╝██║██║   ██║██║██╔════╝██╔════╝╚██╗ ██╔╝██╔════╝  ║
    ║     ██║     ██║██║   ██║██║██║     █████╗   ╚████╔╝ █████╗    ║
    ║     ██║     ██║╚██╗ ██╔╝██║██║     ██╔══╝    ╚██╔╝  ██╔══╝    ║
    ║     ╚██████╗██║ ╚████╔╝ ██║╚██████╗███████╗   ██║   ███████╗  ║
    ║      ╚═════╝╚═╝  ╚═══╝  ╚═╝ ╚═════╝╚══════╝   ╚═╝   ╚══════╝  ║
    ║                                                               ║
    ║           Smart City Surveillance System v1.3.0               ║
    ║                  AMD SLINGSHOT 2026                           ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    
    try:
        import flask
    except ImportError:
        missing.append('flask')
    
    try:
        import flask_cors
    except ImportError:
        missing.append('flask-cors')
    
    try:
        import cv2
    except ImportError:
        missing.append('opencv-python')
    
    try:
        import numpy
    except ImportError:
        missing.append('numpy')
    
    try:
        from ultralytics import YOLO
    except ImportError:
        missing.append('ultralytics')
    
    if missing:
        print("\n⚠️  Missing dependencies detected!")
        print("Please install the following packages:")
        print(f"\n    pip install {' '.join(missing)}\n")
        return False
    
    return True


def get_video_source():
    """Determine the video source to use."""
    # Check for demo footage first
    demo_path = os.path.join(PROJECT_ROOT, 'assets', 'demo_footage.mp4')
    if os.path.exists(demo_path):
        print(f"📹 Using demo footage: {demo_path}")
        return demo_path
    
    # Try webcam
    import cv2
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        cap.release()
        print("📹 Using webcam (index 0)")
        return 0
    
    print("⚠️  No video source found. Using placeholder frames.")
    return None
    # return "http://192.168.1.109:8080/video"


def run_server(video_source):
    """Run the Flask server."""
    from backend.app import app, init_detector, set_video_source
    
    # Initialize detector
    print("🔧 Loading YOLOv8s model...")
    try:
        init_detector()
        print("✅ AI detector initialized")
    except Exception as e:
        print(f"⚠️  Detector init warning: {e}")
        print("   (System will run with placeholder detection)")
    
    # Set video source
    set_video_source(video_source)
    
    # Run Flask
    print("\n🚀 Starting CivicEye server...")
    print("=" * 60)
    print(f"   API Server:        http://localhost:5000")
    print(f"   Video Feed:        http://localhost:5000/video_feed")
    print(f"   Status Endpoint:   http://localhost:5000/status")
    print("=" * 60)
    print("\n📂 Frontend Files:")
    print(f"   Public Display:    {os.path.join(PROJECT_ROOT, 'frontend', 'public_display', 'index.html')}")
    print(f"   Admin Dashboard:   {os.path.join(PROJECT_ROOT, 'frontend', 'admin_dashboard', 'index.html')}")
    print("=" * 60)
    print("\n💡 Tips:")
    print("   - Open both frontend HTML files in your browser")
    print("   - Use the 'DEMO: Trigger Alert' button to test the flow")
    print("   - Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)


def open_browsers():
    """Open frontend pages in browser after a delay."""
    time.sleep(2)  # Wait for server to start
    
    admin_path = os.path.join(PROJECT_ROOT, 'frontend', 'admin_dashboard', 'index.html')
    public_path = os.path.join(PROJECT_ROOT, 'frontend', 'public_display', 'index.html')
    
    try:
        webbrowser.open(f'file:///{admin_path}')
        time.sleep(0.5)
        webbrowser.open(f'file:///{public_path}')
    except Exception as e:
        print(f"⚠️  Could not auto-open browsers: {e}")


def main():
    """Main entry point."""
    print_banner()
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        sys.exit(1)
    print("✅ All dependencies found\n")
    
    # Get video source
    video_source = get_video_source()
    
    # Option to auto-open browsers
    auto_open = input("\n🌐 Auto-open frontend in browser? [Y/n]: ").strip().lower()
    if auto_open != 'n':
        browser_thread = threading.Thread(target=open_browsers, daemon=True)
        browser_thread.start()
    
    # Run server
    try:
        run_server(video_source)
    except KeyboardInterrupt:
        print("\n\n👋 CivicEye shutting down. Goodbye!")
        sys.exit(0)


if __name__ == '__main__':
    main()
