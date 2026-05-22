---
description: PROLIFIC_API_TOKEN 만 있으면 Workspace/Project ID 를 자동으로 찾아 .env 에 기록
---

# /find-prolific-ids — Prolific 워크스페이스/프로젝트 ID 자동 조회

`.env` 의 `PROLIFIC_WORKSPACE_ID` 와 `PROLIFIC_PROJECT_ID` 를 학생이 직접 URL 에서 복사할 필요 없이, 토큰만으로 자동으로 찾아 채워 넣습니다.

## 전제 조건

- `.env` 에 `PROLIFIC_API_TOKEN` 이 채워져 있어야 합니다. 비어 있으면 먼저 `/setup-keys` 를 안내하세요.

## 절차

### 1) 워크스페이스 목록 조회
`mcp__prolific__list_workspaces()` 호출. 결과를 한국어 표로:

```
번호  이름                  ID
─────────────────────────────────────────────────────────
 1    My workspace          644abc12...
 2    Lab #2                65cd34ef...
```

표를 보여줄 때 ID 는 일부만 표시(앞 8자 + ...) 해도 됨 — 학생이 시각적으로 헷갈리지 않도록.

### 2) 워크스페이스 선택
`AskUserQuestion` 으로 사용할 워크스페이스를 학생이 선택. 옵션이 1개면 자동 선택해도 되지만 학생에게 알린다 ("워크스페이스가 1개라 자동 선택했습니다").

### 3) 프로젝트 목록 조회
선택한 workspace_id 로 `mcp__prolific__list_projects(workspace_id)` 호출.

- 결과가 비어 있으면 한국어로 안내:
  > 이 워크스페이스에 프로젝트가 없습니다. Prolific 대시보드의 **New project** 버튼으로 하나 만들고 다시 실행해 주세요. (https://app.prolific.com/researcher/workspaces/<workspace_id>)
- 결과가 있으면 위와 같은 표로 표시.

### 4) 프로젝트 선택
역시 `AskUserQuestion` 으로 선택. 옵션이 1개면 자동 선택.

### 5) `.env` 갱신
`Read` 도구로 `.env` 를 읽어 `PROLIFIC_WORKSPACE_ID=` 와 `PROLIFIC_PROJECT_ID=` 두 줄의 값만 `Edit` 도구로 교체.

- **선택한 ID 의 마지막 몇 자만** 채팅에 표시 (전체 노출 금지는 토큰만 적용 — ID 는 그대로 보여도 무방하지만 일관성 위해 일부만).
- 갱신 완료 후 `✓ PROLIFIC_WORKSPACE_ID 저장됨`, `✓ PROLIFIC_PROJECT_ID 저장됨` 메시지.

### 6) 진단
`uv run python scripts/doctor.py` 를 실행해 Prolific 줄이 ✅ 로 바뀌었는지 확인.

### 7) 다음 단계 안내
> 다음: Qualtrics 토큰도 채워야 한다면 `/setup-keys` 를, 모두 준비됐다면 `/new-survey` 로 설문을 만드세요.

## 에러 처리

- **401 Unauthorized**: 토큰이 잘못됨. `/setup-keys` 재실행 권유.
- **403 / 빈 워크스페이스**: 계정이 Researcher 가 아닐 가능성. https://app.prolific.com Settings → 계정 유형 확인 권유.
- **MCP 서버가 응답 없음**: `claude mcp list` 로 prolific 서버 상태 확인 권유.
