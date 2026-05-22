# 01. 사전 준비 — 계정 만들기와 API 토큰 발급

이 장을 마치면 `.env` 파일의 5개 변수를 모두 채울 수 있습니다.

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

1. https://app.prolific.com 로그인 → 좌측 하단 **Settings**
2. **Go to API tokens** → **Create token** → 이름을 적당히 (`claude-class`) → 생성
   - 토큰은 한 번만 표시됩니다. 이 값이 `PROLIFIC_API_TOKEN`.
3. 워크스페이스 선택 → 브라우저 URL 의 `/workspaces/<여기>` 부분이 `PROLIFIC_WORKSPACE_ID`.
4. 워크스페이스 안에서 **New project** 로 프로젝트 하나 생성 (예: `class-practice`) → 프로젝트를 열면 URL `/projects/<여기>` 가 `PROLIFIC_PROJECT_ID`.

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
