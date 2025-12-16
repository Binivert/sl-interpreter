"""Model loading and management."""

import json
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import yaml

logger = logging.getLogger(__name__)


class ModelLoader:
    """Loads and manages ML models."""
    
    def __init__(self, config: dict):
        self.config = config
        self.models_dir = Path(config.get("models_dir", "models"))
        self.gestures_dir = self.models_dir / "gestures"
        self.voices_dir = self.models_dir / "voices"
        self.languages_dir = self.models_dir / "languages"
        
        # Ensure directories exist
        for dir_path in [self.gestures_dir, self.voices_dir, self.languages_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def load_gesture_model(self, model_name: str) -> Tuple[Path, List[str]]:
        """Load a gesture recognition model.
        
        Returns:
            Tuple of (model_path, labels_list)
        """
        
        model_dir = self.gestures_dir / model_name
        
        if not model_dir.exists():
            raise FileNotFoundError(f"Model not found: {model_name}")
        
        # Find model file
        model_path = None
        for ext in [".onnx", ".pt", ".task"]:
            candidate = model_dir / f"model{ext}"
            if candidate.exists():
                model_path = candidate
                break
        
        if model_path is None:
            raise FileNotFoundError(f"No model file found in {model_dir}")
        
        # Load labels
        labels_path = model_dir / "labels.json"
        if not labels_path.exists():
            raise FileNotFoundError(f"Labels file not found: {labels_path}")
        
        with open(labels_path) as f:
            labels_data = json.load(f)
        
        # Handle both list and dict formats
        if isinstance(labels_data, list):
            labels = labels_data
        elif isinstance(labels_data, dict):
            labels = labels_data.get("labels", list(labels_data.values()))
        else:
            raise ValueError(f"Invalid labels format in {labels_path}")
        
        logger.info(f"Loaded model {model_name}: {model_path}")
        
        return model_path, labels
    
    def list_gesture_models(self) -> List[Dict[str, Any]]:
        """List available gesture models."""
        
        models = []
        
        for model_dir in self.gestures_dir.iterdir():
            if model_dir.is_dir():
                config_path = model_dir / "config.yaml"
                
                model_info = {
                    "name": model_dir.name,
                    "path": str(model_dir)
                }
                
                if config_path.exists():
                    with open(config_path) as f:
                        config = yaml.safe_load(f)
                    model_info.update(config)
                
                # Count labels
                labels_path = model_dir / "labels.json"
                if labels_path.exists():
                    with open(labels_path) as f:
                        labels = json.load(f)
                    if isinstance(labels, list):
                        model_info["sign_count"] = len(labels)
                    elif isinstance(labels, dict):
                        model_info["sign_count"] = len(labels.get("labels", labels))
                
                models.append(model_info)
        
        return models
    
    def load_language_pack(self, language_code: str) -> Dict[str, str]:
        """Load a language mapping pack."""
        
        lang_dir = self.languages_dir / language_code
        mappings_path = lang_dir / "mappings.json"
        
        if not mappings_path.exists():
            raise FileNotFoundError(f"Language pack not found: {language_code}")
        
        with open(mappings_path) as f:
            data = json.load(f)
        
        return data.get("signs", data)
    
    def list_language_packs(self) -> List[Dict[str, str]]:
        """List available language packs."""
        
        packs = []
        
        for lang_dir in self.languages_dir.iterdir():
            if lang_dir.is_dir():
                mappings_path = lang_dir / "mappings.json"
                if mappings_path.exists():
                    with open(mappings_path) as f:
                        data = json.load(f)
                    packs.append({
                        "code": lang_dir.name,
                        "language": data.get("language", lang_dir.name),
                        "sign_count": len(data.get("signs", data))
                    })
        
        return packs
