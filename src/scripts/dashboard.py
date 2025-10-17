# src/scripts/dashboard.py
import os, re
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
from collections import Counter, defaultdict

# Optional
try:
    import yake
    YAKE_OK = True
except Exception:
    YAKE_OK = False

try:
    import networkx as nx
    NX_OK = True
except Exception:
    NX_OK = False

# ======================
# Config & paths
# ======================
LOCAL_TZ = "Asia/Ho_Chi_Minh"
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SENTENCE_CSV = os.path.join(BASE, "outputs", "sentiment", "sentiment_results.csv")
SUMMARY_CSV  = os.path.join(BASE, "outputs", "sentiment", "sentiment_results_summary.csv")

# ======================
# Utils
# ======================
AGENCY_HINTS = {
    r"\bttg\b": "Thủ tướng Chính phủ",
    r"\bcp\b": "Chính phủ",
    r"\bbkhcn\b": "Bộ KH&CN",
    r"\bbtc\b": "Bộ Tài chính",
    r"\bbqp\b": "Bộ Quốc phòng",
    r"\bbgd&dt\b|\bbgd\b": "Bộ GD&ĐT",
    r"\bmoj\b|\bbtp\b": "Bộ Tư pháp",
    r"\bbcvt\b|\bboxntt\b": "Bộ TT&TT",
    r"\bbkh&dt\b|\bbkhdt\b": "Bộ KH&ĐT",
    r"\bmoit\b|\bbct\b": "Bộ Công Thương",
    r"\bbnn&ptnt\b|\bbnn\b": "Bộ NN&PTNT",
    r"\bgiao thông\b|\bbgtvt\b": "Bộ GTVT",
}
LAW_PAT = re.compile(r"\b(\d{2,4}[-_/]?(ttg|cp|btc|bkhcn|bqp|bgd|moj|btp|bct|moit|bnn|gtvt))\b", re.I)

def to_dt(x):
    """Parse về datetime; convert sang LOCAL_TZ rồi bỏ tz (naive)."""
    dt = pd.to_datetime(x, errors="coerce", utc=True)
    if pd.isna(dt):
        return pd.NaT
    try:
        dt = dt.tz_convert(LOCAL_TZ)
    except Exception:
        try:
            dt = dt.tz_localize("UTC").tz_convert(LOCAL_TZ)
        except Exception:
            pass
    return dt.tz_localize(None)

def guess_agency_from_path(s: str) -> str:
    if not isinstance(s, str): return "Khác/Không rõ"
    s_low = s.lower()
    for pat, lab in AGENCY_HINTS.items():
        if re.search(pat, s_low):
            return lab
    m = re.search(r"[-_/](ttg|cp|btc|bkhcn|bqp|bgd|moj|btp|bct|moit|bnn|gtvt)[-_.]", s_low)
    if m:
        token = m.group(1).upper()
        return {
            "TTG":"Thủ tướng Chính phủ", "CP":"Chính phủ", "BTC":"Bộ Tài chính",
            "BKHCN":"Bộ KH&CN", "BQP":"Bộ Quốc phòng", "BGD":"Bộ GD&ĐT",
            "MOJ":"Bộ Tư pháp", "BCT":"Bộ Công Thương", "MOIT":"Bộ Công Thương",
            "BNN":"Bộ NN&PTNT", "GTVT":"Bộ GTVT"
        }.get(token, "Khác/Không rõ")
    return "Khác/Không rõ"

def extract_law_id(text):
    if not isinstance(text, str): return None
    m = LAW_PAT.search(text.lower())
    return m.group(1).upper() if m else None

def normalize_url(u):
    if not isinstance(u, str): return u
    u = u.strip()
    u = re.sub(r"https?://(www\.)?", "https://", u)
    u = re.sub(r"(\?|&)(utm_[^=]+|fbclid|gclid)=[^&]+", "", u)
    return u.rstrip("?&")

def extract_domain(u):
    m = re.search(r"https?://([^/]+)/", str(u))
    return m.group(1).lower() if m else None

def sentiment_score_map(label: str) -> int:
    l = str(label).lower()
    return 1 if l == "positive" else (-1 if l == "negative" else 0)

def compute_time_agg(df, freq="W", sentiment_col="sentiment"):
    ts = df.copy()
    if ts["published_dt"].isna().all():
        ts["published_dt"] = pd.Timestamp.today().normalize()
    ts["published_dt"] = pd.to_datetime(ts["published_dt"]).dt.tz_localize(None)
    ts = ts.set_index("published_dt").sort_index()
    counts = (
        ts.groupby([pd.Grouper(freq=freq), sentiment_col])
          .size().rename("count").reset_index()
    )
    totals = counts.groupby("published_dt")["count"].sum().rename("total")
    counts = counts.merge(totals, on="published_dt", how="left")
    counts["share"] = counts["count"] / counts["total"].replace(0, np.nan)
    return counts

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv(SENTENCE_CSV)
    df["published_dt"] = df["published"].apply(to_dt) if "published" in df.columns else pd.NaT
    df["agency"] = df["doc_path"].apply(guess_agency_from_path) if "doc_path" in df.columns else "Khác/Không rõ"
    text_cols = [c for c in ["title","snippet"] if c in df.columns]
    df["text_all"] = df[text_cols].fillna("").agg(". ".join, axis=1) if text_cols else ""
    summary = pd.read_csv(SUMMARY_CSV) if os.path.exists(SUMMARY_CSV) else None
    return df, summary

def yake_keywords(documents, topk=10, max_ngram=3, lang="vi"):
    if not YAKE_OK:
        return []
    kw = []
    extractor = yake.KeywordExtractor(lan=lang, n=max_ngram, top=topk)
    for text in documents:
        try:
            for k, s in extractor.extract_keywords(str(text)):
                kw.append((k.strip().lower(), s))
        except Exception:
            continue
    return kw

@st.cache_data(show_spinner=False)
def aggregate_keywords(df, topk_per_doc=8, max_ngram=3):
    pairs = yake_keywords(df["text_all"].tolist(), topk=topk_per_doc, max_ngram=max_ngram)
    if not pairs:
        bag = Counter()
        for t in df["text_all"].fillna(""):
            for w in re.findall(r"[a-zA-ZÀ-ỹ0-9\-]{3,}", str(t).lower()):
                bag[w] += 1
        pairs = [(k, 1.0/max(1,v)) for k,v in bag.most_common(1000)]

    agg = defaultdict(lambda: {"score_sum":0.0, "count":0})
    for k, s in pairs:
        agg[k]["score_sum"] += (1.0 / max(1e-9, s))
        agg[k]["count"]    += 1
    rows = [{"keyword":k, "weight":v["score_sum"], "count":v["count"]} for k,v in agg.items()]
    return pd.DataFrame(rows).sort_values(["weight","count"], ascending=False)

# ======================
# UI
# ======================
st.set_page_config(page_title="Sentiment Dashboard for Legal Discussions", layout="wide")
st.title("📊 Legal Discussion Sentiment Dashboard")

# 1) Load data
df, summary = load_data()

# Bảo đảm tz-naive (phòng case CSV khác nhau)
if df["published_dt"].dtype == "datetime64[ns, UTC]":
    df["published_dt"] = df["published_dt"].dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)
else:
    df["published_dt"] = df["published_dt"].apply(
        lambda x: x.tz_localize(None) if hasattr(x, "tzinfo") and x.tzinfo else x
    )

# 2) Sidebar filters
with st.sidebar:
    st.header("Bộ lọc")
    freq = st.selectbox("Chu kỳ thời gian", ["W (tuần)", "M (tháng)"], index=0)
    freq_code = "W" if freq.startswith("W") else "M"

    agencies = sorted(df["agency"].dropna().unique().tolist())
    sel_agencies = st.multiselect("Đơn vị ban hành", agencies, default=agencies)

    date_min = pd.to_datetime(df["published_dt"].min())
    date_max = pd.to_datetime(df["published_dt"].max())
    if pd.isna(date_min) or pd.isna(date_max):
        date_min, date_max = pd.Timestamp("2020-01-01"), pd.Timestamp.today().normalize()
    date_range = st.date_input("Khoảng thời gian", value=(date_min.date(), date_max.date()))
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        d_from = pd.Timestamp(date_range[0])
        d_to   = pd.Timestamp(date_range[1])
    else:
        d_from, d_to = date_min, date_max

    q = st.text_input("🔎 Tìm trong tiêu đề/snippet", "")

    st.markdown("**Trọng số domain (tùy chọn)**")
    dom_weights_raw = st.text_area(
        "domain=weight (mỗi dòng)",
        value="chinhphu.vn=1.5\nmoj.gov.vn=1.3\nvnexpress.net=1.2",
        help="Ví dụ: domain=trọng_số. Nếu để trống sẽ mặc định 1.0"
    )

    smooth_win = st.slider("Làm mượt (rolling kỳ)", 1, 8, 3)
    topk_kw   = st.slider("Số keyword (top-N)", 20, 300, 80, step=10)
    max_ngram = st.slider("Độ dài n-gram tối đa (keyword)", 1, 4, 3)

# 3) Áp dụng filter cơ bản
mask = df["agency"].isin(sel_agencies)
mask &= (df["published_dt"].fillna(pd.Timestamp("1970-01-01")) >= d_from)
mask &= (df["published_dt"].fillna(pd.Timestamp("2100-01-01")) <= d_to)
df_f = df.loc[mask].copy()

# Search text
if q:
    q_l = q.lower()
    df_f = df_f[df_f["text_all"].str.lower().str.contains(q_l, na=False)]

# Dedup URL
if "url" in df_f.columns:
    df_f["url_norm"] = df_f["url"].apply(normalize_url)
    before = len(df_f)
    df_f = df_f.drop_duplicates(subset=["url_norm"])
    st.caption(f"🔁 Dedup theo URL: {before} → {len(df_f)}")

# Domain weights
dom_weight = {}
for line in dom_weights_raw.splitlines():
    try:
        k,v = line.split("=")
        dom_weight[k.strip()] = float(v.strip())
    except:
        pass

if "url" in df_f.columns and dom_weight:
    df_f["domain"] = df_f["url"].apply(extract_domain)
    df_f["w"] = df_f["domain"].map(dom_weight).fillna(1.0)
else:
    df_f["w"] = 1.0

# Law id filter (sau khi có df_f)
df_f["law_id"] = df_f["doc_path"].apply(extract_law_id) if "doc_path" in df_f.columns else None
with st.sidebar:
    law_ids = sorted(x for x in df_f["law_id"].dropna().unique().tolist())
    sel_law = st.multiselect("Lọc theo mã văn bản", law_ids, default=[])
if sel_law:
    df_f = df_f[df_f["law_id"].isin(sel_law)]

# 4) KPI
k1, k2, k3, k4 = st.columns(4)
non_neutral_rate = (df_f["sentiment"].str.lower()!="neutral").mean() if len(df_f) else 0.0
avg_score = df_f["sentiment"].map({"positive":1,"neutral":0,"negative":-1}).mean() if len(df_f) else 0.0
k1.metric("Tổng bài", f"{len(df_f):,}")
k2.metric("% Non-neutral", f"{non_neutral_rate*100:,.1f}%")
k3.metric("Điểm cảm xúc TB", f"{avg_score:+.3f}")
k4.metric("Số agency", df_f["agency"].nunique())

# 5) Tabs
tab_overview, tab_agency, tab_topics, tab_docs = st.tabs(["📈 Overview","🏛️ Agency","🧭 Topics","📄 Docs"])

# ========== Overview ==========
with tab_overview:
    st.subheader("⏱️ Xu hướng cảm xúc theo thời gian")
    time_agg = compute_time_agg(df_f, freq=freq_code)
    if len(time_agg) == 0:
        st.info("Không có dữ liệu sau khi lọc.")
    else:
        area = alt.Chart(time_agg).mark_area(opacity=0.7).encode(
            x=alt.X("published_dt:T", title="Thời gian"),
            y=alt.Y("share:Q", stack="normalize", title="Tỷ trọng"),
            color=alt.Color("sentiment:N", scale=alt.Scale(scheme="tableau10")),
            tooltip=["published_dt:T","sentiment:N","count:Q","share:Q"]
        ).properties(height=280)
        st.altair_chart(area, use_container_width=True)

        total_line = time_agg.groupby("published_dt")["count"].sum().reset_index()
        total_line["count_smooth"] = total_line["count"].rolling(smooth_win, min_periods=1).mean()
        line = alt.Chart(total_line).mark_line(point=True).encode(
            x=alt.X("published_dt:T", title="Thời gian"),
            y=alt.Y("count:Q", title="Số bài thảo luận"),
            tooltip=["published_dt:T","count:Q"]
        ).properties(height=220)
        line_smooth = alt.Chart(total_line).mark_line(point=True).encode(
            x="published_dt:T",
            y=alt.Y("count_smooth:Q", title="Số bài (làm mượt)"),
            tooltip=["published_dt:T","count:Q","count_smooth:Q"]
        ).properties(height=220)
        st.altair_chart(line | line_smooth, use_container_width=True)

    st.subheader("🏷️ Top văn bản")
    if summary is not None and "sentiment_score" in summary.columns and len(summary):
        c1, c2 = st.columns(2)
        top_bad = summary.nsmallest(10, "sentiment_score")[["doc_id","sentiment_score","negative","neutral","positive"]]
        top_good = summary.nlargest(10, "sentiment_score")[["doc_id","sentiment_score","positive","neutral","negative"]]
        c1.write("**Top 10 Bad**");  c1.dataframe(top_bad, use_container_width=True)
        c2.write("**Top 10 Good**"); c2.dataframe(top_good, use_container_width=True)
    else:
        st.caption("Chưa có summary để hiển thị Top văn bản.")

# ========== Agency ==========
with tab_agency:
    st.subheader("📊 So sánh theo Đơn vị ban hành")
    by_agency = df_f.groupby(["agency","sentiment"]).size().rename("count").reset_index()
    if len(by_agency):
        bars = alt.Chart(by_agency).mark_bar().encode(
            x=alt.X("count:Q", title="Số lượng"),
            y=alt.Y("agency:N", sort="-x", title="Đơn vị ban hành"),
            color=alt.Color("sentiment:N"),
            tooltip=["agency:N","sentiment:N","count:Q"]
        ).properties(height=380)
        st.altair_chart(bars, use_container_width=True)

        # Weighted view
        by_agency_w = (df_f.groupby(["agency","sentiment"])["w"].sum()
                       .rename("wcount").reset_index())
        bars_w = alt.Chart(by_agency_w).mark_bar().encode(
            x=alt.X("wcount:Q", title="Số lượng (có trọng số)"),
            y=alt.Y("agency:N", sort="-x"),
            color=alt.Color("sentiment:N"),
            tooltip=["agency","sentiment","wcount"]
        ).properties(height=380)
        st.altair_chart(bars_w, use_container_width=True)

        # Scatter overview
        sc = df_f.copy()
        sc["score"] = sc["sentiment"].apply(sentiment_score_map)
        sc_ag = sc.groupby("agency").agg(
            total=("sentiment","size"),
            non_neutral=("sentiment", lambda s: np.mean(s.str.lower()!="neutral")),
            sentiment_score=("score","mean"),
        ).reset_index()
        scatter = alt.Chart(sc_ag).mark_circle(size=200).encode(
            x=alt.X("sentiment_score:Q", title="Điểm cảm xúc (pos - neg)"),
            y=alt.Y("non_neutral:Q", title="Tỷ lệ non-neutral"),
            color=alt.Color("agency:N"),
            tooltip=["agency:N","total:Q","sentiment_score:Q","non_neutral:Q"]
        ).properties(height=320)
        st.altair_chart(scatter, use_container_width=True)

        # Drill-down
        st.markdown("### 🔍 Drill-down agency")
        pick = st.selectbox("Chọn agency", ["(tất cả)"] + sorted(df_f["agency"].unique().tolist()))
        df_ag = df_f if pick=="(tất cả)" else df_f[df_f["agency"]==pick]
        agg_ag = compute_time_agg(df_ag, freq=freq_code)
        st.altair_chart(alt.Chart(agg_ag).mark_area(opacity=0.7).encode(
            x="published_dt:T", y=alt.Y("share:Q", stack="normalize"), color="sentiment:N"
        ), use_container_width=True)

        df_kw_ag = aggregate_keywords(df_ag, topk_per_doc=8, max_ngram=3).head(50)
        st.dataframe(df_kw_ag, use_container_width=True, height=300)
    else:
        st.info("Không có số liệu agency sau khi lọc.")

# ========== Topics ==========
with tab_topics:
    st.subheader("🗺️ Bản đồ chủ đề theo keyword")
    with st.spinner("Đang trích từ khoá..."):
        df_kw = aggregate_keywords(df_f, topk_per_doc=8, max_ngram=max_ngram)
        if len(df_kw) == 0:
            st.info("Không trích được keyword nào từ dữ liệu đã lọc.")
        else:
            text_all_lower = df_f["text_all"].fillna("").str.lower().tolist()
            sentiments = df_f["sentiment"].str.lower().tolist()
            kw_rows = []
            kw_list = df_kw.head(topk_kw)["keyword"].tolist()

            for kw in kw_list:
                idxs = [i for i, t in enumerate(text_all_lower) if kw in t]
                if not idxs:
                    continue
                labels = [sentiments[i] for i in idxs]
                pos = sum(1 for l in labels if l == "positive")
                neg = sum(1 for l in labels if l == "negative")
                neu = sum(1 for l in labels if l == "neutral")
                score = (pos - neg) / max(1, (pos + neg + neu))
                kw_rows.append({
                    "keyword": kw,
                    "freq": len(idxs),
                    "pos": pos, "neg": neg, "neu": neu,
                    "sentiment_score": score
                })

            df_kw2 = pd.DataFrame(kw_rows).sort_values(["freq","sentiment_score"], ascending=[False, False])

            if len(df_kw2):
                bubble = alt.Chart(df_kw2).mark_circle().encode(
                    x=alt.X("sentiment_score:Q", title="Điểm cảm xúc (pos - neg)"),
                    y=alt.Y("freq:Q", title="Tần suất xuất hiện"),
                    size=alt.Size("freq:Q", legend=None),
                    color=alt.Color("sentiment_score:Q", scale=alt.Scale(scheme="redblue"), legend=None),
                    tooltip=["keyword:N","freq:Q","pos:Q","neg:Q","neu:Q","sentiment_score:Q"]
                ).properties(height=380)
                st.altair_chart(bubble, use_container_width=True)

            if NX_OK and len(df_kw2) >= 5:
                st.markdown("**Mạng đồng xuất hiện keyword (đơn giản)**")
                import itertools
                top_nodes = df_kw2.head(min(30, len(df_kw2)))["keyword"].tolist()

                G = nx.Graph()
                for k in top_nodes:
                    scr = float(df_kw2.loc[df_kw2["keyword"]==k, "sentiment_score"].values[0])
                    G.add_node(k, score=scr)

                for text in text_all_lower:
                    hits = [k for k in top_nodes if k in text]
                    for a, b in itertools.combinations(sorted(set(hits)), 2):
                        if G.has_edge(a,b):
                            G[a][b]["w"] += 1
                        else:
                            G.add_edge(a,b, w=1)

                edges = [(u,v,d["w"]) for u,v,d in G.edges(data=True) if d["w"]>=2]
                if edges:
                    st.dataframe(pd.DataFrame(edges, columns=["kw1","kw2","cooccur"]).sort_values("cooccur", ascending=False))
                else:
                    st.caption("Không đủ đồng xuất hiện mạnh (cooccur >= 2).")

# ========== Docs ==========
with tab_docs:
    st.subheader("📄 Dữ liệu chi tiết")
    st.dataframe(df_f[["doc_id","agency","published_dt","title","snippet","sentiment"]].head(200), use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Tải CSV (bản lọc hiện tại)", data=df_f.to_csv(index=False).encode("utf-8"),
                           file_name="filtered_sentiment_rows.csv", mime="text/csv")
    with c2:
        if summary is not None:
            st.download_button("Tải summary theo văn bản", data=summary.to_csv(index=False).encode("utf-8"),
                               file_name="sentiment_results_summary.csv", mime="text/csv")

st.caption("Tip: dùng bộ lọc bên trái (thời gian/agency/từ khoá) và rolling để nhìn xu hướng rõ hơn.")