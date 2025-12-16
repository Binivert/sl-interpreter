"""Gesture classification using loaded models."""

import logging
from typing import Tuple, Optional, List

import numpy as np
import onnxruntime as ort

from .model_loader import ModelLoader

logger = logging.getLogger(__name__)


class GestureClassifier:
    """Classifies gesture sequences into sign labels."""
    
    def __init__(self, model_loader: ModelLoader, config: dict):
        self.model_loader = model_loader
        self.config = config
        
        self.session: Optional[ort.InferenceSession] = None
        self.labels: List[str] = []
        self.current_model: str = ""
        
        # Load default model
        default_model = config.get("model", "asl_base")
        self.load_model(default_model)
    
    def load_model(self, model_name: str):
        """Load a gesture recognition model."""
        
        model_path, labels = self.model_loader.load_gesture_model(model_name)
        
        # Create ONNX session
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.session = ort.InferenceSession(str(model_path), providers=providers)
        
        self.labels = labels
        self.current_model = model_name
        
        logger.info(f"Loaded model '{model_name}' with {len(labels)} signs")
    
    def predict(self, sequence: np.ndarray) -> Tuple[str, float]:
        """Predict the sign from a gesture sequence.
        
        Args:
            sequence: Array of shape (window_size, feature_size)
        
        Returns:
            Tuple of (predicted_label, confidence)
        """
        
        if self.session is None:
            raise RuntimeError("No model loaded")
        
        # Prepare input
        input_name = self.session.get_inputs()[0].name
        input_data = sequence.astype(np.float32)
        
        # Add batch dimension if needed
        if len(input_data.shape) == 2:
            input_data = np.expand_dims(input_data, axis=0)
        
        # Run inference
        outputs = self.session.run(None, {input_name: input_data})
        
        # Get probabilities
        probs = outputs[0][0]
        
        # Apply softmax if not already applied
        if not np.isclose(np.sum(probs), 1.0):
            probs = self._softmax(probs)
        
        # Get prediction
        pred_idx = np.argmax(probs)
        confidence = probs[pred_idx]
        
        return self.labels[pred_idx], confidence
    
    def predict_top_k(self, sequence: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        """Get top-k predictions."""
        
        if self.session is None:
            raise RuntimeError("No model loaded")
        
        # Prepare input
        input_name = self.session.get_inputs()[0].name
        input_data = sequence.astype(np.float32)
        
        if len(input_data.shape) == 2:
            input_data = np.expand_dims(input_data, axis=0)
        
        # Run inference
        outputs = self.session.run(None, {input_name: input_data})
        probs = outputs[0][0]
        
        if not np.isclose(np.sum(probs), 1.0):
            probs = self._softmax(probs)
        
        # Get top-k
        top_indices = np.argsort(probs)[-k:][::-1]
        
        return [(self.labels[i], float(probs[i])) for i in top_indices]
    
    def reload(self):
        """Reload the current model."""
        
        if self.current_model:
            self.load_model(self.current_model)
    
    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        """Apply softmax."""
        
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum()
