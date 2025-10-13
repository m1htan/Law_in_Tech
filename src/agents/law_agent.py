from typing import Callable
from langgraph.graph import StateGraph
from src.state import AgentState
from src.nodes import load_sources, discover_official_docs

def build_graph() -> Callable[[AgentState], AgentState]:
    g = StateGraph(AgentState)

    g.add_node("LoadSourceRegistry", load_sources.run)
    g.add_node("DiscoverOfficialDocs", discover_official_docs.run)

    g.set_entry_point("LoadSourceRegistry")
    g.add_edge("LoadSourceRegistry", "DiscoverOfficialDocs")

    app = g.compile()
    return app
