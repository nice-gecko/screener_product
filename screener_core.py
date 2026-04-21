"""
screener_core.py
スクリーニングロジック（Streamlit app から呼び出す）
"""

import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ─────────────────────────────────────────────
# 米国株 日本語名
# ─────────────────────────────────────────────
US_NAMES = {
    "AAPL":"アップル","MSFT":"マイクロソフト","NVDA":"エヌビディア",
    "GOOGL":"グーグル（アルファベット）","GOOG":"グーグル（アルファベット）",
    "META":"メタ","AMZN":"アマゾン","TSLA":"テスラ","AVGO":"ブロードコム",
    "ORCL":"オラクル","ADBE":"アドビ","CRM":"セールスフォース",
    "AMD":"AMD","QCOM":"クアルコム","TXN":"テキサス・インスツルメンツ",
    "ADI":"アナログ・デバイセズ","KLAC":"KLAコーポレーション",
    "PANW":"パロアルト・ネットワークス","NOW":"サービスナウ",
    "INTU":"インテュイット","CSCO":"シスコシステムズ",
    "JPM":"JPモルガン・チェース","BAC":"バンク・オブ・アメリカ",
    "GS":"ゴールドマン・サックス","MS":"モルガン・スタンレー",
    "AXP":"アメリカン・エキスプレス","V":"ビザ","MA":"マスターカード",
    "CB":"チャブ","CME":"CMEグループ","BRK-B":"バークシャー・ハサウェイ",
    "PLD":"プロロジス","CI":"シグナ","UNH":"ユナイテッドヘルス",
    "JNJ":"J&J","LLY":"イーライリリー","ABT":"アボット",
    "TMO":"サーモフィッシャー","MRK":"メルク","ABBV":"アッヴィ",
    "DHR":"ダナハー","BMY":"ブリストル・マイヤーズ","AMGN":"アムジェン",
    "GILD":"ギリアド","REGN":"リジェネロン","VRTX":"バーテックス",
    "ISRG":"インテュイティブ・サージカル","SYK":"ストライカー",
    "ZTS":"ゾエティス","ELV":"エレバンス","WMT":"ウォルマート",
    "HD":"ホーム・デポ","MCD":"マクドナルド","SBUX":"スターバックス",
    "NKE":"ナイキ","LOW":"ロウズ","COST":"コストコ","BKNG":"ブッキング",
    "PG":"P&G","KO":"コカ・コーラ","PEP":"ペプシコ","PM":"フィリップ・モリス",
    "MO":"アルトリア","CL":"コルゲート","XOM":"エクソンモービル",
    "CVX":"シェブロン","EOG":"EOGリソーシズ","SLB":"シュルンベルジェ",
    "HON":"ハネウェル","CAT":"キャタピラー","DE":"ジョン・ディア",
    "UPS":"UPS","UNP":"ユニオン・パシフィック","RTX":"RTX",
    "LIN":"リンデ","ACN":"アクセンチュア","NFLX":"ネットフリックス",
    "NEE":"ネクステラ・エナジー","SO":"サザン","DUK":"デューク・エナジー",
    "AON":"エオン","MDLZ":"モンデリーズ",
}

JP_NAMES = {
    "7203.T":"トヨタ自動車","6758.T":"ソニーグループ",
    "9984.T":"ソフトバンクグループ","8035.T":"東京エレクトロン",
    "6861.T":"キーエンス","7974.T":"任天堂",
    "9983.T":"ファーストリテイリング","4063.T":"信越化学工業",
    "6367.T":"ダイキン工業","9433.T":"KDDI",
    "8306.T":"三菱UFJフィナンシャルグループ","4519.T":"中外製薬",
    "7267.T":"本田技研工業","9432.T":"NTT",
    "6954.T":"ファナック","2914.T":"JT",
    "8316.T":"三井住友フィナンシャルグループ","4502.T":"武田薬品工業",
    "6762.T":"TDK","9022.T":"JR東海",
    "4661.T":"オリエンタルランド","8411.T":"みずほフィナンシャルグループ",
    "8058.T":"三菱商事","7741.T":"HOYA",
    "4543.T":"テルモ","6098.T":"リクルートホールディングス",
    "3382.T":"セブン&アイHD","4507.T":"塩野義製薬",
    "8001.T":"伊藤忠商事","6503.T":"三菱電機",
    "7751.T":"キヤノン","4568.T":"第一三共",
    "2802.T":"味の素","8002.T":"丸紅",
    "1925.T":"大和ハウス工業","9020.T":"JR東日本",
    "8830.T":"住友不動産","6971.T":"京セラ",
    "8053.T":"住友商事","7733.T":"オリンパス",
    "7832.T":"バンダイナムコHD","4578.T":"大塚HD",
    "6301.T":"コマツ","4755.T":"楽天グループ",
    "3659.T":"ネクソン","6594.T":"ニデック",
    "7201.T":"日産自動車","5108.T":"ブリヂストン",
    "4704.T":"トレンドマイクロ","6857.T":"アドバンテスト",
    "6752.T":"パナソニックHD","4385.T":"メルカリ",
    "3923.T":"ラクス","3697.T":"SHIFT",
    "6326.T":"クボタ","5201.T":"AGC",
    "7701.T":"島津製作所","3092.T":"ZOZO",
}

SECTOR_JP = {
    "Technology":"テクノロジー","Semiconductors":"半導体",
    "Software":"ソフトウェア","Financial Services":"金融サービス",
    "Healthcare":"ヘルスケア","Consumer Cyclical":"消費財（景気敏感）",
    "Consumer Defensive":"消費財（ディフェンシブ）","Industrials":"産業・製造",
    "Energy":"エネルギー","Basic Materials":"素材","Real Estate":"不動産",
    "Communication Services":"通信・メディア","Utilities":"公共事業",
    "Financial":"金融","Electronic Technology":"電子機器",
    "Health Technology":"医療技術","Retail Trade":"小売",
    "Transportation":"輸送","Producer Manufacturing":"製造業",
    "Commercial Services":"商業サービス",
}

DEFAULT_JP = [
    "7203.T","6758.T","9984.T","8035.T","6861.T","7974.T","9983.T",
    "4063.T","6367.T","9433.T","8306.T","4519.T","7267.T","9432.T",
    "6954.T","2914.T","8316.T","4502.T","6762.T","9022.T","4661.T",
    "8411.T","8058.T","7741.T","4543.T","6098.T","3382.T","4507.T",
    "8001.T","6503.T","7751.T","4568.T","2802.T","8002.T","1925.T",
    "9020.T","8830.T","6971.T","8053.T","7733.T","7832.T","4578.T",
    "6301.T","4755.T","3659.T","6594.T","7201.T","5108.T","4704.T",
    "6857.T","6752.T","4385.T","3923.T","3697.T","6326.T","5201.T",
]

DEFAULT_US = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B",
    "JPM","V","UNH","XOM","LLY","JNJ","MA","PG","HD","AVGO",
    "CVX","MRK","ABBV","COST","PEP","KO","ADBE","WMT","CRM",
    "BAC","TMO","ACN","MCD","CSCO","ABT","LIN","DHR","NFLX",
    "AMD","TXN","NKE","PM","UPS","NEE","BMY","RTX","QCOM",
    "HON","LOW","MS","SBUX","ORCL","GS","CAT","INTU",
    "ELV","DE","AMGN","AXP","ISRG","BKNG","SYK","GILD",
    "REGN","VRTX","ZTS","CB","NOW","AON","SLB","CME","PANW","KLAC",
]

def sector_jp(raw):
    if not raw: return "その他"
    for k, v in SECTOR_JP.items():
        if k.lower() in raw.lower(): return v
    return raw

def price_group(price, currency):
    if currency == "JPY":
        if price < 500:    return "低位株"
        elif price < 3000: return "中位株"
        else:              return "高位株"
    else:
        if price < 30:    return "低位株"
        elif price < 150: return "中位株"
        else:             return "高位株"

def get_display_name(ticker, raw_name):
    if ".T" in ticker:
        return JP_NAMES.get(ticker, raw_name)
    if ticker in US_NAMES:
        return US_NAMES[ticker]
    name = raw_name
    for s in [" Corporation"," Corp."," Corp"," Incorporated",
              " Inc."," Inc"," Limited"," Ltd."," Ltd",
              " Holdings"," Holding"," Technologies"," Technology",
              " International"," & Co."," plc"," PLC"," SE"," AG"]:
        name = name.replace(s, "")
    return name.strip()

def fetch_one(ticker: str, min_score: int, max_pullback: float,
              min_vol: float, rsi_lo: float, rsi_hi: float) -> dict | None:
    try:
        stock  = yf.Ticker(ticker)
        weekly = stock.history(period="2y", interval="1wk", auto_adjust=True)
        daily  = stock.history(period="1y", interval="1d",  auto_adjust=True)
        if weekly.empty or daily.empty or len(weekly) < 52:
            return None

        cw = weekly["Close"]; vd = daily["Volume"]
        cd = daily["Close"];  hd = daily["High"]; ld = daily["Low"]

        price = float(cd.iloc[-1])
        if price <= 0: return None

        h52   = float(cw.iloc[:-1].max())
        cwc   = float(cw.iloc[-1])
        ath   = float(cw.max())
        pb    = (ath - cwc) / ath * 100
        brk   = bool(cw.iloc[-3:].max() >= h52 * 0.995)

        vm20  = float(vd.iloc[-21:-1].mean())
        vt    = float(vd.iloc[-1])
        vr    = vt / vm20 if vm20 > 0 else 0
        v5    = float(vd.iloc[-6:-1].mean())
        v5r   = v5 / vm20 if vm20 > 0 else 0

        d     = cd.diff()
        g     = d.clip(lower=0).rolling(14).mean()
        l     = (-d.clip(upper=0)).rolling(14).mean()
        rsi   = float((100 - 100 / (1 + g / (l + 1e-9))).iloc[-1])

        ma20  = float(cd.rolling(20).mean().iloc[-1])
        ma50  = float(cd.rolling(50).mean().iloc[-1])
        wm13  = float(cw.rolling(13).mean().iloc[-1])
        wm26  = float(cw.rolling(26).mean().iloc[-1]) if len(cw) >= 26 else wm13
        trend = bool(wm13 > wm26)
        abma  = bool(price > ma20)

        tr    = pd.concat([hd-ld,(hd-cd.shift()).abs(),(ld-cd.shift()).abs()],axis=1).max(axis=1)
        atr   = float(tr.rolling(14).mean().iloc[-1]) / price * 100

        cb    = brk or (cwc >= h52 * 0.97)
        cpb   = 0 <= pb <= max_pullback
        cvol  = (v5r >= min_vol) or (vr >= 2.0)
        ctr   = trend
        crsi  = rsi_lo <= rsi <= rsi_hi
        cma   = abma and (price > ma50)

        score = 0
        if cb:   score += 30
        if cpb:  score += 20
        if cvol: score += 20
        if ctr:  score += 15
        if crsi: score += 10
        if cma:  score += 5
        score += min(10, int((v5r - 1.5) * 5)) if v5r > 1.5 else 0

        surge = 0
        if len(cw) >= 5:
            surge = (cw.iloc[-1] - cw.iloc[-5]) / cw.iloc[-5] * 100
            if surge >= 30:   score -= 20
            elif surge >= 20: score -= 10

        if score < min_score: return None

        if brk and pb <= 2.0:   pat = "🚀 ブレイク中"
        elif brk and pb <= 5.0: pat = "📉 ブレイク後押し目"
        elif cb and pb <= max_pullback: pat = "🎯 高値圏待機"
        else:                   pat = "👀 監視"

        risk = "🔴 高" if surge >= 30 else ("🟡 中" if surge >= 20 else "🟢 低")

        try:
            info = stock.info
            raw  = info.get("longName") or info.get("shortName") or ticker
            cur  = info.get("currency", "JPY" if ".T" in ticker else "USD")
            sec  = info.get("sector") or info.get("industry") or ""
            per  = info.get("trailingPE") or info.get("forwardPE")
            eg   = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")
            dy   = info.get("dividendYield")
            mc   = info.get("marketCap")
            ned  = None
            cal  = stock.calendar
            if cal is not None and not cal.empty:
                ed = cal.get("Earnings Date")
                if ed is not None and len(ed) > 0:
                    ned = str(ed.iloc[0])[:10]
        except Exception:
            raw=""; cur="JPY" if ".T" in ticker else "USD"
            sec=""; per=None; eg=None; dy=None; mc=None; ned=None

        name   = get_display_name(ticker, raw)
        flag   = "🇯🇵" if ".T" in ticker else "🇺🇸"
        market = "東証" if ".T" in ticker else "米国"
        sym    = "¥" if cur == "JPY" else "$"

        return {
            "ticker": ticker, "name": name, "flag": flag,
            "market": market, "sector": sector_jp(sec),
            "price_group": price_group(price, cur),
            "pattern": pat, "risk": risk, "score": score,
            "price": round(price, 2), "currency": cur, "sym": sym,
            "high_52w": round(h52, 2), "pullback": round(pb, 2),
            "rsi": round(rsi, 1), "vol_ratio": round(vr, 2),
            "vol_5d": round(v5r, 2), "weekly_trend": "↑上昇" if trend else "↓下降",
            "wma13": round(wm13, 2), "wma26": round(wm26, 2),
            "ma20": round(ma20, 2), "ma50": round(ma50, 2),
            "atr": round(atr, 2), "surge_4w": round(surge, 1),
            "per": round(per, 1) if per else None,
            "earn_growth": round(eg * 100, 1) if eg else None,
            "div_yield": round(dy * 100, 2) if dy else None,
            "next_earnings": ned,
            "chart": cw.iloc[-13:].round(2).tolist(),
            "chart_dates": [d.strftime("%m/%d") for d in cw.iloc[-13:].index],
        }
    except Exception:
        return None


def run_screening(
    use_jp=True, use_us=True,
    min_score=60, max_pullback=8.0,
    min_vol=1.5, rsi_lo=45.0, rsi_hi=80.0,
    max_workers=10, progress_cb=None,
) -> list[dict]:
    tickers = []
    if use_jp: tickers += DEFAULT_JP
    if use_us: tickers += DEFAULT_US

    results, done = [], 0
    total = len(tickers)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(fetch_one, t, min_score, max_pullback,
                             min_vol, rsi_lo, rsi_hi): t for t in tickers}
        for f in as_completed(futures):
            done += 1
            r = f.result()
            if r: results.append(r)
            if progress_cb:
                progress_cb(done / total, f"処理中 {done}/{total}（通過: {len(results)}銘柄）")

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
