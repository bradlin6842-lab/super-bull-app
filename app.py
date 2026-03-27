import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 頁面設定 ---
st.set_page_config(page_title="Super Bull 計算機", layout="wide")
st.title("🐂 Super Bull 計算機")

# --- 側邊欄參數 ---
with st.sidebar:
    st.header("⚙️ 產品參數設定")
    currency = st.selectbox("結算貨幣", ["JPY", "AUD", "USD", "EUR"])
    
    # Tenor 選擇，我們將其轉化為數字以利計算
    tenor_label = st.radio("天期 (Tenor)", ["2M", "4M", "6M"])
    tenor_months = int(tenor_label.replace("M", ""))
    
    # Strike 輸入
    strike_pct_input = st.number_input("Strike / Barrier (%)", min_value=0.0, max_value=150.0, value=90.0, step=0.5)
    strike_val = strike_pct_input / 100
    
    # Bonus Coupon 輸入與年化計算
    bonus_flat = st.number_input("Bonus Coupon (Flat %)", value=9.46, step=0.01)
    
    # 計算年化收益率
    annualized_yield = bonus_flat * (12 / tenor_months)
    
    # 顯示年化收益（用 info 框加強視覺感）
    st.info(f"📅 **對應年化收益率：{round(annualized_yield, 2)}% p.a.**")
    
    st.divider()
    st.write("🔍 **標的比價設定 (相對於期初價 %)**")
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
        st.success("✅ 狀態：高於 Strike (獲利/出場)")
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
    
    fig.add_trace(go.Scatter(
        x=[x*100 for x in x_range], 
        y=y_payoff, 
        name="到期損益線",
        line=dict(color='royalblue', width=4)
    ))
    
    fig.add_trace(go.Scatter(
        x=[worst_perf * 100], 
        y=[payoff_pct], 
        mode='markers', 
        marker=dict(size=15, color='red', symbol='cross'),
        name="目前模擬位置"
    ))
    
    fig.add_vline(x=strike_pct_input, line_dash="dash", line_color="green", annotation_text=f"Strike {strike_pct_input}%")
    fig.add_hline(y=100, line_dash="dot", line_color="gray")

    fig.update_layout(
        title="Super Bull 到期損益曲線 (Worst-of)",
        xaxis_title="最差標的表現 (%)",
        yaxis_title="贖回本金價值 (%)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.info("💡 **計價公式提醒**")
st.latex(r"Redemption = Principal \times \frac{P_{end}}{Strike}")
st.write(f"年化計算基礎：$Flat \times (12 / {tenor_months})$")
