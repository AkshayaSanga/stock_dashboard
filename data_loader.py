import pandas as pd
import yfinance as yf
import streamlit as st

VALID_PERIODS = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    Fetch historical stock market data for a given symbol and period.
    """
    if period not in VALID_PERIODS:
        raise ValueError(f"Invalid period selected: {period}")

    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval="1d", auto_adjust=False)

    if df.empty:
        raise ValueError(f"No data returned for symbol: {symbol}")

    df = df.reset_index()
    df.columns = [str(col).strip().replace(" ", "_") for col in df.columns]

    if "Date" not in df.columns:
        raise ValueError("Expected 'Date' column not found in returned data.")

    required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
    available_columns = [col for col in required_columns if col in df.columns]
    df = df[available_columns].copy()

    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    df = df.dropna(subset=["Close"]).reset_index(drop=True)

    return df


@st.cache_data(ttl=300, show_spinner=False)
def fetch_multiple_closing_prices(symbols: list[str], period: str = "1y") -> pd.DataFrame:
    """
    Fetch close prices for multiple symbols and combine into one DataFrame.
    """
    combined_df = pd.DataFrame()

    for symbol in symbols:
        temp_df = fetch_stock_data(symbol, period)
        temp_df = temp_df[["Date", "Close"]].copy()
        temp_df.rename(columns={"Close": symbol}, inplace=True)

        if combined_df.empty:
            combined_df = temp_df
        else:
            combined_df = pd.merge(combined_df, temp_df, on="Date", how="outer")

    combined_df = combined_df.sort_values("Date").reset_index(drop=True)
    return combined_df


@st.cache_data(ttl=300, show_spinner=False)
def fetch_market_movers(symbols: list[str], period: str = "5d") -> pd.DataFrame:
    """
    Build a small movers table from a custom watchlist.
    """
    rows = []

    for symbol in symbols:
        try:
            df = fetch_stock_data(symbol, period)

            if len(df) < 2:
                continue

            latest_close = df["Close"].iloc[-1]
            prev_close = df["Close"].iloc[-2]

            change_pct = ((latest_close - prev_close) / prev_close) * 100 if prev_close != 0 else 0

            rows.append(
                {
                    "Symbol": symbol,
                    "Latest Price": round(latest_close, 2),
                    "Daily Change %": round(change_pct, 2),
                    "Volume": int(df["Volume"].iloc[-1]),
                }
            )
        except Exception:
            continue

    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_news(symbol: str, max_items: int = 6) -> list[dict]:
    """
    Fetch recent stock news using yfinance ticker news.
    Handles multiple response formats safely.
    """
    try:
        ticker = yf.Ticker(symbol)
        news_items = getattr(ticker, "news", None)

        if not news_items:
            return []

        cleaned_news = []

        for item in news_items[: max_items * 3]:
            title = None
            publisher = None
            link = None

            if isinstance(item, dict):
                # Flat format
                title = item.get("title")
                publisher = item.get("publisher")
                link = item.get("link")

                # Nested content format
                content = item.get("content", {})
                if isinstance(content, dict):
                    if not title:
                        title = content.get("title")

                    provider = content.get("provider", {})
                    if isinstance(provider, dict) and not publisher:
                        publisher = provider.get("displayName")

                    canonical_url = content.get("canonicalUrl", {})
                    if isinstance(canonical_url, dict) and not link:
                        link = canonical_url.get("url")

                # Another provider format
                provider = item.get("provider", {})
                if isinstance(provider, dict) and not publisher:
                    publisher = provider.get("displayName")

            if title and link:
                cleaned_news.append(
                    {
                        "title": title,
                        "publisher": publisher if publisher else "Yahoo Finance",
                        "link": link,
                    }
                )

            if len(cleaned_news) >= max_items:
                break

        return cleaned_news

    except Exception:
        return []