"""
Example: PodChaos - Pod Kill Experiment

This script demonstrates how to use the Chaos Mesh SDK to create
a pod-kill chaos experiment with automatic cleanup.
"""

import logging
import time

from chaos_sdk import (
    ChaosController,
    ChaosManager,
    PodChaos,
    PodChaosAction,
    ChaosSelector,
    ChaosMode,
)


# Configure logging to see SDK activity
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """
    Run a pod-kill chaos experiment.
    
    This example:
    1. Creates a pod-kill chaos targeting pods with app=web label
    2. Injects the chaos and waits for it to take effect
    3. Simulates test execution
    4. Automatically cleans up the chaos experiment
    """
    
    print("=" * 60)
    print("Pod Kill Chaos Experiment Example")
    print("=" * 60)
    
    # Define target selector - using labels
    selector = ChaosSelector.from_labels(
        labels={"app": "web-server"},
        namespaces=["default"]
    )
    
    # Create chaos experiment using convenience constructor
    chaos = PodChaos.pod_kill(
        selector=selector,
        mode=ChaosMode.ONE,  # Kill one random pod
        name="example-pod-kill"
    )
    
    print(f"\nCreated chaos experiment: {chaos}")
    print(f"Target selector: {selector}")
    
    # Use context manager for automatic cleanup (Recommended for Tests)
    print("\n--- Method 1: Automatic Cleanup (ChaosController) ---")
    with ChaosController() as controller:
        print("\n[1/3] Injecting chaos and waiting for injection...")
        controller.inject(chaos, wait=True, timeout=60)
        
        print("\n[2/3] Chaos injected! Pod should be killed now.")
        print("      In a real test, you would verify service resilience here.")
        print("      Waiting 5 seconds to simulate test execution...")
        time.sleep(5)
        
        print("\n[3/3] Test complete. Context manager will cleanup automatically.")
    
    print("\n Cleanup complete! No orphaned experiments left.")
    
    # Demonstration of Manual Control (ChaosManager)
    print("\n--- Method 2: Manual Control (ChaosManager) ---")
    manager = ChaosManager()
    
    print("Applying chaos manually...")
    try:
        manager.apply(chaos)
        manager.wait_for_injection(chaos)
        print("Chaos applied manually.")
        
        print("Deleting chaos manually...")
        manager.delete(chaos)
        manager.wait_for_deletion(chaos)
        print("Chaos deleted manually.")
        
    except Exception as e:
        print(f"Manual operation failed: {e}")
        # Ensure cleanup
        try:
            manager.delete(chaos)
        except:
            pass

    print("\nVerify cleanup with: kubectl get podchaos -A")


if __name__ == "__main__":
    main()
