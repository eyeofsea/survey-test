"""MCP 도구 정의 — Claude 가 호출할 5개 도구.

비용 안전장치:
- create_external_study 는 DRAFT 만 생성 → 과금 없음
- publish_study(confirm=False) 는 거부 → 실수로 과금되는 사고 방지
- 시간당 보상이 Prolific 권장 최저선(£6/h) 미만이면 사전 거부
"""

from __future__ import annotations

from .client import ProlificAPIError, ProlificClient
from .models import CreateStudyInput

MIN_HOURLY_REWARD_PENCE = 600  # £6.00/hour - Prolific 권장 최저선


def _format_currency(pence: int) -> str:
    return f"£{pence / 100:.2f}"


def register_tools(mcp, client: ProlificClient) -> None:
    @mcp.tool()
    def list_studies() -> list[dict]:
        """현재 프로젝트(.env 의 PROLIFIC_PROJECT_ID) 의 스터디 목록을 조회한다."""
        studies = client.list_studies()
        return [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "status": s.get("status"),
                "total_available_places": s.get("total_available_places"),
                "reward": s.get("reward"),
                "estimated_completion_time": s.get("estimated_completion_time"),
            }
            for s in studies
        ]

    @mcp.tool()
    def get_study(study_id: str) -> dict:
        """단일 스터디 상세 조회. /launch-study 전 드래프트 검증에 사용."""
        return client.get_study(study_id)

    @mcp.tool()
    def create_external_study(spec: CreateStudyInput) -> dict:
        """외부 URL 기반 Prolific 스터디를 DRAFT 상태로 생성한다.

        이 호출은 과금되지 않는다 (DRAFT). 실제 청구는 publish_study 시점.
        시간당 보상이 £6/h 미만이면 거부한다 (Prolific 권장 최저선).
        """
        hourly_pence = spec.reward * 60 / spec.estimated_completion_time
        if hourly_pence < MIN_HOURLY_REWARD_PENCE:
            raise ValueError(
                f"시간당 보상이 {_format_currency(int(hourly_pence))}/h 로 "
                f"Prolific 권장 최저선 {_format_currency(MIN_HOURLY_REWARD_PENCE)}/h "
                f"미만입니다. reward 또는 estimated_completion_time 을 조정하세요."
            )

        payload = {
            "name": spec.name,
            "internal_name": spec.name,
            "description": spec.description,
            "external_study_url": spec.external_study_url,
            "prolific_id_option": "url_parameters",
            "completion_codes": [
                {
                    "code": spec.completion_code,
                    "code_type": "COMPLETED",
                    "actions": [{"action": "AUTOMATICALLY_APPROVE"}],
                }
            ],
            "total_available_places": spec.total_available_places,
            "estimated_completion_time": spec.estimated_completion_time,
            "reward": spec.reward,
            "device_compatibility": spec.device_compatibility,
            "peripheral_requirements": [],
        }
        result = client.create_external_study(payload)
        return {
            "id": result.get("id"),
            "status": result.get("status", "UNPUBLISHED"),
            "name": result.get("name"),
            "external_study_url": result.get("external_study_url"),
            "total_cost_pence": spec.reward * spec.total_available_places,
            "total_cost_display": _format_currency(
                spec.reward * spec.total_available_places
            ),
            "_note": "이 스터디는 DRAFT 입니다. publish_study(confirm=True) 호출 전까지 과금되지 않습니다.",
        }

    @mcp.tool()
    def publish_study(study_id: str, confirm: bool = False) -> dict:
        """스터디를 PUBLISHED 상태로 전환한다. **이 시점에 실제 과금**.

        반드시 confirm=True 를 명시해야 한다. 슬래시 커맨드 /launch-study 가
        학생에게 한국어로 비용을 보여주고 동의를 받은 뒤에만 호출하도록 설계됨.
        """
        if not confirm:
            raise ValueError(
                "publish_study 는 confirm=True 를 요구합니다. "
                "/launch-study 슬래시 커맨드를 사용하거나, 비용을 확인했음을 "
                "명시적으로 전달하세요."
            )
        try:
            return client.publish_study(study_id)
        except ProlificAPIError as e:
            raise RuntimeError(f"퍼블리시 실패: {e.message}") from e

    @mcp.tool()
    def list_submissions(study_id: str) -> list[dict]:
        """스터디의 참여자 제출 목록과 상태를 반환한다."""
        subs = client.list_submissions(study_id)
        return [
            {
                "id": s.get("id"),
                "participant_id": s.get("participant_id"),
                "status": s.get("status"),
                "started_at": s.get("started_at"),
                "completed_at": s.get("completed_at"),
                "study_code": s.get("study_code"),
            }
            for s in subs
        ]
