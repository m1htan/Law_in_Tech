# scripts/build_discussion_index.py
import argparse, glob, json, os
from tqdm import tqdm
from src.pipeline.discussion_miner import mine_discussion_for_file
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_dir", default="../../outputs/pdf", help="Thư mục chứa .txt")
    ap.add_argument("--pattern", default="*.txt")
    ap.add_argument("--out_dir", default="../../outputs/discussions")
    ap.add_argument("--max_results", type=int, default=8)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    out_jsonl = os.path.join(args.out_dir, "index.jsonl")
    out_parquet = os.path.join(args.out_dir, "index.parquet")

    files = sorted(glob.glob(os.path.join(args.input_dir, args.pattern)))
    rows = []
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for p in tqdm(files, desc="Mining"):
            dd = mine_discussion_for_file(p, max_results_per_query=args.max_results)
            # ghi JSONL (mỗi doc 1 record lớn)
            f.write(json.dumps({
                "doc_id": dd.doc_id,
                "doc_path": dd.doc_path,
                "legal_ids": dd.legal_ids,
                "queries": dd.queries,
                "results": dd.results
            }, ensure_ascii=False) + "\n")

            # đồng thời flatten để đổ Parquet
            for r in dd.results:
                rows.append({
                    "doc_id": dd.doc_id,
                    "doc_path": dd.doc_path,
                    "query": r.get("query"),
                    "engine": r.get("engine"),
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "snippet": r.get("snippet"),
                    "published": r.get("published"),
                    "extra": json.dumps(r.get("extra"), ensure_ascii=False) if r.get("extra") else None
                })

    if rows:
        df = pd.DataFrame(rows)
        df.to_parquet(out_parquet, index=False)
        print(f"Saved: {out_jsonl}")
        print(f"Saved: {out_parquet}")
    else:
        print("No results collected.")

if __name__ == "__main__":
    main()
