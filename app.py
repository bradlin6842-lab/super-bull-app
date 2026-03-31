import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import time

# --- 頁面設定 ---
st.set_page_config(page_title="Super Bull 計算機", layout="wide")
st.title("🐂 Super Bull 計算機 (穩定加強版)")

# --- 側邊欄參數 ---
with st.sidebar:
    st.header("⚙️ 產品參數設定")
    currency = st.selectbox("結算貨幣", ["JPY", "USD", "HKD", "AUD"])
    
    tenor_label = st.radio("合約總天期 (Max Tenor)", ["2M", "4M", "6M"])
    max_tenor_months = int(tenor_label.replace("M", ""))
    est_exit_months = max_tenor_months / 2
    
    st.divider()
    strike_pct_input = st.number_input("Strike / Barrier (%)", value=90.0, step=0.5)
    strike_val = strike_pct_input / 100
    bonus_flat = st.number_input("Bonus Coupon (Flat %)", value=9.46, step=0.01)
    
    annualized_yield = bonus_flat * (12 / est_exit_months)
    st.info(f"📅 **預估年化收益：{round(annualized_yield, 2)}% p.a.**")

    st.divider()
    st.write("🔍 **自訂標的輸入**")
    
    # 標的 A
    use_t1 = st.checkbox("啟用標的 A", value=True)
    t1 = st.text_input("代碼 A (如 7974.T)", "7974.T") if use_t1 else None
    
    # 標的 B
    use_t2 = st.checkbox("啟用標的 B", value=True)
    t2 = st.text_input("代碼 B (如 9101.T)", "9101.T") if use_t2 else None
    
    # 標的 C
    use_t3 = st.checkbox("啟用標的 C", value=False)
    t3 = st.text_input("代碼 C (如 8058.T)", "8058.T") if use_t3 else None

# --- 強力數據抓取與容錯 ---
def fetch_stock(ticker):
    if not ticker: return None
    try:
        s = yf.Ticker(ticker)
        # 嘗試抓取最新收盤價
        hist = s.history(period="1d")
        if not hist.empty:
            p = hist['Close'].iloc[-1]
            n = s.info.get('shortName', ticker)
            return {"price": p, "name": n, "ok": True}
    except:
        pass
    return {"price": 0.0, "name": ticker, "ok": False}

active_ts = [t for t in [t1, t2, t3] if t]
stock_info = {t: fetch_stock(t) for t in active_ts}

# --- 顯示模擬控制區 ---
st.write("### 📈 標的表現模擬")
sim_prices = []

if not active_ts:
    st.warning("請在左側勾選標的")
else:
    cols = st.columns(len(active_ts))
    for i, t in enumerate(active_ts):
        info = stock_info[t]
        with cols[i]:
            st.write(f"**{info['name']}**")
            # 如果抓不到市價，顯示手動輸入框
            if not info['ok'] or info['price'] == 0:
                st.caption("⚠️ 無法取得即時價，請參考市價模擬")
            
            # Slider 依然以 100% (現價) 為基準
            s = st.slider(f"表現 (%)", 50, 150, 100, key=f"s_{t}") / 100
            sim_prices.append(s)

# --- 計算與繪圖 ---
if sim_prices:
    worst_perf = min(sim_prices)
    payoff_pct = (worst_perf / strike_val) * 100

    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 結算試算")
        st.metric("Worst-of 表現", f"{round(worst_perf*100, 2)}%")
        if worst_perf >= strike_val:
            st.success(f"✅ 高於 Strike\n贖回：{round(payoff_pct, 2)}%")
        else:
            st.error(f"❌ 跌破 Strike\n價值：{round(payoff_pct, 2)}%")

    with c2:
        fig = go.Figure()
        xr = [i/100 for i in range(50, 151)]
        yr = [(x / strike_val) * 100 for x in xr]
        fig.add_trace(go.Scatter(x=[x*100 for x in xr], y=yr, name="收益線"))
        fig.add_trace(go.Scatter(x=[worst_perf*100], y=[payoff_pct], mode='markers', marker=dict(size=12, color='red')))
        fig.add_vline(x=strike_pct_input, line_dash="dash", line_color="green")
        fig.update_layout(height=300, margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig, use_container_width=True)
