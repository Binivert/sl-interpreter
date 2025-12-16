"""Configuration management."""

import logging
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8080
    },
    "vision": {
        "camera_index": 0,
        "resolution": [1280, 720],
        "target_fps": 30,
        "adaptive_sampling": True,
        "min_fps": 15,
        "enable_pose": True,
        "enable_face": True,
        "enhance_low_light": True,
        "denoise": False
    },
    "recognition": {
        "model": "asl_base",
        "confidence_threshold": 0.7,
        "temporal_window": 15,
        "smoothing_factor": 0.3,
        "device": "cpu"
    },
    "audio": {
        "engine": "piper",
        "voice": "en_amy",
        "rate": 1.0,
        "pitch": 1.0,
        "models_dir": "models/voices"
    },
    "training": {
        "epochs": 50,
        "batch_size": 32,
        "learning_rate": 0.001,
        "validation_split": 0.2,
        "early_stopping_patience": 10,
        "augmentation": {
            "rotation_range": 15,
            "scale_range": [0.9, 1.1],
            "translation_range": 0.1,
            "noise_factor": 0.02,
            "flip_horizontal": False
        }
    },
    "ui": {
        "theme": "cyberpunk",
        "show_landmarks": True,
        "show_confidence": True
    },
    "models_dir": "models",
    "data_dir": "data"
}


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    
    config = DEFAULT_CONFIG.copy()
    
    if config_path.exists():
        try:
            with open(config_path) as f:
                user_config = yaml.safe_load(f) or {}
            
            # Deep merge
            config = _deep_merge(config, user_config)
            logger.info(f"Loaded configuration from {config_path}")
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    else:
        logger.warning(f"Config file not found: {config_path}, using defaults")
        
        # Create default config file
        config_path.parent.mkdir(parents=True, exist_ok=True)
        save_config(config, config_path)
    
    return config


def save_config(config: Dict[str, Any], config_path: Path):
    """Save configuration to YAML file."""
    
    try:
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Saved configuration to {config_path}")
    except Exception as e:
        logger.error(f"Error saving config: {e}")


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result
