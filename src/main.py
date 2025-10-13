import uuid
from datetime import datetime
from src.config_loader import load_config
from src.agents.law_agent import build_graph
from src.utils.logger import get_logger

logger = get_logger("main")

def main():
    cfg = load_config("../config/config.yaml")
    app = build_graph()

    initial_state = {
        "run_id": str(uuid.uuid4())[:8],
        "config": cfg,
        "now": datetime.utcnow(),
        "sources": [],
        "discovered_docs": []
    }

    final_state = app.invoke(initial_state)
    docs = final_state.get("discovered_docs", [])
    if not docs:
        logger.info("Không phát hiện văn bản mới (hoặc tất cả đã có trong DB).")
    else:
        logger.info("Danh sách văn bản mới phát hiện (tối đa 20 gần nhất trong DB):")
        # In thêm từ DB để minh họa
        try:
            from src.utils.db import DB
            db = DB(
                primary=cfg["database"]["primary"],
                sqlite_path=cfg["database"]["sqlite_path"],
                postgres_uri=cfg["database"]["postgres_uri"],
            )
            recent = db.list_recent_docs(limit=20)
            for r in recent:
                logger.info(f"- {r.get('title') or '(không tiêu đề)'} | {r.get('url')} | published={r.get('published_at')}")
        except Exception as e:
            logger.warning(f"Lỗi đọc DB: {e}")

if __name__ == "__main__":
    main()
