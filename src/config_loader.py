import os
import yaml
from dotenv import load_dotenv

def load_config(path: str = "../config/config.yaml") -> dict:
    load_dotenv(override=False)
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # Inject env overrides
    cfg["database"]["postgres_uri"] = os.getenv("POSTGRES_URI", cfg["database"]["postgres_uri"])
    cfg["database"]["sqlite_path"] = os.getenv("SQLITE_PATH", cfg["database"]["sqlite_path"])
    cfg.setdefault("models", {})
    cfg["models"]["embedding"] = os.getenv("EMBEDDING_MODEL", cfg["models"].get("embedding", "e5-large-v2"))
    return cfg
