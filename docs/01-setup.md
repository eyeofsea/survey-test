# 01. 사전 준비 — 계정 만들기와 API 토큰 발급

이 장을 마치면 `.env` 파일의 5개 변수를 모두 채울 수 있습니다.

## OS 별 도구 설치

| OS | Claude Code | Node.js 22+ | uv |
|---|---|---|---|
| macOS / Linux | https://claude.com/claude-code | `brew install node` / 패키지 매니저 | `pip install uv` |
| **Windows** | https://claude.com/claude-code (Windows 설치 패키지) | https://nodejs.org/ LTS 다운로드 | PowerShell: `irm https://astral.sh/uv/install.ps1 \| iex` |

**Windows 전용 추가 안내:**
- PowerShell 을 관리자 권한으로 한 번 실행해 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 실행 (스크립트 실행 허용)
- Git for Windows 가 설치돼 있어야 함 (https://git-scm.com/download/win) — `git clone --recurse-submodules` 가 필요
- 부트스트랩은 `./scripts/setup.sh` 대신 `./scripts/setup.ps1` 사용

## 필요한 계정

1. **Qualtrics**: https://www.qualtrics.com/free-account/
   - 기관 계정이 있다면 그것을 써도 되지만, **브랜드 관리자가 API 사용을 잠궈둔 경우** 토큰이 작동하지 않습니다. 진단 단계(`doctor.py`)에서 401 이 뜨면 무료 개인 계정으로 다시 시도하세요.
2. **Prolific (Researcher)**: https://app.prolific.com — 회원 가입 시 "Researcher" 선택.

두 계정 모두 이메일 인증을 완료하세요.

## Qualtrics 토큰 발급

1. Qualtrics 로그인 → 우상단 계정 아이콘 → **Account Settings**
2. 좌측 메뉴 **Qualtrics IDs**
3. **API** 박스에서 **Generate Token** 클릭 → 토큰 복사
   - 이 값이 `QUALTRICS_API_TOKEN` 입니다.
4. 같은 페이지의 **User** 박스에서 **Datacenter ID** 를 확인합니다.
   - 예: `yul1`, `fra1`, `sjc1`, `iad1`
   - 이 값이 `QUALTRICS_DATA_CENTER` 입니다.

> ⚠️ **데이터센터를 잘못 입력하면** 토큰이 맞아도 모든 API 호출이 실패합니다 (404). `doctor.py` 가 이 경우 한국어로 안내합니다.

## Prolific 토큰 + 워크스페이스 + 프로젝트

### 토큰 발급
1. https://app.prolific.com 로그인 → 좌측 하단 **Settings**
2. **Go to API tokens** → **Create token** → 이름을 적당히 (`claude-class`) → 생성
   - 토큰은 한 번만 표시됩니다. 이 값이 `PROLIFIC_API_TOKEN`.

### Workspace ID / Project ID 두 가지 방법

**방법 A — 추천 (Claude 가 자동 조회):**
토큰만 `.env` 에 채운 뒤 Claude Code 에서:
```
/find-prolific-ids
```
워크스페이스/프로젝트 목록을 한국어 표로 보여주고, 선택만 하면 `.env` 의 두 값을 자동으로 채웁니다.
프로젝트가 없으면 안내 메시지가 뜨므로 Prolific 대시보드에서 **New project** 한 번만 클릭하면 됩니다.

**방법 B — 수동 (URL 에서 복사):**
1. 워크스페이스 선택 → 브라우저 URL 확인:
   ```
   https://app.prolific.com/researcher/workspaces/644abc12...fedcba12/...
                                                  └─── 24자리 영숫자 = WORKSPACE_ID ───┘
   ```
2. 워크스페이스 안에서 **New project** 로 프로젝트 생성 (예: `class-practice`) → 프로젝트를 클릭해 열기 → URL:
   ```
   https://app.prolific.com/researcher/workspaces/<workspace_id>/projects/65bd9876...654321
                                                                          └─── 24자리 = PROJECT_ID ───┘
   ```

## `.env` 채우기

가장 쉬운 방법은 Claude Code 에서:

```
/setup-keys
```

각 값을 물어봐서 `.env` 에 안전하게 기록하고, 마지막에 `doctor.py` 로 자동 점검합니다.

수동으로 하려면 `.env.example` 을 복사:
```bash
cp .env.example .env
# 에디터로 5개 값 채우기
uv run python scripts/doctor.py
```

`doctor.py` 출력이 다음과 같으면 성공:

```
✅  Qualtrics   Qualtrics OK (datacenter=yul1)
✅  Prolific    Prolific OK
```

다음 장: [`02-first-survey.md`](02-first-survey.md)
