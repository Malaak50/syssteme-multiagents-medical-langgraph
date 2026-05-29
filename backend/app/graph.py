from langgraph.graph import StateGraph, END
from app.state import MedicalState
from app.nodes.supervisor import supervisor_node
from app.nodes.diagnostic_agent import diagnostic_agent_node
from app.nodes.physician_review import physician_review_node
from app.nodes.report_agent import report_agent_node
from langgraph.checkpoint.memory import InMemorySaver

# Checkpointer mémoire (stocke l'état tant que le serveur tourne)
memory = InMemorySaver()

def route_from_supervisor(state: MedicalState) -> str:
    next_step = state.get("next", "diagnostic_agent")
    if next_step == "FINISH":
        return END
    return next_step

def build_graph():
    workflow = StateGraph(MedicalState)

    # Ajout des agents/nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("diagnostic_agent", diagnostic_agent_node)
    workflow.add_node("physician_review", physician_review_node)
    workflow.add_node("report_agent", report_agent_node)

    # Point d’entrée
    workflow.set_entry_point("supervisor")

    # Routes conditionnelles depuis le superviseur
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "diagnostic_agent": "diagnostic_agent",
            "physician_review": "physician_review",
            "report_agent": "report_agent",
            END: END
        }
    )

    # Boucles de retour vers le superviseur
    workflow.add_edge("diagnostic_agent", "supervisor")
    workflow.add_edge("physician_review", "supervisor")
    workflow.add_edge("report_agent", "supervisor")

    # Compilation avec checkpointer
    graph = workflow.compile(
        checkpointer=memory,
        interrupt_after=["diagnostic_agent"],
        interrupt_before=["physician_review"]
    )

    return graph

# Graphe final utilisé par l’API
graph = build_graph()
