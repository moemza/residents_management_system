"""Small in-process sliding-window rate limiter.

This is a defence-in-depth control for a single application process. It is not
distributed and does not replace a reverse-proxy or platform rate limit. State
is intentionally in memory so the application has no extra infrastructure
dependency.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Track request timestamps per key over a rolling window."""

    def __init__(self, max_keys: int = 10_000) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._max_keys = max_keys

    def check(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        """Record a request and return ``(allowed, retry_after_seconds)``."""
        if limit <= 0:
            return True, 0

        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()

            if len(events) >= limit:
                retry_after = max(1, int(window_seconds - (now - events[0])) + 1)
                return False, retry_after

            events.append(now)
            self._prune_if_needed()
            return True, 0

    def _prune_if_needed(self) -> None:
        """Bound tracked keys so a long-running process cannot grow forever."""
        if len(self._events) <= self._max_keys:
            return

        for key in [key for key, events in self._events.items() if not events]:
            del self._events[key]

        overflow = len(self._events) - self._max_keys
        if overflow > 0:
            oldest = sorted(
                self._events.items(),
                key=lambda item: item[1][-1] if item[1] else float("-inf"),
            )
            for key, _events in oldest[:overflow]:
                del self._events[key]

    @property
    def tracked_keys(self) -> int:
        """Return the number of keys currently held in memory."""
        with self._lock:
            return len(self._events)

    def reset(self) -> None:
        """Clear all state. Used by tests and on explicit administrative reset."""
        with self._lock:
            self._events.clear()


limiter = RateLimiter()
