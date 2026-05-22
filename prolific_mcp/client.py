"""Prolific REST API 의 얇은 httpx 래퍼.

- Bearer 가 아닌 'Token <키>' 헤더 사용 (Prolific 의 표준 인증)
- 429 응답 시 지수 백오프 (2s → 4s → 8s, 최대 3회 재시도)
- 4xx 본문을 그대로 ProlificAPIError 메시지로 전달 → MCP 도구 에러로 노출
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

BASE_URL = "https://api.prolific.com/api/v1"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3


class ProlificAPIError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"Prolific API {status}: {message}")
        self.status = status
        self.message = message


class ProlificClient:
    def __init__(
        self,
        token: str | None = None,
        workspace_id: str | None = None,
        project_id: str | None = None,
    ) -> None:
        self.token = token or os.environ.get("PROLIFIC_API_TOKEN", "")
        self.workspace_id = workspace_id or os.environ.get("PROLIFIC_WORKSPACE_ID", "")
        self.project_id = project_id or os.environ.get("PROLIFIC_PROJECT_ID", "")

        if not self.token:
            raise RuntimeError(
                "PROLIFIC_API_TOKEN 환경변수가 비어 있습니다. .env 파일을 확인하세요."
            )

        self._client = httpx.Client(
            base_url=BASE_URL,
            timeout=DEFAULT_TIMEOUT,
            headers={
                "Authorization": f"Token {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> Any:
        backoff = 2.0
        for attempt in range(MAX_RETRIES + 1):
            resp = self._client.request(method, path, json=json, params=params)
            if resp.status_code == 429 and attempt < MAX_RETRIES:
                time.sleep(backoff)
                backoff *= 2
                continue
            if resp.status_code >= 400:
                try:
                    body = resp.json()
                except Exception:
                    body = resp.text
                raise ProlificAPIError(resp.status_code, str(body))
            if resp.status_code == 204 or not resp.content:
                return None
            return resp.json()
        raise ProlificAPIError(429, "재시도 후에도 rate limit 가 풀리지 않았습니다.")

    # -- 엔드포인트 --

    def me(self) -> dict:
        return self._request("GET", "/users/me")

    def list_studies(self) -> list[dict]:
        params = {"project": self.project_id} if self.project_id else None
        data = self._request("GET", "/studies/", params=params)
        return data.get("results", []) if isinstance(data, dict) else data

    def get_study(self, study_id: str) -> dict:
        return self._request("GET", f"/studies/{study_id}/")

    def create_external_study(self, payload: dict) -> dict:
        if self.project_id and "project" not in payload:
            payload = {**payload, "project": self.project_id}
        return self._request("POST", "/studies/", json=payload)

    def publish_study(self, study_id: str) -> dict:
        return self._request(
            "POST",
            f"/studies/{study_id}/transition/",
            json={"action": "PUBLISH"},
        )

    def list_submissions(self, study_id: str) -> list[dict]:
        data = self._request("GET", "/submissions/", params={"study": study_id})
        return data.get("results", []) if isinstance(data, dict) else data
