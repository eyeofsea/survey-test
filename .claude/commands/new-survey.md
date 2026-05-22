---
description: 자연어 대화로 Qualtrics 설문을 처음부터 생성
---

학생이 한국어 대화만으로 Qualtrics 설문을 만들 수 있도록 안내합니다. Qualtrics MCP 도구를 사용하세요.

## 절차

1. AskUserQuestion 으로 시작 방식을 물어보세요:
   - 샘플 설문 (examples/sample_survey_spec.yaml 의 5문항) 로 빠르게 시작
   - 처음부터 직접 설계

2. **직접 설계**라면 다음을 순서대로 한국어로 물어보세요 (한 번에 하나씩):
   - 설문 제목
   - 설문 주제/목적 (1줄)
   - 사용할 언어 (기본 KO)
   - 문항 수 (대략)
   - 문항 유형 구성 — 객관식 / 리커트 / 자유응답 중 어떤 것을 몇 개씩

3. 답변이 모이면 다음 Qualtrics MCP 도구를 순서대로 호출:
   - `create_survey(name, language, projectCategory)` — projectCategory 는 보통 `"CORE"`
   - 받은 surveyId 로 각 문항을:
     - 객관식 → `add_multiple_choice_question(surveyId, questionText, choices, allowMultipleSelections=false)`
     - 리커트 → `add_likert_question(surveyId, questionText, scaleLabels)` (예: ["전혀 그렇지 않다","그렇지 않다","보통이다","그렇다","매우 그렇다"])
     - 자유응답 → `add_text_entry_question(surveyId, questionText, textType="MultiLine")`
   - 도입 안내문이 필요하면 `add_descriptive_text_question` 사용

4. `update_survey_flow` 로 기본 흐름이 그대로면 건너뛰어도 됩니다. (다음 `/connect-prolific` 가 흐름을 수정합니다)

5. **활성화는 하지 마세요** — `/connect-prolific` 가 embedded data 와 redirect 를 추가한 뒤 마지막에 `activate_survey` 를 호출합니다.

6. 마지막에 surveyId 와 미리보기 링크 (`https://<datacenter>.qualtrics.com/jfe/preview/<surveyId>` 형식) 를 한국어로 출력하고, 학생에게 브라우저로 한 번 클릭하여 문항을 검토하라고 안내하세요.

## 샘플 모드

샘플 선택 시 `examples/sample_survey_spec.yaml` 을 Read 한 다음, 그 명세대로 위와 동일한 도구들을 호출하면 됩니다. 학생에게는 "샘플 5문항으로 생성 중입니다..." 라고만 알리고 진행.

## 마지막 단계

생성 완료 후 학생에게:

> 다음 단계: `/connect-prolific` 를 실행하면 이 설문에 Prolific 메타데이터를 자동으로 배선합니다.
