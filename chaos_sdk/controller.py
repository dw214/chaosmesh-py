"""
Chaos experiment lifecycle controller.

Provides the ChaosController context manager for automatic experiment cleanup.
"""

import logging
from typing import List, Optional

from chaos_sdk.client import ChaosClient
from chaos_sdk.manager import ChaosManager
from chaos_sdk.models.base import BaseChaos


logger = logging.getLogger(__name__)


class ChaosController:
    """
    Context manager for chaos experiment lifecycle management.
    
    Ensures automatic cleanup of experiments, even if tests fail or crash.
    Delegates actual operations to ChaosManager.
    """

    def __init__(self, client: Optional[ChaosClient] = None):
        """Initialize chaos controller with optional custom client."""
        self.manager = ChaosManager(client)
        self.active_experiments: List[BaseChaos] = []
        logger.debug("ChaosController initialized")

    def __enter__(self) -> "ChaosController":
        """Enter context manager."""
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
            wait: Whether to wait for injection to complete
            timeout: Optional timeout for wait operation
            
        Returns:
            The chaos experiment instance (for method chaining)
        """
        self.manager.apply(chaos)
        self.active_experiments.append(chaos)

        if wait:
            self.manager.wait_for_injection(chaos, timeout=timeout)

        return chaos

    def remove(
        self,
        chaos: BaseChaos,
        wait_for_deletion: bool = True
    ) -> None:
        """Manually remove a chaos experiment before context exit."""
        try:
            self.manager.delete(chaos)

            if wait_for_deletion:
                self.manager.wait_for_deletion(chaos)

            if chaos in self.active_experiments:
                self.active_experiments.remove(chaos)

        except Exception as e:
            logger.error("Failed to remove chaos %s: %s", chaos.name, e)
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager and cleanup all active experiments.
        
        Cleanup happens regardless of exceptions. Failures are logged but don't
        prevent cleanup of other experiments.
        """
        if exc_type:
            logger.warning("Exiting with exception: %s", exc_type.__name__)

        logger.info("Cleaning up %d experiments", len(self.active_experiments))

        cleanup_errors = []

        for chaos in self.active_experiments:
            try:
                self.manager.delete(chaos)

                try:
                    self.manager.wait_for_deletion(chaos, timeout=30)
                except Exception as wait_error:
                    logger.warning("Deletion verification failed for %s: %s",
                                   chaos.name, wait_error)

            except Exception as e:
                error_msg = f"Failed to delete {chaos.name}: {e}"
                logger.error(error_msg)
                cleanup_errors.append(error_msg)

        self.active_experiments.clear()

        if cleanup_errors:
            logger.warning(
                f"Cleanup completed with {len(cleanup_errors)} errors:\n"
                f"{'\n'.join(f'  - {err}' for err in cleanup_errors)}"
            )
        else:
            logger.info("Cleanup completed successfully")

        return False  # Don't suppress exceptions from the with block

    def cleanup_all(self) -> None:
        """Manually trigger cleanup of all active experiments."""
        logger.info("Manual cleanup triggered")
        self.__exit__(None, None, None)
