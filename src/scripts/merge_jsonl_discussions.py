# -*- coding: utf-8 -*-
# Chạy: python src/scripts/merge_jsonl_discussions.py
import os, json, glob
import pandas as pd
from pathlib import Path

IN_DIR = "outputs/jsonl"
OUT_FLAT_CSV = "outputs/discussions/index_merged_flat.csv"
OUT_PARQUET  = "outputs/discussions/index_merged_flat.parquet"

def main():
    rows = []
    for fp in glob.glob(os.path.join(IN_DIR, "*.jsonl")):
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                rows.append(d)
    if not rows:
        print("No rows.")
        return
    df = pd.json_normalize(rows)
    os.makedirs(os.path.dirname(OUT_FLAT_CSV), exist_ok=True)
    df.to_csv(OUT_FLAT_CSV, index=False)
    try:
        df.to_parquet(OUT_PARQUET, index=False)
    except Exception:
        pass
    print("Saved:", OUT_FLAT_CSV)
    print("Saved:", OUT_PARQUET)

if __name__ == "__main__":
    main()