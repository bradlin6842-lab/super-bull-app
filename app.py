import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import time

# --- 頁面設定 ---
st.set_page_config(page_title="Super Bull 計算機", layout="wide")
st.title("🐂 Super Bull 計算機")

# --- 側邊欄參數 ---
with st.sidebar:
    st.header("⚙️ 產品參數設定")
    currency = st.selectbox("結算貨幣", ["JPY", "USD", "HKD", "AUD"])
    
    tenor_label = st.radio("合約總天期 (Max Tenor)", ["2M", "4M", "6M"])
    max_tenor_months = int(tenor_label.replace("M", ""))
    # 依據慣例：年化以總天期一半計算
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
    t1_ticker = st.text_input("代碼 A", "7974.T") if use_t1 else None
    use_t2 = st.checkbox("啟用標的 B", value=True)
    t2_ticker = st.text_input("代碼 B", "9101.T") if use_t2 else None
    use_t3 = st.checkbox("啟用標的 C", value=False)
    t3_ticker = st.text_input("代碼 C", "8058.T") if use_t3 else None

# --- 核心邏輯：模擬表現 Slider (放在中間) ---
active_tickers = [t for t in [t1_ticker, t2_ticker, t3_ticker] if t]

st.write("### 📈 模擬表現 (相對期初價 %)")
sim_results = []
slider_cols = st.columns(len(active_tickers)) if active_tickers else st.columns(1)

# 這裡先預設名稱，等下面抓取完再更新
for i, t in enumerate(active_tickers):
    with slider_cols[i]:
        s_pct = st.slider(f"{t} 表現", 50, 150, 100, key=f"s_{t}") / 100
        sim_results.append(s_pct)

# --- 計算試算結果 ---
if sim_results:
    worst_perf = min(sim_results)
    payoff_pct = (worst_perf / strike_val) * 100

    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 試算結果")
        st.metric("Worst-of 表現", f"{round(worst_perf*100, 2)}%")
        if worst_perf >= strike_val:
            st.success(f"✅ 高於 Strike\n贖回價值：{round(payoff_pct, 2)}%")
        else:
            st.error(f"❌ 跌破 Strike\n贖回價值：{round(payoff_pct, 2)}%")
    
    with c2:
        fig = go.Figure()
        xr = [i/100 for i in range(50, 151)]
        yr = [(x / strike_val) * 100 for x in xr]
        fig.add_trace(go.Scatter(x=[x*100 for x in xr], y=yr, name="收益線", line=dict(color='royalblue', width=3)))
        fig.add_trace(go.Scatter(x=[worst_perf*100], y=[payoff_pct], mode='markers', marker=dict(size=15, color='red', symbol='cross')))
        fig.add_vline(x=strike_pct_input, line_dash="dash", line_color="green")
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

# --- 重頭戲：將股價資訊放在最下面 ---
st.divider()
st.write("### 💵 標的即時市價參考 (Yahoo Finance)")

def get_data_footer(ticker):
    try:
        s = yf.Ticker(ticker)
        # 抓取最新收盤價
        hist = s.history(period="1d")
        price = hist['Close'].iloc[-1] if not hist.empty else 0.0
        name = s.info.get('shortName', ticker)
        return {"代碼": ticker, "名稱": name, "目前市價": round(price, 2), "狀態": "🟢 正常"}
    except:
        return {"代碼": ticker, "名稱": ticker, "目前市價": "N/A", "狀態": "🔴 抓取失敗"}

if active_tickers:
    with st.spinner("正在更新底部署價數據..."):
        footer_data = [get_data_footer(t) for t in active_tickers]
        st.table(pd.DataFrame(footer_data))
else:
    st.info("請在側邊欄啟用標的以查看市價。")

st.caption("註：若市價抓取失敗，請檢查 Ticker 是否正確（如日股需加 .T）。")
