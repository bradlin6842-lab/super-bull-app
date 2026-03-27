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
    
    # 這裡讓使用者輸入 Strike，例如圖中的 90% 或 85%
    strike_pct_input = st.slider("Strike / Barrier (%)", 70.0, 100.0, 90.0)
    strike_val = strike_pct_input / 100
    
    # 圖中的 Bonus Coupon (Flat)
    bonus_flat = st.number_input("Bonus Coupon (Flat %)", value=9.46)
    
    st.divider()
    st.write("🔍 **標的比價設定 (相對於期初價 %)**")
    # 模擬三檔標的的表現
    s1 = st.slider("標的 A (如：任天堂)", 50, 150, 100) / 100
    s2 = st.slider("標的 B (如：日本郵船)", 50, 150, 100) / 100
    s3 = st.slider("標的 C (如 : 三菱商事)", 50, 150, 100) / 100

# --- 核心邏輯計算 ---
prices = [s1, s2, s3]
worst_perf = min(prices)
principal = 100.0

# Super Bull 損益公式：
# 贖回金額 = 本金 * (最差標的表現 / Strike)
# 注意：當最差表現 >= Strike 時，這會大於 100% (即為 Super Bull 的看漲紅利)
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
        st.caption(f"註：若為提前出場，尚需參考 Bonus Coupon {bonus_flat}% 之約定。")
    else:
        st.error("❌ 狀態：跌破 Strike (虧損/接貨)")
        st.write(f"預計拿回價值：**{round(payoff_pct, 2)}%**")
        st.write(f"帳面虧損：{round(100 - payoff_pct, 2)}% ({currency})")
        st.info("此情況通常會轉換為實體股票交付。")

with col2:
    # 畫出損益曲線圖
    fig = go.Figure()
    
    # 建立橫軸數據 (標的表現從 50% 到 150%)
    x_range = [i/100 for i in range(50, 151)]
    # 根據公式計算縱軸 (Payoff)
    y_payoff = [(x / strike_val) * 100 for x in x_range]
    
    # 繪製主線
    fig.add_trace(go.Scatter(
        x=[x*100 for x in x_range], 
        y=y_payoff, 
        name="到期損益線",
        line=dict(color='royalblue', width=4)
    ))
    
    # 標記目前位置
    fig.add_trace(go.Scatter(
        x=[worst_perf * 100], 
        y=[payoff_pct], 
        mode='markers', 
        marker=dict(size=15, color='red', symbol='cross'),
        name="目前模擬位置"
    ))
    
    # 繪製 Strike 參考線
    fig.add_vline(x=strike_pct_input, line_dash="dash", line_color="green", annotation_text="Strike Barrier")
    fig.add_hline(y=100, line_dash="dot", line_color="gray")

    fig.update_layout(
        title="Super Bull 到期損益曲線 (Worst-of)",
        xaxis_title="最差標的表現 (%)",
        yaxis_title="贖回本金價值 (%)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

# 修正後的 LaTeX 顯示區域 (不使用 f-string 以避免大括號衝突)
st.divider()
st.info("💡 **計價公式提醒**")
st.latex(r"Redemption = Principal \times \frac{P_{end}}{Strike}")
st.write("其中 $P_{end}$ 為期末觀察日表現最差標的之收盤價格百分比。")
