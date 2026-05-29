from app.state import MedicalState
import logging

logger = logging.getLogger(__name__)


def supervisor_node(state: MedicalState) -> MedicalState:
    question_count = state.get("question_count", 0)
    diagnostic_summary = state.get("diagnostic_summary", "")
    physician_treatment = state.get("physician_treatment", "")
    final_report = state.get("final_report", "")

    if final_report:
        next_step = "FINISH"
    elif physician_treatment and diagnostic_summary:
        next_step = "report_agent"
    elif diagnostic_summary and not physician_treatment:
        next_step = "physician_review"
    else:
        next_step = "diagnostic_agent"

    logger.info(f"Supervisor → {next_step}")
    return {**state, "next": next_step}
