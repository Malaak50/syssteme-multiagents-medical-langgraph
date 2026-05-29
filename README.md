#  Système Multi-Agents Médical

> **Projet académique** — Système d'orientation clinique préliminaire basé sur LangGraph, LangChain, FastAPI, MCP et Streamlit.
>


---

## Architecture

```
medical_project/
├── backend/
│   ├── app/
│   │   ├── graph.py              # Graphe LangGraph principal
│   │   ├── state.py              # MedicalState (TypedDict partagé)
│   │   ├── api.py                # FastAPI routes
│   │   ├── nodes/
│   │   │   ├── supervisor.py     # Orchestre le workflow
│   │   │   ├── diagnostic_agent.py  # 5 questions + synthèse LLM
│   │   │   ├── physician_review.py  # HITL médecin
│   │   │   └── report_agent.py   # Rapport final structuré
│   │   └── tools/
│   │       ├── patient_tools.py  # Tool ask_patient
│   │       ├── care_tools.py     # Tool recommend_interim_care
│   │       └── mcp_client.py     # Client MCP server
│   ├── main.py
│   ├── langgraph.json            # Config LangGraph Studio
│   ├── Dockerfile
│   └── requirements.txt
├── mcp_server/
│   ├── server.py                 # Serveur MCP (FastAPI)
│   └── Dockerfile
├── frontend/
│   ├── app.py                    # Interface Streamlit (4 écrans)
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Workflow LangGraph

```
START → Supervisor → DiagnosticAgent
                         ↓
                  [Tool: ask_patient × 5]
                         ↓
               [Tool: recommend_interim_care]
                         ↓
                     Supervisor
                         ↓
               PhysicianReview ← ⏸ HITL interrupt
                         ↓
                     Supervisor
                         ↓
                    ReportAgent
                         ↓
                     Supervisor → END
```

**Human-in-the-Loop :** LangGraph interrompt le graphe avant le nœud `physician_review` grâce à `interrupt_before=["physician_review"]`. L'API `/consultation/resume` avec `physician_treatment` reprend l'exécution via `graph.update_state()`.

---

## Installation

### Prérequis
- Python 3.11+
- Clé API Anthropic

### Installation manuelle

```bash
# 1. Cloner / décompresser le projet
cd medical_project

# 2. Configurer la clé API
cp backend/.env.example backend/.env
# Éditer backend/.env et renseigner ANTHROPIC_API_KEY

# 3. Installer le backend
cd backend
pip install -r requirements.txt
cd ..

# 4. Installer le frontend
cd frontend
pip install -r requirements.txt
cd ..
```

### Lancement (3 terminaux)

**Terminal 1 — MCP Server (port 8001) :**
```bash
cd mcp_server
pip install fastapi uvicorn
python server.py
```

**Terminal 2 — Backend FastAPI (port 8000) :**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 3 — Frontend Streamlit (port 8501) :**
```bash
cd frontend
streamlit run app.py
```

Ouvrir : http://localhost:8501

---

### Lancement avec Docker

```bash
# Créer backend/.env avec votre clé API
echo "ANTHROPIC_API_KEY=sk-ant-..." > backend/.env

docker-compose up --build
```

Services :
- Frontend : http://localhost:8501
- Backend API : http://localhost:8000
- MCP Server : http://localhost:8001
- Docs API : http://localhost:8000/docs

---

## API FastAPI

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/sessions/start` | Créer une session |
| POST | `/consultation/start` | Démarrer avec le cas initial |
| POST | `/consultation/resume` | Répondre (patient ou médecin) |
| GET | `/consultation/{thread_id}` | État de la consultation |
| GET | `/consultation/{thread_id}/report` | Rapport final |
| GET | `/health` | Santé du service |

### Exemple complet (curl)

```bash
# 1. Créer session
SESSION=$(curl -s -X POST http://localhost:8000/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"patient_name": "Test"}' | python -c "import sys,json; print(json.load(sys.stdin)['thread_id'])")

# 2. Démarrer consultation
curl -s -X POST http://localhost:8000/consultation/start \
  -H "Content-Type: application/json" \
  -d "{\"thread_id\": \"$SESSION\", \"initial_case\": \"Toux sèche depuis 3 jours avec fièvre à 38.5°C\"}"

# 3. Répondre aux 5 questions (répéter pour chaque)
curl -s -X POST http://localhost:8000/consultation/resume \
  -H "Content-Type: application/json" \
  -d "{\"thread_id\": \"$SESSION\", \"answer\": \"Toux sèche, fièvre 38.5°C depuis 3 jours\"}"

# ... (répéter 4 fois de plus)

# 4. Intervention médecin
curl -s -X POST http://localhost:8000/consultation/resume \
  -H "Content-Type: application/json" \
  -d "{\"thread_id\": \"$SESSION\", \"physician_treatment\": \"Repos 5 jours, paracétamol, réévaluation 48h\"}"

# 5. Récupérer le rapport
curl -s http://localhost:8000/consultation/$SESSION/report
```

---

## LangGraph Studio

```bash
cd backend
pip install langgraph-cli
langgraph dev
```

Ouvrir http://localhost:8123 pour visualiser et tester le graphe.

Le fichier `langgraph.json` pointe vers `app/graph.py:graph`.

---

## Jeux de tests

### Cas 1 — Syndrome respiratoire simple
- Initial : "Toux sèche depuis 3 jours, fièvre 38°C, fatigue modérée"
- Q1: "Toux sèche et rhume depuis 3 jours" | Q2: "Oui, 38°C" | Q3: "Aucun antécédent" | Q4: "Aucun médicament" | Q5: "Légère fatigue, pas de dyspnée"

### Cas 2 — Red flags (urgence)
- Initial : "Douleur thoracique intense depuis 1h avec difficultés respiratoires"
- Vérifier : système doit détecter les red flags et recommander consultation urgente

### Cas 3 — Cas bénin
- Initial : "Rhume banal avec nez qui coule depuis 2 jours, pas de fièvre"

---

## Critères d'évaluation couverts

| Critère | Implémentation |
|---------|---------------|
| Architecture LangGraph | `graph.py` — StateGraph avec Supervisor, 4 nœuds |
| Agents et tools | DiagnosticAgent (ask_patient, interim_care), ReportAgent |
| Human-in-the-Loop | `interrupt_before=["physician_review"]` + `update_state()` |
| FastAPI | 5 endpoints REST, CORS, documentation Swagger auto |
| MCP | Serveur MCP dédié (port 8001), client dans `tools/mcp_client.py` |
| Frontend | Streamlit 4 écrans (cas, questions, médecin, rapport) |
| LangGraph Studio | `langgraph.json` configuré |
| Docker | `docker-compose.yml` complet |

---

## Technologies

- **LangGraph** `>=0.2` — Orchestration multi-agents avec HITL


- **LangChain + Anthropic** — `claude-sonnet-4-20250514`
- **FastAPI** — API REST avec documentation automatique
- **MCP** — Serveur d'outils médicaux additionnels
- **Streamlit** — Interface utilisateur 4 écrans
![Diagramme LangGraph 1](https://raw.githubusercontent.com/Malaak50/syssteme-multiagents-medical-langgraph/main/langgraph1.png)
![Diagramme LangGraph 2](https://raw.githubusercontent.com/Malaak50/syssteme-multiagents-medical-langgraph/main/langgraph2.png)

---

*Projet académique — Pr. Mohamed YOUSSFI — Ne pas utiliser à des fins médicales réelles.*
# Syst-me-multi-agents-m-dical-avec-LangGraph
