"""Rate limiting middleware for API protection."""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimiter(BaseHTTPMiddleware):
    """Simple in-memory rate limiter."""

    def __init__(self, app, requests_per_minute: int = 60, burst: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.requests: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, time.time()))

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        path = request.url.path
        if path in ["/api/v1/health", "/api/info"] or path.startswith("/ws/"):
            return await call_next(request)

        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"

        current_time = time.time()
        count, window_start = self.requests[client_id]

        # Reset window if expired
        if current_time - window_start > 60:
            count = 0
            window_start = current_time

        # Check rate limit
        if count >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_id}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )

        # Increment counter
        self.requests[client_id] = (count + 1, window_start)

        response = await call_next(request)
        return response


class InputValidator:
    """Input validation utilities."""

    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """Validate and sanitize stock symbol."""
        if not symbol:
            raise ValueError("Symbol is required")

        symbol = symbol.strip().upper()

        if len(symbol) > 5:
            raise ValueError("Symbol must be 1-5 characters")

        if not symbol.isalpha():
            raise ValueError("Symbol must contain only letters")

        return symbol

    @staticmethod
    def validate_period(period: str) -> str:
        """Validate time period parameter."""
        valid_periods = ["3mo", "6mo", "1y", "2y", "5y"]
        if period not in valid_periods:
            raise ValueError(f"Invalid period. Must be one of: {', '.join(valid_periods)}")
        return period

    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """Sanitize text input."""
        if not text:
            return ""
        text = text.strip()
        if len(text) > max_length:
            text = text[:max_length]
        # Remove potential script tags
        text = text.replace("<script", "").replace("</script>", "")
        text = text.replace("javascript:", "")
        return text
