"""
CivicEye AI Engine - Litter Detection Module
Using YOLOv8 for person/object detection with velocity-based static object detection.
"""

import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import time


class LitterMonitor:
    """
    Monitors video feed for littering incidents using YOLOv8 detection.
    Implements velocity checks and grace timer for accurate detection.
    """
    
    def __init__(self, model_path='yolov8n.pt'):
        """Initializing the LitterMonitor with YOLOv8 model."""
        self.model = YOLO(model_path)
        
        # Detection parameters
        self.PERSON_CLASS = 0
        
        # YOLO COCO classes that could be litter/trash
        # 39=bottle, 41=cup, 43=fork, 44=knife, 45=spoon, 46=bowl,
        # 47=banana, 48=apple, 49=sandwich, 67=cell phone, 73=book
        self.LITTER_CLASSES = {
            39: 'bottle',
            41: 'cup', 
            43: 'fork',
            44: 'knife',
            45: 'spoon',
            46: 'bowl',
            47: 'banana',
            48: 'apple',
            49: 'sandwich',
            67: 'cell phone',
            73: 'book',
            76: 'scissors',
            77: 'teddy bear', 
        }
        
        self.VELOCITY_THRESHOLD = 8  # pixels (slightly relaxed)
        self.VELOCITY_FRAMES = 8     # frames (slightly faster)
        self.DISTANCE_THRESHOLD = 150  # pixels (more sensitive)
        self.GRACE_PERIOD = 5.0  # seconds
        
        # Tracking state
        self.bottle_history = defaultdict(list)  # Track object centroids over frames
        self.static_bottles = {}  # Objects confirmed as static
        self.grace_start_time = None
        self.current_state = "IDLE"
        self.detected_bottle_frame = None
        self.offender_bbox = None
        
        # Simple tracking with counter
        self.next_bottle_id = 0
        self.tracked_bottles = {}  # id -> last_centroid
        
        # Debug info
        self.debug_info = {
            'persons': 0,
            'litter_objects': 0,
            'static_objects': 0,
            'nearest_distance': 0
        }
    
    def _calculate_centroid(self, bbox):
        """Calculating centroid from bounding box [x1, y1, x2, y2]."""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def _calculate_distance(self, point1, point2):
        """Calculating Euclidean distance between two points."""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def _match_bottle_to_track(self, centroid, threshold=50):
        """Simple tracking: match detection to existing track or create new."""
        best_id = None
        best_dist = float('inf')
        
        for bottle_id, last_centroid in self.tracked_bottles.items():
            dist = self._calculate_distance(centroid, last_centroid)
            if dist < threshold and dist < best_dist:
                best_dist = dist
                best_id = bottle_id
        
        if best_id is None:
            best_id = self.next_bottle_id
            self.next_bottle_id += 1
            
        self.tracked_bottles[best_id] = centroid
        return best_id
    
    def _is_bottle_static(self, bottle_id, centroid):
        """Check if bottle has been static (moved < 5px over 10 frames)."""
        self.bottle_history[bottle_id].append(centroid)
        
        # Keep only last VELOCITY_FRAMES
        if len(self.bottle_history[bottle_id]) > self.VELOCITY_FRAMES:
            self.bottle_history[bottle_id].pop(0)
        
        # Need at least VELOCITY_FRAMES to determine if static
        if len(self.bottle_history[bottle_id]) < self.VELOCITY_FRAMES:
            return False
        
        # Calculate total movement over the tracked frames
        history = self.bottle_history[bottle_id]
        total_movement = 0
        for i in range(1, len(history)):
            total_movement += self._calculate_distance(history[i-1], history[i])
        
        return total_movement < self.VELOCITY_THRESHOLD
    
    def _find_nearest_person_distance(self, bottle_centroid, person_bboxes):
        """Find distance to nearest person."""
        if not person_bboxes:
            return float('inf')
        
        min_distance = float('inf')
        for bbox in person_bboxes:
            person_centroid = self._calculate_centroid(bbox)
            dist = self._calculate_distance(bottle_centroid, person_centroid)
            min_distance = min(min_distance, dist)
        
        return min_distance
    
    def detect_frame(self, frame):
        """
        Process a single frame for litter detection.
        
        Args:
            frame: OpenCV frame (BGR)
            
        Returns:
            tuple: (annotated_frame, current_state_flag)
        """
        if frame is None:
            return None, self.current_state
        
        # Run YOLOv8 detection
        results = self.model(frame, verbose=False)
        annotated_frame = frame.copy()
        
        person_bboxes = []
        bottle_detections = []
        
        # Parse detections
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                bbox = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                
                if cls == self.PERSON_CLASS and conf > 0.5:
                    person_bboxes.append(bbox)
                    # Draw person box (blue)
                    cv2.rectangle(annotated_frame, 
                                (int(bbox[0]), int(bbox[1])), 
                                (int(bbox[2]), int(bbox[3])), 
                                (255, 200, 0), 2)
                    cv2.putText(annotated_frame, f'Person {conf:.2f}', 
                              (int(bbox[0]), int(bbox[1]-10)),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2)
                    
                # Check if class is in our litter classes
                elif cls in self.LITTER_CLASSES and conf > 0.3:
                    litter_name = self.LITTER_CLASSES[cls]
                    centroid = self._calculate_centroid(bbox)
                    bottle_detections.append((bbox, centroid, litter_name))
                    # Draw litter object box (cyan)
                    cv2.rectangle(annotated_frame, 
                                (int(bbox[0]), int(bbox[1])), 
                                (int(bbox[2]), int(bbox[3])), 
                                (0, 255, 255), 2)
                    cv2.putText(annotated_frame, f'{litter_name} {conf:.2f}', 
                              (int(bbox[0]), int(bbox[1]-10)),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        # Update debug info
        self.debug_info['persons'] = len(person_bboxes)
        self.debug_info['litter_objects'] = len(bottle_detections)
        
        # Process litter detections
        litter_detected = False
        static_count = 0
        nearest_dist = float('inf')
        
        for bbox, centroid, litter_name in bottle_detections:
            bottle_id = self._match_bottle_to_track(centroid)
            
            # Check if object is static
            if self._is_bottle_static(bottle_id, centroid):
                static_count += 1
                # Check distance to nearest person
                distance = self._find_nearest_person_distance(centroid, person_bboxes)
                nearest_dist = min(nearest_dist, distance)
                
                if distance > self.DISTANCE_THRESHOLD:
                    litter_detected = True
                    self.detected_bottle_frame = bbox
                    
                    # Draw warning indicator
                    cv2.rectangle(annotated_frame, 
                                (int(bbox[0]), int(bbox[1])), 
                                (int(bbox[2]), int(bbox[3])), 
                                (0, 0, 255), 4)
                    cv2.putText(annotated_frame, f'LITTER: {litter_name}!', 
                              (int(bbox[0]), int(bbox[1]-30)),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        self.debug_info['static_objects'] = static_count
        self.debug_info['nearest_distance'] = nearest_dist if nearest_dist != float('inf') else 0
        
        # State machine logic
        if self.current_state == "IDLE":
            if litter_detected:
                if self.grace_start_time is None:
                    self.grace_start_time = time.time()
                elif time.time() - self.grace_start_time >= self.GRACE_PERIOD:
                    self.current_state = "WARNING"
                    self.grace_start_time = None
            else:
                self.grace_start_time = None
                
        elif self.current_state == "WARNING":
            # State will be changed by admin action or timeout (handled in backend)
            pass
        
        elif self.current_state == "SHAMING":
            # State will be reset by backend after display
            pass
        
        # Draw status overlay
        status_color = {
            "IDLE": (0, 255, 0),
            "WARNING": (0, 165, 255),
            "PENDING_REVIEW": (0, 255, 255),
            "SHAMING": (0, 0, 255)
        }.get(self.current_state, (255, 255, 255))
        
        # Main status box
        cv2.rectangle(annotated_frame, (10, 10), (280, 55), (0, 0, 0), -1)
        cv2.putText(annotated_frame, f'Status: {self.current_state}', 
                  (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Debug info box
        cv2.rectangle(annotated_frame, (10, 60), (280, 140), (0, 0, 0), -1)
        cv2.putText(annotated_frame, f'Persons: {self.debug_info["persons"]}', 
                  (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(annotated_frame, f'Objects: {self.debug_info["litter_objects"]} (Static: {static_count})', 
                  (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(annotated_frame, f'Nearest: {self.debug_info["nearest_distance"]:.0f}px (Thresh: {self.DISTANCE_THRESHOLD})', 
                  (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Draw grace timer if active
        if self.grace_start_time is not None:
            elapsed = time.time() - self.grace_start_time
            remaining = max(0, self.GRACE_PERIOD - elapsed)
            cv2.rectangle(annotated_frame, (10, 145), (280, 175), (0, 100, 100), -1)
            cv2.putText(annotated_frame, f'GRACE TIMER: {remaining:.1f}s', 
                      (20, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        return annotated_frame, self.current_state
    
    def set_state(self, state):
        """Set the current state externally (from backend)."""
        self.current_state = state
        if state == "IDLE":
            self.grace_start_time = None
    
    def get_state(self):
        """Get current state."""
        return self.current_state
    
    def reset(self):
        """Reset all tracking state."""
        self.bottle_history.clear()
        self.static_bottles.clear()
        self.tracked_bottles.clear()
        self.grace_start_time = None
        self.current_state = "IDLE"
        self.next_bottle_id = 0
