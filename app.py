import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from data_loader import (
    fetch_stock_data,
    fetch_multiple_closing_prices,
    fetch_market_movers,
    fetch_stock_news,
    VALID_PERIODS,
)
from analytics import (
    add_technical_indicators,
    calculate_summary_metrics,
    generate_insight,
    normalize_prices,
    build_comparison_table,
    split_gainers_losers,
    convert_df_to_csv,
    build_summary_report,
)

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Real-Time Stock Market Analytics Dashboard",
    page_icon="📈",
    layout="wide",
)

# ---------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------
st.markdown(
    """
    <style>
    .main {
        background-color: #0b1220;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }

    .dashboard-header {
        padding: 1rem 0 0.25rem 0;
    }

    .dashboard-title {
        font-size: 2rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.25rem;
    }

    .dashboard-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 1rem;
    }

    .signal-box {
        padding: 14px 16px;
        border-radius: 14px;
        font-weight: 600;
        margin-top: 0.25rem;
        margin-bottom: 1rem;
        font-size: 15px;
    }

    .bullish {
        background-color: rgba(34, 197, 94, 0.12);
        border: 1px solid #22c55e;
        color: #bbf7d0;
    }

    .bearish {
        background-color: rgba(239, 68, 68, 0.12);
        border: 1px solid #ef4444;
        color: #fecaca;
    }

    .neutral {
        background-color: rgba(59, 130, 246, 0.12);
        border: 1px solid #3b82f6;
        color: #bfdbfe;
    }

    .high {
        background-color: rgba(249, 115, 22, 0.12);
        border: 1px solid #f97316;
        color: #fed7aa;
    }

    .stable {
        background-color: rgba(16, 185, 129, 0.12);
        border: 1px solid #10b981;
        color: #a7f3d0;
    }

    .moderate {
        background-color: rgba(234, 179, 8, 0.12);
        border: 1px solid #eab308;
        color: #fde68a;
    }

    .news-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
    }

    .news-title {
        font-size: 1rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 0.35rem;
    }

    .news-meta {
        font-size: 0.85rem;
        color: #94a3b8;
    }

    hr {
        border: none;
        height: 1px;
        background: #1e293b;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.title("⚙️ Dashboard Controls")

available_symbols = [
    "AAPL",
    "TSLA",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
]

selected_symbol = st.sidebar.selectbox(
    "Select primary stock",
    available_symbols,
    index=0,
)

comparison_symbols = st.sidebar.multiselect(
    "Select stocks for comparison",
    available_symbols,
    default=["AAPL", "MSFT", "TSLA"],
)

selected_period = st.sidebar.selectbox(
    "Select historical period",
    VALID_PERIODS,
    index=3,
)

st.sidebar.markdown("---")
st.sidebar.caption("Data source: Yahoo Finance (yfinance)")

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.markdown(
    """
    <div class="dashboard-header">
        <div class="dashboard-title">📊 Real-Time Stock Market Analytics Dashboard</div>
        <div class="dashboard-subtitle">Live market analytics with interactive financial insights</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ---------------------------------------------------
# DATA LOADING
# ---------------------------------------------------
try:
    df = fetch_stock_data(selected_symbol, selected_period)
    df = add_technical_indicators(df)
    metrics = calculate_summary_metrics(df)
    insight = generate_insight(df)
except Exception as error:
    st.error(f"Error loading stock data: {error}")
    st.stop()

# ---------------------------------------------------
# TOP AREA: METRICS + MOVERS
# ---------------------------------------------------
left_top, right_top = st.columns([2.2, 1.2])

with left_top:
    st.subheader("Market Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        label="Latest Price",
        value=f"${metrics['latest_close']:.2f}",
        delta=f"{metrics['price_change_pct']:.2f}%",
    )

    col2.metric(
        label="Daily Change",
        value=f"${metrics['price_change']:.2f}",
        delta=f"{metrics['price_change_pct']:.2f}%",
    )

    col3.metric(
        label="20-Day Avg Volume",
        value=f"{metrics['avg_volume_20d']:,.0f}",
    )

    col4.metric(
        label="20-Day Volatility",
        value=f"{metrics['latest_volatility']:.2%}" if pd.notna(metrics["latest_volatility"]) else "N/A",
    )

    col5, col6, col7, col8 = st.columns(4)

    col5.metric(
        label="Latest Volume",
        value=f"{metrics['latest_volume']:,.0f}" if pd.notna(metrics["latest_volume"]) else "N/A",
    )

    col6.metric(
        label="52-Week High",
        value=f"${metrics['high_52w']:.2f}" if pd.notna(metrics["high_52w"]) else "N/A",
    )

    col7.metric(
        label="52-Week Low",
        value=f"${metrics['low_52w']:.2f}" if pd.notna(metrics["low_52w"]) else "N/A",
    )

    col8.metric(
        label="20-Day Return",
        value=f"{metrics['return_20d']:.2%}" if pd.notna(metrics["return_20d"]) else "N/A",
    )

    st.markdown(
        f'<div class="signal-box {insight["trend_label"]}">Trend Signal: {insight["trend_text"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="signal-box {insight["volatility_label"]}">Risk Signal: {insight["volatility_text"]}</div>',
        unsafe_allow_html=True,
    )

with right_top:
    st.subheader("Top Gainers & Losers")

    movers_watchlist = [
        "AAPL", "TSLA", "MSFT", "GOOGL", "AMZN",
        "NVDA", "META", "RELIANCE.NS", "TCS.NS", "INFY.NS"
    ]
    movers_df = fetch_market_movers(movers_watchlist, period="5d")
    gainers_df, losers_df = split_gainers_losers(movers_df)

    gainers_col, losers_col = st.columns(2)

    with gainers_col:
        st.markdown("**Top Gainers**")
        if not gainers_df.empty:
            st.dataframe(
                gainers_df[["Symbol", "Latest Price", "Daily Change %"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No gainers data available")

    with losers_col:
        st.markdown("**Top Losers**")
        if not losers_df.empty:
            st.dataframe(
                losers_df[["Symbol", "Latest Price", "Daily Change %"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No losers data available")

st.markdown("---")

# ---------------------------------------------------
# TABS
# ---------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "Price Trend",
        "Candlestick",
        "Volume",
        "Returns",
        "Volatility",
        "Comparison",
        "News & Export",
    ]
)

# ---------------------------------------------------
# TAB 1: PRICE TREND
# ---------------------------------------------------
with tab1:
    st.subheader(f"{selected_symbol} Price Trend with Moving Averages")

    fig_price = go.Figure()

    fig_price.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Close"],
            mode="lines",
            name="Close Price",
            line=dict(width=2),
        )
    )

    fig_price.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["MA_50"],
            mode="lines",
            name="50-Day MA",
        )
    )

    fig_price.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["MA_200"],
            mode="lines",
            name="200-Day MA",
        )
    )

    fig_price.update_layout(
        template="plotly_dark",
        height=500,
        xaxis_title="Date",
        yaxis_title="Price",
        legend_title="Legend",
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig_price, use_container_width=True)

    st.subheader("Closing Price Distribution")

    fig_hist = px.histogram(
        df,
        x="Close",
        nbins=30,
        template="plotly_dark",
        title="Closing Price Distribution",
    )

    fig_hist.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    st.plotly_chart(fig_hist, use_container_width=True)

# ---------------------------------------------------
# TAB 2: CANDLESTICK
# ---------------------------------------------------
with tab2:
    st.subheader("Historical Candlestick Chart")

    fig_candle = go.Figure(
        data=[
            go.Candlestick(
                x=df["Date"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Candlestick",
            )
        ]
    )

    fig_candle.update_layout(
        template="plotly_dark",
        height=550,
        xaxis_title="Date",
        yaxis_title="Price",
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig_candle, use_container_width=True)

# ---------------------------------------------------
# TAB 3: VOLUME
# ---------------------------------------------------
with tab3:
    st.subheader("Volume Analysis")

    fig_volume = px.bar(
        df,
        x="Date",
        y="Volume",
        template="plotly_dark",
        title=f"Trading Volume - {selected_symbol}",
    )

    fig_volume.update_layout(
        height=450,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    st.plotly_chart(fig_volume, use_container_width=True)

    fig_volume_line = go.Figure()

    fig_volume_line.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Volume"],
            mode="lines",
            name="Volume",
        )
    )

    fig_volume_line.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Volume_Avg_20"],
            mode="lines",
            name="20-Day Avg Volume",
        )
    )

    fig_volume_line.update_layout(
        template="plotly_dark",
        height=450,
        xaxis_title="Date",
        yaxis_title="Volume",
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig_volume_line, use_container_width=True)

# ---------------------------------------------------
# TAB 4: RETURNS
# ---------------------------------------------------
with tab4:
    st.subheader("Daily Return Analysis")

    fig_returns = px.line(
        df,
        x="Date",
        y="Daily_Return",
        template="plotly_dark",
        title="Daily Return Trend",
    )

    fig_returns.update_layout(
        height=450,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    st.plotly_chart(fig_returns, use_container_width=True)

# ---------------------------------------------------
# TAB 5: VOLATILITY
# ---------------------------------------------------
with tab5:
    st.subheader("Rolling Volatility (20-Day Annualized)")

    fig_vol = px.line(
        df,
        x="Date",
        y="Volatility_20D",
        template="plotly_dark",
        title="Volatility Trend",
    )

    fig_vol.update_layout(
        height=450,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    st.plotly_chart(fig_vol, use_container_width=True)

# ---------------------------------------------------
# TAB 6: COMPARISON
# ---------------------------------------------------
with tab6:
    st.subheader("Multi-Stock Performance Comparison")

    try:
        if len(comparison_symbols) >= 2:
            comp_df = fetch_multiple_closing_prices(comparison_symbols, selected_period)
            normalized_df = normalize_prices(comp_df)

            fig_compare = go.Figure()

            for symbol in comparison_symbols:
                fig_compare.add_trace(
                    go.Scatter(
                        x=normalized_df["Date"],
                        y=normalized_df[symbol],
                        mode="lines",
                        name=symbol,
                    )
                )

            fig_compare.update_layout(
                template="plotly_dark",
                height=500,
                xaxis_title="Date",
                yaxis_title="Normalized Price (Base = 100)",
                margin=dict(l=20, r=20, t=40, b=20),
            )

            st.plotly_chart(fig_compare, use_container_width=True)

            symbol_data = {}
            for symbol in comparison_symbols:
                temp_df = fetch_stock_data(symbol, selected_period)
                temp_df = add_technical_indicators(temp_df)
                symbol_data[symbol] = temp_df

            comparison_table = build_comparison_table(symbol_data)

            st.subheader("Comparison Summary Table")
            st.dataframe(comparison_table, use_container_width=True, hide_index=True)

        else:
            st.warning("Select at least 2 stocks for comparison.")
    except Exception as error:
        st.error(f"Error loading comparison data: {error}")

# ---------------------------------------------------
# TAB 7: NEWS & EXPORT
# ---------------------------------------------------
with tab7:
    left_news, right_export = st.columns([1.8, 1])

    with left_news:
        st.subheader(f"{selected_symbol} Market News")

        news_items = fetch_stock_news(selected_symbol, max_items=6)

        if news_items:
            for item in news_items:
                title = item.get("title", "No title")
                publisher = item.get("publisher", "Unknown publisher")
                link = item.get("link", "")

                st.markdown(
                    f"""
                    <div class="news-card">
                        <div class="news-title">{title}</div>
                        <div class="news-meta">{publisher}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if link:
                    st.link_button("Open article", link)
        else:
            st.info("News is not available right now for this symbol.")

    with right_export:
        st.subheader("Download Report")

        summary_report = build_summary_report(df, metrics, selected_symbol, insight)
        detailed_export = df.copy()

        st.markdown("**Summary Report Preview**")
        st.dataframe(summary_report, use_container_width=True, hide_index=True)

        summary_csv = convert_df_to_csv(summary_report)
        data_csv = convert_df_to_csv(detailed_export)

        st.download_button(
            label="⬇ Download Summary Report (CSV)",
            data=summary_csv,
            file_name=f"{selected_symbol}_summary_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.download_button(
            label="⬇ Download Processed Data (CSV)",
            data=data_csv,
            file_name=f"{selected_symbol}_processed_stock_data.csv",
            mime="text/csv",
            use_container_width=True,
        )

st.markdown("---")
st.subheader("Processed Data Preview")
st.dataframe(df.tail(20), use_container_width=True, hide_index=True)