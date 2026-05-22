"""API 토큰 진단 — Qualtrics, Prolific 모두 살아있는지 확인.

세션 시작 시 .claude/settings.json 의 SessionStart hook 으로 자동 실행되며,
setup.sh 의 마지막 단계에서도 호출된다.

성공 → exit 0. 한쪽이라도 실패 → exit 1 (학생에게 무엇이 잘못됐는지 한국어 안내).
"""

from __future__ import annotations

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()


def check_qualtrics() -> tuple[bool, str]:
    token = os.environ.get("QUALTRICS_API_TOKEN", "").strip()
    dc = os.environ.get("QUALTRICS_DATA_CENTER", "").strip()
    if not token:
        return False, "QUALTRICS_API_TOKEN 이 비어 있습니다 (.env 확인)"
    if not dc:
        return False, "QUALTRICS_DATA_CENTER 가 비어 있습니다 (.env 확인)"

    url = f"https://{dc}.qualtrics.com/API/v3/surveys"
    try:
        r = httpx.get(
            url,
            headers={"X-API-TOKEN": token},
            params={"limit": 1},
            timeout=10.0,
        )
    except httpx.HTTPError as e:
        return False, f"네트워크 오류: {e}"

    if r.status_code == 401:
        return False, "토큰이 유효하지 않습니다 (401). Qualtrics 계정 설정에서 재발급하세요."
    if r.status_code == 404 or r.status_code == 403:
        return (
            False,
            f"데이터 센터 '{dc}' 와 토큰이 일치하지 않을 수 있습니다 (HTTP {r.status_code}). "
            "Account Settings → Qualtrics IDs 에서 Datacenter ID 를 다시 확인하세요.",
        )
    if r.status_code >= 400:
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    return True, f"Qualtrics OK (datacenter={dc})"


def check_prolific() -> tuple[bool, str]:
    token = os.environ.get("PROLIFIC_API_TOKEN", "").strip()
    workspace = os.environ.get("PROLIFIC_WORKSPACE_ID", "").strip()
    project = os.environ.get("PROLIFIC_PROJECT_ID", "").strip()
    if not token:
        return False, "PROLIFIC_API_TOKEN 이 비어 있습니다 (.env 확인)"

    try:
        r = httpx.get(
            "https://api.prolific.com/api/v1/users/me/",
            headers={"Authorization": f"Token {token}"},
            timeout=10.0,
        )
    except httpx.HTTPError as e:
        return False, f"네트워크 오류: {e}"

    if r.status_code == 401:
        return False, "Prolific 토큰이 유효하지 않습니다 (401). app.prolific.com Settings 에서 재발급."
    if r.status_code >= 400:
        return False, f"HTTP {r.status_code}: {r.text[:200]}"

    extras = []
    if not workspace:
        extras.append("PROLIFIC_WORKSPACE_ID 비어 있음")
    if not project:
        extras.append("PROLIFIC_PROJECT_ID 비어 있음")
    suffix = f" (경고: {', '.join(extras)})" if extras else ""
    return True, f"Prolific OK{suffix}"


def main() -> int:
    rows = [
        ("Qualtrics", *check_qualtrics()),
        ("Prolific", *check_prolific()),
    ]
    print()
    print("  진단 결과")
    print("  " + "─" * 60)
    all_ok = True
    for name, ok, msg in rows:
        mark = "✅" if ok else "❌"
        print(f"  {mark}  {name:10s}  {msg}")
        all_ok = all_ok and ok
    print()
    if not all_ok:
        print("  → Claude Code 에서 `/setup-keys` 를 실행해 토큰을 점검하세요.")
        print()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
