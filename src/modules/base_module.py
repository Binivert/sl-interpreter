"""Base class for plugin modules."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseModule(ABC):
    """Abstract base class for all plugin modules."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._enabled = True
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the module name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Return the module version."""
        pass
    
    @property
    def enabled(self) -> bool:
        """Check if module is enabled."""
        return self._enabled
    
    def enable(self):
        """Enable the module."""
        self._enabled = True
    
    def disable(self):
        """Disable the module."""
        self._enabled = False
    
    @abstractmethod
    def initialize(self):
        """Initialize the module."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up module resources."""
        pass
