"""
Utility functions for Chaos Mesh SDK.

This module provides helper functions for name generation, duration parsing,
and orphaned experiment cleanup.
"""

import logging
import time
import re
from typing import Optional
from datetime import datetime


logger = logging.getLogger(__name__)


def generate_unique_name(prefix: str = "chaos") -> str:
    """
    Generate a unique experiment name with timestamp.
    
    Args:
        prefix: Name prefix (default: "chaos")
        
    Returns:
        Unique experiment name in format: {prefix}-{timestamp}
        
    Example:
        >>> generate_unique_name("pod-kill")
        'pod-kill-1700820345'
    """
    timestamp = int(time.time())
    return f"{prefix}-{timestamp}"


def parse_duration(duration: str) -> int:
    """
    Parse duration string to seconds.
    
    Supports formats: "30s", "5m", "2h"
    
    Args:
        duration: Duration string with unit suffix
        
    Returns:
        Duration in seconds
        
    Raises:
        ValueError: If duration format is invalid
        
    Examples:
        >>> parse_duration("30s")
        30
        >>> parse_duration("5m")
        300
        >>> parse_duration("2h")
        7200
    """
    pattern = r'^(\d+)(s|m|h)$'
    match = re.match(pattern, duration)
    
    if not match:
        raise ValueError(
            f"Invalid duration format: {duration}. "
            "Expected format: <number><unit> where unit is s/m/h"
        )
    
    value, unit = match.groups()
    value = int(value)
    
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
    }
    
    return value * multipliers[unit]


def validate_network_param_format(param: str, param_name: str = "parameter") -> str:
    """
    Validate network parameter format (e.g., latency, jitter).
    
    Parameters must be in format: <number><unit> where unit is ms/s/m
    
    Args:
        param: Parameter string to validate
        param_name: Name for error messages
        
    Returns:
        Validated parameter string
        
    Raises:
        ValueError: If format is invalid
        
    Examples:
        >>> validate_network_param_format("100ms", "latency")
        '100ms'
        >>> validate_network_param_format("invalid", "latency")
        ValueError: Invalid latency format...
    """
    pattern = r'^\d+(?:ms|s|m)$'
    
    if not re.match(pattern, param):
        raise ValueError(
            f"Invalid {param_name} format: {param}. "
            "Expected format: <number><unit> where unit is ms/s/m. "
            "Examples: '100ms', '1s', '5m'"
        )
    
    return param


def validate_percentage(value: str, param_name: str = "parameter") -> str:
    """
    Validate percentage parameter (0-100).
    
    Args:
        value: Percentage value as string
        param_name: Name for error messages
        
    Returns:
        Validated percentage string
        
    Raises:
        ValueError: If value is not a valid percentage
    """
    try:
        percentage = float(value)
        if not 0 <= percentage <= 100:
            raise ValueError(
                f"Invalid {param_name}: {value}. Must be between 0 and 100."
            )
    except (ValueError, TypeError):
        raise ValueError(
            f"Invalid {param_name}: {value}. Must be a number between 0 and 100."
        )
    
    return value


def cleanup_orphaned_experiments(
    client: "ChaosClient",  # type: ignore
    namespace: str = "default",
    label_selector: Optional[str] = None,
    dry_run: bool = False
) -> int:
    """
    Find and delete orphaned chaos experiments.
    
    Orphaned experiments are those left behind from crashed test runs
    or manual experiments that were not cleaned up.
    
    Args:
        client: ChaosClient instance
        namespace: Kubernetes namespace to search
        label_selector: Optional label selector to filter experiments
        dry_run: If True, only list experiments without deleting
        
    Returns:
        Number of experiments cleaned up
        
    Example:
        >>> from chaos_sdk.client import ChaosClient
        >>> client = ChaosClient()
        >>> count = cleanup_orphaned_experiments(
        ...     client,
        ...     namespace="test",
        ...     label_selector="created-by=sdk",
        ...     dry_run=True
        ... )
        >>> print(f"Found {count} orphaned experiments")
    """
    from chaos_sdk.models.enums import CHAOS_KINDS
    
    cleaned_count = 0
    
    for kind in CHAOS_KINDS:
        try:
            experiments = client.list_chaos_resources(
                kind=kind,
                namespace=namespace,
                label_selector=label_selector or ""
            )
            
            for exp in experiments:
                name = exp.get("metadata", {}).get("name")
                if not name:
                    continue
                
                if dry_run:
                    logger.info(f"[DRY-RUN] Would delete {kind}/{name}")
                else:
                    logger.info(f"Deleting orphaned experiment: {kind}/{name}")
                    client.delete_chaos_resource(kind, namespace, name)
                
                cleaned_count += 1
                
        except Exception as e:
            logger.warning(f"Error cleaning {kind} experiments: {e}")
    
    return cleaned_count
