"""Captcha solver client — pluggable Turnstile/reCAPTCHA solving via third-party APIs.

Supports 2Captcha (default), CapSolver, and CapMonster via a unified interface.
All three providers use the same createTask / getTaskResult API shape.
"""

import asyncio
import dataclasses
import time

import httpx

from src.logger import Logger

logger = Logger(__name__)


PROVIDER_URLS = {
    "2captcha": "https://api.2captcha.com",
    "capsolver": "https://api.capsolver.com",
    "capmonster": "https://api.capmonster.cloud",
}

_ERROR_ID_SUCCESS = 0
_ERROR_ID_FAIL_CLOSED = 1
_STATUS_READY = "ready"


class CaptchaSolveError(Exception):
    """Raised when the captcha solver API fails or returns no token."""


@dataclasses.dataclass
class CaptchaSolver:
    provider: str
    api_key: str
    base_url: str
    timeout_s: int = 120

    async def solve_turnstile(
        self,
        *,
        site_key: str,
        page_url: str,
        action: str | None = None,
        cdata: str | None = None,
        pagedata: str | None = None,
    ) -> str:
        """Solve a Cloudflare Turnstile challenge and return the token.

        Raises CaptchaSolveError on timeout, bad API key, or any failure.
        """
        task: dict = {
            "type": "TurnstileTaskProxyless",
            "websiteURL": page_url,
            "websiteKey": site_key,
        }
        if action:
            task["action"] = action
        if cdata:
            task["data"] = cdata
        if pagedata:
            task["pagedata"] = pagedata

        t0 = time.monotonic()
        task_id = "unknown"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                create_resp = await client.post(
                    f"{self.base_url}/createTask",
                    json={"clientKey": self.api_key, "task": task},
                )
                create_data = create_resp.json()
                if create_data.get("errorId", _ERROR_ID_FAIL_CLOSED) != _ERROR_ID_SUCCESS:
                    raise CaptchaSolveError(
                        f"createTask failed ({self.provider}): "
                        f"{create_data.get('errorDescription', 'unknown error')}"
                    )
                task_id = create_data["taskId"]
                logger.info(f"Turnstile task created (provider={self.provider}, task_id={task_id})")

                deadline = time.monotonic() + self.timeout_s
                while time.monotonic() < deadline:
                    await asyncio.sleep(3)
                    result_resp = await client.post(
                        f"{self.base_url}/getTaskResult",
                        json={"clientKey": self.api_key, "taskId": task_id},
                    )
                    result_data = result_resp.json()
                    if result_data.get("errorId", _ERROR_ID_FAIL_CLOSED) != _ERROR_ID_SUCCESS:
                        raise CaptchaSolveError(
                            f"getTaskResult error ({self.provider}): "
                            f"{result_data.get('errorDescription', 'unknown')}"
                        )
                    if result_data.get("status") == _STATUS_READY:
                        token = (
                            result_data.get("solution", {}).get("token", "")
                            or result_data.get("solution", {}).get("gRecaptchaResponse", "")
                        )
                        if not token:
                            raise CaptchaSolveError("solver returned ready but no token")
                        duration = time.monotonic() - t0
                        logger.info(
                            f"Turnstile solved in {duration:.1f}s "
                            f"(provider={self.provider}, task_id={task_id})"
                        )
                        return token

                raise CaptchaSolveError(
                    f"Turnstile solve timed out after {self.timeout_s}s ({self.provider})"
                )

            except CaptchaSolveError:
                raise
            except Exception as exc:
                raise CaptchaSolveError(
                    f"Solver network error ({self.provider}): {exc}"
                ) from exc
