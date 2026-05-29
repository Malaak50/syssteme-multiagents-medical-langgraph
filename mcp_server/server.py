"""
MCP Server - fournit des outils médicaux additionnels via le protocole MCP (HTTP simplifié).
Intégration obligatoire selon le cahier des charges.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import json
import os

app = FastAPI(title="Medical MCP Server", version="1.0.0")

# ─── Medical knowledge base (simplified for demo) ────────────────────────────

MEDICAL_CONTEXTS = {
    "respiratoire": """Contexte médical - Syndrome respiratoire:
- Surveiller la fréquence respiratoire (normale: 12-20/min adulte)
- Signes d'alarme: dyspnée de repos, cyanose, tirage
- SpO2 normale > 95%
- Différentiel: rhinopharyngite, bronchite, pneumonie, asthme""",

    "digestif": """Contexte médical - Troubles digestifs:
- Évaluer hydratation (signes de déshydratation)
- Signes d'alarme: sang dans les selles, douleur intense, fièvre > 38.5°C
- Durée: si > 48h ou aggravation → consultation urgente""",

    "cardiovasculaire": """Contexte médical - Symptômes cardiovasculaires:
- URGENCE si: douleur thoracique + irradiation bras/mâchoire, dyspnée soudaine, palpitations
- Facteurs de risque: HTA, diabète, tabac, antécédents familiaux
- Appel 15 si suspicion syndrome coronarien aigu""",

    "general": """Contexte médical général:
- Évaluation initiale: ABCDE (Airway, Breathing, Circulation, Disability, Exposure)
- Signes vitaux: PA, FC, FR, T°, SpO2
- Antécédents et traitements en cours essentiels
- Orientation selon gravité: médecin traitant / urgences / SAMU"""
}

CARE_GUIDELINES = {
    "default": """Recommandations de soins standards:
1. Repos au lit si fièvre > 38°C
2. Hydratation: 1.5-2L/jour minimum
3. Antipyrétique si T° > 38.5°C (paracétamol en première intention)
4. Surveillance: température 2x/jour, signes d'aggravation
5. Réévaluation médicale si pas d'amélioration à 48h""",

    "respiratoire": """Recommandations - Voies respiratoires:
1. Position semi-assise
2. Humidification de l'air (humidificateur ou bain vapeur prudent)
3. Éviter les irritants (tabac, poussières)
4. Mouchage régulier, lavage nasal sérum physiologique
5. Consultation rapide si: détresse respiratoire, T° > 39.5°C, aggravation rapide"""
}

# ─── Schemas ─────────────────────────────────────────────────────────────────

class ToolCallRequest(BaseModel):
    name: str
    arguments: dict

# ─── Tool implementations ────────────────────────────────────────────────────

def get_medical_context(symptoms: str) -> str:
    symptoms_lower = symptoms.lower()
    if any(w in symptoms_lower for w in ["toux", "respir", "poumon", "bronch", "rhinite", "gorge"]):
        return MEDICAL_CONTEXTS["respiratoire"]
    elif any(w in symptoms_lower for w in ["nausée", "vomiss", "diarrhée", "ventre", "digest"]):
        return MEDICAL_CONTEXTS["digestif"]
    elif any(w in symptoms_lower for w in ["coeur", "thorax", "cardia", "palpita"]):
        return MEDICAL_CONTEXTS["cardiovasculaire"]
    return MEDICAL_CONTEXTS["general"]


def get_care_guidelines(condition: str) -> str:
    condition_lower = condition.lower()
    if any(w in condition_lower for w in ["respir", "toux", "bronch", "rhinite"]):
        return CARE_GUIDELINES["respiratoire"]
    return CARE_GUIDELINES["default"]


def list_available_tools() -> list:
    return [
        {"name": "get_medical_context", "description": "Obtenir le contexte médical pour des symptômes"},
        {"name": "get_care_guidelines", "description": "Obtenir des recommandations de soins"},
    ]

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/tools")
def list_tools():
    return {"tools": list_available_tools()}


@app.post("/tools/call")
def call_tool(req: ToolCallRequest):
    try:
        if req.name == "get_medical_context":
            result = get_medical_context(req.arguments.get("symptoms", ""))
            return {"result": result, "tool": req.name}
        elif req.name == "get_care_guidelines":
            result = get_care_guidelines(req.arguments.get("condition", ""))
            return {"result": result, "tool": req.name}
        else:
            return {"error": f"Tool '{req.name}' not found", "available": [t["name"] for t in list_available_tools()]}
    except Exception as e:
        return {"error": str(e)}


@app.get("/health")
def health():
    return {"status": "ok", "service": "Medical MCP Server"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
