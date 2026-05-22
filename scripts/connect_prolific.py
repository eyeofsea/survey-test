"""Connect the AI Transformation survey to a Prolific external study (DRAFT).

Steps:
  1) Resolve Prolific workspace + project IDs (write to .env if missing)
  2) Generate a completion code
  3) Add embedded data: PROLIFIC_PID, STUDY_ID, SESSION_ID, PROLIFIC_COMPLETION_CODE
  4) Append EndSurvey redirect to the main flow path
  5) Create anonymous link
  6) Activate survey
  7) Create Prolific external study (DRAFT, unbilled)

Persists the state to .survey_state.json so /launch-study / /collect-results can find it.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import sys
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
STATE_PATH = REPO_ROOT / ".survey_state.json"
load_dotenv(ENV_PATH)

QUAL_TOKEN = os.environ["QUALTRICS_API_TOKEN"]
QUAL_DC = os.environ["QUALTRICS_DATA_CENTER"]
QUAL_BASE = f"https://{QUAL_DC}.qualtrics.com/API/v3"
QUAL_HEADERS = {"X-API-TOKEN": QUAL_TOKEN, "Content-Type": "application/json"}

PROL_TOKEN = os.environ["PROLIFIC_API_TOKEN"]
PROL_BASE = "https://api.prolific.com/api/v1"
PROL_HEADERS = {
    "Authorization": f"Token {PROL_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

state = json.loads(STATE_PATH.read_text())
SID = state["survey_id"]


def q(method: str, path: str, **kw: Any) -> dict:
    r = requests.request(method, f"{QUAL_BASE}{path}", headers=QUAL_HEADERS, timeout=30, **kw)
    if not r.ok:
        raise RuntimeError(f"Qualtrics {method} {path} -> {r.status_code}: {r.text}")
    return r.json() if r.content else {}


def p(method: str, path: str, **kw: Any) -> dict:
    r = requests.request(method, f"{PROL_BASE}{path}", headers=PROL_HEADERS, timeout=30, **kw)
    if not r.ok:
        raise RuntimeError(f"Prolific {method} {path} -> {r.status_code}: {r.text}")
    return r.json() if r.content else {}


def update_env(key: str, value: str) -> None:
    text = ENV_PATH.read_text()
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    if pattern.search(text):
        new_text = pattern.sub(f"{key}={value}", text)
    else:
        new_text = text.rstrip() + f"\n{key}={value}\n"
    ENV_PATH.write_text(new_text)


# ---------------- Step 1: Prolific workspace/project ----------------

def find_workspace_project() -> tuple[str, str]:
    ws_id = os.environ.get("PROLIFIC_WORKSPACE_ID") or ""
    pr_id = os.environ.get("PROLIFIC_PROJECT_ID") or ""

    if not ws_id:
        wss = p("GET", "/workspaces/")
        results = wss.get("results", []) if isinstance(wss, dict) else wss
        if not results:
            raise RuntimeError("Prolific 워크스페이스가 하나도 없습니다.")
        ws_id = results[0]["id"]
        ws_title = results[0].get("title", "(unnamed)")
        print(f"  → workspace 자동 선택: {ws_title} ({ws_id})")
        update_env("PROLIFIC_WORKSPACE_ID", ws_id)

    if not pr_id:
        prs = p("GET", f"/workspaces/{ws_id}/projects/")
        results = prs.get("results", []) if isinstance(prs, dict) else prs
        if not results:
            raise RuntimeError(
                f"워크스페이스 {ws_id} 에 프로젝트가 없습니다. Prolific 대시보드에서 'New project' 로 먼저 생성하세요."
            )
        pr_id = results[0]["id"]
        pr_title = results[0].get("title", "(unnamed)")
        print(f"  → project 자동 선택: {pr_title} ({pr_id})")
        update_env("PROLIFIC_PROJECT_ID", pr_id)

    return ws_id, pr_id


# ---------------- Step 3: embedded data ----------------

REQUIRED_ED_FIELDS = ("PROLIFIC_PID", "STUDY_ID", "SESSION_ID")


def add_embedded_fields(completion_code: str) -> None:
    """Modify the existing EmbeddedData element in the flow to include all required fields."""
    flow_resp = q("GET", f"/survey-definitions/{SID}/flow")
    flow = flow_resp["result"]

    ed_element = None
    for el in flow["Flow"]:
        if el.get("Type") == "EmbeddedData":
            ed_element = el
            break

    if ed_element is None:
        new_ed = {
            "FlowID": "FL_2",
            "Type": "EmbeddedData",
            "EmbeddedData": [],
        }
        flow["Flow"].insert(0, new_ed)
        ed_element = new_ed

    existing_names = {f.get("Field") for f in ed_element.get("EmbeddedData", [])}

    for name in REQUIRED_ED_FIELDS:
        if name in existing_names:
            continue
        ed_element["EmbeddedData"].append({
            "Description": name,
            "Type": "Custom",
            "Field": name,
            "VariableType": "String",
            "DataVisibility": [],
            "AnalyzeText": False,
        })

    if "PROLIFIC_COMPLETION_CODE" not in existing_names:
        ed_element["EmbeddedData"].append({
            "Description": "PROLIFIC_COMPLETION_CODE",
            "Type": "Custom",
            "Field": "PROLIFIC_COMPLETION_CODE",
            "VariableType": "String",
            "Value": completion_code,
            "DataVisibility": [],
            "AnalyzeText": False,
        })
    else:
        for f in ed_element["EmbeddedData"]:
            if f.get("Field") == "PROLIFIC_COMPLETION_CODE":
                f["Value"] = completion_code

    return flow


# ---------------- Step 4: end-of-survey redirect ----------------

def append_end_redirect(flow: dict, completion_code: str) -> dict:
    """Append an EndSurvey element with Prolific redirect at the bottom of the main flow."""
    redirect_url = f"https://app.prolific.com/submissions/complete?cc={completion_code}"

    used_ids = []
    def walk(items):
        for it in items:
            fid = it.get("FlowID", "")
            if fid.startswith("FL_"):
                try:
                    used_ids.append(int(fid.split("_")[1]))
                except ValueError:
                    pass
            if "Flow" in it and isinstance(it["Flow"], list):
                walk(it["Flow"])
    walk(flow["Flow"])
    next_fid = max(used_ids + [1]) + 1

    existing_end = None
    if flow["Flow"]:
        last = flow["Flow"][-1]
        if last.get("Type") == "EndSurvey":
            existing_end = last

    if existing_end is not None:
        existing_end["EndingType"] = "Advanced"
        existing_end["Options"] = {
            "Advanced": "true",
            "SurveyTermination": "Redirect",
            "EOSRedirectURL": redirect_url,
        }
    else:
        flow["Flow"].append({
            "FlowID": f"FL_{next_fid}",
            "Type": "EndSurvey",
            "EndingType": "Advanced",
            "Options": {
                "Advanced": "true",
                "SurveyTermination": "Redirect",
                "EOSRedirectURL": redirect_url,
            },
        })
        next_fid += 1

    flow["Properties"]["Count"] = next_fid
    return flow


def put_flow(flow: dict) -> None:
    payload = {
        "Type": flow.get("Type", "Root"),
        "FlowID": flow.get("FlowID", "FL_1"),
        "Flow": flow["Flow"],
        "Properties": flow["Properties"],
    }
    q("PUT", f"/survey-definitions/{SID}/flow", data=json.dumps(payload))


# ---------------- Step 5: anonymous link ----------------

def create_anonymous_link() -> str:
    """Qualtrics anonymous link is just the public /jfe/form/{surveyId} URL.

    It becomes responsive as soon as the survey is activated. The /distributions
    POST endpoint is for email distributions and requires a mailing list, so we
    skip it for the Prolific anonymous flow.
    """
    return f"https://{QUAL_DC}.qualtrics.com/jfe/form/{SID}"


# ---------------- Step 6: activate ----------------

def activate_survey() -> None:
    q("PUT", f"/surveys/{SID}", data=json.dumps({"isActive": True}))


# ---------------- Step 7: Prolific study ----------------

def create_prolific_study(
    ws_id: str,
    project_id: str,
    name: str,
    description: str,
    anon_url: str,
    completion_code: str,
    reward: int,
    places: int,
    duration_min: int,
) -> dict:
    sep = "&" if "?" in anon_url else "?"
    external_url = (
        f"{anon_url}{sep}PROLIFIC_PID={{{{%PROLIFIC_PID%}}}}"
        f"&STUDY_ID={{{{%STUDY_ID%}}}}&SESSION_ID={{{{%SESSION_ID%}}}}"
    )
    payload = {
        "name": name,
        "internal_name": name,
        "description": description,
        "external_study_url": external_url,
        "prolific_id_option": "url_parameters",
        "completion_codes": [
            {
                "code": completion_code,
                "code_type": "COMPLETED",
                "actions": [{"action": "AUTOMATICALLY_APPROVE"}],
            }
        ],
        "total_available_places": places,
        "estimated_completion_time": duration_min,
        "reward": reward,
        "device_compatibility": ["desktop", "tablet", "mobile"],
        "peripheral_requirements": [],
        "project": project_id,
    }
    return p("POST", "/studies/", data=json.dumps(payload))


# ---------------- Driver ----------------

def main() -> None:
    # Config
    study_name = "Survey on AI Transformation Initiatives in Corporate"
    study_desc = (
        "AI 프로젝트에 참여 중인 직장인을 대상으로 AI 전환 이니셔티브에 대한 경험과 태도를 묻는 약 5-6분 분량의 학술 설문입니다. "
        "응답은 익명으로 처리되며 학술 연구 목적으로만 사용됩니다."
    )
    reward_pence = 50  # £0.50
    places = 1
    duration_min = 5

    print("[1/7] Prolific workspace/project 조회")
    ws_id, project_id = find_workspace_project()

    print("[2/7] 완료 코드 생성")
    completion_code = secrets.token_hex(3).upper()
    print(f"  → completion_code = {completion_code}")

    print("[3/7] embedded data 추가 (PROLIFIC_PID, STUDY_ID, SESSION_ID, PROLIFIC_COMPLETION_CODE)")
    flow = add_embedded_fields(completion_code)

    print("[4/7] 종료 redirect 설정")
    flow = append_end_redirect(flow, completion_code)
    put_flow(flow)

    print("[5/7] 익명 링크 발급")
    anon_url = create_anonymous_link()
    print(f"  → anon_url = {anon_url}")

    print("[6/7] 설문 활성화")
    activate_survey()

    print("[7/7] Prolific 외부 스터디 DRAFT 생성")
    study = create_prolific_study(
        ws_id, project_id, study_name, study_desc, anon_url,
        completion_code, reward_pence, places, duration_min,
    )
    study_id = study.get("id")
    print(f"  → studyId = {study_id}")

    state.update({
        "prolific": {
            "workspace_id": ws_id,
            "project_id": project_id,
            "study_id": study_id,
            "completion_code": completion_code,
            "anon_url": anon_url,
            "reward_pence": reward_pence,
            "places": places,
            "duration_min": duration_min,
        }
    })
    STATE_PATH.write_text(json.dumps(state, indent=2))

    print()
    print("=" * 70)
    print(f"Survey ID       : {SID}")
    print(f"Anonymous link  : {anon_url}")
    print(f"Prolific study  : {study_id} (DRAFT)")
    print(f"Completion code : {completion_code}")
    total_cost = reward_pence * places
    print(f"예상 비용        : £{total_cost/100:.2f} ({places}명 × £{reward_pence/100:.2f})")
    print("상태             : DRAFT (아직 과금되지 않음)")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
