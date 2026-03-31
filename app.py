import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# --- 頁面設定 ---
st.set_page_config(page_title="Super Bull 計算機", layout="wide")
st.title("🐂 Super Bull 計算機 (實戰穩定版)")

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
    t1_ticker = st.text_input("代碼 A", "7974.T") if use_t1 else None
    
    # 標的 B
    use_t2 = st.checkbox("啟用標的 B", value=True)
    t2_ticker = st.text_input("代碼 B", "9101.T") if use_t2 else None
    
    # 標的 C
    use_t3 = st.checkbox("啟用標的 C", value=False)
    t3_ticker = st.text_input("代碼 C", "8058.T") if use_t3 else None

# --- 數據抓取函數 ---
def get_live_price(ticker):
    if not ticker: return 0.0, ticker
    try:
        stock = yf.Ticker(ticker)
        # 使用更輕量的方法抓取價格
        price = stock.fast_info['last_price']
        name = stock.info.get('shortName', ticker)
        return round(price, 2), name
    except:
        return 0.0, ticker

# 執行抓取
active_tickers = [t for t in [t1_ticker, t2_ticker, t3_ticker] if t]
prices_map = {t: get_live_price(t) for t in active_tickers}

# --- 顯示區：即時市價 (放在最醒目的地方) ---
st.write("### 💵 當前市價參考")
price_cols = st.columns(len(active_tickers)) if active_tickers else st.columns(1)

final_market_prices = {}

for i, t in enumerate(active_tickers):
    with price_cols[i]:
        fetched_p, fetched_n = prices_map[t]
        # 如果抓到 0.0，讓使用者手動輸入
        val = st.number_input(f"{fetched_n} 現價", value=fetched_p if fetched_p > 0 else 100.0, key=f"p_{t}")
        final_market_prices[t] = val

st.divider()

# --- 模擬表現 Slider ---
st.write("### 📈 模擬表現 (相對現價 %)")
sim_results = []
slider_cols = st.columns(len(active_tickers)) if active_tickers else st.columns(1)

for i, t in enumerate(active_tickers):
    with slider_cols[i]:
        name = prices_map[t][1]
        # 滑桿模擬
        s_pct = st.slider(f"{name} 表現", 50, 150, 100, key=f"s_{t}") / 100
        sim_results.append(s_pct)

# --- 核心邏輯計算 ---
if sim_results:
    worst_perf = min(sim_results)
    payoff_pct = (worst_perf / strike_val) * 100

    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 試算結果")
        st.metric("Worst-of 表現", f"{round(worst_perf*100, 2)}%")
        if worst_perf >= strike_val:
            st.success(f"✅ 狀態：高於 Strike\n贖回價值：{round(payoff_pct, 2)}%")
        else:
            st.error(f"❌ 狀態：跌破 Strike\n贖回價值：{round(payoff_pct, 2)}%")
        
        # 顯示換算後的預估價格 (以第一檔標的為例示意)
        st.caption(f"註：若為 2M/4M 產品，請注意 Autocall 比價日。")

    with c2:
        # Plotly 圖表
        fig = go.Figure()
        xr = [i/100 for i in range(50, 151)]
        yr = [(x / strike_val) * 100 for x in xr]
        fig.add_trace(go.Scatter(x=[x*100 for x in xr], y=yr, name="收益線", line=dict(color='royalblue', width=3)))
        fig.add_trace(go.Scatter(x=[worst_perf*100], y=[payoff_pct], mode='markers', marker=dict(size=15, color='red', symbol='cross')))
        fig.add_vline(x=strike_pct_input, line_dash="dash", line_color="green")
        fig.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

st.divider()
with st.expander("📝 說明"):
    st.write("若 Yahoo Finance 抓取失敗，請在『當前市價參考』區手動輸入價格。滑桿將以該價格為 100% 進行模擬。")
