from typing import List, Dict, Any, Optional, TypedDict
from datetime import datetime

class AgentState(TypedDict, total=False):
    run_id: str
    config: Dict[str, Any]
    sources: List[Dict[str, Any]]
    discovered_docs: List[Dict[str, Any]]
    now: datetime