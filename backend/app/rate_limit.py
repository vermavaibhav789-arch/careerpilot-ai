"""
A minimal in-memory rate limiter, applied to auth endpoints where brute
force / spam matters most (login, register, forgot-password).

This is single-process only - fine for one `uvicorn` process (the setup
this project ships with), but it won't coordinate across multiple worker
processes or multiple machines. If you deploy with more than one worker,
swap this for Redis-backed rate limiting (e.g. via `slowapi` with a Redis
backend) - the call sites below wouldn't need to change, just this module.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request

_buckets: dict[str, list[float]] = defaultdict(list)


def rate_limit(max_requests: int, window_seconds: int):
    """FastAPI dependency factory: Depends(rate_limit(5, 60)) allows 5 requests per 60s per IP+route."""

    def dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        key = f"{request.url.path}:{client_host}"
        now = time.time()

        bucket = _buckets[key]
        while bucket and bucket[0] < now - window_seconds:
            bucket.pop(0)

        if len(bucket) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests - please wait a moment and try again.",
            )

        bucket.append(now)

    return dependency
