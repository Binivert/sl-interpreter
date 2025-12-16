"""Module registry for plugin management."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base_module import BaseModule
from .loader import ModuleLoader

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """Central registry for all loadable modules."""
    
    def __init__(self, config: dict):
        self.config = config
        self.modules_dir = Path(config.get("modules_dir", "models"))
        self.loader = ModuleLoader()
        
        self._gesture_models: Dict[str, dict] = {}
        self._voice_models: Dict[str, dict] = {}
        self._language_packs: Dict[str, dict] = {}
        self._plugins: Dict[str, BaseModule] = {}
        
        self._scan_modules()
    
    def _scan_modules(self):
        """Scan for available modules."""
        
        # Scan gesture models
        gestures_dir = self.modules_dir / "gestures"
        if gestures_dir.exists():
            for model_dir in gestures_dir.iterdir():
                if model_dir.is_dir():
                    self._gesture_models[model_dir.name] = {
                        "path": str(model_dir),
                        "loaded": False
                    }
        
        # Scan voice models
        voices_dir = self.modules_dir / "voices"
        if voices_dir.exists():
            for voice_dir in voices_dir.iterdir():
                if voice_dir.is_dir():
                    self._voice_models[voice_dir.name] = {
                        "path": str(voice_dir),
                        "loaded": False
                    }
        
        # Scan language packs
        languages_dir = self.modules_dir / "languages"
        if languages_dir.exists():
            for lang_dir in languages_dir.iterdir():
                if lang_dir.is_dir():
                    self._language_packs[lang_dir.name] = {
                        "path": str(lang_dir),
                        "loaded": False
                    }
        
        logger.info(
            f"Found {len(self._gesture_models)} gesture models, "
            f"{len(self._voice_models)} voices, "
            f"{len(self._language_packs)} language packs"
        )
    
    def list_gesture_models(self) -> List[str]:
        """List available gesture models."""
        return list(self._gesture_models.keys())
    
    def list_voice_models(self) -> List[str]:
        """List available voice models."""
        return list(self._voice_models.keys())
    
    def list_language_packs(self) -> List[str]:
        """List available language packs."""
        return list(self._language_packs.keys())
    
    def get_module_info(self, module_type: str, module_name: str) -> Optional[dict]:
        """Get information about a specific module."""
        
        if module_type == "gesture":
            return self._gesture_models.get(module_name)
        elif module_type == "voice":
            return self._voice_models.get(module_name)
        elif module_type == "language":
            return self._language_packs.get(module_name)
        
        return None
    
    def register_plugin(self, name: str, plugin: BaseModule):
        """Register a plugin module."""
        
        self._plugins[name] = plugin
        logger.info(f"Registered plugin: {name}")
    
    def get_plugin(self, name: str) -> Optional[BaseModule]:
        """Get a registered plugin."""
        
        return self._plugins.get(name)
    
    def refresh(self):
        """Rescan for modules."""
        
        self._gesture_models.clear()
        self._voice_models.clear()
        self._language_packs.clear()
        self._scan_modules()
