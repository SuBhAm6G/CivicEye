"""
CivicEye AI Engine - Face Recognition Module
Mock implementation that returns dummy data for hackathon demo.
"""

import json
import os
import random


class FaceMatcher:
    """
    Mock face matching class that returns dummy criminal data.
    In production, this would use actual face recognition (e.g., face_recognition library).
    """
    
    def __init__(self, database_path=None):
        """Initialize FaceMatcher with path to dummy criminals database."""
        if database_path is None:
            # Default path relative to project root
            self.database_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'backend', 'database', 'dummy_criminals.json'
            )
        else:
            self.database_path = database_path
            
        self.criminals_db = self._load_database()
    
    def _load_database(self):
        """Load the dummy criminals database."""
        try:
            with open(self.database_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default dummy data if file not found
            return self._get_default_criminals()
    
    def _get_default_criminals(self):
        """Return default dummy criminal data."""
        return [
            {
                "id": "CIV-001",
                "name": "John Doe",
                "photo_url": "https://randomuser.me/api/portraits/men/1.jpg",
                "prior_offenses": 2
            },
            {
                "id": "CIV-002", 
                "name": "Jane Smith",
                "photo_url": "https://randomuser.me/api/portraits/women/2.jpg",
                "prior_offenses": 1
            },
            {
                "id": "CIV-003",
                "name": "Mike Johnson",
                "photo_url": "https://randomuser.me/api/portraits/men/3.jpg",
                "prior_offenses": 3
            },
            {
                "id": "CIV-004",
                "name": "Sarah Wilson",
                "photo_url": "https://randomuser.me/api/portraits/women/4.jpg",
                "prior_offenses": 0
            },
            {
                "id": "CIV-005",
                "name": "Alex Chen",
                "photo_url": "https://randomuser.me/api/portraits/men/5.jpg",
                "prior_offenses": 1
            }
        ]
    
    def match_face(self, face_image=None):
        """
        Mock face matching - returns a random criminal from the database.
        
        Args:
            face_image: Face image (ignored in mock implementation)
            
        Returns:
            dict: Criminal data with match confidence
        """
        if not self.criminals_db:
            return None
            
        # Return random criminal for demo purposes
        criminal = random.choice(self.criminals_db)
        return {
            "id": criminal["id"],
            "name": criminal["name"],
            "photo_url": criminal["photo_url"],
            "prior_offenses": criminal.get("prior_offenses", 0),
            "match_confidence": round(random.uniform(0.85, 0.98), 2)
        }
    
    def get_all_criminals(self):
        """Return all criminals in database."""
        return self.criminals_db
    
    def get_criminal_by_id(self, criminal_id):
        """Get a specific criminal by ID."""
        for criminal in self.criminals_db:
            if criminal["id"] == criminal_id:
                return criminal
        return None
