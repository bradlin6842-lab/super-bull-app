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
    st.info(f"📅 **預估年化收益：{round(annualized_yield, 2)}% p.a.**")

    st.divider()
    st.write("🔍 **自訂標的輸入**")
    use_t1 = st.checkbox("啟用標的 A", value=True)
    t1_ticker = st.text_input("代碼 A", "7011.T") if use_t1 else None
    use_t2 = st.checkbox("啟用標的 B", value=True)
    t2_ticker = st.text_input("代碼 B", "7012.T") if use_t2 else None
    use_t3 = st.checkbox("啟用標的 C", value=False)
    t3_ticker = st.text_input("代碼 C", "8058.T") if use_t3 else None

# --- 模擬表現 Slider ---
active_tickers = [t for t in [t1_ticker, t2_ticker, t3_ticker] if t]

st.write("### 📈 模擬表現 (相對期初價 %)")
sim_results = []

if active_tickers:
    slider_cols = st.columns(len(active_tickers))
    for i, t in enumerate(active_tickers):
        with slider_cols[i]:
            s_pct = st.slider(f"{t} 表現", 50, 150, 100, key=f"s_{t}") / 100
            sim_results.append(s_pct)

# --- 核心結算試算區 ---
if sim_results:
    worst_perf = min(sim_results)
    payoff_pct = (worst_perf / strike_val) * 100

    st.write("### 📊 試算結果")
    col_metric, col_status = st.columns([1, 2])
    
    with col_metric:
        st.metric("Worst-of 表現", f"{round(worst_perf*100, 2)}%")
    
    with col_status:
        if worst_perf >= strike_val:
            st.success(f"✅ 高於 Strike 贖回價值：{round(payoff_pct, 2)}%")
            st.caption(f"提前出場：領取 100% + {bonus_flat}% Bonus")
        else:
            st.error(f"❌ 跌破 Strike 贖回價值：{round(payoff_pct, 2)}%")
            st.caption(f"帳面損失：{round(100 - payoff_pct, 2)}% (通常轉為實體股票)")

    # --- 損益圖表 ---
    fig = go.Figure()
    xr = [i/100 for i in range(50, 151)]
    yr = [(x / strike_val) * 100 for x in xr]
    fig.add_trace(go.Scatter(x=[x*100 for x in xr], y=yr, name="收益線", line=dict(color='royalblue', width=3)))
    fig.add_trace(go.Scatter(x=[worst_perf*100], y=[payoff_pct], mode='markers', 
                             marker=dict(size=15, color='red', symbol='cross'), name="目前位置"))
    fig.add_vline(x=strike_pct_input, line_dash="dash", line_color="green")
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

# --- 最底部：即時股價表格 ---
st.divider()
st.write("### 💵 標的即時市價參考 (Yahoo Finance)")

def get_footer_price(ticker):
    try:
        s = yf.Ticker(ticker)
        hist = s.history(period="1d")
        p = hist['Close'].iloc[-1] if not hist.empty else 0.0
        n = s.info.get('shortName', ticker)
        return {"代碼": ticker, "名稱": n, "目前市價": round(p, 2)}
    except:
        return {"代碼": ticker, "名稱": ticker, "目前市價": "N/A"}

if active_tickers:
    with st.spinner("更新股價中..."):
        data_list = [get_footer_price(t) for t in active_tickers]
        st.table(pd.DataFrame(data_list))
