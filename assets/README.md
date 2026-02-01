# CivicEye Assets

This folder contains media assets for the CivicEye system.

## Required Files

### siren.mp3
Alert sound played during WARNING state. 
- **Recommended**: A 2-5 second warning siren or beep sound
- **Format**: MP3, 128kbps or higher
- **Note**: If this file is missing, the system uses a Web Audio API fallback

### demo_footage.mp4
Demo video for testing without a live camera.
- **Recommended**: 30-60 second video showing:
  - A person walking
  - A bottle/object being dropped
  - Person walking away from object
- **Format**: MP4 (H.264), 720p or 1080p
- **Note**: If missing, the system will try to use webcam (index 0)

## Free Asset Sources

1. **Siren Sound**: 
   - https://freesound.org (search "siren" or "alarm")
   - https://pixabay.com/sound-effects/

2. **Stock Video**:
   - https://www.pexels.com/videos/
   - https://pixabay.com/videos/

## Quick Download Commands

```bash
# Example: Download a sample siren (replace with actual URL)
# curl -o siren.mp3 "YOUR_AUDIO_URL_HERE"

# Example: Download sample footage (replace with actual URL)  
# curl -o demo_footage.mp4 "YOUR_VIDEO_URL_HERE"
```
