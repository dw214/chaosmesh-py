"""
Custom exception hierarchy for Chaos Mesh SDK.

This module defines all custom exceptions used by the SDK, providing
clear, business-semantic error types for different failure scenarios.
"""


class ChaosMeshSDKError(Exception):
    """
    Base exception for all Chaos Mesh SDK errors.
    
    All custom exceptions inherit from this class, allowing users to catch
    all SDK-specific errors with a single except clause.
    """
    pass


class ChaosMeshConnectionError(ChaosMeshSDKError):
    """
    Raised when unable to connect to Kubernetes API server.
    
    This typically indicates authentication failures, network issues,
    or API server unavailability.
    """
    pass


class ExperimentAlreadyExistsError(ChaosMeshSDKError):
    """
    Raised when attempting to create an experiment that already exists.
    
    Corresponds to HTTP 409 Conflict from Kubernetes API.
    The experiment name must be unique within the namespace.
    """
    pass


class ChaosResourceNotFoundError(ChaosMeshSDKError):
    """
    Raised when attempting to access a non-existent chaos experiment.
    
    Corresponds to HTTP 404 Not Found from Kubernetes API.
    This can occur when:
    - Querying a deleted experiment
    - Using an incorrect experiment name
    - Targeting the wrong namespace
    """
    pass


class AmbiguousSelectorError(ChaosMeshSDKError):
    """
    Raised when selector configuration is ambiguous or conflicting.
    
    This occurs when users specify both label-based and pod-name-based
    selection simultaneously. Chaos Mesh has priority rules for selectors,
    but the SDK enforces mutual exclusivity for clarity.
    """
    pass


class ExperimentTimeoutError(ChaosMeshSDKError):
    """
    Raised when waiting for experiment status exceeds timeout.
    
    This can occur during:
    - wait_for_injection() when chaos doesn't activate in time
    - _wait_for_deletion() when cleanup takes too long
    
    Common causes:
    - Chaos Mesh controller issues
    - Target pods don't exist
    - Selector doesn't match any pods
    """
    pass


class ValidationError(ChaosMeshSDKError):
    """
    Raised when input validation fails.
    
    This is typically raised by Pydantic model validation, but re-exported
    here for consistency with the SDK's exception hierarchy.
    """
    pass
