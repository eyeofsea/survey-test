# 설문 실습 레포 (Qualtrics × Prolific × Claude Code)

**Repository:** https://github.com/eyeofsea/survey-test

Claude Code 한 곳에서 **Qualtrics 설문을 만들고 → Prolific 외부 스터디에 연결하고 → 응답을 수집**하기까지 전체 흐름을 자연어로 실습하는 강의용 레포입니다.

학생은 브라우저로 설정 화면을 클릭할 필요가 없습니다. **모든 제어는 Claude 와의 대화에서** 일어납니다.

---

## 5분 퀵스타트

### 1. 사전 준비

| 항목 | 설치 / 발급 |
|---|---|
| Claude Code | https://claude.com/claude-code (macOS / Linux / **Windows** 모두 지원) |
| Node.js ≥ 22 | `node --version` 으로 확인 |
| Python ≥ 3.10 + uv | macOS/Linux: `pip install uv` · Windows: `irm https://astral.sh/uv/install.ps1 \| iex` |
| Qualtrics 계정 | 무료 체험 계정으로 충분. 기관 계정은 잠겨 있을 수 있음 (docs/05 참고) |
| Prolific 계정 | https://app.prolific.com (Researcher 가입) |

### 2. 레포 받기

**macOS / Linux** (bash / zsh):
```bash
git clone --recurse-submodules https://github.com/eyeofsea/survey-test.git
cd survey-test
./scripts/setup.sh
```

**Windows** (PowerShell):
```powershell
git clone --recurse-submodules https://github.com/eyeofsea/survey-test.git
cd survey-test
./scripts/setup.ps1
```

> PowerShell 실행 정책 오류 시: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 한 번만 실행.

`setup.sh` 가 다음을 수행합니다:
- `vendor/qualtrics-mcp-server` (Node) 의존성 설치 (pnpm)
- `prolific_mcp` (Python) 의존성 설치 (uv)
- `.env` 파일 존재 여부 확인

### 3. API 토큰 입력

Claude Code 를 이 디렉터리에서 실행한 뒤:

```
/setup-keys
```

Claude 가 토큰을 하나씩 물어봐서 `.env` 에 안전하게 기록합니다 (채팅창에 토큰을 다시 표시하지 않습니다).

> Prolific 의 `WORKSPACE_ID` / `PROJECT_ID` 를 URL 에서 직접 찾기 어렵다면 토큰 입력 후 `/find-prolific-ids` 를 실행하세요 — API 로 자동 조회해 `.env` 를 채워줍니다.

### 4. 설문 만들기 → Prolific 연결 → 발행

```
/new-survey         설문을 한국어로 대화하며 생성
/connect-prolific   Qualtrics ↔ Prolific 배선 (embedded data, redirect URL, 익명 링크, 스터디 생성)
/launch-study       비용 안내 후 확인을 받고 Prolific 스터디 퍼블리시
/collect-results    Qualtrics 응답 + Prolific 제출 수집
```

---

## 슬래시 커맨드 요약

| 커맨드 | 하는 일 |
|---|---|
| `/setup-keys` | `.env` 대화형 작성 + `doctor.py` 진단 |
| `/find-prolific-ids` | 토큰만으로 Prolific 워크스페이스/프로젝트 ID 자동 조회 → `.env` 갱신 |
| `/new-survey` | 자연어 질의로 Qualtrics 설문 생성 |
| `/connect-prolific` | Qualtrics 설문에 Prolific 메타데이터 배선 + DRAFT 스터디 생성 |
| `/launch-study` | DRAFT 스터디 검토 후 명시 확인을 받고 퍼블리시 (과금 발생) |
| `/collect-results` | 응답·제출 데이터를 표로 출력 |

---

## 강의 자료

- `docs/01-setup.md` — 계정 만들기, API 토큰 발급
- `docs/02-first-survey.md` — `/new-survey` 따라하기
- `docs/03-prolific-integration.md` — embedded data 와 completion code 이해
- `docs/04-launch-and-collect.md` — 비용 안전장치, 응답 수집
- `docs/05-troubleshooting.md` — 자주 발생하는 오류

---

## 비용 안전 메시지

**Prolific 스터디는 DRAFT 상태까지는 과금되지 않습니다.** 실제 청구는 `/launch-study` 가 호출하는 `publish_study` 시점에 발생합니다. `/launch-study` 는 학생이 "퍼블리시" 라고 명시 확인하기 전에는 호출하지 않습니다.

---

## 무료 Qualtrics 계정으로 응답 수집하기 (QSF 워크플로우)

학생 대부분은 **무료 Qualtrics 계정**을 사용합니다. 무료 계정은 _"End of Survey → Redirect to URL"_ 옵션을 지원하지 않기 때문에, 참여자가 설문을 끝낸 뒤 Prolific 완료 페이지로 자동 이동시키는 것이 불가능합니다. 이 레포는 이 한계를 우회하기 위해 다음 흐름을 권장합니다.

```
1. 본 레포의 API 로 설문을 설계/배선 (creator 계정에서)
   /new-survey  →  /connect-prolific
2. Qualtrics 에서 설문을 QSF 로 export
3. 학생의 무료 Qualtrics 계정으로 QSF import → 응답 수집
```

### 핵심 트릭: completion code 를 종료 화면에 직접 표시

자동 redirect 가 막혀 있으므로, **completion code 를 설문 마지막 안내문 자체에 큰 글씨로 baked-in 해 둡니다.** 참여자는 화면의 코드를 복사해 Prolific 에 직접 붙여넣습니다.

```bash
uv run python scripts/embed_completion_code.py \
  --survey-id SV_xxxxxxxxxxxxxxx \
  --code FF18AB
```

이 스크립트는:

- "End of Survey" 블록의 마지막 descriptive text(DB) 문항을 찾아 36px 굵은 글씨로 코드를 표시하는 HTML 로 교체합니다.
- 동일한 메시지를 사용자 라이브러리(`UR_*`)에 `category: endOfSurvey` 메시지로 저장해 두어 향후 재사용/추적 가능합니다.
- QSF 로 export 하면 코드가 그대로 따라가므로 무료 계정에서도 동일하게 동작합니다.

> 유료 계정으로 redirect 를 쓸 수 있는 경우에도 이 스크립트를 함께 실행해 두는 편이 안전합니다 — redirect 가 실패할 때의 fallback 이 됩니다.

---

## 출처 / 라이선스

- Qualtrics MCP 서버: https://github.com/yrvelez/qualtrics-mcp-server (MIT)
- Prolific 외부 스터디 가이드: https://github.com/prolific-oss/prolific-external-study-link-getting-started
- 본 레포의 학습용 코드는 MIT.
