"""Frame preprocessing utilities."""

import cv2
import numpy as np


class FramePreprocessor:
    """Preprocesses frames for optimal landmark detection."""
    
    def __init__(self, config: dict):
        self.config = config
        self.target_size = tuple(config.get("resolution", [1280, 720]))
        self.enhance_low_light = config.get("enhance_low_light", True)
        self.denoise = config.get("denoise", False)
    
    def process(self, frame: np.ndarray) -> np.ndarray:
        """Process a frame."""
        
        # Resize if needed
        if frame.shape[:2][::-1] != self.target_size:
            frame = cv2.resize(frame, self.target_size)
        
        # Enhance low light conditions
        if self.enhance_low_light:
            frame = self._enhance_lighting(frame)
        
        # Denoise if enabled
        if self.denoise:
            frame = cv2.fastNlMeansDenoisingColored(frame, None, 5, 5, 7, 21)
        
        return frame
    
    def _enhance_lighting(self, frame: np.ndarray) -> np.ndarray:
        """Enhance frame in low light conditions."""
        
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Check if image is dark
        mean_brightness = np.mean(l)
        
        if mean_brightness < 100:
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge and convert back
            lab = cv2.merge([l, a, b])
            frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return frame
    
    def segment_background(self, frame: np.ndarray) -> np.ndarray:
        """Simple background segmentation."""
        
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Detect skin tones
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Apply mask
        result = cv2.bitwise_and(frame, frame, mask=mask)
        
        return result
