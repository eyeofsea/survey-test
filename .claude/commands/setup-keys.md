---
description: .env 파일에 Qualtrics/Prolific API 토큰을 대화형으로 입력
---

학생이 5개의 환경변수를 `.env` 파일에 안전하게 채우도록 도와줍니다.

## 절차

1. 우선 `.env` 가 있는지 `ls .env` 로 확인하세요. 없으면 `cp .env.example .env` 로 복사하세요.

2. AskUserQuestion 으로 어떤 항목을 입력할지 물어보세요. 옵션:
   - 모든 토큰을 처음부터 입력
   - Qualtrics 만 입력
   - Prolific 만 입력

3. 선택한 그룹에 대해 **한 항목씩** `AskUserQuestion` 으로 값을 물어보세요. 각 질문에는 발급 위치를 한국어로 명확히 안내하세요:
   - `QUALTRICS_API_TOKEN`: "Qualtrics → 우상단 계정 아이콘 → Account Settings → Qualtrics IDs → API 박스의 Token"
   - `QUALTRICS_DATA_CENTER`: "같은 페이지의 User 박스 → Datacenter ID (예: yul1, fra1, sjc1, iad1)"
   - `PROLIFIC_API_TOKEN`: "app.prolific.com → Settings → Go to API tokens → Create token"
   - `PROLIFIC_WORKSPACE_ID`: "Prolific 대시보드 URL /workspaces/<여기> 부분"
   - `PROLIFIC_PROJECT_ID`: "워크스페이스에서 프로젝트 진입 시 URL /projects/<여기> 부분"

4. 각 답변을 받으면 `.env` 파일에서 해당 줄의 `KEY=` 우측 값만 Edit 도구로 갱신하세요. **답변 받은 토큰 값을 채팅에 다시 출력하지 마세요** — 유출 위험. 갱신 후에는 "✓ <KEY> 저장됨" 같이 키 이름만 표시.

5. 모든 입력이 끝나면 `uv run python scripts/doctor.py` 를 실행하고 결과를 그대로 보여주세요.

6. 진단이 통과하면 "이제 `/new-survey` 로 설문을 만들 수 있습니다." 라고 안내하세요.

## 주의

- 학생이 "건너뛰기" 같은 답변을 하면 그 줄은 그대로 둡니다.
- 절대 토큰 값을 다시 echo, 요약, 캡션에 포함하지 마세요.
- Edit 도구로 값을 바꿀 때 `KEY=` 라인이 비어있다면 `old_string=KEY=`, `new_string=KEY=<새값>` 으로 정확히 한 줄만 교체.
