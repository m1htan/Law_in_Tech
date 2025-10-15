from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import os
import json
from crawlers.crawl4ai_runner import run_crawl
from utils.scd import scd2_upsert_many

class State(BaseModel):
    seeds: List[str] = Field(default_factory=list)
    docs: List[Dict[str, Any]] = Field(default_factory=list)

def seed_node(state: Dict) -> Dict:
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "seeds.json"))
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Không tìm thấy file cấu hình seeds.json tại: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        state["seeds"] = json.load(f)
    return state

def crawl_node(state: Dict) -> Dict:
    docs = run_crawl(state["seeds"])
    state["docs"] = docs
    return state

def store_node(state: Dict) -> Dict:
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs", "jsonl"))
    os.makedirs(out_dir, exist_ok=True)
    scd2_upsert_many(state["docs"], out_dir=out_dir)
    return state

graph = StateGraph(dict)
graph.add_node("seed", seed_node)
graph.add_node("crawl", crawl_node)
graph.add_node("store", store_node)

graph.set_entry_point("seed")
graph.add_edge("seed","crawl")
graph.add_edge("crawl","store")
graph.add_edge("store", END)

app = graph.compile()

if __name__ == "__main__":
    state = {}
    app.invoke(state)
    import logging
    logging.basicConfig(level=logging.INFO)
    print("[DEBUG] starting crawl...")
    print("DONE")
