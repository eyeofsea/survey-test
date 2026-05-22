# 03. Qualtrics ↔ Prolific 통합 — `/connect-prolific`

설문 자체보다 **이 배선 단계가 가장 헷갈립니다.** Claude 가 자동화해 주지만, 무엇이 일어나는지 이해하면 디버깅이 쉬워집니다.

## 통합의 원리

```
[Prolific 참여자]
   │
   │ Prolific 이 자동으로 만든 외부 URL 클릭:
   │   https://<DC>.qualtrics.com/jfe/form/SV_xxx
   │     ?PROLIFIC_PID=5f9b...        ← 참여자 고유 ID
   │     &STUDY_ID=66a1...            ← 스터디 ID
   │     &SESSION_ID=66a2...          ← 세션 ID
   ▼
[Qualtrics 설문]
   │ embedded data 로 위 3개 값을 응답 데이터에 기록
   │ 참여자가 설문을 끝마치면 종료 흐름이 발동
   ▼
[Qualtrics → Prolific 리다이렉트]
   https://app.prolific.com/submissions/complete?cc=<완료코드>
   │
   ▼
[Prolific 이 완료코드 매칭 → 자동 승인]
```

요약하면 **3가지가 정확히 맞아야** 합니다:
1. Qualtrics 가 URL 쿼리 3개 값을 embedded data 로 받아 저장
2. Qualtrics 종료 시 redirect URL 에 `cc=<완료코드>` 포함
3. Prolific 스터디의 `completion_codes[0].code` 가 위 `<완료코드>` 와 일치

## `/connect-prolific` 가 자동으로 하는 5단계

| 단계 | 호출 도구 | 효과 |
|---|---|---|
| 1 | `add_embedded_data(PROLIFIC_PID, STUDY_ID, SESSION_ID)` | URL 쿼리 자동 캡처 |
| 2 | (코드 생성) | 6자리 영숫자 무작위 — 두 곳에 동일 적용 |
| 3 | `update_survey_flow` | 종료 시 Prolific 완료 URL 로 리다이렉트 |
| 4 | `create_anonymous_link` + `activate_survey` | 외부 공유 가능 + 응답 수집 활성화 |
| 5 | `create_external_study` | Prolific 측 DRAFT 스터디 생성 |

## 직접 검증 (퍼블리시 전에 꼭 한 번!)

Claude 가 알려준 익명 링크 끝에 가짜 파라미터를 붙여 직접 응답해 보세요:

```
<익명 링크>?PROLIFIC_PID=test123&STUDY_ID=teststudy&SESSION_ID=testsession
```

설문을 끝까지 응답한 후 두 가지를 확인:
1. **Qualtrics 응답 탭** 에서 새 응답의 embedded data 컬럼에 `test123` 등이 보이는지
2. **응답 직후** 브라우저가 `https://app.prolific.com/submissions/complete?cc=...` 로 이동하는지

둘 다 OK 면 배선 완료. 하나라도 실패면 `/connect-prolific` 를 다시 실행하기 전에 원인을 좁혀 보세요 ([`05-troubleshooting.md`](05-troubleshooting.md)).

다음 장: [`04-launch-and-collect.md`](04-launch-and-collect.md)
