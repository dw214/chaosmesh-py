"""
Abstract base class for all Chaos Mesh experiments.

This module implements the Template Method pattern, defining the skeleton
of chaos experiment lifecycle while allowing subclasses to customize
action-specific behavior.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field, model_validator

from chaos_sdk.config import config
from chaos_sdk.client import ChaosClient
from chaos_sdk.models.selector import ChaosSelector
from chaos_sdk.models.enums import ChaosMode
from chaos_sdk.exceptions import (
    ExperimentTimeoutError,
    ChaosResourceNotFoundError,
)
from chaos_sdk.utils import generate_unique_name


logger = logging.getLogger(__name__)


class BaseChaos(BaseModel, ABC):
    """
    Abstract base class for all chaos experiments.
    
    This class implements the Template Method pattern:
    - Defines common chaos experiment structure (metadata, selector, mode, duration)
    - Provides lifecycle methods (apply, delete, wait_for_injection)
    - Delegates action-specific spec building to subclasses via _build_action_spec()
    
    Attributes:
        name: Experiment name (auto-generated if not provided)
        namespace: Kubernetes namespace (default: "default")
        selector: Target pod selection criteria
        mode: Target selection mode
        value: Value for fixed/fixed-percent modes
        duration: Experiment duration (e.g., "30s", "5m")
    
    Example:
        >>> # Subclass implementation
        >>> class PodChaos(BaseChaos):
        ...     action: PodChaosAction
        ...     
        ...     def _build_action_spec(self) -> dict:
        ...         return {"action": self.action.value}
    """
    
    # Common fields for all chaos types
    name: str = Field(default_factory=lambda: generate_unique_name("chaos"))
    namespace: str = "default"
    selector: ChaosSelector
    mode: ChaosMode = ChaosMode.ONE
    value: Optional[str] = None
    duration: Optional[str] = None
    
    # Pydantic configuration
    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True
        use_enum_values = False  # Keep enum objects, not string values
    
    @model_validator(mode='after')
    def validate_mode_value(self) -> "BaseChaos":
        """
        Validate that 'value' is provided when required by mode.
        
        Raises:
            ValueError: If value is missing for modes that require it
        """
        modes_requiring_value = {
            ChaosMode.FIXED,
            ChaosMode.FIXED_PERCENT,
            ChaosMode.RANDOM_MAX_PERCENT,
        }
        
        if self.mode in modes_requiring_value and not self.value:
            raise ValueError(
                f"Mode '{self.mode.value}' requires 'value' parameter. "
                f"For example: value='2' for fixed count or value='50' for percentage."
            )
        
        return self
    
    @abstractmethod
    def _build_action_spec(self) -> Dict[str, Any]:
        """
        Build action-specific spec fields.
        
        Subclasses must implement this method to provide chaos-type-specific
        configuration (e.g., PodChaos action, NetworkChaos delay parameters).
        
        Returns:
            Dictionary with action-specific spec fields
        """
        pass
    
    def to_crd(self) -> Dict[str, Any]:
        """
        Build complete Chaos Mesh CRD definition.
        
        This is the Template Method - it defines the overall structure
        and calls _build_action_spec() for customization.
        
        Returns:
            Complete CRD as dictionary, ready for Kubernetes API
        """
        # Get the CRD kind from class name
        kind = self.__class__.__name__
        
        # Build base spec
        spec = {
            "selector": self.selector.to_crd_dict(),
            "mode": self.mode.value,
        }
        
        # Add optional value for fixed modes
        if self.value is not None:
            spec["value"] = self.value
        
        # Add optional duration
        if self.duration is not None:
            spec["duration"] = self.duration
        
        # Merge action-specific spec from subclass
        action_spec = self._build_action_spec()
        spec.update(action_spec)
        
        # Build complete CRD
        crd = {
            "apiVersion": f"{config.api_group}/{config.api_version}",
            "kind": kind,
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
            },
            "spec": spec,
        }
        
        logger.debug(f"Built CRD for {kind}/{self.name}")
        return crd
    
    def apply(self, client: Optional[ChaosClient] = None) -> "BaseChaos":
        """
        Apply the chaos experiment to Kubernetes cluster.
        
        Args:
            client: ChaosClient instance (creates new if not provided)
            
        Returns:
            Self for method chaining
            
        Raises:
            ExperimentAlreadyExistsError: If experiment name already exists
            ChaosMeshConnectionError: If API call fails
        """
        if client is None:
            client = ChaosClient()
        
        kind = self.__class__.__name__
        crd = self.to_crd()
        
        client.create_chaos_resource(
            kind=kind,
            namespace=self.namespace,
            body=crd
        )
        
        logger.info(
            f"Applied {kind}/{self.name} targeting {self.selector}"
        )
        
        return self
    
    def delete(self, client: Optional[ChaosClient] = None) -> None:
        """
        Delete the chaos experiment from Kubernetes cluster.
        
        Args:
            client: ChaosClient instance (creates new if not provided)
            
        Raises:
            ChaosMeshConnectionError: If API call fails
        """
        if client is None:
            client = ChaosClient()
        
        kind = self.__class__.__name__
        
        client.delete_chaos_resource(
            kind=kind,
            namespace=self.namespace,
            name=self.name
        )
        
        logger.info(f"Deleted {kind}/{self.name}")
    
    def get_status(self, client: Optional[ChaosClient] = None) -> Dict[str, Any]:
        """
        Get current status of the chaos experiment.
        
        Args:
            client: ChaosClient instance (creates new if not provided)
            
        Returns:
            Resource status dictionary from Kubernetes
            
        Raises:
            ChaosResourceNotFoundError: If experiment doesn't exist
        """
        if client is None:
            client = ChaosClient()
        
        kind = self.__class__.__name__
        
        resource = client.get_chaos_resource(
            kind=kind,
            namespace=self.namespace,
            name=self.name
        )
        
        return resource.get("status", {})
    
    def wait_for_injection(
        self,
        client: Optional[ChaosClient] = None,
        timeout: Optional[int] = None,
        poll_interval: Optional[float] = None
    ) -> bool:
        """
        Wait for chaos injection to complete by polling status.
        
        This method bridges the gap between Kubernetes' asynchronous
        reconciliation and synchronous test scripts.
        
        Args:
            client: ChaosClient instance (creates new if not provided)
            timeout: Maximum wait time in seconds (uses config default if None)
            poll_interval: Status check interval in seconds (uses config default if None)
            
        Returns:
            True when injection is confirmed
            
        Raises:
            ExperimentTimeoutError: If injection doesn't complete within timeout
            ChaosResourceNotFoundError: If experiment is deleted during wait
        """
        if client is None:
            client = ChaosClient()
        
        timeout = timeout or config.wait_timeout
        poll_interval = poll_interval or config.poll_interval
        
        kind = self.__class__.__name__
        start_time = time.time()
        
        logger.info(
            f"Waiting for {kind}/{self.name} injection "
            f"(timeout: {timeout}s, poll: {poll_interval}s)"
        )
        
        while time.time() - start_time < timeout:
            try:
                status = self.get_status(client)
                
                # Check for AllInjected condition
                conditions = status.get("conditions", [])
                for condition in conditions:
                    if condition.get("type") == "AllInjected":
                        if condition.get("status") == "True":
                            elapsed = time.time() - start_time
                            logger.info(
                                f"Chaos {self.name} injected successfully "
                                f"after {elapsed:.1f}s"
                            )
                            return True
                
                logger.debug(
                    f"Chaos {self.name} not yet injected, "
                    f"waiting {poll_interval}s..."
                )
                
            except ChaosResourceNotFoundError:
                logger.warning(
                    f"Chaos {self.name} not found yet, "
                    f"retrying in {poll_interval}s..."
                )
            
            time.sleep(poll_interval)
        
        # Timeout reached
        elapsed = time.time() - start_time
        raise ExperimentTimeoutError(
            f"Chaos {self.name} injection timeout after {elapsed:.1f}s. "
            f"Check if:\n"
            f"  - Chaos Mesh controller is running\n"
            f"  - Selector matches target pods: {self.selector}\n"
            f"  - Target pods exist and are ready"
        )
    
    def wait_for_deletion(
        self,
        client: Optional[ChaosClient] = None,
        timeout: int = 30,
        poll_interval: float = 1.0
    ) -> bool:
        """
        Wait for chaos experiment to be fully deleted.
        
        Args:
            client: ChaosClient instance (creates new if not provided)
            timeout: Maximum wait time in seconds
            poll_interval: Check interval in seconds
            
        Returns:
            True when deletion is confirmed
            
        Raises:
            ExperimentTimeoutError: If deletion doesn't complete within timeout
        """
        if client is None:
            client = ChaosClient()
        
        kind = self.__class__.__name__
        start_time = time.time()
        
        logger.debug(f"Waiting for {kind}/{self.name} deletion")
        
        while time.time() - start_time < timeout:
            try:
                # Try to get the resource
                self.get_status(client)
                # Still exists, keep waiting
                time.sleep(poll_interval)
                
            except ChaosResourceNotFoundError:
                # Resource deleted successfully
                elapsed = time.time() - start_time
                logger.info(
                    f"Chaos {self.name} deleted successfully "
                    f"after {elapsed:.1f}s"
                )
                return True
        
        # Timeout reached
        raise ExperimentTimeoutError(
            f"Chaos {self.name} deletion timeout after {timeout}s"
        )
    
    def __str__(self) -> str:
        """Human-readable experiment description."""
        kind = self.__class__.__name__
        return f"{kind}(name={self.name}, selector={self.selector}, mode={self.mode.value})"
