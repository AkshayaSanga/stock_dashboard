import numpy as np
import pandas as pd


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add moving averages, daily returns, volatility, rolling volume,
    and 52-week range metrics to the stock data.
    """
    data = df.copy()

    data["MA_50"] = data["Close"].rolling(window=50).mean()
    data["MA_200"] = data["Close"].rolling(window=200).mean()
    data["Daily_Return"] = data["Close"].pct_change()
    data["Volatility_20D"] = data["Daily_Return"].rolling(window=20).std() * np.sqrt(252)
    data["Volume_Avg_20"] = data["Volume"].rolling(window=20).mean()
    data["52W_High"] = data["Close"].rolling(window=252).max()
    data["52W_Low"] = data["Close"].rolling(window=252).min()
    data["Return_20D"] = data["Close"].pct_change(periods=20)

    return data


def calculate_summary_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate summary statistics for the latest available stock data.
    """
    latest_close = df["Close"].iloc[-1]
    prev_close = df["Close"].iloc[-2] if len(df) > 1 else latest_close

    price_change = latest_close - prev_close
    price_change_pct = (price_change / prev_close) * 100 if prev_close != 0 else 0

    avg_volume_20d = df["Volume"].tail(20).mean() if "Volume" in df.columns else np.nan
    latest_volume = df["Volume"].iloc[-1] if "Volume" in df.columns else np.nan
    latest_volatility = df["Volatility_20D"].iloc[-1] if "Volatility_20D" in df.columns else np.nan
    high_52w = df["52W_High"].iloc[-1] if "52W_High" in df.columns else np.nan
    low_52w = df["52W_Low"].iloc[-1] if "52W_Low" in df.columns else np.nan
    return_20d = df["Return_20D"].iloc[-1] if "Return_20D" in df.columns else np.nan

    return {
        "latest_close": latest_close,
        "price_change": price_change,
        "price_change_pct": price_change_pct,
        "avg_volume_20d": avg_volume_20d,
        "latest_volume": latest_volume,
        "latest_volatility": latest_volatility,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "return_20d": return_20d,
    }


def generate_insight(df: pd.DataFrame) -> dict:
    """
    Generate automated insight text and labels based on moving averages and volatility.
    """
    latest_row = df.iloc[-1]

    close_price = latest_row.get("Close", np.nan)
    ma_50 = latest_row.get("MA_50", np.nan)
    ma_200 = latest_row.get("MA_200", np.nan)
    volatility = latest_row.get("Volatility_20D", np.nan)

    if pd.isna(ma_50) or pd.isna(ma_200):
        trend_text = "Insufficient data for long-term trend"
        trend_label = "neutral"
    elif close_price > ma_50 > ma_200:
        trend_text = "Bullish trend"
        trend_label = "bullish"
    elif close_price < ma_50 < ma_200:
        trend_text = "Bearish trend"
        trend_label = "bearish"
    else:
        trend_text = "Sideways / mixed trend"
        trend_label = "neutral"

    if pd.isna(volatility):
        volatility_text = "Volatility unavailable"
        volatility_label = "neutral"
    elif volatility > 0.40:
        volatility_text = "High volatility"
        volatility_label = "high"
    elif volatility < 0.20:
        volatility_text = "Stable trend"
        volatility_label = "stable"
    else:
        volatility_text = "Moderate volatility"
        volatility_label = "moderate"

    return {
        "trend_text": trend_text,
        "trend_label": trend_label,
        "volatility_text": volatility_text,
        "volatility_label": volatility_label,
        "full_text": f"{trend_text} | {volatility_text}",
    }


def normalize_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize close prices to a base value of 100 for easier comparison.
    """
    normalized_df = df.copy()
    numeric_columns = [col for col in normalized_df.columns if col != "Date"]

    for col in numeric_columns:
        first_valid_values = normalized_df[col].dropna()
        if not first_valid_values.empty:
            normalized_df[col] = (normalized_df[col] / first_valid_values.iloc[0]) * 100

    return normalized_df


def build_comparison_table(symbol_data: dict) -> pd.DataFrame:
    """
    Build a summary comparison table for multiple stocks.
    """
    rows = []

    for symbol, df in symbol_data.items():
        if df.empty:
            continue

        latest_price = df["Close"].iloc[-1]
        total_return = ((df["Close"].iloc[-1] / df["Close"].iloc[0]) - 1) * 100
        volatility = df["Volatility_20D"].iloc[-1] * 100 if not pd.isna(df["Volatility_20D"].iloc[-1]) else np.nan
        avg_volume = df["Volume"].tail(20).mean() if "Volume" in df.columns else np.nan

        rows.append(
            {
                "Stock": symbol,
                "Latest Price": round(latest_price, 2),
                "Total Return %": round(total_return, 2),
                "Volatility %": round(volatility, 2) if not pd.isna(volatility) else np.nan,
                "Avg Volume (20D)": round(avg_volume, 0) if not pd.isna(avg_volume) else np.nan,
            }
        )

    return pd.DataFrame(rows)


def split_gainers_losers(movers_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split movers into top gainers and losers.
    """
    if movers_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    gainers = movers_df.sort_values("Daily Change %", ascending=False).head(5).reset_index(drop=True)
    losers = movers_df.sort_values("Daily Change %", ascending=True).head(5).reset_index(drop=True)

    return gainers, losers


def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """
    Convert DataFrame to CSV bytes for download.
    """
    return df.to_csv(index=False).encode("utf-8")


def build_summary_report(df: pd.DataFrame, metrics: dict, symbol: str, insight: dict) -> pd.DataFrame:
    """
    Build a compact summary report for export.
    """
    latest_row = df.iloc[-1]

    report = pd.DataFrame(
        [
            {"Metric": "Stock Symbol", "Value": symbol},
            {"Metric": "Latest Close", "Value": round(metrics["latest_close"], 2)},
            {"Metric": "Daily Price Change", "Value": round(metrics["price_change"], 2)},
            {"Metric": "Daily Change %", "Value": round(metrics["price_change_pct"], 2)},
            {"Metric": "20-Day Average Volume", "Value": round(metrics["avg_volume_20d"], 2)},
            {"Metric": "Latest Volume", "Value": round(metrics["latest_volume"], 2)},
            {
                "Metric": "20-Day Volatility",
                "Value": round(metrics["latest_volatility"], 4) if pd.notna(metrics["latest_volatility"]) else "N/A",
            },
            {
                "Metric": "52-Week High",
                "Value": round(metrics["high_52w"], 2) if pd.notna(metrics["high_52w"]) else "N/A",
            },
            {
                "Metric": "52-Week Low",
                "Value": round(metrics["low_52w"], 2) if pd.notna(metrics["low_52w"]) else "N/A",
            },
            {
                "Metric": "20-Day Return",
                "Value": round(metrics["return_20d"], 4) if pd.notna(metrics["return_20d"]) else "N/A",
            },
            {"Metric": "Trend Signal", "Value": insight["trend_text"]},
            {"Metric": "Risk Signal", "Value": insight["volatility_text"]},
            {"Metric": "Latest Date", "Value": str(latest_row["Date"])},
        ]
    )

    return report