"""
Chaos experiment selector model.

This module provides the ChaosSelector class for defining target pod selection
with mutual exclusivity validation between label-based and pod-name-based targeting.
"""

import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

from chaos_sdk.exceptions import AmbiguousSelectorError


logger = logging.getLogger(__name__)


class ChaosSelector(BaseModel):
    """
    Unified selector for chaos experiment targets.
    
    Supports two mutually exclusive selection methods:
    1. Label-based: Select pods matching label selector(s)
    2. Pod-specific: Select specific pods by name
    
    Chaos Mesh prioritizes 'pods' field if both are specified, but this SDK
    enforces mutual exclusivity for clarity.
    
    Attributes:
        namespaces: List of namespaces to target (empty = all namespaces)
        label_selectors: Label key-value pairs for pod matching
        pods: Dictionary mapping namespace to list of pod names
        field_selectors: Kubernetes field selectors (advanced usage)
        annotation_selectors: Annotation key-value pairs for pod matching
    
    Examples:
        >>> # Label-based selection
        >>> selector = ChaosSelector(
        ...     namespaces=["production"],
        ...     label_selectors={"app": "web-server", "tier": "frontend"}
        ... )
        
        >>> # Pod-specific selection
        >>> selector = ChaosSelector.from_pods(
        ...     namespace="default",
        ...     pod_names=["nginx-7d8b6", "nginx-9f3a2"]
        ... )
    """
    
    namespaces: List[str] = Field(default_factory=list)
    label_selectors: Dict[str, str] = Field(default_factory=dict)
    pods: Dict[str, List[str]] = Field(default_factory=dict)
    field_selectors: Dict[str, str] = Field(default_factory=dict)
    annotation_selectors: Dict[str, str] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def validate_mutual_exclusivity(self) -> "ChaosSelector":
        """
        Ensure only one primary selection method is used.
        
        Raises:
            AmbiguousSelectorError: If both label_selectors and pods are specified
        """
        if self.label_selectors and self.pods:
            raise AmbiguousSelectorError(
                "Cannot use both 'label_selectors' and 'pods' simultaneously. "
                "Chaos Mesh prioritizes 'pods' field, but this SDK requires "
                "explicit choice. Use either:\n"
                "  - label_selectors for label-based selection, OR\n"
                "  - pods for pod-name-based selection"
            )
        
        # At least one selection method must be specified
        if not (self.label_selectors or self.pods or self.field_selectors or 
                self.annotation_selectors):
            raise AmbiguousSelectorError(
                "At least one selection method must be specified: "
                "label_selectors, pods, field_selectors, or annotation_selectors"
            )
        
        return self
    
    @classmethod
    def from_labels(
        cls,
        labels: Dict[str, str],
        namespaces: Optional[List[str]] = None
    ) -> "ChaosSelector":
        """
        Convenience constructor for label-based selection.
        
        Args:
            labels: Label key-value pairs
            namespaces: Optional list of namespaces to target
            
        Returns:
            ChaosSelector configured for label-based selection
        """
        return cls(
            namespaces=namespaces or [],
            label_selectors=labels
        )
    
    @classmethod
    def from_pods(
        cls,
        namespace: str,
        pod_names: List[str]
    ) -> "ChaosSelector":
        """
        Convenience constructor for pod-specific selection.
        
        Args:
            namespace: Namespace containing the pods
            pod_names: List of pod names to target
            
        Returns:
            ChaosSelector configured for pod-specific selection
        """
        return cls(
            namespaces=[namespace],
            pods={namespace: pod_names}
        )
    
    def to_crd_dict(self) -> Dict:
        """
        Convert selector to Chaos Mesh CRD format.
        
        Returns:
            Dictionary matching Chaos Mesh selector specification
        """
        selector_dict = {}
        
        # Add namespaces if specified
        if self.namespaces:
            selector_dict["namespaces"] = self.namespaces
        
        # Add label selectors (convert to proper format)
        if self.label_selectors:
            selector_dict["labelSelectors"] = self.label_selectors
        
        # Add pod selectors
        if self.pods:
            selector_dict["pods"] = self.pods
        
        # Add field selectors
        if self.field_selectors:
            selector_dict["fieldSelectors"] = self.field_selectors
        
        # Add annotation selectors
        if self.annotation_selectors:
            selector_dict["annotationSelectors"] = self.annotation_selectors
        
        return selector_dict
    
    def __str__(self) -> str:
        """Human-readable selector description."""
        if self.pods:
            pods_str = ", ".join(
                f"{ns}/{','.join(names)}" for ns, names in self.pods.items()
            )
            return f"Pods: {pods_str}"
        elif self.label_selectors:
            labels_str = ", ".join(
                f"{k}={v}" for k, v in self.label_selectors.items()
            )
            ns_str = f" in {', '.join(self.namespaces)}" if self.namespaces else ""
            return f"Labels: {labels_str}{ns_str}"
        else:
            return "Custom selector"
