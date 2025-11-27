"""
Global configuration management for Chaos Mesh SDK.

This module provides a singleton configuration class for managing API settings,
retry behavior, and polling intervals.
"""

import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ChaosConfig:
    """
    Global configuration for Chaos Mesh SDK.
    
    This class uses a singleton pattern to ensure consistent configuration
    across all SDK components.
    
    Attributes:
        api_group: Chaos Mesh API group (default: chaos-mesh.org)
        api_version: Chaos Mesh API version (default: v1alpha1)
        retry_max_attempts: Maximum retry attempts for transient failures
        retry_backoff_multiplier: Exponential backoff multiplier
        retry_min_wait: Minimum wait time between retries (seconds)
        retry_max_wait: Maximum wait time between retries (seconds)
        poll_interval: Status polling interval (seconds)
        wait_timeout: Default timeout for wait operations (seconds)
        kubeconfig_path: Optional path to kubeconfig file
    """

    api_group: str = "chaos-mesh.org"
    api_version: str = "v1alpha1"

    # Retry configuration
    retry_max_attempts: int = 3
    retry_backoff_multiplier: float = 1.0
    retry_min_wait: float = 1.0
    retry_max_wait: float = 10.0

    # Polling configuration
    poll_interval: float = 2.0
    wait_timeout: int = 60

    # Kubernetes configuration
    kubeconfig_path: Optional[str] = None

    # Singleton instance
    _instance: Optional["ChaosConfig"] = field(default=None, init=False, repr=False)

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ChaosConfig":
        """
        Get the singleton configuration instance.
        
        Returns:
            The global ChaosConfig instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (mainly for testing)."""
        cls._instance = None

    def update(self, **kwargs) -> None:
        """
        Update configuration values.
        
        Args:
            **kwargs: Configuration key-value pairs to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info("Updated config: %s=%s", key, value)
            else:
                logger.warning("Unknown config key: %s", key)


# Global configuration instance
config = ChaosConfig.get_instance()
