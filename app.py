import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# --- 頁面設定 ---
st.set_page_config(page_title="Super Bull 計算機", layout="wide")
st.title("🐂 Super Bull 計算機")

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
    st.info(f"📅 預估年化收益：{round(annualized_yield, 2)}% p.a.")

    st.divider()
    st.write("🔍 **標的設定**")
    # 標的 A
    use_t1 = st.checkbox("啟用標的 A", value=True)
    t1_t = st.text_input("Ticker A", "7011.T") if use_t1 else None
    # 標的 B
    use_t2 = st.checkbox("啟用標的 B", value=True)
    t2_t = st.text_input("Ticker B", "7012.T") if use_t2 else None
    # 標的 C (恢復)
    use_t3 = st.checkbox("啟用標的 C", value=True)
    t3_t = st.text_input("Ticker C", "8058.T") if use_t3 else None

# --- 強力抓取函數 ---
def fetch_price(ticker):
    if not ticker: return None
    try:
        s = yf.Ticker(ticker)
        p = s.fast_info['last_price']
        n = s.info.get('shortName', ticker)
        return {"p": round(p, 2), "n": n, "status": "🟢"}
    except:
        return {"p": None, "n": ticker, "status": "🔴"}

active_tickers = [t for t in [t1_t, t2_t, t3_t] if t]
stock_data = {t: fetch_price(t) for t in active_tickers}

# --- 模擬表現區 ---
st.write("### 📈 模擬表現 (相對期初價 %)")
sim_results = []
if active_tickers:
    cols = st.columns(len(active_tickers))
    for i, t in enumerate(active_tickers):
        with cols[i]:
            info = stock_data[t]
            current_p = info['p'] if info['p'] else st.number_input(f"手動輸入 {t} 現價", value=100.0, key=f"p_{t}")
            st.caption(f"{info['status']} {info['n']}: {current_p}")
            s_pct = st.slider(f"模擬 {t} 漲跌", 50, 150, 100, key=f"s_{t}") / 100
            sim_results.append(s_pct)

# --- 結算試算區 ---
if sim_results:
    worst_perf = min(sim_results)
    payoff_pct = (worst_perf / strike_val) * 100
    st.divider()
    st.subheader("📊 試算結果")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Worst-of 表現", f"{round(worst_perf*100, 2)}%")
        if worst_perf >= strike_val:
            st.success(f"✅ 高於 Strike: {round(payoff_pct, 2)}%")
        else:
            st.error(f"❌ 跌破 Strike: {round(payoff_pct, 2)}%")
    with c2:
        fig = go.Figure()
        xr = [i/100 for i in range(50, 151)]
        yr = [(x / strike_val) * 100 for x in xr]
        fig.add_trace(go.Scatter(x=[x*100 for x in xr], y=yr, name="收益線", line=dict(color='royalblue', width=3)))
        fig.add_trace(go.Scatter(x=[worst_perf*100], y=[payoff_pct], mode='markers', marker=dict(size=12, color='red', symbol='cross')))
        fig.add_vline(x=strike_pct_input, line_dash="dash", line_color="green")
        fig.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)

# --- 底部市價表 ---
st.divider()
st.write("### 💵 標的即時市價 (Yahoo Finance)")
if active_tickers:
    footer = [{"代碼": t, "名稱": stock_data[t]['n'], "市價": stock_data[t]['p'] if stock_data[t]['p'] else "N/A", "狀態": stock_data[t]['status']} for t in active_tickers]
    st.table(pd.DataFrame(footer))
