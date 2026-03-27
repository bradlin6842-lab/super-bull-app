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
    t1 = st.text_input("標的 A", "7974.T")
    t2 = st.text_input("標的 B", "9101.T")
    t3 = st.text_input("標的 C", "8058.T")

# --- 進階數據抓取邏輯 (增加重試和穩定性) ---
def get_single_price(ticker):
    try:
        # 強制指定 Yahoo Finance 抓取一天內的即時歷史數據，這在雲端比 fast_info 穩定
        stock = yf.Ticker(ticker)
        # 增加一秒延遲，避免 Yahoo 阻擋
        time.sleep(0.5) 
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            last_price = hist['Close'].iloc[-1]
            # 優先抓取簡稱，如果抓不到，改抓 longName，再抓不到就顯示 Ticker
            name = stock.info.get('shortName', stock.info.get('longName', ticker))
            return {"price": last_price, "name": name, "success": True}
    except Exception as e:
        pass # 抓取失敗，交給下面的備案邏輯
    
    # 失敗備案：顯示 Ticker 作為名稱，股價預設 100
    return {"price": 100.0, "name": f"{ticker}", "success": False}

# 快取數據，ttl 設短一點 (1 分鐘) 方便手機重新整理
@st.cache_data(ttl=60)
def get_all_prices(tickers):
    st.spinner("正在抓取即時報價...") # 顯示一個載入小動畫
    data = {}
    for t in tickers:
        data[t] = get_single_price(t)
    return data

stock_data = get_all_prices([t1, t2, t3])

# --- 模擬表現 (Slider 現在連動即時股價) ---
st.write("### 📈 模擬各標的表現 (相對目前市價 %)")
col_s1, col_s2, col_s3 = st.columns(3)

# 即使抓不到名稱，這裡也會顯示 Ticker，不會顯示 "未知標的"
with col_s1:
    display_name_1 = stock_data[t1]['name']
    s1 = st.slider(f"{display_name_1}", 50, 150, 100, key="s1") / 100
with col_s2:
    display_name_2 = stock_data[t2]['name']
    s2 = st.slider(f"{display_name_2}", 50, 150, 100, key="s2") / 100
with col_s3:
    display_name_3 = stock_data[t3]['name']
    s3 = st.slider(f"{display_name_3}", 50, 150, 100, key="s3") / 100

# --- 核心邏輯計算 ---
prices = [s1, s2, s3]
worst_perf = min(prices)
# 公式：Redemption = Principal * (Worst / Strike)
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
    # 繪製損益曲線圖
    fig = go.Figure()
    # 橫軸數據 (標的表現 50% 到 150%)
    x_range = [i/100 for i in range(50, 151)]
    # 公式：Worst / Strike
    y_payoff = [(x / strike_val) * 100 for x in x_range]
    fig.add_trace(go.Scatter(x=[x*100 for x in x_range], y=y_payoff, name="到期損益線", line=dict(color='royalblue', width=4)))
    # 目前位置
    fig.add_trace(go.Scatter(x=[worst_perf * 100], y=[payoff_pct], mode='markers', marker=dict(size=15, color='red', symbol='cross'), name="目前模擬位置"))
    # Strike 參考線
    fig.add_vline(x=strike_pct_input, line_dash="dash", line_color="green", annotation_text=f"Strike {strike_pct_input}%")
    fig.add_hline(y=100, line_dash="dot", line_color="gray")
    fig.update_layout(title="Super Bull 損益曲線 (Worst-of)", xaxis_title="最差標的表現 (%)", yaxis_title="贖回價值 (%)", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# --- 即時報價清單 (視覺強化) ---
st.divider()
with st.expander("🔍 查看目前標的即時市價 (Yahoo Finance)"):
    # 在這裡標記哪些是成功抓到的，哪些是使用預設值的
    df_prices = pd.DataFrame([
        {
            "代碼": k, 
            "名稱": v['name'], 
            "目前市價": f"{round(v['price'], 2)}", 
            "數據狀態": "🟢 成功抓取" if v['success'] else "🟠 使用預設值(網路超時)"
        } for k, v in stock_data.items()
    ])
    st.table(df_prices)
