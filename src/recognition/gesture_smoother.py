"""Gesture smoothing to prevent flickering."""

import time
from collections import deque
from typing import Optional, Tuple


class GestureSmoother:
    """Smooths gesture predictions to prevent flickering."""
    
    def __init__(self, min_duration: float = 0.3, cooldown: float = 0.5):
        self.min_duration = min_duration
        self.cooldown = cooldown
        
        self.current_gesture: Optional[str] = None
        self.gesture_start_time: float = 0.0
        self.last_output_time: float = 0.0
        self.output_history: deque = deque(maxlen=10)
    
    def update(self, prediction: str, confidence: float) -> Optional[Tuple[str, float]]:
        """Update with a new prediction.
        
        Returns:
            Tuple of (gesture, confidence) if a gesture should be output, None otherwise.
        """
        
        current_time = time.time()
        
        if prediction != self.current_gesture:
            # New gesture detected
            self.current_gesture = prediction
            self.gesture_start_time = current_time
            return None
        
        # Same gesture - check duration
        duration = current_time - self.gesture_start_time
        
        if duration < self.min_duration:
            return None
        
        # Check cooldown
        if current_time - self.last_output_time < self.cooldown:
            return None
        
        # Check if same as last output
        if self.output_history and self.output_history[-1][0] == prediction:
            return None
        
        # Output the gesture
        self.last_output_time = current_time
        self.output_history.append((prediction, confidence, current_time))
        
        return prediction, confidence
    
    def reset(self):
        """Reset the smoother state."""
        
        self.current_gesture = None
        self.gesture_start_time = 0.0
        self.output_history.clear()
