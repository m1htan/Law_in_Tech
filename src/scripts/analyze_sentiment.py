# src/scripts/analyze_sentiment.py
# Chạy:  python src/scripts/analyze_sentiment.py

import os, re, json
from typing import List, Dict, Optional
import pandas as pd
from tqdm import tqdm
from collections import Counter

# ========================
# CẤU HÌNH CỨNG
# ========================
INPUT_CSV  = "../../outputs/discussions/index_merged_flat.csv"  # file CSV phẳng
OUTDIR     = "../../outputs/sentiment"                          # thư mục xuất kết quả
MODEL      = "hf"                                               # "underthesea" hoặc "hf"
HF_MODEL   = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
VOTE_THRESHOLD = 0.3
MAX_LEN_PER_SENT = 180

# ======== Từ vựng cảm xúc ========
POS_CUES = {
    "tích cực","khuyến khích","thuận lợi","giảm gánh nặng","minh bạch hơn",
    "hỗ trợ","được lợi","cơ hội","cải thiện","hài lòng","hoan nghênh","đột phá", "thuận tiện","giảm thủ tục","đơn giản hóa","tạo điều kiện","khơi thông","thúc đẩy"
}
NEG_CUES = {
    "bất cập","vướng mắc","gây khó","lo ngại","phản đối","chồng chéo",
    "thiếu rõ ràng","tăng chi phí","khó khăn","thiếu minh bạch","rủi ro","bất ổn", "bị phạt","thiếu khả thi","đi ngược","làm khó","đình trệ","điểm nghẽn","khiếu nại"
}

# ======== Import tùy chọn ========
HF_AVAILABLE = True
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
except Exception:
    HF_AVAILABLE = False

UTS_AVAILABLE = True
try:
    from underthesea import sentiment as uts_sentiment
except Exception:
    UTS_AVAILABLE = False

# ======== Tiền xử lý ========
def normalize_text(s: Optional[str]) -> str:
    if not isinstance(s, str):
        return ""
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def split_sentences(txt: str) -> List[str]:
    parts = re.split(r"[.!?;\n]+", txt)
    return [p.strip() for p in parts if len(p.strip()) > 2]

def looks_english(s: str, ratio: float = 0.85) -> bool:  # nới lỏng
    letters = [c for c in s if c.isalpha()]
    if not letters: return False
    ascii_letters = sum(1 for c in letters if ord(c) < 128)
    return ascii_letters / max(1, len(letters)) > ratio

def noisy_or_quote(s_lower: str) -> bool:
    return any([
        s_lower.startswith(("theo ", "tại ", "căn cứ ", "ngày ")),
        s_lower.startswith(("bộ ", "ủy ban", "chính phủ", "thủ tướng")),
        s_lower.startswith(("“","\"", "''", "'"))
    ])

def contains_lexicon(s: str, lexicon: set) -> bool:
    t = s.lower()
    return any(k in t for k in lexicon)

def lexicon_boost(text: str, base_label: str) -> str:
    t = text.lower()
    def cnt(t, lex): return sum(t.count(k) for k in lex)
    pos_cnt = cnt(t, POS_CUES)
    neg_cnt = cnt(t, NEG_CUES)
    if pos_cnt >= max(1, int(1.2 * max(1, neg_cnt))):
        return "positive"
    if neg_cnt >= max(1, int(1.2 * max(1, pos_cnt))):
        return "negative"
    return base_label

# ======== Bộ phân loại ========
class UndertheseaClassifier:
    name = "underthesea"
    def __init__(self):
        if not UTS_AVAILABLE:
            raise RuntimeError("underthesea chưa cài. pip install underthesea")
    def predict_label(self, text: str) -> str:
        try:
            return uts_sentiment(text)
        except Exception:
            return "neutral"

class HFClassifier:
    name = "hf"
    def __init__(self, model_name: str):
        if not HF_AVAILABLE:
            raise RuntimeError("transformers chưa cài. pip install transformers torch")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            # return_all_scores=True để lấy đủ score
            self.pipe = TextClassificationPipeline(model=self.model, tokenizer=self.tokenizer, top_k=None, return_all_scores=True)
            self.model_name = model_name
        except Exception as e:
            raise RuntimeError(f"Không tải được mô hình HF '{model_name}'. Lỗi: {e}")

    @staticmethod
    def _map(raw: str) -> str:
        r = str(raw).lower()
        if "pos" in r or r == "positive": return "positive"
        if "neg" in r or r == "negative": return "negative"
        return "neutral"

    def predict_label(self, text: str) -> str:
        # Giữ để tương thích (không dùng score)
        try:
            out = self.pipe(text[:512])[0]
            # out là list [{'label':'negative','score':...}, ...]
            top = max(out, key=lambda x: x["score"])
            return self._map(top["label"])
        except Exception:
            return "neutral"

    def predict_scores(self, text: str) -> dict:
        """Trả về dict {'positive': p, 'neutral': p, 'negative': p}"""
        try:
            out = self.pipe(text[:512])[0]
            d = { self._map(x["label"]): float(x["score"]) for x in out }
            # Bảo đảm đủ 3 nhãn
            for k in ("positive","neutral","negative"):
                d.setdefault(k, 0.0)
            # Chuẩn hóa tổng = 1 (phòng trường hợp rounding)
            s = sum(d.values()) or 1.0
            return {k: v/s for k,v in d.items()}
        except Exception:
            return {"positive":0.0,"neutral":1.0,"negative":0.0}

class LexiconOnlyClassifier:
    name = "lexicon"
    def predict_label(self, text: str) -> str:
        return lexicon_boost(text, "neutral")

# ======== Chấm theo câu + voting + lexicon boost ========
def analyze_sent_piecewise(text: str, clf) -> str:
    text = normalize_text(text)
    if not text: return "neutral"
    if looks_english(text):  # vẫn bỏ qua tiếng Anh rõ rệt
        return "neutral"

    # --- tách title & snippet: title = trước dấu chấm đầu tiên
    parts = text.split(". ", 1)
    title_txt = parts[0]
    snippet_txt = parts[1] if len(parts) > 1 else ""

    # tham số
    title_weight = 2.0
    max_len = MAX_LEN_PER_SENT
    vote_th = VOTE_THRESHOLD

    # gom câu
    sents = []
    for sen in split_sentences(title_txt):
        sents.append(("title", sen))
    for sen in split_sentences(snippet_txt):
        sents.append(("snippet", sen))

    # tích lũy xác suất
    acc = {"positive":0.0,"neutral":0.0,"negative":0.0}
    valid = 0

    for src, sen in sents:
        if len(sen) > max_len: continue
        s_lower = sen.lower()
        if noisy_or_quote(s_lower): continue

        if hasattr(clf, "predict_scores"):
            scores = clf.predict_scores(sen)
            top_label = max(scores, key=scores.get)
            top_conf = scores[top_label]
        else:
            lbl = clf.predict_label(sen)
            scores = {"positive":0.0,"neutral":0.0,"negative":0.0}
            scores[lbl] = 1.0
            top_label, top_conf = lbl, 1.0

        w = title_weight if src=="title" else 1.0

        # nếu tự tin thấp (<0.55), cho lexicon “đẩy” nhẹ câu đó
        if top_conf < 0.55:
            boosted = lexicon_boost(sen, top_label)
            if boosted != top_label:
                # tăng biên độ 0.15 cho nhãn boosted
                scores[boosted] = min(1.0, scores.get(boosted,0)+0.15)

        # cộng dồn có trọng số
        for k in acc:
            acc[k] += w * scores.get(k,0.0)
        valid += 1

    if valid == 0:
        label = "neutral"
    else:
        # chuẩn hóa & quyết định
        s = sum(acc.values()) or 1.0
        pos_r = acc["positive"]/s
        neg_r = acc["negative"]/s
        # Ngưỡng cực trị mềm
        if max(pos_r, neg_r) >= vote_th:
            label = "positive" if pos_r >= neg_r else "negative"
        else:
            label = "neutral"

    # cuộn lần cuối theo lexicon toàn văn
    return lexicon_boost(text, label)

# ======== Tổng hợp theo văn bản ========
def summarize_by_doc(df_pred: pd.DataFrame) -> pd.DataFrame:
    g = (df_pred.groupby("doc_id")["sentiment"]
         .value_counts(normalize=True)
         .unstack(fill_value=0)
         .reset_index())
    g["sentiment_score"] = g.get("positive", 0) - g.get("negative", 0)
    def categorize(row):
        if row["sentiment_score"] > 0.2: return "good"
        if row["sentiment_score"] < -0.2: return "bad"
        return "neutral"
    g["category"] = g.apply(categorize, axis=1)
    return g.sort_values("sentiment_score", ascending=False)

# ======== Đánh giá proxy ========
def evaluate_proxy(df_pred: pd.DataFrame) -> Dict[str, float]:
    non_neutral = (df_pred["sentiment"] != "neutral").mean()
    text_all = (df_pred["title"].fillna("") + " " + df_pred["snippet"].fillna("")).str.lower()
    has_pos = text_all.apply(lambda s: contains_lexicon(s, POS_CUES))
    has_neg = text_all.apply(lambda s: contains_lexicon(s, NEG_CUES))
    pos_subset = df_pred[has_pos]
    neg_subset = df_pred[has_neg]
    pos_precision = (pos_subset["sentiment"] == "positive").mean() if len(pos_subset) else None
    neg_precision = (neg_subset["sentiment"] == "negative").mean() if len(neg_subset) else None
    return {
        "non_neutral_rate": round(float(non_neutral), 4),
        "pos_precision_on_pos_lexicon": None if pos_precision is None else round(float(pos_precision), 4),
        "neg_precision_on_neg_lexicon": None if neg_precision is None else round(float(neg_precision), 4),
        "pos_lexicon_support": int(len(pos_subset)),
        "neg_lexicon_support": int(len(neg_subset)),
    }

def main():
    os.makedirs(OUTDIR, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)
    if "title" not in df.columns or "snippet" not in df.columns:
        raise ValueError("CSV cần có cột 'title' và 'snippet'.")
    df["text"] = (df["title"].fillna("") + ". " + df["snippet"].fillna("")).apply(normalize_text)

    # Dùng biến cục bộ để tránh làm MODEL thành biến local bị “dùng trước khi gán”
    model_choice = MODEL
    clf = None

    if model_choice == "hf":
        try:
            clf = HFClassifier(HF_MODEL)
        except Exception as e:
            print(f"[WARN] HF model lỗi: {e}. Fallback sang underthesea.")
            model_choice = "underthesea"

    if clf is None and model_choice == "underthesea":
        try:
            clf = UndertheseaClassifier()
        except Exception as e:
            print(f"[WARN] underthesea lỗi: {e}. Fallback sang lexicon-only.")
            clf = LexiconOnlyClassifier()

    if clf is None:
        clf = LexiconOnlyClassifier()

    tqdm.pandas(desc=f"Scoring with {clf.name}")
    df["sentiment"] = df["text"].progress_apply(lambda s: analyze_sent_piecewise(s, clf))

    # Lấy confidence nhanh cho một số dòng để debug
    def top_confidence(text):
        if hasattr(clf, "predict_scores"):
            sc = clf.predict_scores(text)
            lbl = max(sc, key=sc.get);
            conf = sc[lbl]
            return lbl, round(conf, 3)
        else:
            return "n/a", 1.0

    df[["pred_label_raw", "pred_conf"]] = df["text"].apply(
        lambda t: pd.Series(top_confidence(t))
    )

    out_pred = os.path.join(OUTDIR, "sentiment_results.csv")
    df.to_csv(out_pred, index=False)

    summary = summarize_by_doc(df)
    out_summary = os.path.join(OUTDIR, "sentiment_results_summary.csv")
    summary.to_csv(out_summary, index=False)

    proxy = evaluate_proxy(df)
    out_eval = os.path.join(OUTDIR, "sentiment_eval.json")
    with open(out_eval, "w", encoding="utf-8") as f:
        json.dump({"model": clf.name, "proxy": proxy}, f, ensure_ascii=False, indent=2)

    print("Saved:", out_pred)
    print("Saved:", out_summary)
    print("Saved:", out_eval)
    print("Proxy evaluation:", json.dumps(proxy, ensure_ascii=False))

if __name__ == "__main__":
    main()