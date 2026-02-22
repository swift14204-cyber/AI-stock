import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta  # 导入技术分析库
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 页面配置
st.set_page_config(page_title="进阶股票分析工具", layout="wide")
st.title("🚀 进阶股票分析 + 多维度预测")

def get_ticker_from_name(query):
    try:
        search = yf.Search(query, max_results=1)
        return search.quotes[0]['symbol'] if search.quotes else query.upper()
    except:
        return query.upper()

user_input = st.text_input("输入股票名称或代码", value="AAPL")

if user_input:
    symbol = get_ticker_from_name(user_input)
    # 获取更久的数据以计算技术指标
    df = yf.Ticker(symbol).history(period="2y") 

    if not df.empty:
        # --- 技巧 A & B：计算技术指标和滚动平均 ---
        # 计算 RSI (14天强弱指标)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        # 计算 MACD
        macd = ta.macd(df['Close'])
        df = pd.concat([df, macd], axis=1)
        # 计算 20 日和 50 日滚动移动平均线 (技巧 B)
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)

        # --- 技巧 C：简单情绪辅助（成交量分析） ---
        avg_volume = df['Volume'].tail(20).mean()
        curr_volume = df['Volume'].iloc[-1]
        vol_status = "放量" if curr_volume > avg_volume * 1.5 else "平稳"

        # 1. 顶部指标展示
        curr_price = df['Close'].iloc[-1]
        curr_rsi = df['RSI'].iloc[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("当前价格", f"${curr_price:.2f}")
        col2.metric("RSI (14)", f"{curr_rsi:.2f}", help=">70超买, <30超卖")
        col3.metric("市场情绪(成交量)", vol_status)
        col4.metric("20日均线", f"${df['SMA_20'].iloc[-1]:.2f}")

        # 2. 增强型图表
        # --- 优化后的绘图部分 ---
        fig = go.Figure()
        
        # 1. 主股价线：绿色加粗，最显眼
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="实时收盘价", 
                                 line=dict(color='#00FF00', width=3)))
        
        # 2. 均线：半透明一点，不要抢主线的风头
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="20日线(月趋势)", 
                                 line=dict(color='red', width=1.5, dash='solid')))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="50日线(季趋势)", 
                                 line=dict(color='royalblue', width=1.5, dash='solid')))

        # 3. 预测线：让它更明显
        last_sma = df['SMA_20'].tail(15).dropna()
        if len(last_sma) > 1:
            x_sma = np.arange(len(last_sma))
            slope, intercept = np.polyfit(x_sma, last_sma.values, 1)
            future_days = 14 # 改为预测14天
            future_dates = [df.index[-1] + timedelta(days=i) for i in range(1, future_days + 1)]
            preds = slope * (np.arange(len(last_sma), len(last_sma) + future_days)) + intercept
            fig.add_trace(go.Scatter(x=future_dates, y=preds, name="趋势外推预测", 
                                     line=dict(dash='dashdot', color='orange', width=2)))

        # 4. 解决你之前的 width 警告
        fig.update_layout(height=600, template="plotly_dark", hovermode="x unified",
                          title=f"{symbol} 深度技术分析图")
        st.plotly_chart(fig, width='stretch') # 这里改成了 stretch 消除警告
        
        # 3. RSI 风险提示
        if curr_rsi > 70:
            st.warning("⚠️ RSI 提示超买，短期可能存在回调风险。")
        elif curr_rsi < 30:
            st.success("✅ RSI 提示超卖，可能存在反弹机会。")

    else:
        st.error("无法获取数据。")
