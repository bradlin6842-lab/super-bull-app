import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 頁面設定 ---
st.set_page_config(page_title="Super Bull 計算機", layout="wide")
st.title("🐂 Super Bull 計算機 (預估年化版)")

# --- 側邊欄參數 ---
with st.sidebar:
    st.header("⚙️ 產品參數設定")
    currency = st.selectbox("結算貨幣", ["JPY", "AUD", "USD", "EUR"])
    
    # 合約總天期
    tenor_label = st.radio("合約總天期 (Max Tenor)", ["2M", "4M", "6M"])
    max_tenor_months = int(tenor_label.replace("M", ""))
    
    # 依據慣例：年化收益以「合約總天期 / 2」作為預估出場時間
    est_exit_months = max_tenor_months / 2
    
    st.divider()
    
    # Strike 輸入
    strike_pct_input = st.number_input("Strike / Barrier (%)", min_value=0.0, max_value=150.0, value=90.0, step=0.5)
    strike_val = strike_pct_input / 100
    
    # Bonus Coupon (Flat) 輸入
    bonus_flat = st.number_input("Bonus Coupon (Flat %)", value=9.46, step=0.01)
    
    # --- 年化計算邏輯更新：Max Tenor / 2 ---
    annualized_yield = bonus_flat * (12 / est_exit_months)
    
    st.info(f"📅 **預估年化收益：{round(annualized_yield, 2)}% p.a.**")
    st.caption(f"(依慣例以合約半數時間 {est_exit_months}M 計算年化)")

    st.divider()
    st.write("🔍 **標的比價模擬 (相對期初價 %)**")
    s1 = st.slider("標的 A (如：任天堂)", 50, 150, 100) / 100
    s2 = st.slider("標的 B (如：日本郵船)", 50, 150, 100) / 100
    s3 = st.slider("標的 C (如 : 三菱商事)", 50, 150, 100) / 100

# --- 核心邏輯計算 ---
prices = [s1, s2, s3]
worst_perf = min(prices)
payoff_pct = (worst_perf / strike_val) * 100

# --- 結果呈現 ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 結算試算")
    st.metric("最差標的表現 (Worst-of)", f"{round(worst_perf*100, 2)}%")
    
    if worst_perf >= strike_val:
        st.success(f"✅ 狀態：觸發 Autocall / 高於 Strike")
        # 顯示兩種可能的收益邏輯
        st.write("**可能收益路徑：**")
        st.write(f"1. **提前出場：** 領取 **{100 + bonus_flat}%** (本金 + Bonus)")
        st.write(f"2. **持有到期：** 領取 **{round(payoff_pct, 2)}%** (參與漲幅)")
        st.caption("註：最終收益視觸發自動贖回之比價日而定。")
    else:
        st.error("❌ 狀態：跌破 Strike (虧損/接貨)")
        st.write(f"預計拿回價值：**{round(payoff_pct, 2)}%**")
        st.write(f"帳面虧損：{round(100 - payoff_pct, 2)}% ({currency})")

with col2:
    fig = go.Figure()
    x_range = [i/100 for i in range(50, 151)]
    y_payoff = [(x / strike_val) * 100 for x in x_range]
    
    fig.add_trace(go.Scatter(x=[x*100 for x in x_range], y=y_payoff, name="到期損益線", line=dict(color='royalblue', width=4)))
    fig.add_trace(go.Scatter(x=[worst_perf * 100], y=[payoff_pct], mode='markers', marker=dict(size=15, color='red', symbol='cross'), name="目前模擬位置"))
    
    fig.add_vline(x=strike_pct_input, line_dash="dash", line_color="green", annotation_text=f"Strike {strike_pct_input}%")
    fig.add_hline(y=100, line_dash="dot", line_color="gray")

    fig.update_layout(title="Super Bull 損益曲線 (Worst-of)", xaxis_title="最差標的表現 (%)", yaxis_title="贖回價值 (%)", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.info("💡 **計價與年化說明**")
st.write(f"- **年化算法：** 使用 Bonus Flat {bonus_flat}% 乘上 (12 / {est_exit_months} 個月)。")
st.write(f"- **收益邏輯：** 若發生 Autocall，領取固定 Bonus；若未 Autocall 且到期未破 Strike，則領取標的表現與 Strike 之比值。")
