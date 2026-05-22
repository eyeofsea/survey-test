from typing import Literal

from pydantic import BaseModel, Field


class StudySummary(BaseModel):
    id: str
    name: str
    status: str
    total_available_places: int | None = None
    reward: int | None = None
    estimated_completion_time: int | None = None


class CreateStudyInput(BaseModel):
    name: str = Field(description="스터디 제목 (학생/Prolific 대시보드 표시용)")
    description: str = Field(description="참여자에게 보이는 설명")
    external_study_url: str = Field(
        description=(
            "Prolific 이 참여자를 보낼 외부 URL. Qualtrics 익명 링크에 "
            "?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}} "
            "쿼리를 붙인 형태."
        )
    )
    completion_code: str = Field(
        min_length=4,
        max_length=20,
        description="참여자가 Qualtrics 종료 후 Prolific 으로 돌아올 때 사용할 완료 코드",
    )
    reward: int = Field(
        gt=0,
        description="보상 금액 (penny 단위, £1.00 = 100). 예: 100 = £1.00",
    )
    total_available_places: int = Field(
        gt=0,
        description="모집 인원 수",
    )
    estimated_completion_time: int = Field(
        gt=0,
        description="예상 소요 시간 (분)",
    )
    device_compatibility: list[Literal["desktop", "tablet", "mobile"]] = Field(
        default_factory=lambda: ["desktop", "tablet", "mobile"]
    )


class StudyDetail(StudySummary):
    description: str | None = None
    external_study_url: str | None = None
    completion_codes: list[dict] | None = None
    internal_name: str | None = None
    project: str | None = None


class Submission(BaseModel):
    id: str
    participant_id: str | None = None
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    study_code: str | None = None
