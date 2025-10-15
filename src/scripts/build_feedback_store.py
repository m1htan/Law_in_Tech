import os, glob, orjson, csv, re

JSONL_DIR = os.path.abspath(os.path.join("outputs","jsonl"))
OUT_DIR    = os.path.abspath(os.path.join("outputs","feedback"))
os.makedirs(OUT_DIR, exist_ok=True)

EMAIL = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+', re.I)
PHONE = re.compile(r'(\+?84|0)(\d{9,10})\b')

def scrub(s: str) -> str:
    if not s: return s
    s = EMAIL.sub("[email]", s)
    s = PHONE.sub("[phone]", s)
    return s

rows = []
for fp in glob.glob(os.path.join(JSONL_DIR, "*.jsonl")):
    with open(fp, "rb") as f:
        for line in f:
            try:
                rec = orjson.loads(line)
            except:
                continue
            if not rec.get("is_current"):
                continue
            dt = rec.get("du_thao") or {}
            if not dt or not dt.get("dang_lay_y_kien"):
                continue
            lst = dt.get("noi_dung_y_kien") or []
            for c in lst:
                rows.append({
                    "vb_url": rec.get("url"),
                    "so_hieu": rec.get("so_hieu"),
                    "author": (c.get("author") if isinstance(c, dict) else None),
                    "text": scrub(c.get("text") if isinstance(c, dict) else str(c))
                })

# Xuất JSONL
jsonl_path = os.path.join(OUT_DIR, "y_kien.jsonl")
with open(jsonl_path, "wb") as fo:
    for r in rows:
        fo.write(orjson.dumps(r) + b"\n")

# Xuất CSV
csv_path = os.path.join(OUT_DIR, "y_kien.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as fo:
    w = csv.DictWriter(fo, fieldnames=["vb_url","so_hieu","author","text"])
    w.writeheader(); w.writerows(rows)

print(f"OK: {len(rows)} records ->")
print(" -", jsonl_path)
print(" -", csv_path)
