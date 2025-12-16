"""Dynamic module loading."""

import importlib.util
import logging
from pathlib import Path
from typing import Optional, Type

from .base_module import BaseModule

logger = logging.getLogger(__name__)


class ModuleLoader:
    """Dynamically loads plugin modules."""
    
    def load_from_file(self, module_path: Path) -> Optional[Type[BaseModule]]:
        """Load a module from a Python file."""
        
        if not module_path.exists():
            logger.error(f"Module file not found: {module_path}")
            return None
        
        try:
            spec = importlib.util.spec_from_file_location(
                module_path.stem,
                module_path
            )
            
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create spec for {module_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find BaseModule subclass
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type) and
                    issubclass(attr, BaseModule) and
                    attr is not BaseModule
                ):
                    logger.info(f"Loaded module: {attr_name} from {module_path}")
                    return attr
            
            logger.warning(f"No BaseModule subclass found in {module_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading module {module_path}: {e}")
            return None
    
    def load_from_directory(self, directory: Path) -> list:
        """Load all modules from a directory."""
        
        modules = []
        
        if not directory.exists():
            return modules
        
        for py_file in directory.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            module_class = self.load_from_file(py_file)
            if module_class:
                modules.append(module_class)
        
        return modules
