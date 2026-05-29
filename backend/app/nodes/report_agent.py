from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from app.state import MedicalState
from app.tools.mcp_client import call_mcp_sync
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

llm = ChatOpenAI(model="gpt-4o", temperature=0.2)


def report_agent_node(state: MedicalState) -> MedicalState:
    patient_initial_case = state.get("patient_initial_case", "")
    diagnostic_summary = state.get("diagnostic_summary", "")
    interim_care = state.get("interim_care", "")
    physician_treatment = state.get("physician_treatment", "")

    mcp_guidelines = call_mcp_sync("get_care_guidelines", {"condition": diagnostic_summary[:200]})
    mcp_section = f"\n\nRecommandations additionnelles (MCP): {mcp_guidelines}" if mcp_guidelines else ""

    system_prompt = """Tu es un assistant médical académique. Génère un RAPPORT MÉDICAL FINAL structuré.
Le rapport DOIT:
1. Commencer par un en-tête avec la date et l'heure
2. Inclure: Présentation du cas, Synthèse clinique préliminaire, Recommandations intermédiaires, Traitement proposé par le médecin, Conclusion et suivi recommandé
3. Se terminer OBLIGATOIREMENT par: "⚠️ Ce système ne remplace pas une consultation médicale. Ce rapport est produit à titre académique uniquement."
4. Être clair, structuré et professionnel"""

    now = datetime.now().strftime("%d/%m/%Y à %H:%M")

    user_prompt = f"""Génère le rapport médical final:

DATE: {now}
CAS INITIAL: {patient_initial_case}

SYNTHÈSE CLINIQUE PRÉLIMINAIRE:
{diagnostic_summary}

RECOMMANDATIONS INTERMÉDIAIRES:
{interim_care}

TRAITEMENT / CONDUITE À TENIR (Médecin traitant):
{physician_treatment}{mcp_section}"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    logger.info(f"ReportAgent: rapport généré ({len(response.content)} chars)")
    return {**state, "final_report": response.content, "status": "complete"}
