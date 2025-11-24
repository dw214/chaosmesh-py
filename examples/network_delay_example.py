"""
Example: NetworkChaos - Network Delay Experiment

This script demonstrates how to use the Chaos Mesh SDK to inject
network latency with automatic parameter conversion.
"""

import logging
import time

from chaos_sdk import (
    ChaosController,
    NetworkChaos,
    ChaosSelector,
    ChaosMode,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """
    Run a network delay chaos experiment.
    
    This example demonstrates:
    - User-friendly parameter syntax (e.g., latency='100ms')
    - Automatic conversion to Chaos Mesh CRD format
    - Synchronous wait for injection
    - Automatic cleanup
    """
    
    print("=" * 60)
    print("Network Delay Chaos Experiment Example")
    print("=" * 60)
    
    # Define target - pods with app=web label in default namespace
    selector = ChaosSelector.from_labels(
        labels={"app": "web-show"},
        namespaces=["default"]
    )
    
    # Create network delay experiment using convenience method
    # Notice the user-friendly parameter format!
    chaos = NetworkChaos.create_delay(
        selector=selector,
        latency="100ms",  # Add 100ms latency
        jitter="10ms",    # ±10ms variation
        correlation="50", # 50% correlation
        mode=ChaosMode.ALL,
        duration="30s",   # Run for 30 seconds
        name="example-network-delay"
    )
    
    print(f"\nCreated network delay chaos:")
    print(f"  - Latency: 100ms ± 10ms")
    print(f"  - Correlation: 50%")
    print(f"  - Duration: 30s")
    print(f"  - Target: {selector}")
    
    # Use context manager for automatic cleanup
    with ChaosController() as controller:
        print("\n[1/3] Injecting network delay chaos...")
        controller.inject(chaos, wait=True, timeout=60)
        
        print("\n[2/3] Network delay active!")
        print("      Target pods should experience ~100ms added latency.")
        print("      Test your application's latency tolerance here.")
        print("      Waiting 15 seconds to simulate test execution...")
        time.sleep(15)
        
        print("\n[3/3] Test complete. Removing chaos...")
    
    print("\n✅ Cleanup complete! Network should be back to normal.")
    print("\nVerify cleanup with: kubectl get networkchaos -A")


if __name__ == "__main__":
    main()
