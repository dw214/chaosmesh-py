"""
Enumerations for Chaos Mesh SDK.

This module defines all enums used across the SDK for type safety
and IDE autocompletion.
"""

from enum import Enum


class ChaosMode(str, Enum):
    """
    Chaos experiment target selection mode.
    
    Determines how target pods are selected from the matched set.
    
    Attributes:
        ONE: Select one random target
        ALL: Select all matching targets
        FIXED: Select a fixed number of targets (requires 'value' parameter)
        FIXED_PERCENT: Select a fixed percentage of targets (requires 'value' parameter)
        RANDOM_MAX_PERCENT: Select a random percentage up to maximum (requires 'value' parameter)
    """

    ONE = "one"
    ALL = "all"
    FIXED = "fixed"
    FIXED_PERCENT = "fixed-percent"
    RANDOM_MAX_PERCENT = "random-max-percent"


class PodChaosAction(str, Enum):
    """
    Pod-level chaos experiment actions.
    
    Attributes:
        POD_FAILURE: Make pod unavailable for a duration
        POD_KILL: Kill and restart the pod
        CONTAINER_KILL: Kill specific container(s) in the pod
    """

    POD_FAILURE = "pod-failure"
    POD_KILL = "pod-kill"
    CONTAINER_KILL = "container-kill"


class NetworkChaosAction(str, Enum):
    """
    Network-level chaos experiment actions.
    
    Attributes:
        DELAY: Add network latency
        LOSS: Drop network packets
        DUPLICATE: Duplicate network packets
        CORRUPT: Corrupt network packet data
        PARTITION: Create network partition between pods
        BANDWIDTH: Limit network bandwidth
        REORDER: Reorder network packets
    """

    DELAY = "delay"
    LOSS = "loss"
    DUPLICATE = "duplicate"
    CORRUPT = "corrupt"
    PARTITION = "partition"
    BANDWIDTH = "bandwidth"
    REORDER = "reorder"


class NetworkDirection(str, Enum):
    """
    Network partition direction.
    
    Used for partition action to specify traffic direction.
    
    Attributes:
        TO: Block traffic TO target
        FROM: Block traffic FROM target
        BOTH: Block traffic in BOTH directions
    """

    TO = "to"
    FROM = "from"
    BOTH = "both"


# List of all Chaos Mesh CRD kinds
CHAOS_KINDS = [
    "PodChaos",
    "NetworkChaos",
    "IOChaos",
    "StressChaos",
    "TimeChaos",
    "KernelChaos",
    "DNSChaos",
    "HTTPChaos",
    "JVMChaos",
    "AWSChaos",
    "GCPChaos",
]
