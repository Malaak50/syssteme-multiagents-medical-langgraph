import streamlit as st
import requests
import json
import time

# ─── Config ──────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Système Médical Multi-Agents",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title { font-size: 2rem; font-weight: 700; color: #1a5276; text-align: center; margin-bottom: 0.3rem; }
    .subtitle { text-align: center; color: #7f8c8d; margin-bottom: 2rem; font-size: 0.95rem; }
    .step-badge { 
        background: #eaf2ff; border: 1px solid #3498db; border-radius: 20px; 
        padding: 4px 14px; font-size: 0.8rem; color: #1a5276; font-weight: 600; display: inline-block;
    }
    .status-collecting { color: #2980b9; font-weight: 600; }
    .status-awaiting { color: #e67e22; font-weight: 600; }
    .status-complete { color: #27ae60; font-weight: 600; }
    .question-box { 
        background: #eaf4fb; border-left: 4px solid #3498db; 
        padding: 1rem 1.2rem; border-radius: 4px; margin: 0.8rem 0; 
    }
    .report-box { 
        background: #f0f9f0; border: 1px solid #27ae60; 
        border-radius: 8px; padding: 1.5rem; 
    }
    .warning-box { 
        background: #fef9e7; border-left: 4px solid #f39c12; 
        padding: 0.8rem 1rem; border-radius: 4px; font-size: 0.9rem;
    }
    .physician-box { 
        background: #fdf2f8; border-left: 4px solid #8e44ad;
        padding: 1rem 1.2rem; border-radius: 4px; margin: 0.8rem 0;
    }
    div[data-testid="stProgress"] > div > div { background-color: #3498db; }
</style>
""", unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "thread_id": None,
        "screen": "home",
        "patient_name": "",
        "initial_case": "",
        "question_count": 0,
        "current_question": "",
        "patient_answers": [],
        "diagnostic_summary": "",
        "interim_care": "",
        "physician_treatment": "",
        "final_report": "",
        "status": "",
        "error": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ─── API helpers ─────────────────────────────────────────────────────────────
def api_post(endpoint, data):
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=data, timeout=60)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Impossible de se connecter à l'API. Démarrez le backend (uvicorn main:app)"
    except Exception as e:
        return None, f"Erreur API: {str(e)}"

def api_get(endpoint):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=30)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "❌ Impossible de se connecter à l'API."
    except Exception as e:
        return None, f"Erreur API: {str(e)}"

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 Navigation")
    
    if st.session_state.thread_id:
        st.markdown(f"**Session:** `{st.session_state.thread_id[:8]}...`")
        st.markdown(f"**Patient:** {st.session_state.patient_name or 'N/A'}")
        
        status_map = {
            "collecting": ("🔵 Collecte des données", "status-collecting"),
            "awaiting_physician": ("🟠 Attente médecin", "status-awaiting"),
            "physician_validated": ("🟣 Médecin validé", "status-awaiting"),
            "complete": ("🟢 Consultation terminée", "status-complete")
        }
        s = st.session_state.status
        label, cls = status_map.get(s, (f"• {s}", ""))
        st.markdown(f"**Statut:** {label}")

        if st.session_state.question_count > 0:
            st.markdown(f"**Questions:** {min(st.session_state.question_count, 5)}/5")
            st.progress(min(st.session_state.question_count / 5, 1.0))

    st.markdown("---")
    st.markdown("### Étapes")
    screens = [
        ("home", "1️⃣ Cas initial"),
        ("questions", "2️⃣ Questions patient"),
        ("physician", "3️⃣ Revue médecin"),
        ("report", "4️⃣ Rapport final"),
    ]
    for screen_id, label in screens:
        is_current = st.session_state.screen == screen_id
        icon = "▶️ " if is_current else "   "
        st.markdown(f"{icon}**{label}**" if is_current else f"{icon}{label}")

    st.markdown("---")
    if st.button("🔄 Nouvelle consultation", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown("---")
    st.markdown("##### ⚠️ Avertissement")
    st.caption("Ce système est un exercice académique et ne remplace pas une consultation médicale.")

# ─── SCREEN 1: Home / Cas initial ────────────────────────────────────────────
if st.session_state.screen == "home":
    st.markdown('<div class="main-title">🏥 Système d\'Orientation Clinique</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Système multi-agents médical — LangGraph · FastAPI · MCP<br><em>Projet académique — ne remplace pas une consultation médicale</em></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<span class="step-badge">Étape 1 sur 4</span>', unsafe_allow_html=True)
        st.markdown("### 👤 Informations patient")

        with st.form("start_form"):
            patient_name = st.text_input("Nom du patient (optionnel)", placeholder="Ex: Jean Dupont")
            initial_case = st.text_area(
                "Décrivez votre cas clinique initial *",
                placeholder="Ex: Je ressens depuis 3 jours des douleurs thoraciques et une toux sèche accompagnée de fièvre à 38.5°C...",
                height=150
            )
            submitted = st.form_submit_button("🚀 Démarrer la consultation", use_container_width=True, type="primary")

        if submitted:
            if not initial_case.strip():
                st.error("Veuillez décrire votre cas clinique.")
            else:
                with st.spinner("Création de la session..."):
                    data, err = api_post("/sessions/start", {"patient_name": patient_name or "Patient"})
                    if err:
                        st.error(err)
                    else:
                        thread_id = data["thread_id"]
                        with st.spinner("Démarrage de la consultation..."):
                            cdata, cerr = api_post("/consultation/start", {
                                "thread_id": thread_id,
                                "initial_case": initial_case
                            })
                            if cerr:
                                st.error(cerr)
                            else:
                                st.session_state.thread_id = thread_id
                                st.session_state.patient_name = patient_name or "Patient"
                                st.session_state.initial_case = initial_case
                                st.session_state.question_count = cdata.get("question_count", 0)
                                st.session_state.current_question = cdata.get("current_question", "")
                                st.session_state.status = cdata.get("status", "collecting")
                                st.session_state.screen = "questions"
                                st.rerun()

        st.markdown('<div class="warning-box">⚠️ Ce système est destiné à un usage académique uniquement. Il ne produit pas de diagnostic médical définitif.</div>', unsafe_allow_html=True)

# ─── SCREEN 2: Questions patient ─────────────────────────────────────────────
elif st.session_state.screen == "questions":
    st.markdown('<div class="main-title">💬 Entretien Diagnostique</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<span class="step-badge">Étape 2 sur 4</span>', unsafe_allow_html=True)
        st.markdown(f"**Cas initial:** _{st.session_state.initial_case[:150]}{'...' if len(st.session_state.initial_case) > 150 else ''}_")
    with col2:
        q_num = min(st.session_state.question_count + 1, 5)
        st.metric("Question", f"{q_num} / 5")
        st.progress(st.session_state.question_count / 5)

    # Show previous Q&A
    if st.session_state.patient_answers:
        with st.expander(f"📋 Réponses précédentes ({len(st.session_state.patient_answers)})", expanded=False):
            QUESTIONS = [
                "Symptômes principaux et durée ?",
                "Fièvre ? Température ?",
                "Antécédents médicaux ?",
                "Médicaments actuels ?",
                "Autres signes associés ?"
            ]
            for i, ans in enumerate(st.session_state.patient_answers):
                st.markdown(f"**Q{i+1}:** {QUESTIONS[i] if i < len(QUESTIONS) else '?'}")
                st.markdown(f"> {ans}")

    if st.session_state.status == "awaiting_physician":
        st.success("✅ Toutes les questions ont été posées !")
        st.markdown("**Synthèse clinique préliminaire générée.** Passage à la revue du médecin.")
        
        if st.session_state.diagnostic_summary:
            with st.expander("🔬 Voir la synthèse clinique", expanded=True):
                st.markdown(st.session_state.diagnostic_summary)
        if st.session_state.interim_care:
            with st.expander("💊 Recommandations intermédiaires"):
                st.markdown(st.session_state.interim_care)

        if st.button("➡️ Passer à la revue médecin", type="primary", use_container_width=True):
            st.session_state.screen = "physician"
            st.rerun()
    else:
        # Show current question
        if st.session_state.current_question:
            st.markdown(f'<div class="question-box"><strong>🩺 Question {q_num}/5 :</strong><br><br>{st.session_state.current_question}</div>', unsafe_allow_html=True)

            with st.form("answer_form"):
                answer = st.text_area("Votre réponse", placeholder="Décrivez en détail...", height=120)
                submitted = st.form_submit_button("✅ Valider la réponse", type="primary", use_container_width=True)

            if submitted:
                if not answer.strip():
                    st.error("Veuillez saisir une réponse.")
                else:
                    with st.spinner("Enregistrement..."):
                        rdata, rerr = api_post("/consultation/resume", {
                            "thread_id": st.session_state.thread_id,
                            "answer": answer
                        })
                        if rerr:
                            st.error(rerr)
                        else:
                            st.session_state.patient_answers.append(answer)
                            st.session_state.question_count = rdata.get("question_count", 0)
                            st.session_state.status = rdata.get("status", "collecting")
                            st.session_state.current_question = rdata.get("current_question", "")

                            if rdata.get("status") == "awaiting_physician":
                                st.session_state.diagnostic_summary = rdata.get("diagnostic_summary", "")
                                st.session_state.interim_care = rdata.get("interim_care", "")

                            st.rerun()
        else:
            st.info("Chargement de la prochaine question...")
            time.sleep(1)
            st.rerun()

# ─── SCREEN 3: Physician Review ──────────────────────────────────────────────
elif st.session_state.screen == "physician":
    st.markdown('<div class="main-title">👨‍⚕️ Revue du Médecin Traitant</div>', unsafe_allow_html=True)
    st.markdown('<span class="step-badge">Étape 3 sur 4 — Human-in-the-Loop</span>', unsafe_allow_html=True)
    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔬 Synthèse clinique préliminaire")
        if st.session_state.diagnostic_summary:
            st.markdown(st.session_state.diagnostic_summary)
        else:
            # Fetch from API if not in session
            sdata, serr = api_get(f"/consultation/{st.session_state.thread_id}")
            if sdata:
                st.session_state.diagnostic_summary = sdata.get("diagnostic_summary", "")
                st.session_state.interim_care = sdata.get("interim_care", "")
                st.markdown(st.session_state.diagnostic_summary or "Synthèse non disponible.")

    with col2:
        st.markdown("#### 💊 Recommandations intermédiaires")
        if st.session_state.interim_care:
            st.markdown(st.session_state.interim_care)

    st.markdown("---")
    st.markdown('<div class="physician-box"><strong>👨‍⚕️ Intervention du médecin traitant</strong><br>Après avoir pris connaissance de la synthèse clinique, veuillez indiquer votre traitement ou conduite à tenir.</div>', unsafe_allow_html=True)
    st.markdown("")

    with st.form("physician_form"):
        physician_treatment = st.text_area(
            "Traitement / Conduite à tenir *",
            placeholder="""Ex:
- Repos à domicile pendant 5 jours
- Paracétamol 1g x3/jour si fièvre > 38.5°C
- Amoxicilline 1g x3/jour pendant 7 jours si suspicion bactérienne
- Réévaluation à 48h
- Consultation urgente si aggravation respiratoire""",
            height=200
        )
        col_a, col_b = st.columns(2)
        with col_a:
            submitted = st.form_submit_button("✅ Valider le traitement", type="primary", use_container_width=True)
        with col_b:
            cancel = st.form_submit_button("← Retour aux questions", use_container_width=True)

    if cancel:
        st.session_state.screen = "questions"
        st.rerun()

    if submitted:
        if not physician_treatment.strip():
            st.error("Veuillez saisir le traitement ou la conduite à tenir.")
        else:
            with st.spinner("🔄 Génération du rapport final en cours..."):
                rdata, rerr = api_post("/consultation/resume", {
                    "thread_id": st.session_state.thread_id,
                    "physician_treatment": physician_treatment
                })
                if rerr:
                    st.error(rerr)
                else:
                    st.session_state.physician_treatment = physician_treatment
                    st.session_state.final_report = rdata.get("final_report", "")
                    st.session_state.status = rdata.get("status", "complete")

                    if not st.session_state.final_report:
                        # Try fetching report
                        time.sleep(2)
                        report_data, _ = api_get(f"/consultation/{st.session_state.thread_id}/report")
                        if report_data:
                            st.session_state.final_report = report_data.get("final_report", "")

                    st.session_state.screen = "report"
                    st.rerun()

# ─── SCREEN 4: Final Report ───────────────────────────────────────────────────
elif st.session_state.screen == "report":
    st.markdown('<div class="main-title">📄 Rapport Final</div>', unsafe_allow_html=True)
    st.markdown('<span class="step-badge">Étape 4 sur 4 — Consultation terminée</span>', unsafe_allow_html=True)
    st.success("✅ La consultation est terminée. Le rapport final a été généré.")
    st.markdown("")

    # Fetch report if not in session
    if not st.session_state.final_report:
        rdata, rerr = api_get(f"/consultation/{st.session_state.thread_id}/report")
        if rdata:
            st.session_state.final_report = rdata.get("final_report", "")
        elif rerr:
            st.error(rerr)

    if st.session_state.final_report:
        col1, col2 = st.columns([3, 1])
        with col2:
            st.download_button(
                "⬇️ Télécharger le rapport",
                data=st.session_state.final_report,
                file_name=f"rapport_medical_{st.session_state.thread_id[:8]}.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.markdown('<div class="report-box">', unsafe_allow_html=True)
        st.markdown(st.session_state.final_report)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="warning-box">⚠️ <strong>Ce système ne remplace pas une consultation médicale.</strong> Ce rapport est produit à titre académique uniquement dans le cadre du projet Multi-Agents Médical (LangGraph / FastAPI / MCP).</div>', unsafe_allow_html=True)
    else:
        st.warning("Rapport en cours de génération...")
        if st.button("🔄 Actualiser"):
            st.rerun()

    st.markdown("")
    if st.button("🏠 Nouvelle consultation", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
