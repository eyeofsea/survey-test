---
description: Qualtrics 설문을 Prolific 외부 스터디로 자동 배선
---

이 명령이 학생이 가장 헤매는 **5단계 배선**을 자동화합니다. Qualtrics MCP 도구와 Prolific MCP 도구를 함께 사용합니다.

## 입력 받기

AskUserQuestion 으로 다음을 순서대로 물어보세요:
1. 연결할 Qualtrics 설문 ID (모르면 `list_surveys` 호출해서 후보를 보여주고 선택)
2. 스터디 제목과 한 줄 설명
3. 모집 인원 수 (예: 5)
4. 예상 소요 시간 (분)
5. 보상 (penny, 100 = £1.00)

## 배선 5단계

### 1. embedded data 추가 (Qualtrics)
`add_embedded_data(surveyId, fields)` 로 다음 3개 필드를 설문 시작 흐름에 추가:
- `PROLIFIC_PID`
- `STUDY_ID`
- `SESSION_ID`

이렇게 하면 Qualtrics 가 URL 쿼리에서 이 값들을 자동 캡처합니다.

### 2. completion code 생성
6자리 영숫자 (대문자 + 숫자) 코드를 Python 의 `secrets.token_hex(3).upper()` 같은 방식으로 임의 생성하세요. 예: `A3F9D1`. 이 코드는 절대 노출하지 말고 학생에게도 잠시만 보여줍니다.

### 3. 종료 redirect 설정 (Qualtrics)
`update_survey_flow` 또는 적절한 endOfSurvey 흐름 요소로 종료 시 다음 URL 로 리다이렉트하도록 설정:

```
https://app.prolific.com/submissions/complete?cc=<생성한 코드>
```

설정 후 `add_embedded_data` 로 같은 코드를 `PROLIFIC_COMPLETION_CODE` 필드에 메모 (학생이 나중에 추적 가능하도록).

### 4. 익명 배포 링크 발급 (Qualtrics)
`create_anonymous_link(surveyId)` 호출 → 받은 URL 을 `anon_url` 로 보관.

이어서 `activate_survey(surveyId)` 호출 — 활성화되어야 익명 링크가 실제로 응답을 받습니다.

### 5. Prolific 외부 스터디 생성 (DRAFT)
`create_external_study` 도구를 다음 인자로 호출:

```
name: <학생 입력>
description: <학생 입력>
external_study_url: <anon_url>?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}
completion_code: <생성한 코드>
reward: <학생 입력 penny>
total_available_places: <학생 입력 인원>
estimated_completion_time: <학생 입력 분>
```

(URL 의 중괄호 placeholder 는 Prolific 이 참여자별로 자동 치환합니다.)

## 출력

다음을 한국어 표로 학생에게 보여주세요:
- Qualtrics surveyId, 익명 링크
- Prolific studyId, completion code, 총 예상 비용
- "스터디는 DRAFT 상태이며 아직 과금되지 않았습니다" 안내
- "다음 단계: `/launch-study` 로 검토 후 퍼블리시" 안내

## 자체 테스트 권유

학생에게 다음을 권유:
> 익명 링크 끝에 `?PROLIFIC_PID=test123&STUDY_ID=test&SESSION_ID=test` 를 붙여 한 번 직접 응답해보세요. Qualtrics 응답 탭에서 세 값이 캡처되고, 종료 시 Prolific 완료 URL 로 이동하면 배선이 정상입니다.
