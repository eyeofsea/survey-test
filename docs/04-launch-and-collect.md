# 04. 스터디 발행과 결과 수집

## 💰 비용 안내 (꼭 읽기)

| 단계 | 과금 여부 |
|---|---|
| `/new-survey` (Qualtrics 설문 생성) | **무료** |
| `/connect-prolific` (DRAFT 스터디 생성) | **무료** |
| `/launch-study` (Prolific 퍼블리시) | **유료 — 이 시점에 청구** |
| `/collect-results` (응답 조회/다운로드) | **무료** |

Prolific 비용 = `1인당 보상금 × 모집 인원 + Prolific 수수료 (약 33%)`

예: 10분 설문, 보상 £1.00, 5명 모집 → 약 £6.65 청구.

## `/launch-study` 안전장치

```
/launch-study
```

Claude 가 수행하는 순서:
1. `get_study` 로 최신 DRAFT 상태 확인.
2. 비용 요약을 한국어 표로 출력 (1인당, 시간당 환산, 총액).
3. 외부 URL 에 `{{%PROLIFIC_PID%}}` 등 placeholder 가 포함됐는지 확인.
4. **AskUserQuestion 으로 "퍼블리시 / 취소" 명시 확인.**
5. "퍼블리시" 응답 시에만 `publish_study(study_id=..., confirm=True)` 호출.

`publish_study` 도구는 `confirm=True` 가 없으면 코드 레벨에서 거부합니다 — 실수로 호출되어 과금되는 것을 막는 두 번째 안전망.

> ⚠️ **시간당 보상 £6 미만이면 `create_external_study` 단계에서 거부됩니다.** Prolific 권장 최저선과 일치시킨 사전 검증입니다.

## `/collect-results` 사용

스터디 발행 후 잠시 기다리면 (보통 수 분 ~ 수 시간) 참여자가 응답을 시작합니다.

```
/collect-results
```

Claude 가:
- **Prolific 제출 수**: 상태별 집계 (`ACTIVE`, `AWAITING_REVIEW`, `APPROVED`, …)
- **Qualtrics 응답 수**: `export_responses` 비동기 호출 + `check_export_status` 폴링
- **불일치 진단**: 두 숫자가 다르면 가능 원인을 한국어로 안내

큰 설문은 CSV 가 `exports/` 디렉터리에 자동 저장됩니다 (`.gitignore` 로 보호).

## 승인 / 거부

본 강의는 데이터 수집까지만 다룹니다. 승인은 Prolific 대시보드에서 진행하세요. (자동 승인이 필요하면 `completion_codes[0].actions` 에 `AUTOMATICALLY_APPROVE` 가 들어가 있어 정상 응답은 자동 처리됩니다.)

다음 장: [`05-troubleshooting.md`](05-troubleshooting.md)
