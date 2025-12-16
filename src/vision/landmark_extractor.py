"""Extract landmarks from video frames using MediaPipe."""

import logging
from typing import Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np

logger = logging.getLogger(__name__)


class LandmarkExtractor:
    """Extracts hand, pose, and face landmarks from frames."""
    
    # Landmark counts
    HAND_LANDMARKS = 21
    POSE_LANDMARKS = 33
    FACE_LANDMARKS = 468
    
    def __init__(self, config: dict):
        self.config = config
        self.enable_pose = config.get("enable_pose", True)
        self.enable_face = config.get("enable_face", True)
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_face = mp.solutions.face_mesh
        
        # Create detectors
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        self.pose = None
        if self.enable_pose:
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        
        self.face = None
        if self.enable_face:
            self.face = self.mp_face.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        
        logger.info(f"LandmarkExtractor initialized (pose={self.enable_pose}, face={self.enable_face})")
    
    def extract(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Extract landmarks from a frame.
        
        Returns:
            Flattened numpy array of landmarks, or None if no detection.
        """
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process hands
        hands_result = self.hands.process(rgb_frame)
        
        if not hands_result.multi_hand_landmarks:
            return None
        
        landmarks = []
        
        # Extract hand landmarks (up to 2 hands)
        hand_data = self._extract_hands(hands_result)
        landmarks.extend(hand_data)
        
        # Extract pose landmarks
        if self.pose:
            pose_result = self.pose.process(rgb_frame)
            pose_data = self._extract_pose(pose_result)
            landmarks.extend(pose_data)
        
        # Extract face landmarks (subset)
        if self.face:
            face_result = self.face.process(rgb_frame)
            face_data = self._extract_face(face_result)
            landmarks.extend(face_data)
        
        return np.array(landmarks, dtype=np.float32)
    
    def _extract_hands(self, result) -> list:
        """Extract hand landmarks."""
        
        hand_data = []
        
        # Process up to 2 hands
        for i in range(2):
            if result.multi_hand_landmarks and i < len(result.multi_hand_landmarks):
                hand = result.multi_hand_landmarks[i]
                for landmark in hand.landmark:
                    hand_data.extend([landmark.x, landmark.y, landmark.z])
            else:
                # Pad with zeros if hand not detected
                hand_data.extend([0.0] * (self.HAND_LANDMARKS * 3))
        
        return hand_data
    
    def _extract_pose(self, result) -> list:
        """Extract pose landmarks."""
        
        pose_data = []
        
        if result and result.pose_landmarks:
            # Extract only upper body landmarks (0-24)
            for i, landmark in enumerate(result.pose_landmarks.landmark):
                if i < 25:
                    pose_data.extend([landmark.x, landmark.y, landmark.z, landmark.visibility])
        else:
            pose_data.extend([0.0] * (25 * 4))
        
        return pose_data
    
    def _extract_face(self, result) -> list:
        """Extract face landmarks (key points only)."""
        
        # Key face landmarks for expression
        KEY_POINTS = [33, 133, 362, 263, 1, 61, 291, 199]  # Eyes, nose, mouth corners
        
        face_data = []
        
        if result and result.multi_face_landmarks:
            face = result.multi_face_landmarks[0]
            for idx in KEY_POINTS:
                landmark = face.landmark[idx]
                face_data.extend([landmark.x, landmark.y, landmark.z])
        else:
            face_data.extend([0.0] * (len(KEY_POINTS) * 3))
        
        return face_data
    
    def get_feature_size(self) -> int:
        """Get total feature vector size."""
        
        size = 2 * self.HAND_LANDMARKS * 3  # Two hands
        
        if self.enable_pose:
            size += 25 * 4  # Upper body pose with visibility
        
        if self.enable_face:
            size += 8 * 3  # Key face points
        
        return size
    
    def close(self):
        """Release resources."""
        
        self.hands.close()
        if self.pose:
            self.pose.close()
        if self.face:
            self.face.close()
