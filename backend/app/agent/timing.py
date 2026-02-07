"""
Timing utility for agent workflow profiling.
Wraps node functions to log execution time.
"""
import time
from functools import wraps
from typing import Callable, Any


def timed_node(node_name: str):
    """Decorator to time and log node execution."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            print(f"\n⏱️  [{node_name}] Starting...")
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                print(f"✅ [{node_name}] Completed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start
                print(f"❌ [{node_name}] Failed after {elapsed:.2f}s: {str(e)[:100]}")
                raise
        return wrapper
    return decorator


def log_step(step_name: str):
    """Context manager for timing sub-steps within a node."""
    class StepTimer:
        def __init__(self):
            self.start = None
            
        def __enter__(self):
            self.start = time.time()
            print(f"   → {step_name}...")
            return self
            
        def __exit__(self, *args):
            elapsed = time.time() - self.start
            print(f"   ← {step_name}: {elapsed:.2f}s")
    
    return StepTimer()
