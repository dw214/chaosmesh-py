"""
Example: Pytest Integration

This script demonstrates how to integrate Chaos Mesh SDK with pytest
using fixtures for automatic setup/teardown.
"""

import pytest
import time

from chaos_sdk import (
    ChaosController,
    PodChaos,
    NetworkChaos,
    ChaosSelector,
    PodChaosAction,
    ChaosMode,
)


@pytest.fixture
def chaos_controller():
    """
    Pytest fixture providing ChaosController with automatic cleanup.
    
    Usage:
        def test_something(chaos_controller):
            chaos = PodChaos.pod_kill(...)
            chaos_controller.inject(chaos)
            # Test logic
            # Automatic cleanup after test
    """
    controller = ChaosController()
    controller.__enter__()
    
    yield controller
    
    # Cleanup happens regardless of test result
    controller.__exit__(None, None, None)


@pytest.fixture
def web_selector():
    """Fixture providing selector for web-server pods."""
    return ChaosSelector.from_labels(
        labels={"app": "web-server"},
        namespaces=["test"]
    )


def test_pod_resilience_with_pod_kill(chaos_controller, web_selector):
    """
    Test: Service should recover when pods are killed.
    
    This test verifies that the service can handle pod failures
    and recover within acceptable time limits.
    """
    # Arrange - inject pod-kill chaos
    chaos = PodChaos.pod_kill(
        selector=web_selector,
        mode=ChaosMode.ONE
    )
    chaos_controller.inject(chaos, wait=True)
    
    # Act - wait for Kubernetes to restart the pod
    time.sleep(5)
    
    # Assert - verify service is still responsive
    assert check_service_health(), "Service should remain healthy during pod kill"


def test_latency_tolerance_with_network_delay(chaos_controller, web_selector):
    """
    Test: Service should handle 200ms network latency gracefully.
    
    This test verifies that the service doesn't timeout or fail
    when network latency is introduced.
    """
    # Arrange - inject network delay
    chaos = NetworkChaos.create_delay(
       selector=web_selector,
        latency="200ms",
        jitter="20ms",
        duration="30s",
        mode=ChaosMode.ALL
    )
    chaos_controller.inject(chaos, wait=True)
    
    # Act & Assert - verify service still works with increased latency
    response_time = measure_api_response_time()
    
    # Response time should increase but not timeout
    assert 200 <= response_time <= 5000, \
        f"Response time {response_time}ms should be between 200ms and 5s"


def test_partition_resilience(chaos_controller):
    """
    Test: Frontend should handle backend partition gracefully.
    
    This test creates a network partition between frontend and backend
    to verify the system's partition tolerance.
    """
    # Arrange - define frontend and backend selectors
    frontend_selector = ChaosSelector.from_labels(
        labels={"tier": "frontend"},
        namespaces=["test"]
    )
    
    backend_selector = ChaosSelector.from_labels(
        labels={"tier": "backend"},
        namespaces=["test"]
    )
    
    # Inject network partition
    chaos = NetworkChaos.create_partition(
        selector=frontend_selector,
        target=backend_selector,
        direction="to",  # Block traffic FROM frontend TO backend
        mode=ChaosMode.ALL
    )
    chaos_controller.inject(chaos, wait=True)
    
    # Act & Assert - verify frontend shows degraded state, not error
    status = get_frontend_status()
    assert status in ["degraded", "partial"], \
        "Frontend should show degraded state, not crash"


def test_multiple_chaos_experiments(chaos_controller, web_selector):
    """
    Test: System should handle multiple simultaneous chaos events.
    
    This test injects both pod chaos and network chaos simultaneously
    to test worst-case scenarios.
    """
    # Inject pod chaos
    pod_chaos = PodChaos.pod_failure(
        selector=web_selector,
        duration="20s"
    )
    chaos_controller.inject(pod_chaos, wait=True)
    
    # Inject network chaos
    network_chaos = NetworkChaos.create_loss(
        selector=web_selector,
        loss="10",  # 10% packet loss
        duration="20s"
    )
    chaos_controller.inject(network_chaos, wait=True)
    
    # Both chaos experiments are active now
    time.sleep(5)
    
    # Verify system still functions
    assert check_service_health(), \
        "Service should survive multiple simultaneous failures"
    
    # Both experiments will be cleaned up automatically


# Mock helper functions (replace with actual implementations)

def check_service_health() -> bool:
    """Check if the service is healthy."""
    # In real tests, make HTTP request to health endpoint
    # Example: return requests.get("http://service/health").status_code == 200
    return True


def measure_api_response_time() -> float:
    """Measure API response time in milliseconds."""
    # In real tests, time an actual API call
    # Example:
    # start = time.time()
    # requests.get("http://service/api")
    # return (time.time() - start) * 1000
    return 250.0  # Mock value


def get_frontend_status() -> str:
    """Get frontend application status."""
    # In real tests, query frontend status endpoint
    return "degraded"


if __name__ == "__main__":
    # Run tests with pytest
    # pytest pytest_integration.py -v
    print("Run with: pytest pytest_integration.py -v")
