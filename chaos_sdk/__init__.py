"""
Chaos Mesh SDK - Enterprise-grade Python SDK for Chaos Mesh automation.

This SDK provides type-safe, user-friendly interfaces for creating and managing
Chaos Mesh experiments in Kubernetes clusters, with automatic cleanup and
synchronous wait mechanisms for integration with automated testing frameworks.
"""

from chaos_sdk.config import ChaosConfig
from chaos_sdk.controller import ChaosController
from chaos_sdk.exceptions import (
    ChaosMeshSDKError,
    ChaosMeshConnectionError,
    ExperimentAlreadyExistsError,
    ChaosResourceNotFoundError,
    AmbiguousSelectorError,
    ExperimentTimeoutError,
)
from chaos_sdk.models.selector import ChaosSelector
from chaos_sdk.models.enums import ChaosMode, PodChaosAction, NetworkChaosAction
from chaos_sdk.experiments.pod_chaos import PodChaos
from chaos_sdk.experiments.network_chaos import (
    NetworkChaos,
    NetworkDelayParams,
    NetworkLossParams,
    NetworkDuplicateParams,
    NetworkCorruptParams,
    NetworkPartitionParams,
    NetworkBandwidthParams,
    NetworkReorderParams,
)

__version__ = "0.1.0"
__all__ = [
    # Configuration
    "ChaosConfig",
    # Controller
    "ChaosController",
    # Exceptions
    "ChaosMeshSDKError",
    "ChaosMeshConnectionError",
    "ExperimentAlreadyExistsError",
    "ChaosResourceNotFoundError",
    "AmbiguousSelectorError",
    "ExperimentTimeoutError",
    # Models
    "ChaosSelector",
    "ChaosMode",
    "PodChaosAction",
    "NetworkChaosAction",
    # Experiments
    "PodChaos",
    "NetworkChaos",
    "NetworkDelayParams",
    "NetworkLossParams",
    "NetworkDuplicateParams",
    "NetworkCorruptParams",
    "NetworkPartitionParams",
    "NetworkBandwidthParams",
    "NetworkReorderParams",
]
