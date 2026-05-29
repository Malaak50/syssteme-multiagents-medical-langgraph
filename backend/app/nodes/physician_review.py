from app.state import MedicalState
import logging

logger = logging.getLogger(__name__)


def physician_review_node(state: MedicalState) -> MedicalState:
    """
    PhysicianReview : étape Human-in-the-Loop.
    Ce nœud est interrompu par LangGraph (interrupt_before) pour attendre
    l'intervention manuelle du médecin traitant via l'API.
    Le médecin reçoit la synthèse et propose un traitement ou une conduite à tenir.
    """
    physician_treatment = state.get("physician_treatment", "")

    if not physician_treatment:
        # This state should not be reached normally due to interrupt_before
        # but we handle it gracefully
        logger.warning("PhysicianReview reached without treatment - interrupt should have occurred")
        return {**state, "status": "awaiting_physician"}

    logger.info(f"PhysicianReview: treatment received ({len(physician_treatment)} chars)")
    return {**state, "status": "physician_validated"}
