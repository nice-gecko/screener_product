"""
app.py  ─  新高値ブレイク スクリーナー（Streamlit版）
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
from screener_core import run_screening, DEFAULT_JP, DEFAULT_US

# ─────────────────────────────────────────────
# ページ設定
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="新高値ブレイク スクリーナー",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# カスタムCSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  /* フォント */
  html, body, [class*="css"] { font-family: 'Hiragino Sans','Noto Sans JP',sans-serif; }

  /* ヘッダー */
  .main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    padding: 24px 32px; border-radius: 14px; margin-bottom: 24px;
    border: 1px solid #1e40af;
  }
  .main-header h1 { color: #f8fafc; font-size: 26px; font-weight: 900;
    margin: 0; letter-spacing: -0.5px; }
  .main-header p  { color: #94a3b8; font-size: 13px; margin: 6px 0 0; }

  /* 統計カード */
  .stat-row { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
  .stat-card {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 14px 20px; min-width: 120px; flex: 1;
  }
  .stat-label { font-size: 11px; color: #64748b; text-transform: uppercase;
    letter-spacing: .8px; margin-bottom: 4px; }
  .stat-val   { font-size: 28px; font-weight: 700; color: #2563eb; font-family: monospace; }
  .stat-val.green  { color: #16a34a; }
  .stat-val.yellow { color: #d97706; }
  .stat-val.purple { color: #7c3aed; }

  /* スコアバー */
  .score-wrap { display: flex; align-items: center; gap: 6px; }
  .score-num  { font-weight: 700; font-family: monospace; font-size: 15px; min-width: 28px; }
  .score-bar  { flex: 1; height: 5px; background: #e2e8f0; border-radius: 3px; min-width: 60px; }
  .score-fill { height: 5px; border-radius: 3px;
    background: linear-gradient(90deg, #2563eb, #7c3aed); }

  /* 銘柄行 */
  .ticker-name   { font-weight: 700; font-size: 14px; color: #0f172a; }
  .ticker-code   { font-family: monospace; font-size: 11px; color: #2563eb; }
  .ticker-sector { font-size: 10px; color: #94a3b8; }

  /* バッジ */
  .badge { display: inline-block; font-size: 11px; padding: 2px 8px;
    border-radius: 4px; font-weight: 600; }
  .badge-jp { background: #dcfce7; color: #15803d; }
  .badge-us { background: #dbeafe; color: #1d4ed8; }
  .badge-low  { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
  .badge-mid  { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
  .badge-high { background: #fefce8; color: #854d0e; border: 1px solid #fde68a; }

  /* 詳細パネル */
  .detail-panel {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 20px; margin-top: 8px;
  }
  .detail-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; }
  .detail-item { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; }
  .detail-lbl  { font-size: 10px; color: #94a3b8; text-transform: uppercase; letter-spacing: .7px; }
  .detail-val  { font-size: 16px; font-weight: 700; font-family: monospace; color: #0f172a; }

  /* 免責 */
  .disclaimer {
    background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px;
    padding: 12px 16px; font-size: 12px; color: #92400e; margin-top: 24px;
  }

  /* Streamlit デフォルトの余白調整 */
  .block-container { padding-top: 1.5rem; }
  div[data-testid="stExpander"] { border: 1px solid #e2e8f0; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ヘッダー
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>📈 新高値ブレイク スクリーナー</h1>
  <p>ヘッジファンドが使う新高値フィルターを自動実行｜東証 ＋ 米国株（日米対応）</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# サイドバー：設定
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ スクリーニング設定")

    st.markdown("**対象市場**")
    use_jp = st.checkbox("🇯🇵 東証（日本株）", value=True)
    use_us = st.checkbox("🇺🇸 米国株（S&P500）", value=True)

    st.divider()

    st.markdown("**スコア・条件**")
    min_score    = st.slider("最低スコア",        40, 90, 60, 5)
    max_pullback = st.slider("最大押し目（%）",   1.0, 15.0, 8.0, 0.5)
    min_vol      = st.slider("出来高比率（倍）",  1.0, 3.0, 1.5, 0.1)
    rsi_range    = st.slider("RSI範囲",           20, 90, (45, 80))

    st.divider()

    run_btn = st.button("🚀 スクリーニング実行", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:11px;color:#94a3b8;line-height:1.7">
    ⚠️ このツールは情報提供のみを目的としています。<br>
    投資の最終判断はご自身の責任で行ってください。<br>
    データはYahoo Financeから取得しています。
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# セッション状態
# ─────────────────────────────────────────────
if "results"    not in st.session_state: st.session_state.results    = []
if "last_run"   not in st.session_state: st.session_state.last_run   = None
if "filter_mkt" not in st.session_state: st.session_state.filter_mkt = "すべて"
if "filter_pat" not in st.session_state: st.session_state.filter_pat = "すべて"
if "filter_pg"  not in st.session_state: st.session_state.filter_pg  = "すべて"
if "sort_by"    not in st.session_state: st.session_state.sort_by    = "スコア"

# ─────────────────────────────────────────────
# スクリーニング実行
# ─────────────────────────────────────────────
if run_btn:
    if not use_jp and not use_us:
        st.warning("対象市場を1つ以上選択してください")
    else:
        prog_bar  = st.progress(0.0, text="スクリーニング開始中...")
        prog_text = st.empty()

        def on_progress(pct, msg):
            prog_bar.progress(min(pct, 1.0), text=msg)

        with st.spinner(""):
            results = run_screening(
                use_jp=use_jp, use_us=use_us,
                min_score=min_score, max_pullback=max_pullback,
                min_vol=min_vol, rsi_lo=rsi_range[0], rsi_hi=rsi_range[1],
                progress_cb=on_progress,
            )

        prog_bar.empty()
        st.session_state.results  = results
        st.session_state.last_run = datetime.now().strftime("%Y/%m/%d %H:%M")
        st.success(f"✅ {len(results)}銘柄が通過しました！")

# ─────────────────────────────────────────────
# 結果表示
# ─────────────────────────────────────────────
results = st.session_state.results

if not results:
    st.info("👈 左のサイドバーから「スクリーニング実行」を押してください（5〜10分かかります）")
    st.stop()

# ── 統計カード ──
total     = len(results)
breakouts = sum(1 for r in results if "ブレイク中" in r["pattern"])
pullbacks = sum(1 for r in results if "押し目" in r["pattern"])
jp_count  = sum(1 for r in results if r["market"] == "東証")
us_count  = sum(1 for r in results if r["market"] == "米国")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("通過銘柄",     total)
col2.metric("🚀 ブレイク中", breakouts)
col3.metric("📉 押し目候補", pullbacks)
col4.metric("🇯🇵 東証",      jp_count)
col5.metric("🇺🇸 米国",      us_count)

st.caption(f"最終実行: {st.session_state.last_run}")

st.divider()

# ── フィルター・ソート ──
fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])
with fc1:
    mkt_opts = ["すべて","東証","米国"]
    st.session_state.filter_mkt = st.selectbox("市場", mkt_opts,
        index=mkt_opts.index(st.session_state.filter_mkt))
with fc2:
    pat_opts = ["すべて","🚀 ブレイク中","📉 ブレイク後押し目","🎯 高値圏待機"]
    st.session_state.filter_pat = st.selectbox("パターン", pat_opts,
        index=pat_opts.index(st.session_state.filter_pat))
with fc3:
    pg_opts = ["すべて","低位株","中位株","高位株"]
    st.session_state.filter_pg = st.selectbox("株価帯", pg_opts,
        index=pg_opts.index(st.session_state.filter_pg))
with fc4:
    sort_opts = ["スコア","RSI","出来高比率","押し目%"]
    st.session_state.sort_by = st.selectbox("並び順", sort_opts,
        index=sort_opts.index(st.session_state.sort_by))

# フィルタリング
filtered = results
if st.session_state.filter_mkt != "すべて":
    filtered = [r for r in filtered if r["market"] == st.session_state.filter_mkt]
if st.session_state.filter_pat != "すべて":
    filtered = [r for r in filtered if r["pattern"] == st.session_state.filter_pat]
if st.session_state.filter_pg != "すべて":
    filtered = [r for r in filtered if r["price_group"] == st.session_state.filter_pg]

# ソート
sort_key = {"スコア": lambda x: -x["score"],
             "RSI":    lambda x: -x["rsi"],
             "出来高比率": lambda x: -x["vol_5d"],
             "押し目%": lambda x: x["pullback"]}
filtered.sort(key=sort_key[st.session_state.sort_by])

st.caption(f"{len(filtered)} 銘柄表示中")

# ── CSVダウンロード ──
if filtered:
    df_csv = pd.DataFrame([{
        "ティッカー": r["ticker"], "銘柄名": r["name"],
        "市場": r["market"], "パターン": r["pattern"],
        "急騰リスク": r["risk"], "スコア": r["score"],
        "現在値": r["price"], "通貨": r["currency"],
        "52W高値": r["high_52w"], "押し目(%)": r["pullback"],
        "RSI": r["rsi"], "出来高比率(5D)": r["vol_5d"],
        "週足トレンド": r["weekly_trend"],
        "PER": r["per"], "利益成長率(%)": r["earn_growth"],
        "次回決算": r["next_earnings"],
    } for r in filtered])

    csv_buf = io.BytesIO()
    df_csv.to_csv(csv_buf, index=False, encoding="utf-8-sig")
    st.download_button(
        "📥 CSVダウンロード（楽天証券用）",
        data=csv_buf.getvalue(),
        file_name=f"screener_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

st.divider()

# ─────────────────────────────────────────────
# 銘柄リスト（展開式）
# ─────────────────────────────────────────────
for r in filtered:
    sym   = r["sym"]
    price_str = f"{sym}{r['price']:,.0f}" if r["currency"] == "JPY" else f"{sym}{r['price']:,.2f}"
    h52_str   = f"{sym}{r['high_52w']:,.0f}" if r["currency"] == "JPY" else f"{sym}{r['high_52w']:,.2f}"
    pull_str  = "AT HIGH" if r["pullback"] == 0 else f"-{r['pullback']}%"
    pg_cls    = {"低位株":"badge-low","中位株":"badge-mid","高位株":"badge-high"}.get(r["price_group"],"")
    mkt_cls   = "badge-jp" if r["market"] == "東証" else "badge-us"

    label = (
        f"{r['flag']} **{r['name']}** `{r['ticker']}`　"
        f"{r['pattern']}　スコア **{r['score']}**　{price_str}　{pull_str}　RSI {r['rsi']}"
    )

    with st.expander(label):
        # 楽天証券リンク
        if r["market"] == "東証":
            code = r["ticker"].replace(".T","")
            rakuten_url = f"https://www.rakuten-sec.co.jp/web/market/search/ipmenu_stock.html?ID={code}"
        else:
            rakuten_url = f"https://www.rakuten-sec.co.jp/web/market/search/ipmenu_us_stock.html?ID={r['ticker']}"

        st.markdown(f"🏭 {r['sector']}　|　"
                    f"<span class='badge {pg_cls}'>{r['price_group']}</span>　|　"
                    f"[楽天証券で確認]({rakuten_url})　|　"
                    f"急騰リスク: {r['risk']}",
                    unsafe_allow_html=True)

        # 詳細グリッド
        dc = st.columns(4)
        dc[0].metric("現在値",       price_str)
        dc[1].metric("52週高値",     h52_str)
        dc[2].metric("高値からの乖離", pull_str)
        dc[3].metric("RSI (14日)",   r["rsi"])

        dc2 = st.columns(4)
        dc2[0].metric("出来高比率(5D)", f"×{r['vol_5d']}")
        dc2[1].metric("週足トレンド",  r["weekly_trend"])
        dc2[2].metric("ATR(%)",       f"{r['atr']}%")
        dc2[3].metric("直近4週上昇",  f"{r['surge_4w']}%")

        dc3 = st.columns(4)
        dc3[0].metric("PER",     f"{r['per']}倍"   if r["per"]          else "—")
        dc3[1].metric("利益成長率", f"+{r['earn_growth']}%" if r["earn_growth"] else "—")
        dc3[2].metric("配当利回り",  f"{r['div_yield']}%" if r["div_yield"]   else "—")
        dc3[3].metric("次回決算",    r["next_earnings"] or "未定")

        # スパークライン（週足13週）
        if r.get("chart"):
            chart_df = pd.DataFrame({
                "週": r["chart_dates"],
                "終値": r["chart"],
            }).set_index("週")
            st.line_chart(chart_df, height=160, use_container_width=True)

        # スコア根拠
        with st.expander("📊 スコア根拠を見る"):
            score_items = [
                ("新高値ブレイク",   30, r["pullback"] <= 8 and r["score"] >= 30),
                ("適切な押し目",     20, 0 <= r["pullback"] <= 8),
                ("出来高急増",       20, r["vol_5d"] >= 1.5),
                ("週足上昇トレンド", 15, "↑" in r["weekly_trend"]),
                ("RSI健全域",        10, 45 <= r["rsi"] <= 80),
                ("移動平均線上位",    5, r["price"] > r["ma20"] and r["price"] > r["ma50"]),
            ]
            for label, pts, ok in score_items:
                icon  = "✅" if ok else "⬜"
                color = "#2563eb" if ok else "#94a3b8"
                st.markdown(
                    f"{icon} **{label}** "
                    f"<span style='color:{color};font-family:monospace'>"
                    f"{'＋' if ok else '('}{ pts}{'pt' if ok else 'pt)'}"
                    f"</span>",
                    unsafe_allow_html=True
                )
            if r["surge_4w"] >= 20:
                st.markdown(
                    f"⚠️ **急騰ペナルティ** "
                    f"<span style='color:#dc2626;font-family:monospace'>"
                    f"−{ 20 if r['surge_4w'] >= 30 else 10}pt</span>　"
                    f"直近4週 +{r['surge_4w']}%上昇",
                    unsafe_allow_html=True
                )

st.markdown("""
<div class="disclaimer">
⚠️ このツールは情報提供のみを目的としています。投資助言ではありません。
株式投資には元本割れのリスクがあります。投資の最終判断はご自身の責任で行ってください。
データはYahoo Financeから取得しており、遅延・誤りが生じる場合があります。
</div>
""", unsafe_allow_html=True)
