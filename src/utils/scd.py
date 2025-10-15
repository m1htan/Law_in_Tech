import os, orjson, glob
from datetime import datetime, timezone

def _jsonl_path(out_dir: str, site: str):
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, f"{site}.jsonl")

def scd2_upsert_many(docs, out_dir="outputs/jsonl"):
    # append-only; đóng record cũ (is_current=False) khi gặp content_hash mới cùng “khóa”: (url, so_hieu)
    index = {}
    for d in docs:
        site = d.get("source_site","unknown")
        p = _jsonl_path(out_dir, site)
        _scd2_upsert_one(d, p)

def _scd2_upsert_one(rec, path):
    key = (rec.get("url",""), rec.get("so_hieu",""))
    now = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    rec["record_valid_from"] = rec.get("record_valid_from") or now
    # đọc cũ (stream)
    old = []
    if os.path.exists(path):
        with open(path,"rb") as f:
            for line in f:
                try:
                    oldrec = orjson.loads(line)
                    old.append(oldrec)
                except: pass
    # kiểm tra current
    changed = True
    for o in reversed(old):
        if o.get("is_current") and (o.get("url",""), o.get("so_hieu",""))==key:
            if o.get("content_hash")==rec.get("content_hash"):
                changed = False
            else:
                o["is_current"] = False
                o["record_valid_to"] = now
            break
    # ghi lại
    with open(path,"wb") as f:
        for o in old:
            f.write(orjson.dumps(o)+b"\n")
        if changed:
            f.write(orjson.dumps(rec)+b"\n")
