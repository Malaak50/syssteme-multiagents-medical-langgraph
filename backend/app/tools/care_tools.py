from langchain_core.tools import tool


@tool
def recommend_interim_care(symptoms_summary: str) -> str:
    """
    Génère une recommandation intermédiaire prudente basée sur le résumé des symptômes.
    Cette recommandation est générale et ne remplace pas un avis médical.
    """
    base_recommendations = [
        "Repos suffisant et éviter les efforts physiques intenses.",
        "Hydratation adéquate (au moins 1,5 à 2 litres d'eau par jour).",
        "Surveillance régulière des symptômes et de la température.",
        "Consulter rapidement un médecin en cas d'aggravation des symptômes.",
        "Éviter l'automédication sans avis médical."
    ]

    red_flags = [
        "difficultés respiratoires",
        "douleur thoracique",
        "perte de conscience",
        "confusion",
        "fièvre élevée",
        "saignement",
        "paralysie",
        "convulsion"
    ]

    summary_lower = symptoms_summary.lower()
    has_red_flags = any(flag in summary_lower for flag in red_flags)

    if has_red_flags:
        urgent = "⚠️ ATTENTION : Des signes potentiellement graves ont été détectés. Consultation médicale urgente recommandée (appeler le 15 ou se rendre aux urgences si nécessaire).\n\n"
        return urgent + "Recommandations en attendant la consultation :\n" + "\n".join(f"• {r}" for r in base_recommendations)

    return (
        "Recommandations intermédiaires générales (en attendant la consultation médicale) :\n"
        + "\n".join(f"• {r}" for r in base_recommendations)
        + "\n\n⚠️ Ces recommandations sont générales et ne remplacent pas une consultation médicale."
    )
