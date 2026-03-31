import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import time

# --- 頁面設定 ---
st.set_page_config(page_title="Super Bull 計算機", layout="wide")
st.title("🐂 Super Bull 計算機 (全球標的版)")

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
    st.write("🔍 **自訂標的輸入 (Yahoo Ticker)**")
    # 這裡讓使用者決定要啟用幾檔標的
    use_t1 = st.checkbox("啟用標的 A", value=True)
    t1 = st.text_input("代碼 A", "7974.T") if use_t1 else None
    
    use_t2 = st.checkbox("啟用標的 B", value=True)
    t2 = st.text_input("代碼 B", "9101.T") if use_t2 else None
    
    use_t3 = st.checkbox("啟用標的 C", value=False) # 預設關閉第三檔
    t3 = st.text_input("代碼 C", "8058.T") if use_t3 else None

# --- 進階數據抓取邏輯 ---
def get_single_price(ticker):
    if not ticker: return None
    try:
        stock = yf.Ticker(ticker)
        time.sleep(0.2) 
        hist = stock.history(period="1d")
        if not hist.empty:
            last_price = hist['Close'].iloc[-1]
            name = stock.info.get('shortName', stock.info.get('longName', ticker))
            return {"price": last_price, "name": name, "success": True}
    except:
        pass
    return {"price": 100.0, "name": f"{ticker}", "success": False}

# 準備有效的 Ticker 列表
active_tickers = [t for t in [t1, t2, t3] if t]

@st.cache_data(ttl=60)
def get_all_prices(tickers):
    data = {}
    for t in tickers:
        data[t] = get_single_price(t)
    return data

stock_data = get_all_prices(active_tickers)

# --- 模擬表現 Slider ---
st.write("### 📈 模擬有效標的之表現 (%)")
sim_prices = []

# 動態生成 Slider
cols = st.columns(len(active_tickers)) if active_tickers else st.columns(1)

if not active_tickers:
    st.warning("請至少在左側勾選一檔標的。")
else:
    for i, t in enumerate(active_tickers):
        with cols[i]:
            display_name = stock_data[t]['name']
            s = st.slider(f"{display_name}", 50, 150, 100, key=f"s_{t}") / 100
            sim_prices.append(s)

# --- 核心邏輯計算 (只計算勾選的標的) ---
if sim_prices:
    worst_perf = min(sim_prices) # 這裡就只會從勾選的裡面選最差的
    payoff_pct = (worst_perf / strike_val) * 100

    # --- 結果呈現 ---
    col_res, col_chart = st.columns([1, 2])

    with col_res:
        st.subheader("📊 結算試算")
        st.metric("選定標的最差表現 (Worst-of)", f"{round(worst_perf*100, 2)}%")
        
        if worst_perf >= strike_val:
            st.success("✅ 狀態：高於 Strike")
            st.write(f"- 提前出場：{100 + bonus_flat}%")
            st.write(f"- 到期領回：{round(payoff_pct, 2)}%")
        else:
            st.error("❌ 狀態：跌破 Strike")
            st.write(f"預計拿回價值：**{round(payoff_pct, 2)}%**")

    with col_chart:
        fig = go.Figure()
        x_range = [i/100 for i in range(50, 151)]
        y_payoff = [(x / strike_val) * 100 for x in x_range]
        fig.add_trace(go.Scatter(x=[x*100 for x in x_range], y=y_payoff, name="到期損益線", line=dict(color='royalblue', width=4)))
        fig.add_trace(go.Scatter(x=[worst_perf * 100], y=[payoff_pct], mode='markers', marker=dict(size=15, color='red', symbol='cross'), name="目前位置"))
        fig.add_vline(x=strike_pct_input, line_dash="dash", line_color="green")
        fig.update_layout(title="Super Bull 損益曲線", xaxis_title="Worst-of 表現 (%)", yaxis_title="贖回價值 (%)")
        st.plotly_chart(fig, use_container_width=True)
