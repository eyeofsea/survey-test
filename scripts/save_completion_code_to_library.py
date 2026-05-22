"""Save the Prolific completion code as a Qualtrics library message and update the
End of Survey block (QID26) to display the code prominently.

The redirect to https://app.prolific.com/submissions/complete?cc=<code> still
fires after the participant clicks the submit button on the final page, but if
the redirect ever fails the code is plainly visible so the participant can
copy it manually.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = REPO_ROOT / ".survey_state.json"
load_dotenv(REPO_ROOT / ".env")

DC = os.environ["QUALTRICS_DATA_CENTER"]
TOK = os.environ["QUALTRICS_API_TOKEN"]
BASE = f"https://{DC}.qualtrics.com/API/v3"
H = {"X-API-TOKEN": TOK, "Content-Type": "application/json"}

state = json.loads(STATE_PATH.read_text())
SID = state["survey_id"]
END_QID = state["questions"]["end"]
COMPLETION_CODE = state["prolific"]["completion_code"]
PROLIFIC_RETURN_URL = f"https://app.prolific.com/submissions/complete?cc={COMPLETION_CODE}"


def q(method: str, path: str, **kw):
    r = requests.request(method, f"{BASE}{path}", headers=H, timeout=30, **kw)
    if not r.ok:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text}")
    return r.json() if r.content else {}


# ---------------- HTML for the end-of-survey screen ----------------

END_HTML = f"""
<div style="text-align:center; padding: 20px;">
  <h2>Thank you for taking part in this study.</h2>
  <p>Please copy the completion code below and paste it on your Prolific submission.</p>
  <p>Your browser will be automatically redirected to Prolific after you click the submit button below.</p>

  <div style="margin: 30px auto; padding: 20px 40px; display: inline-block;
              border: 2px dashed #444; border-radius: 8px;
              background: #f7f7f7;">
    <div style="font-size: 14px; color: #555; margin-bottom: 8px;">
      Completion code
    </div>
    <div style="font-size: 36px; font-weight: 700; letter-spacing: 4px;
                font-family: 'Courier New', monospace; color: #111;">
      {COMPLETION_CODE}
    </div>
  </div>

  <p style="margin-top: 30px;">
    If the redirect does not happen automatically, please
    <a href="{PROLIFIC_RETURN_URL}" target="_self">click here to return to Prolific</a>.
  </p>
</div>
""".strip()


def find_user_library() -> str:
    libs = q("GET", "/libraries")["result"]["elements"]
    for lib in libs:
        if lib["libraryId"].startswith("UR_"):
            return lib["libraryId"]
    raise RuntimeError("사용자 라이브러리(UR_) 를 찾지 못했습니다.")


def upsert_library_message(lib_id: str, description: str, html: str) -> str:
    """If a previous message with the same description exists, update it; else create."""
    existing_id = None
    page = q("GET", f"/libraries/{lib_id}/messages")
    for m in page.get("result", {}).get("elements", []):
        if m.get("description") == description:
            existing_id = m["id"]
            break

    payload = {
        "category": "endOfSurvey",
        "description": description,
        "messages": {"en": html},
    }
    if existing_id:
        q("PUT", f"/libraries/{lib_id}/messages/{existing_id}", data=json.dumps(payload))
        print(f"  → 기존 메시지 갱신: {existing_id}")
        return existing_id

    out = q("POST", f"/libraries/{lib_id}/messages", data=json.dumps(payload))
    new_id = out["result"]["id"]
    print(f"  → 새 메시지 생성: {new_id}")
    return new_id


def update_end_question(html: str) -> None:
    # GET current, preserve type/selector, replace QuestionText
    current = q("GET", f"/survey-definitions/{SID}/questions/{END_QID}")["result"]
    payload = {
        "QuestionType": current["QuestionType"],
        "Selector": current["Selector"],
        "QuestionText": html,
        "DataExportTag": current.get("DataExportTag", "EndMsg"),
    }
    if current.get("SubSelector"):
        payload["SubSelector"] = current["SubSelector"]
    q("PUT", f"/survey-definitions/{SID}/questions/{END_QID}", data=json.dumps(payload))


def main() -> None:
    print(f"Completion code: {COMPLETION_CODE}")
    print(f"Return URL     : {PROLIFIC_RETURN_URL}")
    print()

    print("[1/2] 사용자 라이브러리에 End-of-Survey 메시지 저장")
    lib_id = find_user_library()
    print(f"  → library = {lib_id}")
    msg_id = upsert_library_message(
        lib_id,
        f"AI Transformation Survey - Completion Code {COMPLETION_CODE}",
        END_HTML,
    )

    print("[2/2] End of Survey 블록의 안내문(QID) 갱신")
    update_end_question(END_HTML)
    print(f"  → {END_QID} 업데이트 완료")

    state.setdefault("prolific", {})["library_id"] = lib_id
    state["prolific"]["library_message_id"] = msg_id
    STATE_PATH.write_text(json.dumps(state, indent=2))

    print()
    print(f"Library   : {lib_id}")
    print(f"Message   : {msg_id}")
    print(f"End QID   : {END_QID}")
    print()
    print("→ 미리보기에서 끝까지 진행 시 완료 코드가 큰 글씨로 표시되고,")
    print("  하단의 '제출' 버튼 클릭 시 Prolific 으로 자동 redirect 됩니다.")
    print()
    print(f"  https://{DC}.qualtrics.com/jfe/preview/{SID}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
