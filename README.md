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

## 출처 / 라이선스

- Qualtrics MCP 서버: https://github.com/yrvelez/qualtrics-mcp-server (MIT)
- Prolific 외부 스터디 가이드: https://github.com/prolific-oss/prolific-external-study-link-getting-started
- 본 레포의 학습용 코드는 MIT.
