import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 頁面設定 ---
st.set_page_config(page_title="Super Bull 計算機", layout="wide")
st.title("🐂 Super Bull 計算機 (Autocall 版)")

# --- 側邊欄參數 ---
with st.sidebar:
    st.header("⚙️ 產品參數設定")
    currency = st.selectbox("結算貨幣", ["JPY", "AUD", "USD", "EUR"])
    
    # 原定合約天期
    tenor_label = st.radio("合約總天期 (Max Tenor)", ["2M", "4M", "6M"])
    max_tenor_months = int(tenor_label.replace("M", ""))
    
    # 新增：實際出場時間 (用於計算年化)
    # 這裡限制實際出場月份不能超過合約總天期
    exit_month = st.number_input("實際出場月份 (Exit Month)", min_value=1, max_value=max_tenor_months, value=1, step=1)
    
    st.divider()
    
    # Strike 輸入
    strike_pct_input = st.number_input("Strike / Barrier (%)", min_value=0.0, max_value=150.0, value=90.0, step=0.5)
    strike_val = strike_pct_input / 100
    
    # Bonus Coupon (Flat) 輸入
    bonus_flat = st.number_input("Bonus Coupon (Flat %)", value=9.46, step=0.01)
    
    # --- 年化計算邏輯變更 ---
    # 依據「實際出場月份」來年化
    annualized_yield = bonus_flat * (12 / exit_month)
    
    st.info(f"📅 **持有 {exit_month} 個月之年化收益：{round(annualized_yield, 2)}% p.a.**")
    st.caption(f"(計算公式: {bonus_flat}% * 12 / {exit_month}M)")

    st.divider()
    st.write("🔍 **標的比價模擬 (相對於期初價 %)**")
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
    
    # 判斷是否滿足 Autocall 或到期高於 Strike
    if worst_perf >= strike_val:
        st.success(f"✅ 狀態：觸發 Autocall / 高於 Strike")
        
        # 這裡根據你的需求，中途出場領的是 Bonus，到期領的是表現比例
        if exit_month < max_tenor_months:
            st.write(f"**中途出場收益：**")
            st.write(f"1. 拿回本金：100%")
            st.write(f"2. Bonus Coupon：{bonus_flat}% ({currency})")
            st.write(f"**總計領回：{100 + bonus_flat}%**")
        else:
            st.write(f"**到期結算收益：**")
            st.write(f"預計拿回本金比例：**{round(payoff_pct, 2)}%**")
            st.write(f"淨獲利：{round(payoff_pct - 100, 2)}% ({currency})")
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
st.info("💡 **計價邏輯提醒**")
st.write(f"- **提前出場 (Autocall)：** 領回 100% 本金 + {bonus_flat}% Bonus Coupon。")
st.write(f"- **持有到期：** 領回 $Principal \\times (P_{{end}} / Strike)$。")
