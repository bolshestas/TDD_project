"""
Simple in-memory rate limiting middleware.

This middleware restricts the number of requests a client can make
within a defined time window. The rate limit is applied only to
specific endpoints defined in RATE_LIMITED_PATHS.

Implementation notes:
- Uses an in-memory sliding window algorithm
- Tracks request timestamps per client IP
- Thread-safe via a lock

Limitations:
This implementation works for a single application instance.
In a distributed environment a shared store (e.g., Redis)
would be required to enforce rate limits across multiple nodes.
"""

import time
import logging
from collections import defaultdict
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

logger = logging.getLogger(__name__)

# Endpoints that should be protected by rate limiting
RATE_LIMITED_PATHS = {"/shorten"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware implementing simple IP-based rate limiting.

    Each client IP is allowed a limited number of requests
    within a configured time window.
    """

    def __init__(self, app):
        super().__init__(app)

        # Stores timestamps of requests per IP address
        self._requests: dict[str, list[float]] = defaultdict(list)

        # Lock ensures thread-safe access to request counters
        self._lock = Lock()

    def reset(self) -> None:
        """Reset all counters. Used in tests"""
        with self._lock:
            self._requests.clear()

    def _get_client_ip(self, request: Request) -> str:
        """
        Determine the client's IP address.

        If the application is running behind a reverse proxy,
        the X-Forwarded-For header is used. Otherwise, the
        direct client host is returned.

        Args:
            request: Incoming FastAPI request

        Returns:
            Client IP address as string
        """

        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For may contain multiple IPs: client, proxy1, proxy2...
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, ip: str) -> bool:
        """
        Check whether the client has exceeded the rate limit.

        Uses a sliding window approach:
        - Remove timestamps outside the time window
        - Count remaining requests
        - Reject if limit exceeded

        Args:
            ip: Client IP address

        Returns:
            True if rate limit exceeded, otherwise False
        """

        now = time.monotonic()
        window_start = now - RATE_LIMIT_WINDOW

        with self._lock:
            # Remove timestamps outside the current window
            self._requests[ip] = [
                ts for ts in self._requests[ip] if ts > window_start
            ]

            # Check if request limit has been reached
            if len(self._requests[ip]) >= RATE_LIMIT_REQUESTS:
                return True
            
            # Record the new request timestamp
            self._requests[ip].append(now)
            return False

    async def dispatch(self, request: Request, call_next):
        """
        Middleware entry point.

        If the request path is protected by rate limiting,
        check the client's request frequency before forwarding
        the request to the application.
        """
        
        if request.url.path in RATE_LIMITED_PATHS:
            ip = self._get_client_ip(request)
            if self._is_rate_limited(ip):
                logger.warning("Rate limit exceeded for IP: %s", ip)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Too many requests. Max {RATE_LIMIT_REQUESTS} per {RATE_LIMIT_WINDOW}s."
                    },
                )
        return await call_next(request)