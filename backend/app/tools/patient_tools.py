from langchain_core.tools import tool
from typing import Optional

DIAGNOSTIC_QUESTIONS = [
    "Quels sont vos symptômes principaux et depuis combien de temps les ressentez-vous ?",
    "Avez-vous de la fièvre ? Si oui, quelle est votre température ?",
    "Avez-vous des antécédents médicaux connus (maladies chroniques, allergies, chirurgies) ?",
    "Prenez-vous actuellement des médicaments ? Si oui, lesquels ?",
    "Avez-vous remarqué d'autres signes associés (douleurs, difficultés respiratoires, nausées, vertiges) ?"
]


@tool
def ask_patient_question(question_index: int) -> str:
    """Retourne la question à poser au patient selon l'index (0 à 4)."""
    if 0 <= question_index < len(DIAGNOSTIC_QUESTIONS):
        return DIAGNOSTIC_QUESTIONS[question_index]
    return "Toutes les questions ont été posées."


@tool
def get_all_questions() -> list:
    """Retourne la liste complète des 5 questions diagnostiques."""
    return DIAGNOSTIC_QUESTIONS
