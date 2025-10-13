import os
import yaml
from dotenv import load_dotenv


def _project_root() -> str:
    # /workspace/src -> /workspace
    return os.path.dirname(os.path.dirname(__file__))


def _resolve_project_path(p: str) -> str:
    if not p:
        return p
    if os.path.isabs(p):
        return p
    # Chuẩn hóa các tiền tố ../ hoặc ./ về path tương đối từ project root
    q = p
    while q.startswith("../"):
        q = q[3:]
    while q.startswith("./"):
        q = q[2:]
    return os.path.normpath(os.path.join(_project_root(), q))


def load_config(path: str | None = None) -> dict:
    load_dotenv(override=False)

    # Bỏ qua path được truyền nếu không tuyệt đối; luôn ưu tiên file config chuẩn trong repo
    cfg_path = os.path.join(_project_root(), "config", "config.yaml")
    if path and os.path.isabs(path):
        cfg_path = path

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Inject env overrides
    cfg["database"]["postgres_uri"] = os.getenv("POSTGRES_URI", cfg["database"]["postgres_uri"])
    cfg["database"]["sqlite_path"] = os.getenv("SQLITE_PATH", cfg["database"].get("sqlite_path"))

    # Chuẩn hóa đường dẫn về tuyệt đối theo root
    cfg["data"]["sources_path"] = _resolve_project_path(cfg["data"].get("sources_path", "data/sources.csv"))
    cfg["data"]["storage_dir"] = _resolve_project_path(cfg["data"].get("storage_dir", "data/docs"))
    cfg["database"]["sqlite_path"] = _resolve_project_path(cfg["database"].get("sqlite_path", "data/law_demo.db"))

    cfg.setdefault("models", {})
    cfg["models"]["embedding"] = os.getenv("EMBEDDING_MODEL", cfg["models"].get("embedding", "e5-large-v2"))
    return cfg
