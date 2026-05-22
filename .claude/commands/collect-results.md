---
description: Qualtrics 응답과 Prolific 제출 데이터를 함께 수집·요약
---

## 절차

1. AskUserQuestion 으로 `study_id` 와 `survey_id` 를 받으세요. (모르면 `list_studies` / `list_surveys` 호출)

2. 출력 포맷을 물어보세요: CSV 파일로 저장 / 화면 표로만 / 둘 다.

3. Qualtrics 응답 내보내기:
   - `export_responses(surveyId, format="csv")` 호출 → `check_export_status` 로 폴링 (완료까지 1~30초).
   - 완료되면 파일 경로를 받아 `exports/qualtrics_<surveyId>_<timestamp>.csv` 로 저장 위치를 표시.

4. Prolific 제출 조회:
   - `list_submissions(study_id)` 호출.
   - 각 제출의 status (`AWAITING_REVIEW` / `APPROVED` / `REJECTED` / `TIMED_OUT` / `RETURNED`) 별로 집계.

5. 다음 항목을 한국어 표로 학생에게 출력:
   - 총 모집 인원 / 응답 완료 / 검토 대기 / 승인 / 거부
   - Qualtrics 응답 수 vs Prolific 완료 수 (둘이 같으면 배선 OK, 다르면 누락 의심)
   - CSV 파일 경로 (저장한 경우)

6. **불일치 발견 시** 학생에게:
   > Qualtrics 응답 < Prolific 완료 인 경우: 참여자가 completion URL 로 가기 전에 창을 닫았을 가능성.
   > Qualtrics 응답 > Prolific 완료 인 경우: 일부 응답에 PROLIFIC_PID 가 비어 있을 가능성 (URL 직접 공유 등).

## 주의

- `export_responses` 가 대형 설문에서는 비동기. `check_export_status` 로 폴링하되 30초 이상 걸리면 중단하고 학생에게 "백그라운드 진행 중, 잠시 후 다시 시도" 안내.
