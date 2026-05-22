# 05. 문제 해결 가이드

## 🔴 doctor.py 가 실패

### "QUALTRICS_API_TOKEN 이 비어 있습니다"
- `.env` 가 실제로 만들어졌는지: `ls .env`
- 변수 줄에 공백/따옴표가 들어가지 않았는지 확인 (`KEY=값` 형식, 등호 양쪽 공백 없음)
- `/setup-keys` 로 다시 입력해 보세요.

### "토큰이 유효하지 않습니다 (401)"
- Qualtrics 에서 새 토큰 발급 → 기존 토큰은 즉시 만료
- 기관 계정이라면 브랜드 관리자가 API 사용을 차단했을 수 있음 → 개인 무료 계정으로 시도

### "데이터센터 '...' 와 토큰이 일치하지 않을 수 있습니다 (HTTP 404/403)"
- Account Settings → Qualtrics IDs → User 박스 → "Datacenter ID" 를 정확히 재확인
- 흔한 오타: `yul-1`, `YUL1` 등은 X. 소문자 + 숫자 형식 (`yul1`).

### "Prolific 토큰이 유효하지 않습니다 (401)"
- app.prolific.com Settings → API tokens 에서 재발급
- Researcher 계정인지 확인 (Participant 계정은 API 토큰 발급 불가)

## 🔴 /new-survey 가 도구 호출에서 실패

### "Unauthorized" 가 모든 호출에서 발생
- Claude 가 MCP 서버를 못 띄운 경우. 터미널에서 직접 확인:
  ```
  uv run python -m prolific_mcp.server  # 한 줄 출력 후 멈추면 정상 (stdio 대기)
  npx tsx vendor/qualtrics-mcp-server/src/index.ts
  ```
- `.mcp.json` 의 `${...}` 변수 확장이 셸에서 동작하는지 확인. zsh/bash 모두 OK 지만 fish 등에서는 환경변수 export 가 필요할 수 있음.

### `add_*_question` 에서 422 / Validation error
- Likert 의 `scaleLabels` 가 정확히 5개 또는 7개인지
- 객관식 `choices` 가 1개만 있으면 거부됨 (최소 2개)

## 🔴 /connect-prolific 후 자체 테스트 실패

### Qualtrics 응답에 embedded data 가 비어 있음
- `add_embedded_data` 가 설문 **시작 흐름** 에 추가되어야 함 — 끝 흐름에 들어갔다면 캡처 못 함
- URL 의 파라미터 이름 대소문자 확인 (`PROLIFIC_PID` 정확히)

### 종료 후 Prolific 완료 URL 로 안 감
- Qualtrics 종료 흐름의 endOfSurvey 요소가 redirect 로 설정되었는지 (브라우저로 설문 편집 화면을 열어 확인)
- 무료 Qualtrics 계정은 종료 redirect 기능에 제약이 있을 수 있음 → 학생용 체험 계정 권장

### Prolific 이 자동 승인을 안 함
- 완료 코드 불일치. `/connect-prolific` 를 다시 돌려 두 곳의 코드를 일치시킬 것.
- `completion_codes[0].actions` 가 `AUTOMATICALLY_APPROVE` 인지 `get_study` 로 확인.

## 🔴 /launch-study 가 거부됨

### "시간당 보상이 £X.XX/h 로 Prolific 권장 최저선 £6.00/h 미만"
- 보상을 올리거나 예상 시간을 줄여 시간당 £6 이상으로 맞춤
- 짧은 설문(< 3분) 은 학생 실습용으로만 권장 — 실 운영 시 윤리적 최저선 확인

### Prolific 가 "Insufficient funds" 로 거부
- Prolific 대시보드 → Billing 에서 충전 후 재시도

## 🔴 /collect-results 의 응답 수가 0

- 스터디가 정말 PUBLISHED 인지 (`get_study` 로 status 확인)
- 참여자 풀이 비어있을 수 있음 — Prolific 의 필터(국가, 언어 등) 가 너무 좁지 않은지 확인
- 학생 자기 자신은 Researcher 계정으로는 Participant 가 될 수 없음 → 다른 계정/지인의 도움 필요

## 그래도 막힐 때

- 도구 호출 에러 메시지 전체를 그대로 강사 / 조교에게 전달
- 토큰/이메일은 **절대** 함께 보내지 말 것
