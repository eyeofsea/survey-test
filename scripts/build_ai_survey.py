"""Build the 'Survey on AI Transformation Initiatives in Corporate' survey end-to-end.

Idempotent-ish: creates a NEW survey on each run. Prints the survey id and preview URL
at the end. Does NOT activate the survey — that's deferred to /connect-prolific.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

API_TOKEN = os.environ["QUALTRICS_API_TOKEN"]
DATA_CENTER = os.environ["QUALTRICS_DATA_CENTER"]
BASE_URL = f"https://{DATA_CENTER}.qualtrics.com/API/v3"
SESSION = requests.Session()
SESSION.headers.update({"X-API-TOKEN": API_TOKEN, "Content-Type": "application/json"})


def _request(method: str, path: str, **kw: Any) -> dict:
    url = f"{BASE_URL}{path}"
    resp = SESSION.request(method, url, timeout=30, **kw)
    if not resp.ok:
        raise RuntimeError(f"{method} {path} -> {resp.status_code}: {resp.text}")
    return resp.json()


def create_survey(name: str, language: str = "EN") -> str:
    data = {"SurveyName": name, "Language": language, "ProjectCategory": "CORE"}
    out = _request("POST", "/survey-definitions", data=json.dumps(data))
    return out["result"]["SurveyID"]


def get_definition(survey_id: str) -> dict:
    return _request("GET", f"/survey-definitions/{survey_id}")["result"]


def create_block(survey_id: str, description: str) -> str:
    data = {"Description": description, "Type": "Standard"}
    out = _request("POST", f"/survey-definitions/{survey_id}/blocks", data=json.dumps(data))
    return out["result"]["BlockID"]


def update_block(survey_id: str, block_id: str, description: str) -> None:
    cur = _request("GET", f"/survey-definitions/{survey_id}/blocks/{block_id}")["result"]
    data = {"Type": cur.get("Type", "Standard"), "Description": description}
    _request("PUT", f"/survey-definitions/{survey_id}/blocks/{block_id}", data=json.dumps(data))


def create_question(survey_id: str, block_id: str, q: dict) -> str:
    out = _request(
        "POST",
        f"/survey-definitions/{survey_id}/questions?blockId={block_id}",
        data=json.dumps(q),
    )
    return out["result"]["QuestionID"]


def add_descriptive(survey_id: str, block_id: str, html: str, tag: str) -> str:
    return create_question(
        survey_id,
        block_id,
        {
            "QuestionText": html,
            "QuestionType": "DB",
            "Selector": "TB",
            "DataExportTag": tag,
        },
    )


def add_text_entry(
    survey_id: str, block_id: str, text: str, tag: str, text_type: str = "single", force: bool = False
) -> str:
    selector_map = {"single": "SL", "multi": "ML", "essay": "ESTB"}
    data: dict = {
        "QuestionText": text,
        "QuestionType": "TE",
        "Selector": selector_map[text_type],
        "DataExportTag": tag,
    }
    if force:
        data["Validation"] = {
            "Settings": {"ForceResponse": "ON", "ForceResponseType": "ON", "Type": "None"}
        }
    return create_question(survey_id, block_id, data)


def add_mc(
    survey_id: str,
    block_id: str,
    text: str,
    choices: list[str],
    tag: str,
    multi: bool = False,
    force: bool = False,
) -> str:
    choices_obj = {str(i + 1): {"Display": c} for i, c in enumerate(choices)}
    data: dict = {
        "QuestionText": text,
        "QuestionType": "MC",
        "Selector": "MAVR" if multi else "SAVR",
        "SubSelector": "TX",
        "DataExportTag": tag,
        "Choices": choices_obj,
        "ChoiceOrder": [str(i + 1) for i in range(len(choices))],
    }
    if force:
        data["Validation"] = {
            "Settings": {"ForceResponse": "ON", "ForceResponseType": "ON", "Type": "None"}
        }
    return create_question(survey_id, block_id, data)


LIKERT7 = [
    "Strongly disagree",
    "Disagree",
    "Somewhat disagree",
    "Neither agree nor disagree",
    "Somewhat agree",
    "Agree",
    "Strongly agree",
]


def add_matrix(
    survey_id: str,
    block_id: str,
    text: str,
    statements: list[str],
    scale_points: list[str],
    tag: str,
    force: bool = False,
) -> str:
    choices = {str(i + 1): {"Display": s} for i, s in enumerate(statements)}
    answers = {str(i + 1): {"Display": p} for i, p in enumerate(scale_points)}
    data: dict = {
        "QuestionText": text,
        "QuestionType": "Matrix",
        "Selector": "Likert",
        "SubSelector": "SingleAnswer",
        "DataExportTag": tag,
        "Choices": choices,
        "ChoiceOrder": [str(i + 1) for i in range(len(statements))],
        "Answers": answers,
        "AnswerOrder": [str(i + 1) for i in range(len(scale_points))],
    }
    if force:
        data["Validation"] = {
            "Settings": {"ForceResponse": "ON", "ForceResponseType": "ON", "Type": "None"}
        }
    return create_question(survey_id, block_id, data)


# ---------------------- Survey content ----------------------

INTRO_HTML = """
<p>This survey is exclusively for individuals who are currently employed and involved in an AI project.</p>
<p><b>Purpose of the Survey</b><br>
The survey's primary purpose is to gather a comprehensive perspective on the attitudes and experiences associated with AI transformation initiatives in corporate environments. It seeks to collect data from a variety of organizations and roles to pinpoint best practices, prevalent challenges, and key factors for successful AI integration. This data will ultimately assist organizations in honing their strategies and enhancing the outcomes of their AI projects.</p>
""".strip()

CONSENT_HTML = """
<p>The responses are gauged on a Likert 7-point scale, which ranges from "Strongly Disagree" to "Strongly Agree". This scale allows for detailed feedback, giving participants the ability to accurately convey their views on the significance and effectiveness of AI initiatives.</p>
<p><b>Please note that the survey will be discontinued if incorrect responses are provided to attention check questions.</b></p>
<p>You are cordially invited to take part in a research survey designed to explore the elements that influence AI transformation efforts within organizations. Participation is completely optional and the survey should take about 6 minutes to complete. All responses will remain confidential and will be utilized strictly for academic research. By moving forward, you confirm that you are at least 20 years of age and consent to participate in this study.</p>
""".strip()


def build() -> dict:
    survey_id = create_survey("Survey on AI Transformation Initiatives in Corporate", "EN")
    defn = get_definition(survey_id)

    # Default block — rename to Intro and add the intro descriptive text
    default_block_id = None
    for bid, b in defn["Blocks"].items():
        if b.get("Type") == "Default" or b.get("Description") in ("Default Question Block", ""):
            default_block_id = bid
            break
    if not default_block_id:
        default_block_id = next(iter(defn["Blocks"]))

    update_block(survey_id, default_block_id, "Intro")
    add_descriptive(survey_id, default_block_id, INTRO_HTML, "Intro")

    # Block 9 — Prolific ID
    pid_block = create_block(survey_id, "Block 9")
    pid_qid = add_text_entry(
        survey_id,
        pid_block,
        "What is your Prolific ID? Please note that this response should be filled with the correct ID.",
        "PROLIFIC_PID_Q",
        text_type="single",
        force=False,
    )

    # Consent Form
    consent_block = create_block(survey_id, "Consent Form")
    add_descriptive(survey_id, consent_block, CONSENT_HTML, "Info_csnt")
    consent_qid = add_mc(
        survey_id,
        consent_block,
        "Do you consent to participate in this study?",
        ["Yes", "No"],
        "Consent",
        force=True,
    )

    # Scr Q1
    scr_block = create_block(survey_id, "Scr Q1")
    scr_qid = add_mc(
        survey_id,
        scr_block,
        "Which of the following best describes your current situation?",
        [
            "I am currently employed but have not been involved in AI-related work.",
            "I am not currently employed but have been involved in AI-related work.",
            "I am currently employed and have been involved in AI-related work.",
            "I am not currently employed and have not been involved in AI-related work.",
        ],
        "ScrQ",
        force=True,
    )

    # AS block — AS / PL / TS
    as_block = create_block(survey_id, "AS")
    as_qid = add_matrix(
        survey_id, as_block,
        "Please answer the questions below with your opinion. (AS)",
        [
            "Being willing to take calculated risks in adopting AI technologies is important.",
            "Embracing the risks associated with changing workforce expectations due to AI is essential.",
            "Prioritizing managing risks rather than avoiding them is crucial.",
            "Encouraging a willingness to disrupt standard practices through AI is necessary.",
        ],
        LIKERT7, "AS",
    )
    pl_qid = add_matrix(
        survey_id, as_block,
        "Please answer the questions below with your opinion. (PL)",
        [
            "Leadership should value the benefits of breaking down organizational silos to facilitate AI integration.",
            "Cultivating leaders who focus on future AI developments is vital.",
            "Leaders committing to continuous self-education in AI is essential.",
        ],
        LIKERT7, "PL",
    )
    ts_qid = add_matrix(
        survey_id, as_block,
        "Please answer the questions below with your opinion. (TS)",
        [
            "Driving decision-making processes with AI-driven data insights is important.",
            "Empowering employees to use AI tools to make decisions confidently is crucial.",
            "Overcoming process inertia to embrace AI innovations is necessary.",
            "Implementing a system for monitoring technology enablers is vital.",
        ],
        LIKERT7, "TS",
    )

    # RC block — RC / DR / MC / SP
    rc_block = create_block(survey_id, "RC")
    rc_qid = add_matrix(
        survey_id, rc_block,
        "Please answer the questions below with your opinion. (RC)",
        [
            "Actively exploring innovative AI possibilities is essential.",
            "Providing leaders with support to foster experimentation with AI is important.",
        ],
        LIKERT7, "RC",
    )
    dr_qid = add_matrix(
        survey_id, rc_block,
        "Please answer the questions below with your opinion. (DR)",
        [
            "Establishing an appropriate AI technology support model is crucial.",
            "Recognizing the need for changes in technology and processes to support AI is necessary.",
            "Emphasizing the importance of future scalability of AI systems is vital.",
        ],
        LIKERT7, "DR",
    )
    mc_qid = add_matrix(
        survey_id, rc_block,
        "Please answer the questions below with your opinion. (MC)",
        [
            "Engaging deeply with the market to understand AI trends is important.",
            "Understanding and leveraging the potential value of our AI offerings is crucial.",
        ],
        LIKERT7, "MC",
    )
    sp_qid = add_matrix(
        survey_id, rc_block,
        "Please answer the questions below with your opinion. (SP)",
        [
            "Ensuring accountability for AI processes and outcomes is necessary.",
            "Effectively coordinating AI platform development within our enterprise is important.",
            "Demonstrating strong enterprise commitment to AI transformation goals is vital.",
        ],
        LIKERT7, "SP",
    )

    # ID block — attention check + ID + OT
    id_block = create_block(survey_id, "ID")
    attn_qid = add_mc(
        survey_id, id_block,
        "Is AI an abbreviation for Artichoke Information?",
        ["No", "Yes"],
        "AttnCheck",
        force=True,
    )
    id_qid = add_matrix(
        survey_id, id_block,
        "Please answer the questions below with your opinion. (ID)",
        [
            "Continuously evolving our competitive advantage through AI is essential.",
            "Using AI to identify and capitalize on new market niches is important.",
            "Leveraging AI to respond swiftly to environmental changes is crucial.",
            "Considering AI strategies for repositioning within the industry is necessary.",
        ],
        LIKERT7, "ID",
    )
    ot_qid = add_matrix(
        survey_id, id_block,
        "Please answer the questions below with your opinion. (OT)",
        [
            "Proactively addressing concerns about potential AI disruptors is vital.",
            "Excelling in identifying and seizing new opportunities through AI is essential.",
        ],
        LIKERT7, "OT",
    )

    # DV block
    dv_block = create_block(survey_id, "DV")
    dv_qid = add_matrix(
        survey_id, dv_block,
        "Please answer the questions below with your opinion. (DV)",
        [
            "Our organization has achieved/will be able to achieve significant operational efficiency improvements and cost reductions due to AI implementation.",
            "We have developed/will develop innovative products or services enabled by AI.",
            "Our financial performance has improved/will improve as a result of AI initiatives.",
            "Our market position has strengthened/will be strengthened, and customer satisfaction levels have increased/will increase due to AI capabilities.",
        ],
        LIKERT7, "DV",
    )

    # HCD block — HCD + OS
    hcd_block = create_block(survey_id, "HCD")
    hcd_qid = add_matrix(
        survey_id, hcd_block,
        "Please answer the questions below with your opinion. (HCD)",
        [
            "Acknowledging that focusing on AI solutions that enhance human capabilities leads to better adoption and outcomes is important.",
            "Aligning decision-making processes with ethical standards is crucial for the success of AI initiatives.",
            "Fostering a culture of accountability enhances the effectiveness of responsible AI implementation.",
            "Measuring the societal impact of AI technologies is essential for evaluating the success of AI initiatives.",
            "Empowering individuals within the organization to address ethical concerns contributes to better AI outcomes.",
        ],
        LIKERT7, "HCD",
    )
    os_qid = add_matrix(
        survey_id, hcd_block,
        "Please answer the questions below with your opinion. (OS)",
        [
            "Forming an appropriate team for Responsible AI (RAI) is crucial to the success of AI initiatives.",
            "Having core leadership positions like a Head of Responsible AI, Ethics Advisor, and Regulatory Specialist is crucial to the success of AI initiatives.",
            "Including AI developers, data scientists, AI security specialists, and domain experts enhances responsible AI implementation.",
            "Appointing roles like Change Manager and RAI Project Manager is essential for adjusting processes and coordinating resources for successful AI integration.",
            "Having Communication Specialists and HR & Training Specialists promotes collaboration and integration of responsible AI principles across the organization.",
            "Establishing roles such as Independent AI Auditor and Data & Ethics Board is necessary for providing objective monitoring and guidance, influencing the effectiveness of AI projects.",
        ],
        LIKERT7, "OS",
    )

    # Demographics
    demo_block = create_block(survey_id, "Demographics")
    ind_qid = add_mc(
        survey_id, demo_block,
        "Which industry do you work in?",
        ["Technology", "Finance", "Healthcare", "Manufacturing", "Education", "Retail"],
        "Ind",
    )
    comsz_qid = add_mc(
        survey_id, demo_block,
        "How many employees are in your company?",
        ["Fewer than 50", "50-99", "100-499", "500-999", "1000-4999", "5000 or more"],
        "ComSz",
    )
    yrex_qid = add_mc(
        survey_id, demo_block,
        "How many years have you worked with AI technologies?",
        ["Less than 1 year", "1-2 years", "3-5 years", "6-10 years", "More than 10 years"],
        "YrEx",
    )
    rolai_qid = add_mc(
        survey_id, demo_block,
        "What's your role in your company's AI projects?",
        [
            "Executive/Senior Management",
            "Middle Management",
            "Technical Staff/Engineer",
            "Researcher/Scientist",
            "Consultant",
        ],
        "RolAI",
    )
    gender_qid = add_mc(survey_id, demo_block, "Gender", ["Male", "Female"], "Gender")
    age_qid = add_mc(survey_id, demo_block, "Age", ["-30", "31-40", "41-50", "51-"], "Age")
    edu_qid = add_mc(
        survey_id, demo_block,
        "What is your highest level of education completed?",
        ["High school", "College", "Undergraduate", "Postgraduate"],
        "Edu",
    )

    # End of Survey
    end_block = create_block(survey_id, "End of Survey")
    end_qid = add_descriptive(
        survey_id,
        end_block,
        "<p>Thanks for taking part in this study. A completion code will be provided on the next page. Please copy the code and paste it on your Prolific submission.</p>",
        "EndMsg",
    )

    return {
        "survey_id": survey_id,
        "blocks": {
            "intro": default_block_id,
            "pid": pid_block,
            "consent": consent_block,
            "scr": scr_block,
            "as": as_block,
            "rc": rc_block,
            "id": id_block,
            "dv": dv_block,
            "hcd": hcd_block,
            "demo": demo_block,
            "end": end_block,
        },
        "questions": {
            "pid": pid_qid,
            "consent": consent_qid,
            "scr": scr_qid,
            "as": as_qid, "pl": pl_qid, "ts": ts_qid,
            "rc": rc_qid, "dr": dr_qid, "mc": mc_qid, "sp": sp_qid,
            "attn": attn_qid, "id": id_qid, "ot": ot_qid,
            "dv": dv_qid,
            "hcd": hcd_qid, "os": os_qid,
            "ind": ind_qid, "comsz": comsz_qid, "yrex": yrex_qid, "rolai": rolai_qid,
            "gender": gender_qid, "age": age_qid, "edu": edu_qid,
            "end": end_qid,
        },
    }


if __name__ == "__main__":
    try:
        info = build()
    except Exception as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        sys.exit(1)

    out_path = REPO_ROOT / ".survey_state.json"
    out_path.write_text(json.dumps(info, indent=2))
    sid = info["survey_id"]
    preview = f"https://{DATA_CENTER}.qualtrics.com/jfe/preview/{sid}"
    edit = f"https://{DATA_CENTER}.qualtrics.com/survey-builder/{sid}/edit"
    print(f"surveyId   = {sid}")
    print(f"preview    = {preview}")
    print(f"edit       = {edit}")
    print(f"state file = {out_path}")
