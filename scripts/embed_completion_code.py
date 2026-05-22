"""Display the Prolific completion code on the survey's End of Survey screen.

Motivation
----------
Free Qualtrics accounts do not support "End of Survey → Redirect to URL", which
means participants cannot be automatically sent back to Prolific after they
finish. This script bakes the completion code directly into the survey content
(into the last descriptive-text question in the "End of Survey" block) so that
participants see the code on screen and can paste it on Prolific manually.

The code is also saved as a reusable end-of-survey message in the API token
owner's Qualtrics library, for future reference.

After running this script the survey can be exported as QSF and imported into
any Qualtrics account (including free accounts) and the end screen will still
show the completion code.

Usage
-----
    uv run python scripts/embed_completion_code.py \
        --survey-id SV_xxxxxxxxxxxxxxx \
        --code FF18AB

Optional flags:
    --block-name "End of Survey"   (override the block name to search for)
    --question-id QID26            (skip block search; update this question directly)
    --skip-library                 (do not save a copy to the user's library)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

try:
    DC = os.environ["QUALTRICS_DATA_CENTER"]
    TOK = os.environ["QUALTRICS_API_TOKEN"]
except KeyError as exc:
    print(f"❌ {exc.args[0]} 환경변수가 비어 있습니다. /setup-keys 를 실행하세요.", file=sys.stderr)
    sys.exit(1)

BASE = f"https://{DC}.qualtrics.com/API/v3"
H = {"X-API-TOKEN": TOK, "Content-Type": "application/json"}


def q(method: str, path: str, **kw):
    r = requests.request(method, f"{BASE}{path}", headers=H, timeout=30, **kw)
    if not r.ok:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text}")
    return r.json() if r.content else {}


def render_html(code: str) -> str:
    return_url = f"https://app.prolific.com/submissions/complete?cc={code}"
    return f"""
<div style="text-align:center; padding: 20px;">
  <h2>Thank you for taking part in this study.</h2>
  <p>Please copy the completion code below and paste it on your Prolific submission.</p>

  <div style="margin: 30px auto; padding: 20px 40px; display: inline-block;
              border: 2px dashed #444; border-radius: 8px;
              background: #f7f7f7;">
    <div style="font-size: 14px; color: #555; margin-bottom: 8px;">
      Completion code
    </div>
    <div style="font-size: 36px; font-weight: 700; letter-spacing: 4px;
                font-family: 'Courier New', monospace; color: #111;">
      {code}
    </div>
  </div>

  <p style="margin-top: 30px;">
    Or <a href="{return_url}" target="_self">click here to return to Prolific</a>.
  </p>
</div>
""".strip()


def find_end_question(survey_id: str, block_name: str) -> str:
    """Locate the last descriptive-text (DB) question inside the named block.

    Falls back to the last block in the survey if the named block is not found.
    """
    defn = q("GET", f"/survey-definitions/{survey_id}")["result"]
    blocks = defn.get("Blocks", {})

    candidate = None
    for bid, b in blocks.items():
        if (b.get("Description") or "").strip().lower() == block_name.lower():
            candidate = (bid, b)
            break

    if candidate is None:
        flow = defn.get("SurveyFlow", {}).get("Flow", []) or []
        last_block_id = None
        for el in reversed(flow):
            if el.get("Type") == "Block":
                last_block_id = el.get("ID")
                break
        if last_block_id and last_block_id in blocks:
            candidate = (last_block_id, blocks[last_block_id])

    if candidate is None:
        raise RuntimeError(
            f"블록 '{block_name}' 도, 마지막 블록도 찾지 못했습니다."
        )

    bid, block = candidate
    elements = block.get("BlockElements", []) or []
    db_qids = []
    for el in elements:
        if el.get("Type") != "Question":
            continue
        qid = el.get("QuestionID")
        qdef = q("GET", f"/survey-definitions/{survey_id}/questions/{qid}")["result"]
        if qdef.get("QuestionType") == "DB":
            db_qids.append(qid)

    if not db_qids:
        raise RuntimeError(
            f"블록 '{block.get('Description')}' 안에 descriptive text(DB) 문항이 없습니다."
        )
    return db_qids[-1]


def update_question_html(survey_id: str, question_id: str, html: str) -> None:
    current = q("GET", f"/survey-definitions/{survey_id}/questions/{question_id}")["result"]
    payload = {
        "QuestionType": current["QuestionType"],
        "Selector": current["Selector"],
        "QuestionText": html,
    }
    if current.get("SubSelector"):
        payload["SubSelector"] = current["SubSelector"]
    if current.get("DataExportTag"):
        payload["DataExportTag"] = current["DataExportTag"]
    q("PUT", f"/survey-definitions/{survey_id}/questions/{question_id}", data=json.dumps(payload))


def upsert_library_message(code: str, html: str) -> tuple[str, str] | None:
    libs = q("GET", "/libraries")["result"]["elements"]
    lib_id = next((l["libraryId"] for l in libs if l["libraryId"].startswith("UR_")), None)
    if not lib_id:
        print("  ! 사용자 라이브러리(UR_) 를 찾지 못해 라이브러리 저장을 건너뜁니다.")
        return None

    description = f"Prolific Completion Code {code}"
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
        return lib_id, existing_id

    out = q("POST", f"/libraries/{lib_id}/messages", data=json.dumps(payload))
    return lib_id, out["result"]["id"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--survey-id", required=True, help="Qualtrics 설문 ID (예: SV_xxx)")
    parser.add_argument("--code", required=True, help="Prolific completion code (예: FF18AB)")
    parser.add_argument("--block-name", default="End of Survey", help="대상 블록 이름 (기본: 'End of Survey')")
    parser.add_argument("--question-id", help="블록 검색을 생략하고 이 question id 를 직접 갱신")
    parser.add_argument("--skip-library", action="store_true", help="사용자 라이브러리 저장 생략")
    args = parser.parse_args()

    html = render_html(args.code)

    if args.question_id:
        qid = args.question_id
        print(f"[1/2] 지정 문항 갱신: {qid}")
    else:
        print(f"[1/2] '{args.block_name}' 블록의 마지막 안내문 검색")
        qid = find_end_question(args.survey_id, args.block_name)
        print(f"  → {qid}")

    update_question_html(args.survey_id, qid, html)
    print(f"  → 갱신 완료 ({len(html)} bytes)")

    if args.skip_library:
        print("[2/2] 라이브러리 저장 생략 (--skip-library)")
    else:
        print("[2/2] 사용자 라이브러리에 End-of-Survey 메시지 저장")
        result = upsert_library_message(args.code, html)
        if result:
            lib_id, msg_id = result
            print(f"  → library {lib_id} / message {msg_id}")

    print()
    print(f"완료. 미리보기: https://{DC}.qualtrics.com/jfe/preview/{args.survey_id}")
    print("마지막 문항까지 진행하면 큰 글씨로 completion code 가 표시됩니다.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
