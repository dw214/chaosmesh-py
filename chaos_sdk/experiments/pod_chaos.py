"""
PodChaos experiment implementation.

This module provides the PodChaos class for pod-level fault injection,
including pod-failure, pod-kill, and container-kill actions.
"""

import logging
from typing import Optional, List, Dict, Any

from pydantic import Field, model_validator

from chaos_sdk.models.base import BaseChaos
from chaos_sdk.models.enums import PodChaosAction

logger = logging.getLogger(__name__)


class PodChaos(BaseChaos):
    """
    Pod-level chaos experiment.
    
    Supports pod-failure, pod-kill, and container-kill actions.
    
    Attributes:
        action: Type of pod chaos to inject
        container_names: Container names (required for container-kill)
        grace_period: Termination grace period in seconds
    """

    action: PodChaosAction = Field(..., description="Pod chaos action type")
    container_names: Optional[List[str]] = Field(
        default=None,
        description="Container names to target (required for container-kill)"
    )
    grace_period: Optional[int] = Field(
        default=None,
        description="Termination grace period in seconds",
        ge=0
    )

    scheduler: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Scheduler configuration for recurring chaos experiments"
    )
    remote_cluster: Optional[str] = Field(
        default=None,
        description="Remote cluster name for multi-cluster chaos scenarios"
    )

    @model_validator(mode='after')
    def validate_container_kill(self) -> "PodChaos":
        """Validate container_names is provided for container-kill action."""
        if self.action == PodChaosAction.CONTAINER_KILL and not self.container_names:
            raise ValueError(
                "container-kill requires container_names, e.g.: "
                "container_names=['nginx', 'sidecar']"
            )
        return self

    def _build_action_spec(self) -> Dict[str, Any]:
        """Build PodChaos-specific spec fields."""
        spec = {"action": self.action.value}

        if self.container_names:
            spec["containerNames"] = self.container_names

        if self.grace_period is not None:
            spec["gracePeriod"] = self.grace_period

        if self.scheduler is not None:
            spec["scheduler"] = self.scheduler

        if self.remote_cluster is not None:
            spec["remoteCluster"] = self.remote_cluster

        return spec

    @classmethod
    def pod_failure(
            cls,
            selector: "ChaosSelector",  # type: ignore
            duration: str = "30s",
            **kwargs
    ) -> "PodChaos":
        """
        Convenience constructor for pod-failure chaos.
        
        Args:
            selector: Target pod selector
            duration: Failure duration (e.g., "30s", "5m")
            **kwargs: Additional PodChaos parameters
            
        Returns:
            Configured PodChaos instance
        """
        return cls(
            action=PodChaosAction.POD_FAILURE,
            selector=selector,
            duration=duration,
            **kwargs
        )

    @classmethod
    def pod_kill(
            cls,
            selector: "ChaosSelector",  # type: ignore
            grace_period: Optional[int] = None,
            **kwargs
    ) -> "PodChaos":
        """
        Convenience constructor for pod-kill chaos.
        
        Args:
            selector: Target pod selector
            grace_period: Optional termination grace period
            **kwargs: Additional PodChaos parameters
            
        Returns:
            Configured PodChaos instance
        """
        return cls(
            action=PodChaosAction.POD_KILL,
            selector=selector,
            grace_period=grace_period,
            **kwargs
        )

    @classmethod
    def container_kill(
            cls,
            selector: "ChaosSelector",  # type: ignore
            container_names: List[str],
            grace_period: Optional[int] = None,
            **kwargs
    ) -> "PodChaos":
        """
        Convenience constructor for container-kill chaos.
        
        Args:
            selector: Target pod selector
            container_names: List of container names to kill
            grace_period: Optional termination grace period
            **kwargs: Additional PodChaos parameters
            
        Returns:
            Configured PodChaos instance
        """
        return cls(
            action=PodChaosAction.CONTAINER_KILL,
            selector=selector,
            container_names=container_names,
            grace_period=grace_period,
            **kwargs
        )
