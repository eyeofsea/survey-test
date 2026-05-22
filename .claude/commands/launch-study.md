---
description: Prolific DRAFT 스터디를 검토 후 학생 명시 확인을 받아 퍼블리시
---

**경고: 이 명령은 실제 과금을 발생시킵니다.** 안전장치를 절대 우회하지 마세요.

## 절차

1. AskUserQuestion 으로 퍼블리시할 `study_id` 를 물어보세요. 모르면 Prolific MCP 의 `list_studies` 로 후보를 보여주고 선택받으세요.

2. `get_study(study_id)` 로 상세 조회 후 다음을 한국어 표로 정리해서 출력:
   - 제목
   - 설명 첫 줄
   - 모집 인원
   - 보상 (penny + £ 표시)
   - 예상 소요 시간 (분)
   - 시간당 환산 보상
   - **총 예상 비용 = reward × 인원 + Prolific 수수료 (대략 +33%)**
   - 외부 URL 이 `{{%PROLIFIC_PID%}}` 등 placeholder 를 포함하는지 검증

3. AskUserQuestion 으로 명시 확인을 받으세요. 질문 예시:

> 위 내용으로 Prolific 스터디를 퍼블리시하면 표시된 비용이 청구됩니다. 진행하시겠습니까?
> - 퍼블리시
> - 취소

4. **"퍼블리시" 선택 시에만** `publish_study(study_id=<id>, confirm=true)` 호출.
   "취소" 또는 그 외 답변이면 호출하지 마세요. 학생에게 "취소되었습니다. 스터디는 그대로 DRAFT 입니다." 라고만 알려주세요.

5. 퍼블리시 성공 후 학생에게:
   - Prolific 대시보드 URL (`https://app.prolific.com/researcher/workspaces/<workspace>/projects/<project>/studies/<study>`) 안내
   - "참여자가 모이는 동안 `/collect-results` 로 진행 상황을 확인하세요"

## 절대 하지 말 것

- 학생 동의 없이 `publish_study` 호출
- `confirm=false` 또는 confirm 인자 누락으로 호출
- 비용을 축소하거나 생략하여 표시
