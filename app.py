import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 頁面設定 ---
st.set_page_config(page_title="Super Bull Analyzer", layout="wide")
st.title("📈 Super Bull 股權連結票券分析器")

# --- 側邊欄參數 ---
with st.sidebar:
    st.header("⚙️ 產品參數設定")
    currency = st.selectbox("結算貨幣", ["JPY", "AUD", "USD"])
    tenor = st.radio("天期 (Tenor)", ["2M", "4M"])
    strike_pct = st.slider("Strike / Barrier (%)", 70.0, 100.0, 90.0) / 100
    bonus_flat = st.number_input("Bonus Coupon (Flat %)", value=9.46) / 100
    
    st.divider()
    st.write("🔍 **標的比價設定 (相對於期初價 %)**")
    s1 = st.slider("標的 A (如：任天堂)", 50, 150, 100) / 100
    s2 = st.slider("標的 B (如：日本郵船)", 50, 150, 100) / 100
    s3 = st.slider("標的 C (如：三菱商事)", 50, 150, 100) / 100

# --- 核心邏輯計算 ---
prices = [s1, s2, s3]
worst_perf = min(prices)
principal = 100.0

# Super Bull 損益公式
# If Worst >= Strike: Principal * (Worst / Strike)
# If Worst < Strike: Physical Delivery (Value = Principal * (Worst / Strike))
payoff_pct = (worst_perf / strike_pct) * 100

# --- 結果呈現 ---
col1, col2 = st.columns([1, 2])

with col1:
    st.metric("最差標的表現 (Worst-of)", f"{round(worst_perf*100, 2)}%")
    
    if worst_perf >= strike_pct:
        st.success(f"✅ 觸發出場 / 到期獲利")
        st.write(f"預計拿回本金：**{round(payoff_pct, 2)}%**")
        st.write(f"額外獲利：{round(payoff_pct - 100, 2)}%")
    else:
        st.error(f"❌ 跌破 Strike")
        st.write(f"預計拿回價值：**{round(payoff_pct, 2)}%**")
        st.write(f"帳面虧損：{round(100 - payoff_pct, 2)}%")

with col2:
    # 畫一個簡單的 Payoff 圖表
    fig = go.Figure()
    # 畫出損益曲線
    x_range = [i/100 for i in range(50, 151)]
    y_payoff = [(x / strike_pct) * 100 for x in x_range]
    
    fig.add_trace(go.Scatter(x=x_range, y=y_payoff, name="Payoff Line", line=dict(color='royalblue', width=4)))
    # 標記目前點
    fig.add_trace(go.Scatter(x=[worst_perf], y=[payoff_pct], mode='markers', 
                             marker=dict(size=15, color='red'), name="Current Position"))
    
    fig.update_layout(title="到期損益曲線圖", xaxis_title="Worst-of 標的表現 (%)", yaxis_title="拿回本金比例 (%)")
    st.plotly_chart(fig, use_container_width=True)

st.info(f"💡 公式提醒：當 Worst-of 表現為 $P_{{end}}$ 時，到期贖回金額為 $Principal \\times \\frac{P_{{end}}}{Strike}$")
