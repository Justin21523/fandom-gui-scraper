# utils/file_manager.py
"""
Thread management utilities for concurrent operations.
Provides thread pool management and async operations support.
"""

import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from queue import Queue
import time


class ThreadManager:
    """
    Advanced thread manager for concurrent operations.

    Features:
    - Thread pool management
    - Task queuing and execution
    - Progress tracking
    - Error handling and recovery
    - Resource management
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize thread manager.

        Args:
            config: Configuration dictionary with thread parameters
        """
        self.logger = logging.getLogger(__name__)

        # Default configuration
        self.config = {
            "max_workers": 4,
            "timeout": 300,  # 5 minutes default timeout
            "retry_attempts": 3,
            "retry_delay": 1.0,
            "progress_callback": None,
        }

        if config:
            self.config.update(config)

        self.executor = None
        self.active_futures = []
        self.results = []
        self.errors = []
        self._lock = threading.Lock()

    def execute_parallel(
        self, tasks: List[Dict[str, Any]], worker_function: Callable
    ) -> Dict[str, Any]:
        """
        Execute tasks in parallel using thread pool.

        Args:
            tasks: List of task dictionaries
            worker_function: Function to execute for each task

        Returns:
            Execution results with statistics
        """
        if not tasks:
            return {"success": True, "results": [], "errors": []}

        self.logger.info(f"Starting parallel execution of {len(tasks)} tasks")

        try:
            with ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
                self.executor = executor

                # Submit all tasks
                future_to_task = {}
                for i, task in enumerate(tasks):
                    future = executor.submit(
                        self._execute_with_retry, worker_function, task, i
                    )
                    future_to_task[future] = (i, task)
                    self.active_futures.append(future)

                # Collect results
                completed = 0
                for future in as_completed(
                    future_to_task, timeout=self.config["timeout"]
                ):
                    task_index, task = future_to_task[future]

                    try:
                        result = future.result()
                        with self._lock:
                            self.results.append(
                                {
                                    "task_index": task_index,
                                    "task": task,
                                    "result": result,
                                    "success": True,
                                }
                            )
                    except Exception as e:
                        with self._lock:
                            self.errors.append(
                                {
                                    "task_index": task_index,
                                    "task": task,
                                    "error": str(e),
                                    "success": False,
                                }
                            )
                        self.logger.error(f"Task {task_index} failed: {e}")

                    completed += 1

                    # Progress callback
                    if self.config["progress_callback"]:
                        progress = (completed / len(tasks)) * 100
                        self.config["progress_callback"](
                            progress, completed, len(tasks)
                        )

                success_count = len(self.results)
                error_count = len(self.errors)

                return {
                    "success": True,
                    "total_tasks": len(tasks),
                    "successful_tasks": success_count,
                    "failed_tasks": error_count,
                    "success_rate": (success_count / len(tasks)) * 100,
                    "results": self.results,
                    "errors": self.errors,
                }

        except Exception as e:
            self.logger.error(f"Parallel execution failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            self.cleanup()

    def _execute_with_retry(
        self, worker_function: Callable, task: Dict[str, Any], task_index: int
    ) -> Any:
        """Execute task with retry logic."""
        last_exception = None

        for attempt in range(self.config["retry_attempts"]):
            try:
                return worker_function(task)
            except Exception as e:
                last_exception = e
                if attempt < self.config["retry_attempts"] - 1:
                    self.logger.warning(
                        f"Task {task_index} attempt {attempt + 1} failed: {e}, retrying..."
                    )
                    time.sleep(self.config["retry_delay"] * (attempt + 1))
                else:
                    self.logger.error(
                        f"Task {task_index} failed after {self.config['retry_attempts']} attempts"
                    )

        raise last_exception

    def cleanup(self):
        """Clean up resources."""
        self.active_futures.clear()
        self.results.clear()
        self.errors.clear()
        self.executor = None


def create_thread_config() -> Dict[str, Any]:
    """Create default configuration for thread manager."""
    return {
        "max_workers": 4,
        "timeout": 300,
        "retry_attempts": 3,
        "retry_delay": 1.0,
        "progress_callback": None,
    }
