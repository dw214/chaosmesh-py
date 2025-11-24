"""
Chaos experiment lifecycle controller.

This module provides the ChaosController context manager for automatic
experiment cleanup and lifecycle management.
"""

import logging
from typing import List, Optional

from chaos_sdk.client import ChaosClient
from chaos_sdk.models.base import BaseChaos


logger = logging.getLogger(__name__)


class ChaosController:
    """
    Context manager for chaos experiment lifecycle management.
    
    Provides automatic cleanup of experiments, even if tests fail or crash.
    This ensures no orphaned chaos resources remain after test execution.
    
    Example:
        >>> from chaos_sdk import ChaosController, PodChaos, PodChaosAction
        >>> from chaos_sdk import ChaosSelector
        
        >>> with ChaosController() as controller:
        ...     # Create chaos
        ...     chaos = PodChaos.pod_kill(
        ...         selector=ChaosSelector.from_labels({"app": "web"})
        ...     )
        ...     
        ...     # Inject and wait for chaos
        ...     controller.inject(chaos, wait=True)
        ...     
        ...     # Run test assertions
        ...     assert check_service_recovery()
        ...     
        ...     # Automatic cleanup happens here on exit
        
        >>> # Cleanup happens even if test raises an exception
        >>> with ChaosController() as controller:
        ...     controller.inject(chaos)
        ...     raise Exception("Test failed!")
        ...     # Cleanup still executes
    """
    
    def __init__(self, client: Optional[ChaosClient] = None):
        """
        Initialize chaos controller.
        
        Args:
            client: Optional ChaosClient instance (creates new if not provided)
        """
        self.client = client or ChaosClient()
        self.active_experiments: List[BaseChaos] = []
        
        logger.debug("ChaosController initialized")
    
    def __enter__(self) -> "ChaosController":
        """
        Enter context manager.
        
        Returns:
            Self for use in with statement
        """
        logger.debug("Entering ChaosController context")
        return self
    
    def inject(
        self,
        chaos: BaseChaos,
        wait: bool = True,
        timeout: Optional[int] = None
    ) -> BaseChaos:
        """
        Inject chaos experiment and track it for cleanup.
        
        Args:
            chaos: Chaos experiment to inject
            wait: Whether to wait for injection to complete (default: True)
            timeout: Optional timeout for wait operation
            
        Returns:
            The chaos experiment instance (for method chaining)
            
        Raises:
            ExperimentAlreadyExistsError: If experiment name already exists
            ExperimentTimeoutError: If wait=True and injection times out
        
        Example:
            >>> controller.inject(chaos, wait=True, timeout=60)
        """
        # Apply the chaos
        chaos.apply(self.client)
        
        # Track for cleanup
        self.active_experiments.append(chaos)
        
        logger.info(f"Injected chaos: {chaos}")
        
        # Wait for injection if requested
        if wait:
            chaos.wait_for_injection(self.client, timeout=timeout)
        
        return chaos
    
    def remove(
        self,
        chaos: BaseChaos,
        wait_for_deletion: bool = True
    ) -> None:
        """
        Manually remove a chaos experiment before context exit.
        
        Args:
            chaos: Chaos experiment to remove
            wait_for_deletion: Whether to wait for deletion confirmation
        
        Example:
            >>> # Inject multiple chaos experiments
            >>> chaos1 = controller.inject(pod_chaos)
            >>> chaos2 = controller.inject(network_chaos)
            >>> 
            >>> # Remove one early
            >>> controller.remove(chaos1)
            >>> 
            >>> # chaos2 still cleaned up on exit
        """
        try:
            chaos.delete(self.client)
            
            if wait_for_deletion:
                chaos.wait_for_deletion(self.client)
            
            # Remove from tracking list
            if chaos in self.active_experiments:
                self.active_experiments.remove(chaos)
            
            logger.info(f"Removed chaos: {chaos.name}")
            
        except Exception as e:
            logger.error(f"Failed to remove chaos {chaos.name}: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager and cleanup all active experiments.
        
        Cleanup happens regardless of whether an exception occurred.
        Each cleanup failure is logged but doesn't prevent cleanup of other experiments.
        
        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        if exc_type:
            logger.warning(
                f"Exiting ChaosController with exception: {exc_type.__name__}"
            )
        else:
            logger.debug("Exiting ChaosController normally")
        
        logger.info(
            f"Cleaning up {len(self.active_experiments)} active experiments"
        )
        
        # Cleanup all experiments
        cleanup_errors = []
        
        for chaos in self.active_experiments:
            try:
                logger.info(f"Deleting {chaos.name}...")
                chaos.delete(self.client)
                
                # Wait for deletion to complete
                try:
                    chaos.wait_for_deletion(self.client, timeout=30)
                except Exception as wait_error:
                    logger.warning(
                        f"Deletion verification failed for {chaos.name}: {wait_error}"
                    )
                
            except Exception as e:
                error_msg = f"Failed to delete {chaos.name}: {e}"
                logger.error(error_msg)
                cleanup_errors.append(error_msg)
                # Continue with other experiments
        
        # Clear the list
        self.active_experiments.clear()
        
        if cleanup_errors:
            logger.warning(
                f"Cleanup completed with {len(cleanup_errors)} errors:\n" +
                "\n".join(f"  - {err}" for err in cleanup_errors)
            )
        else:
            logger.info("Cleanup completed successfully")
        
        # Don't suppress exceptions from the with block
        return False
    
    def cleanup_all(self) -> None:
        """
        Manually trigger cleanup of all active experiments.
        
        Useful for explicit cleanup without exiting the context.
        
        Example:
            >>> with ChaosController() as controller:
            ...     # Phase 1 chaos
            ...     controller.inject(chaos1)
            ...     run_phase1_tests()
            ...     controller.cleanup_all()
            ...     
            ...     # Phase 2 chaos
            ...     controller.inject(chaos2)
            ...     run_phase2_tests()
            ...     # Automatic cleanup on exit
        """
        logger.info("Manual cleanup triggered")
        
        # Trigger cleanup by calling __exit__ without exception
        self.__exit__(None, None, None)
