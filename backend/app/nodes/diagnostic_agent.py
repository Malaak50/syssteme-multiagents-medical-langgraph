from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from app.state import MedicalState
from app.tools.patient_tools import DIAGNOSTIC_QUESTIONS
from app.tools.care_tools import recommend_interim_care
from app.tools.mcp_client import call_mcp_sync
import logging

logger = logging.getLogger(__name__)

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)


def diagnostic_agent_node(state: MedicalState) -> MedicalState:
    question_count = state.get("question_count", 0)
    patient_answers = state.get("patient_answers", [])
    patient_initial_case = state.get("patient_initial_case", "")

    if question_count >= 5 and len(patient_answers) >= 5:
        summary = _produce_diagnostic_summary(patient_initial_case, patient_answers)
        interim = _produce_interim_care(summary)
        return {**state, "diagnostic_summary": summary, "interim_care": interim, "status": "awaiting_physician"}

    if question_count < len(DIAGNOSTIC_QUESTIONS):
        current_question = DIAGNOSTIC_QUESTIONS[question_count]
        logger.info(f"DiagnosticAgent question {question_count + 1}/5")
        return {**state, "current_question": current_question, "status": "collecting"}

    return state


def _produce_diagnostic_summary(initial_case: str, answers: list) -> str:
    qa_text = ""
    for i, (q, a) in enumerate(zip(DIAGNOSTIC_QUESTIONS, answers), 1):
        qa_text += f"\nQuestion {i}: {q}\nRéponse: {a}\n"

    mcp_context = call_mcp_sync("get_medical_context", {"symptoms": initial_case + " " + str(answers)})
    mcp_section = f"\n\nContexte médical additionnel (MCP): {mcp_context}" if mcp_context else ""

    system_prompt = """Tu es un assistant médical académique. Tu dois produire une SYNTHÈSE CLINIQUE PRÉLIMINAIRE
basée sur les informations recueillies. IMPORTANT:
- N'émets PAS de diagnostic définitif
- Utilise les termes: "orientation clinique préliminaire", "synthèse clinique", "recommandation intermédiaire"
- Reste prudent et factuel
- Structure ta réponse avec: Présentation, Symptômes rapportés, Points d'attention, Orientation préliminaire
- Rappelle toujours que cette synthèse ne remplace pas une consultation médicale"""

    user_prompt = f"""Cas initial du patient: {initial_case}

Entretien diagnostique:
{qa_text}{mcp_section}

Produis une synthèse clinique préliminaire structurée."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    return response.content


def _produce_interim_care(summary: str) -> str:
    return recommend_interim_care.invoke({"symptoms_summary": summary})
