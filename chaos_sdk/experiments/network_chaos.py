"""
NetworkChaos experiment implementation.

This module provides the NetworkChaos class for network-level fault injection,
with user-friendly parameter conversion and validation.
"""

import logging
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator, model_validator

from chaos_sdk.models.base import BaseChaos
from chaos_sdk.models.selector import ChaosSelector
from chaos_sdk.models.enums import NetworkChaosAction, NetworkDirection
from chaos_sdk.utils import validate_network_param_format, validate_percentage


logger = logging.getLogger(__name__)


class NetworkDelayParams(BaseModel):
    """
    Parameters for network delay chaos.
    
    Attributes:
        latency: Network latency (e.g., "100ms", "1s")
        jitter: Latency variation (e.g., "10ms")
        correlation: Correlation percentage ("0" to "100")
        reorder: Packet reorder configuration
    
    Example:
        >>> params = NetworkDelayParams(
        ...     latency="100ms",
        ...     jitter="10ms",
        ...     correlation="50"
        ... )
    """
    
    latency: str = Field(..., description="Network latency (e.g., '100ms', '1s')")
    jitter: str = Field(default="0ms", description="Latency variation")
    correlation: str = Field(default="0", description="Correlation percentage (0-100)")
    reorder: Optional[Dict[str, str]] = Field(
        default=None,
        description="Packet reorder configuration"
    )
    
    @field_validator('latency', 'jitter')
    @classmethod
    def validate_duration_format(cls, v: str) -> str:
        """Validate latency/jitter format."""
        return validate_network_param_format(v, "latency/jitter")
    
    @field_validator('correlation')
    @classmethod
    def validate_correlation(cls, v: str) -> str:
        """Validate correlation is a percentage."""
        return validate_percentage(v, "correlation")


class NetworkLossParams(BaseModel):
    """
    Parameters for network packet loss chaos.
    
    Attributes:
        loss: Packet loss percentage ("0" to "100")
        correlation: Correlation percentage ("0" to "100")
    
    Example:
        >>> params = NetworkLossParams(loss="20", correlation="50")
    """
    
    loss: str = Field(..., description="Packet loss percentage (0-100)")
    correlation: str = Field(default="0", description="Correlation percentage (0-100)")
    
    @field_validator('loss', 'correlation')
    @classmethod
    def validate_percentage_field(cls, v: str) -> str:
        """Validate percentage values."""
        return validate_percentage(v, "percentage")


class NetworkDuplicateParams(BaseModel):
    """
    Parameters for network packet duplication chaos.
    
    Attributes:
        duplicate: Packet duplication percentage ("0" to "100")
        correlation: Correlation percentage ("0" to "100")
    
    Example:
        >>> params = NetworkDuplicateParams(duplicate="10", correlation="25")
    """
    
    duplicate: str = Field(..., description="Packet duplication percentage (0-100)")
    correlation: str = Field(default="0", description="Correlation percentage (0-100)")
    
    @field_validator('duplicate', 'correlation')
    @classmethod
    def validate_percentage_field(cls, v: str) -> str:
        """Validate percentage values."""
        return validate_percentage(v, "percentage")


class NetworkCorruptParams(BaseModel):
    """
    Parameters for network packet corruption chaos.
    
    Attributes:
        corrupt: Packet corruption percentage ("0" to "100")
        correlation: Correlation percentage ("0" to "100")
    
    Example:
        >>> params = NetworkCorruptParams(corrupt="5", correlation="10")
    """
    
    corrupt: str = Field(..., description="Packet corruption percentage (0-100)")
    correlation: str = Field(default="0", description="Correlation percentage (0-100)")
    
    @field_validator('corrupt', 'correlation')
    @classmethod
    def validate_percentage_field(cls, v: str) -> str:
        """Validate percentage values."""
        return validate_percentage(v, "percentage")


class NetworkPartitionParams(BaseModel):
    """
    Parameters for network partition chaos.
    
    Attributes:
        direction: Traffic direction to block ("to", "from", "both")
        target: Target pod selector for partition
    
    Example:
        >>> params = NetworkPartitionParams(
        ...     direction=NetworkDirection.TO,
        ...     target=ChaosSelector.from_labels({"app": "database"})
        ... )
    """
    
    direction: NetworkDirection = Field(..., description="Traffic direction")
    target: ChaosSelector = Field(..., description="Target selector for partition")


class NetworkBandwidthParams(BaseModel):
    """
    Parameters for network bandwidth limitation chaos.
    
    Attributes:
        rate: Bandwidth rate (e.g., "1mbps", "10kbps")
        limit: Buffer size limit (e.g., "1000")
        buffer: Buffer size (e.g., "10000")
        peakrate: Peak rate (optional)
        minburst: Minimum burst size (optional)
    
    Example:
        >>> params = NetworkBandwidthParams(
        ...     rate="1mbps",
        ...     limit="1000",
        ...     buffer="10000"
        ... )
    """
    
    rate: str = Field(..., description="Bandwidth rate (e.g., '1mbps')")
    limit: str = Field(..., description="Buffer limit")
    buffer: str = Field(..., description="Buffer size")
    peakrate: Optional[str] = Field(default=None, description="Peak rate")
    minburst: Optional[str] = Field(default=None, description="Minimum burst size")


class NetworkReorderParams(BaseModel):
    """
    Parameters for network packet reordering chaos.
    
    Attributes:
        reorder: Packet reorder percentage ("0" to "100")
        correlation: Correlation percentage ("0" to "100")
        gap: Gap for reorder
    
    Example:
        >>> params = NetworkReorderParams(
        ...     reorder="25",
        ...     correlation="50",
        ...     gap="5"
        ... )
    """
    
    reorder: str = Field(..., description="Packet reorder percentage (0-100)")
    correlation: str = Field(default="0", description="Correlation percentage (0-100)")
    gap: str = Field(..., description="Gap value for reorder")
    
    @field_validator('reorder', 'correlation')
    @classmethod
    def validate_percentage_field(cls, v: str) -> str:
        """Validate percentage values."""
        return validate_percentage(v, "percentage")


class NetworkChaos(BaseChaos):
    """
    Network-level chaos experiment.
    
    Injects various network faults:
    - delay: Add network latency
    - loss: Drop packets
    - duplicate: Duplicate packets
    - corrupt: Corrupt packet data
    - partition: Create network partition
    - bandwidth: Limit bandwidth
    - reorder: Reorder packets
    
    Attributes:
        action: Type of network chaos to inject
        delay: Delay parameters (for DELAY action)
        loss: Loss parameters (for LOSS action)
        duplicate: Duplicate parameters (for DUPLICATE action)
        corrupt: Corrupt parameters (for CORRUPT action)
        partition: Partition parameters (for PARTITION action)
        bandwidth: Bandwidth parameters (for BANDWIDTH action)
        reorder: Reorder parameters (for REORDER action)
    
    Examples:
        >>> from chaos_sdk import (
        ...     NetworkChaos,
        ...     NetworkChaosAction,
        ...     ChaosSelector,
        ...     NetworkDelayParams
        ... )
        
        >>> # Delay chaos using convenience method
        >>> chaos = NetworkChaos.create_delay(
        ...     selector=ChaosSelector.from_labels({"app": "web"}),
        ...     latency="100ms",
        ...     jitter="10ms",
        ...     duration="30s"
        ... )
        
        >>> # Loss chaos using direct construction
        >>> chaos = NetworkChaos(
        ...     action=NetworkChaosAction.LOSS,
        ...     loss=NetworkLossParams(loss="20", correlation="50"),
        ...     selector=ChaosSelector.from_labels({"tier": "frontend"}),
        ...     duration="1m"
        ... )
    """
    
    action: NetworkChaosAction = Field(..., description="Network chaos action type")
    
    # Action-specific parameters (only one should be set based on action)
    delay: Optional[NetworkDelayParams] = None
    loss: Optional[NetworkLossParams] = None
    duplicate: Optional[NetworkDuplicateParams] = None
    corrupt: Optional[NetworkCorruptParams] = None
    partition: Optional[NetworkPartitionParams] = None
    bandwidth: Optional[NetworkBandwidthParams] = None
    reorder: Optional[NetworkReorderParams] = None
    
    @model_validator(mode='after')
    def validate_action_params(self) -> "NetworkChaos":
        """
        Ensure required parameters are provided for the selected action.
        
        Raises:
            ValueError: If action parameters don't match the action type
        """
        param_map = {
            NetworkChaosAction.DELAY: self.delay,
            NetworkChaosAction.LOSS: self.loss,
            NetworkChaosAction.DUPLICATE: self.duplicate,
            NetworkChaosAction.CORRUPT: self.corrupt,
            NetworkChaosAction.PARTITION: self.partition,
            NetworkChaosAction.BANDWIDTH: self.bandwidth,
            NetworkChaosAction.REORDER: self.reorder,
        }
        
        required_param = param_map.get(self.action)
        
        if required_param is None:
            raise ValueError(
                f"Action '{self.action.value}' requires corresponding parameters. "
                f"For example, for delay action, provide: "
                f"delay=NetworkDelayParams(latency='100ms')"
            )
        
        return self
    
    def _build_action_spec(self) -> Dict[str, Any]:
        """
        Build NetworkChaos-specific spec fields.
        
        Returns:
            Dictionary with action and action-specific parameters
        """
        spec = {
            "action": self.action.value
        }
        
        # Map action to corresponding spec field
        if self.action == NetworkChaosAction.DELAY and self.delay:
            spec["delay"] = self.delay.model_dump(exclude_none=True)
            
        elif self.action == NetworkChaosAction.LOSS and self.loss:
            spec["loss"] = self.loss.model_dump(exclude_none=True)
            
        elif self.action == NetworkChaosAction.DUPLICATE and self.duplicate:
            spec["duplicate"] = self.duplicate.model_dump(exclude_none=True)
            
        elif self.action == NetworkChaosAction.CORRUPT and self.corrupt:
            spec["corrupt"] = self.corrupt.model_dump(exclude_none=True)
            
        elif self.action == NetworkChaosAction.PARTITION and self.partition:
            spec["direction"] = self.partition.direction.value
            spec["target"] = self.partition.target.to_crd_dict()
            
        elif self.action == NetworkChaosAction.BANDWIDTH and self.bandwidth:
            spec["bandwidth"] = self.bandwidth.model_dump(exclude_none=True)
            
        elif self.action == NetworkChaosAction.REORDER and self.reorder:
            spec["reorder"] = self.reorder.model_dump(exclude_none=True)
        
        return spec
    
    # Convenience constructors for common actions
    
    @classmethod
    def create_delay(
        cls,
        selector: ChaosSelector,
        latency: str = "100ms",
        jitter: str = "10ms",
        correlation: str = "0",
        **kwargs
    ) -> "NetworkChaos":
        """
        Create network delay chaos experiment.
        
        Args:
            selector: Target pod selector
            latency: Network latency (e.g., "100ms", "1s")
            jitter: Latency variation
            correlation: Correlation percentage ("0" to "100")
            **kwargs: Additional NetworkChaos parameters (e.g., duration, mode)
            
        Returns:
            Configured NetworkChaos instance
        """
        return cls(
            action=NetworkChaosAction.DELAY,
            selector=selector,
            delay=NetworkDelayParams(
                latency=latency,
                jitter=jitter,
                correlation=correlation
            ),
            **kwargs
        )
    
    @classmethod
    def create_loss(
        cls,
        selector: ChaosSelector,
        loss: str = "20",
        correlation: str = "0",
        **kwargs
    ) -> "NetworkChaos":
        """
        Create network packet loss chaos experiment.
        
        Args:
            selector: Target pod selector
            loss: Packet loss percentage ("0" to "100")
            correlation: Correlation percentage
            **kwargs: Additional NetworkChaos parameters
            
        Returns:
            Configured NetworkChaos instance
        """
        return cls(
            action=NetworkChaosAction.LOSS,
            selector=selector,
            loss=NetworkLossParams(
                loss=loss,
                correlation=correlation
            ),
            **kwargs
        )
    
    @classmethod
    def create_partition(
        cls,
        selector: ChaosSelector,
        target: ChaosSelector,
        direction: NetworkDirection = NetworkDirection.TO,
        **kwargs
    ) -> "NetworkChaos":
        """
        Create network partition chaos experiment.
        
        Args:
            selector: Source pod selector
            target: Target pod selector
            direction: Traffic direction to block
            **kwargs: Additional NetworkChaos parameters
            
        Returns:
            Configured NetworkChaos instance
        """
        return cls(
            action=NetworkChaosAction.PARTITION,
            selector=selector,
            partition=NetworkPartitionParams(
                direction=direction,
                target=target
            ),
            **kwargs
        )
    
    @classmethod
    def create_bandwidth(
        cls,
        selector: ChaosSelector,
        rate: str = "1mbps",
        limit: str = "1000",
        buffer: str = "10000",
        **kwargs
    ) -> "NetworkChaos":
        """
        Create network bandwidth limitation chaos experiment.
        
        Args:
            selector: Target pod selector
            rate: Bandwidth rate (e.g., "1mbps", "100kbps")
            limit: Buffer limit
            buffer: Buffer size
            **kwargs: Additional NetworkChaos parameters
            
        Returns:
            Configured NetworkChaos instance
        """
        return cls(
            action=NetworkChaosAction.BANDWIDTH,
            selector=selector,
            bandwidth=NetworkBandwidthParams(
                rate=rate,
                limit=limit,
                buffer=buffer
            ),
            **kwargs
        )
