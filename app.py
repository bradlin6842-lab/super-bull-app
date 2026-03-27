import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# --- 頁面設定 ---
st.set_page_config(page_title="Super Bull 計算機 (即時報價版)", layout="wide")
st.title("🐂 Super Bull 計算機 (全球標的版)")

# --- 側邊欄參數 ---
with st.sidebar:
    st.header("⚙️ 產品參數設定")
    currency = st.selectbox("結算貨幣", ["JPY", "USD", "HKD", "AUD", "EUR"])
    
    # 合約總天期
    tenor_label = st.radio("合約總天期 (Max Tenor)", ["2M", "4M", "6M"])
    max_tenor_months = int(tenor_label.replace("M", ""))
    est_exit_months = max_tenor_months / 2
    
    st.divider()
    
    # Strike 與 Bonus 輸入
    strike_pct_input = st.number_input("Strike / Barrier (%)", value=90.0, step=0.5)
    strike_val = strike_pct_input / 100
    bonus_flat = st.number_input("Bonus Coupon (Flat %)", value=9.46, step=0.01)
    
    # 年化計算 (依據 Max Tenor / 2)
    annualized_yield = bonus_flat * (12 / est_exit_months)
    st.info(f"📅 **預估年化收益：{round(annualized_yield, 2)}% p.a.**")
    st.caption(f"(依慣例以 {est_exit_months}M 計算)")

    st.divider()
    st.write("🔍 **自訂標的輸入 (Yahoo Finance Ticker)**")
    st.caption("日股加 .T (如 7974.T), 港股加 .HK (如 0700.HK), 美股直接輸入 (如 NVDA)")
    
    t1 = st.text_input("標的 A Ticker", "7974.T")
    t2 = st.text_input("標的 B Ticker", "9101.T")
    t3 = st.text_input("標的 C Ticker", "8058.T")

# --- 數據抓取邏輯 ---
@st.cache_data(ttl=3600)
def get_price_info(tickers):
    data = {}
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            price = stock.fast_info['last_price']
            name = stock.info.get('shortName', t)
            data[t] = {"price": price, "name": name}
        except:
            data[t] = {"price": 100.0, "name": f"未知標的({t})"}
    return data

stock_data = get_price_info([t1, t2, t3])

# --- 模擬表現 (Slider 現在連動即時股價，預設為 100% 也就是當前價) ---
st.write("### 📈 模擬各標的表現 (相對於目前市價 %)")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    s1 = st.slider(f"{stock_data[t1]['name']}", 50, 150, 100, key="s1") / 100
with col_s2:
    s2 = st.slider(f"{stock_data[t2]['name']}", 50, 150, 100, key="s2") / 100
with col_s3:
    s3 = st.slider(f"{stock_data[t3]['name']}", 50, 150, 100, key="s3") / 100

# --- 核心邏輯計算 ---
prices = [s1, s2, s3]
worst_perf = min(prices)
payoff_pct = (worst_perf / strike_val) * 100

# --- 結果呈現 ---
col_res, col_chart = st.columns([1, 2])

with col_res:
    st.subheader("📊 結算試算")
    st.metric("最差標的表現 (Worst-of)", f"{round(worst_perf*100, 2)}%")
    
    if worst_perf >= strike_val:
        st.success("✅ 狀態：高於 Strike (獲利/出場)")
        st.write(f"1. **提前出場：** 領取 **{100 + bonus_flat}%**")
        st.write(f"2. **持有到期：** 領取 **{round(payoff_pct, 2)}%**")
    else:
        st.error("❌ 狀態：跌破 Strike (虧損/接貨)")
        st.write(f"預計拿回價值：**{round(payoff_pct, 2)}%**")
        st.write(f"帳面虧損：{round(100 - payoff_pct, 2)}% ({currency})")

with col_chart:
    fig = go.Figure()
    x_range = [i/100 for i in range(50, 151)]
    y_payoff = [(x / strike_val) * 100 for x in x_range]
    fig.add_trace(go.Scatter(x=[x*100 for x in x_range], y=y_payoff, name="到期損益線", line=dict(color='royalblue', width=4)))
    fig.add_trace(go.Scatter(x=[worst_perf * 100], y=[payoff_pct], mode='markers', marker=dict(size=15, color='red', symbol='cross'), name="目前位置"))
    fig.add_vline(x=strike_pct_input, line_dash="dash", line_color="green")
    fig.update_layout(title="Super Bull 損益曲線", xaxis_title="Worst-of 表現 (%)", yaxis_title="贖回價值 (%)")
    st.plotly_chart(fig, use_container_width=True)

# --- 即時報價清單 ---
with st.expander("查看目前標的市價 (Yahoo Finance)"):
    df_prices = pd.DataFrame([
        {"代碼": k, "名稱": v['name'], "目前市價": f"{round(v['price'], 2)}"} for k, v in stock_data.items()
    ])
    st.table(df_prices)
