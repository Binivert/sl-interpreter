"""Camera management and frame capture."""

import logging
import threading
import time
from typing import Optional, Callable, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraManager:
    """Manages camera capture with adaptive frame rate."""
    
    def __init__(self, config: dict):
        self.config = config
        self.camera_index = config.get("camera_index", 0)
        self.resolution = tuple(config.get("resolution", [1280, 720]))
        self.target_fps = config.get("target_fps", 30)
        self.adaptive_sampling = config.get("adaptive_sampling", True)
        self.min_fps = config.get("min_fps", 15)
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.current_fps = 0.0
        self.frame_callback: Optional[Callable] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._last_frame: Optional[np.ndarray] = None
        self._frame_times: list[float] = []
    
    def start(self, callback: Optional[Callable] = None):
        """Start camera capture."""
        
        if self.is_running:
            logger.warning("Camera already running")
            return
        
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera {self.camera_index}")
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        
        self.frame_callback = callback
        self.is_running = True
        
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        
        logger.info(f"Camera started: {self.resolution[0]}x{self.resolution[1]} @ {self.target_fps}fps")
    
    def stop(self):
        """Stop camera capture."""
        
        self.is_running = False
        
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        logger.info("Camera stopped")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame."""
        
        with self._lock:
            return self._last_frame.copy() if self._last_frame is not None else None
    
    def get_fps(self) -> float:
        """Get current FPS."""
        
        return self.current_fps
    
    def _capture_loop(self):
        """Main capture loop."""
        
        frame_interval = 1.0 / self.target_fps
        
        while self.is_running:
            start_time = time.perf_counter()
            
            ret, frame = self.cap.read()
            
            if not ret:
                logger.warning("Failed to read frame")
                time.sleep(0.1)
                continue
            
            with self._lock:
                self._last_frame = frame
            
            # Call callback if set
            if self.frame_callback:
                try:
                    self.frame_callback(frame)
                except Exception as e:
                    logger.error(f"Frame callback error: {e}")
            
            # Update FPS calculation
            self._update_fps(start_time)
            
            # Adaptive frame rate
            if self.adaptive_sampling:
                frame_interval = self._adapt_frame_rate(frame_interval)
            
            # Sleep to maintain target FPS
            elapsed = time.perf_counter() - start_time
            sleep_time = max(0, frame_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _update_fps(self, frame_start: float):
        """Update FPS calculation."""
        
        current_time = time.perf_counter()
        self._frame_times.append(current_time)
        
        # Keep only last second of frame times
        cutoff = current_time - 1.0
        self._frame_times = [t for t in self._frame_times if t > cutoff]
        
        self.current_fps = len(self._frame_times)
    
    def _adapt_frame_rate(self, current_interval: float) -> float:
        """Adapt frame rate based on system load."""
        
        if self.current_fps < self.min_fps:
            # Increase interval (reduce FPS) if struggling
            return min(current_interval * 1.1, 1.0 / self.min_fps)
        elif self.current_fps > self.target_fps * 0.95:
            # Decrease interval if we have headroom
            return max(current_interval * 0.95, 1.0 / self.target_fps)
        
        return current_interval
    
    @staticmethod
    def list_cameras() -> list[dict]:
        """List available cameras."""
        
        cameras = []
        
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append({
                    "index": i,
                    "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    "fps": int(cap.get(cv2.CAP_PROP_FPS))
                })
                cap.release()
        
        return cameras
