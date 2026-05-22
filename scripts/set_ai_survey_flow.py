"""Set the survey flow: declare PROLIFIC_PID embedded data + insert three EndSurvey branches.

Branch logic:
1. After Consent block: if Consent (QID4) = 'No' (choice 2) -> EndSurvey
2. After Scr Q1 block: if Scr (QID5) in {1, 2, 4} (not eligible) -> EndSurvey
3. After ID block: if Attention check (QID13) = 'Yes' (choice 2) -> EndSurvey
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

API_TOKEN = os.environ["QUALTRICS_API_TOKEN"]
DATA_CENTER = os.environ["QUALTRICS_DATA_CENTER"]
BASE_URL = f"https://{DATA_CENTER}.qualtrics.com/API/v3"
HEADERS = {"X-API-TOKEN": API_TOKEN, "Content-Type": "application/json"}

state = json.loads((REPO_ROOT / ".survey_state.json").read_text())
SID = state["survey_id"]
B = state["blocks"]
Q = state["questions"]


def choice_branch(question_id: str, choice_indices: list[int], description: str) -> dict:
    """Build a BranchLogic that fires if any of the listed choices is selected."""
    inner: dict = {}
    for n, idx in enumerate(choice_indices):
        cond = {
            "LogicType": "Question",
            "QuestionID": question_id,
            "QuestionIsInLoop": "no",
            "ChoiceLocator": f"q://{question_id}/SelectableChoice/{idx}",
            "Operator": "Selected",
            "QuestionIDFromLocator": question_id,
            "LeftOperand": f"q://{question_id}/SelectableChoice/{idx}",
            "Type": "Expression",
            "Description": description,
        }
        if n > 0:
            cond["Conjuction"] = "Or"  # Qualtrics actually misspells this
        inner[str(n)] = cond
    inner["Type"] = "If"
    return {"0": inner, "Type": "BooleanExpression"}


def end_survey_flow(flow_id: int) -> dict:
    return {
        "FlowID": f"FL_{flow_id}",
        "Type": "EndSurvey",
        "EndingType": "Advanced",
        "Options": {"Advanced": "true", "SurveyTermination": "DefaultMessage"},
    }


def branch(flow_id: int, description: str, logic: dict, child_flow_id: int) -> dict:
    return {
        "FlowID": f"FL_{flow_id}",
        "Type": "Branch",
        "Description": description,
        "BranchLogic": logic,
        "Flow": [end_survey_flow(child_flow_id)],
    }


def block_node(flow_id: int, block_id: str) -> dict:
    return {"FlowID": f"FL_{flow_id}", "Type": "Block", "ID": block_id, "Autofill": []}


fid = iter(range(2, 1000))


def nxt() -> int:
    return next(fid)


def main() -> None:
    embedded = {
        "FlowID": f"FL_{nxt()}",
        "Type": "EmbeddedData",
        "EmbeddedData": [
            {
                "Description": "PROLIFIC_PID",
                "Type": "Recipient",
                "Field": "PROLIFIC_PID",
                "VariableType": "String",
                "DataVisibility": [],
                "AnalyzeText": False,
            }
        ],
    }

    flow_elements = [
        embedded,
        block_node(nxt(), B["intro"]),
        block_node(nxt(), B["pid"]),
        block_node(nxt(), B["consent"]),
    ]

    # Branch: consent == No (choice 2)
    branch_fid = nxt()
    end_fid = nxt()
    flow_elements.append(
        branch(
            branch_fid,
            "If Consent = No, End Survey",
            choice_branch(
                Q["consent"], [2],
                'If <span class="QuestionText">Do you consent to participate</span> No Is Selected'
            ),
            end_fid,
        )
    )

    flow_elements.append(block_node(nxt(), B["scr"]))

    # Branch: Scr != eligible (choices 1, 2, 4 -> end)
    branch_fid = nxt()
    end_fid = nxt()
    flow_elements.append(
        branch(
            branch_fid,
            "If Screening != Currently employed + AI involved, End Survey",
            choice_branch(
                Q["scr"], [1, 2, 4],
                'If Screening: not currently employed + AI involved'
            ),
            end_fid,
        )
    )

    flow_elements.append(block_node(nxt(), B["as"]))
    flow_elements.append(block_node(nxt(), B["rc"]))
    flow_elements.append(block_node(nxt(), B["id"]))

    # Branch: Attention check (QID13) = "Yes" (choice 2) -> EndSurvey
    branch_fid = nxt()
    end_fid = nxt()
    flow_elements.append(
        branch(
            branch_fid,
            "If Attention check answered Yes (incorrect), End Survey",
            choice_branch(
                Q["attn"], [2],
                'If Attention check "Is AI an abbreviation for Artichoke Information?" Yes Is Selected'
            ),
            end_fid,
        )
    )

    flow_elements.append(block_node(nxt(), B["dv"]))
    flow_elements.append(block_node(nxt(), B["hcd"]))
    flow_elements.append(block_node(nxt(), B["demo"]))
    flow_elements.append(block_node(nxt(), B["end"]))

    max_flow_id = max(
        int(elem["FlowID"].split("_")[1])
        for elem in flow_elements
        for elem in ([elem] + elem.get("Flow", []))
    )

    payload = {
        "Type": "Root",
        "FlowID": "FL_1",
        "Flow": flow_elements,
        "Properties": {"Count": max_flow_id},
    }

    r = requests.put(
        f"{BASE_URL}/survey-definitions/{SID}/flow",
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=30,
    )
    if not r.ok:
        print("FLOW UPDATE FAILED:", r.status_code, r.text, file=sys.stderr)
        sys.exit(1)
    print("Flow updated OK")
    print(f"Properties.Count = {max_flow_id}")
    print(f"Elements        = {len(flow_elements)}")


if __name__ == "__main__":
    main()
