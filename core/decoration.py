# core/decoration.py
import functools
import logging
from typing import Any, Callable
import httpx

logger = logging.getLogger("api_integration")

def handle_api_errors(service_name: str):
    """
    Decorator: Captures third-party API request exceptions, logs detailed 
    information, and raises sanitized error messages.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                # Log detailed response body to internal logs, including e.response.text
                logger.error(
                    f"[{service_name}] HTTP Error: {e.response.status_code} "
                    f"| Body: {e.response.text} | URL: {e.request.url}"
                )
                raise Exception(f"External service '{service_name}' returned an error. Please try again later.")
            
            except httpx.RequestError as e:
                # Log network-layer errors (e.g., timeouts, DNS failures)
                logger.error(f"[{service_name}] Network Error: {str(e)}")
                raise Exception(f"Unable to connect to the '{service_name}' interface.")
            
            except Exception as e:
                # Log other unexpected errors
                logger.exception(f"[{service_name}] Unexpected Error: {str(e)}")
                raise Exception("An internal system error occurred. Our team has been notified.")
        
        return wrapper
    return decorator