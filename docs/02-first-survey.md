# 02. 첫 설문 만들기 — `/new-survey`

Qualtrics 웹 UI 를 한 번도 클릭하지 않고 Claude 와 대화만으로 설문을 완성합니다.

## 실습

Claude Code 에서:
```
/new-survey
```

Claude 가 다음을 차례로 묻습니다:

1. **샘플로 시작 vs 직접 설계?**
   - 처음이면 "샘플" 선택 — `examples/sample_survey_spec.yaml` 의 5문항 데모가 자동 생성됩니다.
2. (직접 설계 선택 시) 설문 제목, 목적, 언어, 문항 수, 문항 유형 비율
3. (직접 설계 선택 시) 각 문항의 본문

## 내부에서 일어나는 일

Claude 가 호출하는 Qualtrics MCP 도구들:

| 단계 | 도구 |
|---|---|
| 빈 설문 생성 | `create_survey` |
| 객관식 문항 | `add_multiple_choice_question` |
| 리커트 문항 | `add_likert_question` |
| 자유응답 문항 | `add_text_entry_question` |
| 도입 설명문 | `add_descriptive_text_question` |

학생은 도구 이름을 외울 필요가 없습니다 — 한국어로 "5점 만족도 문항 추가해줘" 처럼 말하면 됩니다.

## 결과 확인

생성이 끝나면 Claude 가 다음을 표로 보여줍니다:
- **Survey ID** (예: `SV_abc123xyz`) — 이후 단계에서 계속 사용
- **미리보기 링크** — 브라우저로 열어 문항이 의도대로 나오는지 확인

> ⚠️ 이 시점에서 설문은 아직 **비활성** 상태입니다. 익명 링크를 외부에 공유해도 응답을 받지 못합니다. `/connect-prolific` 가 활성화까지 처리하므로 지금 단계에서 직접 활성화하지 마세요.

## 자주 묻는 질문

- **잘못 만들었어요. 다시 만들어도 되나요?** — 네. 학습용 Qualtrics 계정에는 설문 개수 제한이 넉넉합니다. 지우고 싶다면 Claude 에게 "설문 SV_xxx 삭제" 라고 말하면 `delete_survey` 가 호출됩니다.
- **언어를 영어로 하고 싶어요.** — `/new-survey` 에서 "언어는 영어" 라고 답하면 됩니다.

다음 장: [`03-prolific-integration.md`](03-prolific-integration.md)
