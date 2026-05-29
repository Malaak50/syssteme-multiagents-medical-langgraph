from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import logging

from app.graph import graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Système Médical Multi-Agents", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class StartSessionRequest(BaseModel):
    patient_name: Optional[str] = "Patient"

class StartConsultationRequest(BaseModel):
    thread_id: str
    initial_case: str

class ResumeConsultationRequest(BaseModel):
    thread_id: str
    answer: Optional[str] = None
    physician_treatment: Optional[str] = None


def get_config(thread_id: str):
    return {"configurable": {"thread_id": thread_id}}
def get_state(thread_id):
    return graph.get_state({"configurable": {"thread_id": thread_id}})



def build_question_response(thread_id: str, state: dict) -> dict:
    return {
        "thread_id": thread_id,
        "status": state.get("status", "collecting"),
        "question_count": state.get("question_count", 0),
        "current_question": state.get("current_question", ""),
        "question_number": state.get("question_count", 0) + 1,
        "total_questions": 5,
        "next": state.get("next", "")
    }


@app.post("/sessions/start")
def start_session(req: StartSessionRequest):
    thread_id = str(uuid.uuid4())
    return {"thread_id": thread_id, "patient_name": req.patient_name}


@app.post("/consultation/start")
def start_consultation(req: StartConsultationRequest):
    config = get_config(req.thread_id)
    initial_state = {
        "patient_initial_case": req.initial_case,
        "question_count": 0,
        "patient_answers": [],
        "status": "collecting",
        "messages": []
    }
    try:
        graph.invoke(initial_state, config)
        state = get_state(req.thread_id).values
        return build_question_response(req.thread_id, state)
    except Exception as e:
        logger.error(f"Error starting consultation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/consultation/resume")
def resume_consultation(req: ResumeConsultationRequest):
    config = get_config(req.thread_id)
    try:
        snapshot = get_state(req.thread_id)
        if not snapshot or not snapshot.values:
            raise HTTPException(status_code=404, detail="Session non trouvée")

        state = snapshot.values

        # ── Physician submits treatment ──────────────────────────────────────
        if req.physician_treatment:
            graph.update_state(config, {"physician_treatment": req.physician_treatment})
            graph.invoke(None, config)
            new_state = get_state(req.thread_id).values
            return {
                "thread_id": req.thread_id,
                "status": new_state.get("status", "complete"),
                "final_report": new_state.get("final_report", "")
            }

        # ── Patient answers a question ───────────────────────────────────────
        if req.answer is not None:
            current_answers = list(state.get("patient_answers", []))
            current_answers.append(req.answer)
            new_count = state.get("question_count", 0) + 1

            graph.update_state(config, {
                "patient_answers": current_answers,
                "question_count": new_count
            })

            graph.invoke(None, config)
            new_state = get_state(req.thread_id).values

            # All 5 answers collected → diagnostic summary ready
            if new_state.get("status") == "awaiting_physician":
                return {
                    "thread_id": req.thread_id,
                    "status": "awaiting_physician",
                    "question_count": new_state.get("question_count", 0),
                    "diagnostic_summary": new_state.get("diagnostic_summary", ""),
                    "interim_care": new_state.get("interim_care", ""),
                    "next": new_state.get("next", "")
                }

            # Still collecting questions
            return build_question_response(req.thread_id, new_state)

        raise HTTPException(status_code=400, detail="Fournir 'answer' ou 'physician_treatment'")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/consultation/{thread_id}")
def get_consultation(thread_id: str):
    try:
        snapshot = get_state(thread_id)
        if not snapshot or not snapshot.values:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        state = snapshot.values
        return {
            "thread_id": thread_id,
            "status": state.get("status", ""),
            "question_count": state.get("question_count", 0),
            "patient_initial_case": state.get("patient_initial_case", ""),
            "patient_answers": state.get("patient_answers", []),
            "current_question": state.get("current_question", ""),
            "diagnostic_summary": state.get("diagnostic_summary", ""),
            "interim_care": state.get("interim_care", ""),
            "physician_treatment": state.get("physician_treatment", ""),
            "next": state.get("next", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/consultation/{thread_id}/report")
def get_report(thread_id: str):
    try:
        snapshot = get_state(thread_id)
        if not snapshot or not snapshot.values:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        state = snapshot.values
        final_report = state.get("final_report", "")
        if not final_report:
            raise HTTPException(status_code=404, detail="Rapport non encore généré")
        return {"thread_id": thread_id, "final_report": final_report, "status": "complete"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "service": "Medical Multi-Agent System"}
