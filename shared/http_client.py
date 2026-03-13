"""Base HTTP client with retry logic."""

import httpx
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class ServiceClient:
    """HTTP client for inter-service communication."""
    
    def __init__(self, base_url: str, timeout: float = 30.0, max_retries: int = 3):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def _request(
        self,
        method: str,
        path: str,
        headers: Optional[dict] = None,
        json_data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """Make an HTTP request with retry logic."""
        url = f"{self.base_url}{path}"
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=json_data,
                        params=params,
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
                raise
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Request to {url} failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
        
        if last_exception:
            raise last_exception
        raise RuntimeError(f"Request to {url} failed after {self.max_retries} retries with no captured exception")
    
    async def get(self, path: str, **kwargs) -> dict:
        return await self._request("GET", path, **kwargs)
    
    async def post(self, path: str, **kwargs) -> dict:
        return await self._request("POST", path, **kwargs)
    
    async def put(self, path: str, **kwargs) -> dict:
        return await self._request("PUT", path, **kwargs)
    
    async def delete(self, path: str, **kwargs) -> dict:
        return await self._request("DELETE", path, **kwargs)
