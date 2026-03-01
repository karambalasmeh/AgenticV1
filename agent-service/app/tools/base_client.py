import asyncio
import logging
import time
from typing import Any, Optional

import httpx
from pydantic import BaseModel

from app.core.errors import AppError
from app.core.tracing import get_request_id

logger = logging.getLogger(__name__)


class BaseClient:
    # English comments only
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[BaseModel] = None,
        params: Optional[dict[str, Any]] = None,
        max_retries: int = 3,
        base_delay: float = 0.5,
    ) -> dict[str, Any]:
        # English comments only
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": get_request_id(),
        }
        
        json_data = payload.model_dump() if payload else None

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        json=json_data,
                        params=params,
                        headers=headers,
                    )
                    
                    if response.is_success:
                        return response.json()
                    
                    # Handle specific error status codes
                    try:
                        error_data = response.json()
                        details = error_data.get("details") or error_data
                    except Exception:
                        details = response.text

                    raise AppError(
                        error_code=f"DOWNSTREAM_ERROR_{response.status_code}",
                        message=f"Service at {url} returned {response.status_code}",
                        status_code=response.status_code,
                        details=details,
                    )

            except (httpx.RequestError, httpx.TimeoutException) as e:
                if attempt == max_retries:
                    logger.error(f"Final attempt failed for {url}: {str(e)}")
                    raise AppError(
                        error_code="SERVICE_UNAVAILABLE",
                        message=f"Failed to connect to {url} after {max_retries} retries",
                        status_code=503,
                        details={"error": str(e)},
                    )
                
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {url}, retrying in {delay}s: {str(e)}")
                await asyncio.sleep(delay)
            
            except AppError as ae:
                # Don't retry on recognized application errors (like 400, 403, 404)
                # Unless they are 5xx or transient
                if 500 <= ae.status_code <= 599 and attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed with {ae.status_code}, retrying in {delay}s")
                    await asyncio.sleep(delay)
                    continue
                raise ae

        raise AppError(
            error_code="MAX_RETRIES_EXCEEDED",
            message=f"Max retries reached for {url}",
            status_code=500,
        )
