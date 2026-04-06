from __future__ import annotations

import json
import threading
import time
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from typing import Any

import pandas as pd
import yfinance as yf
from cachetools import TTLCache
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

MASTER_STOCKS = [
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "exchange": "NSE"},
    {"symbol": "INFY.NS", "name": "Infosys", "exchange": "NSE"},
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "exchange": "NSE"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "exchange": "NSE"},
    {"symbol": "WIPRO.NS", "name": "Wipro", "exchange": "NSE"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "exchange": "NSE"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "exchange": "NSE"},
    {"symbol": "ITC.NS", "name": "ITC", "exchange": "NSE"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "exchange": "NSE"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance", "exchange": "NSE"},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises", "exchange": "NSE"},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors", "exchange": "NSE"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki", "exchange": "NSE"},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharmaceutical", "exchange": "NSE"},
    {"symbol": "TITAN.NS", "name": "Titan Company", "exchange": "NSE"},
    {"symbol": "TECHM.NS", "name": "Tech Mahindra", "exchange": "NSE"},
    {"symbol": "HCLTECH.NS", "name": "HCL Technologies", "exchange": "NSE"},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank", "exchange": "NSE"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "exchange": "NSE"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro", "exchange": "NSE"},
    {"symbol": "ONGC.NS", "name": "ONGC", "exchange": "NSE"},
    {"symbol": "NTPC.NS", "name": "NTPC", "exchange": "NSE"},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corporation", "exchange": "NSE"},
    {"symbol": "COALINDIA.NS", "name": "Coal India", "exchange": "NSE"},
    {"symbol": "BPCL.NS", "name": "Bharat Petroleum", "exchange": "NSE"},
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement", "exchange": "NSE"},
    {"symbol": "NESTLEIND.NS", "name": "Nestle India", "exchange": "NSE"},
    {"symbol": "BRITANNIA.NS", "name": "Britannia Industries", "exchange": "NSE"},
    {"symbol": "AAPL", "name": "Apple", "exchange": "NASDAQ"},
    {"symbol": "MSFT", "name": "Microsoft", "exchange": "NASDAQ"},
    {"symbol": "GOOGL", "name": "Alphabet", "exchange": "NASDAQ"},
    {"symbol": "AMZN", "name": "Amazon", "exchange": "NASDAQ"},
    {"symbol": "META", "name": "Meta Platforms", "exchange": "NASDAQ"},
    {"symbol": "TSLA", "name": "Tesla", "exchange": "NASDAQ"},
    {"symbol": "NVDA", "name": "NVIDIA", "exchange": "NASDAQ"},
    {"symbol": "JPM", "name": "JPMorgan Chase", "exchange": "NYSE"},
    {"symbol": "BAC", "name": "Bank of America", "exchange": "NYSE"},
    {"symbol": "WMT", "name": "Walmart", "exchange": "NYSE"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "exchange": "NYSE"},
    {"symbol": "PG", "name": "Procter & Gamble", "exchange": "NYSE"},
    {"symbol": "V", "name": "Visa", "exchange": "NYSE"},
    {"symbol": "MA", "name": "Mastercard", "exchange": "NYSE"},
    {"symbol": "UNH", "name": "UnitedHealth Group", "exchange": "NYSE"},
    {"symbol": "HD", "name": "Home Depot", "exchange": "NYSE"},
    {"symbol": "DIS", "name": "Walt Disney", "exchange": "NYSE"},
    {"symbol": "NFLX", "name": "Netflix", "exchange": "NASDAQ"},
    {"symbol": "PYPL", "name": "PayPal", "exchange": "NASDAQ"},
    {"symbol": "INTC", "name": "Intel", "exchange": "NASDAQ"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "exchange": "NASDAQ"},
    {"symbol": "CSCO", "name": "Cisco", "exchange": "NASDAQ"},
    {"symbol": "PFE", "name": "Pfizer", "exchange": "NYSE"},
    {"symbol": "KO", "name": "Coca-Cola", "exchange": "NYSE"},
    {"symbol": "PEP", "name": "PepsiCo", "exchange": "NASDAQ"},
    {"symbol": "MCD", "name": "McDonald's", "exchange": "NYSE"},
    {"symbol": "NKE", "name": "Nike", "exchange": "NYSE"},
    {"symbol": "SBUX", "name": "Starbucks", "exchange": "NASDAQ"},
    {"symbol": "UBER", "name": "Uber", "exchange": "NYSE"},
]

MARKET_OVERVIEW_SYMBOLS = [
    {"symbol": "^NSEI", "name": "Nifty 50"},
    {"symbol": "^BSESN", "name": "Sensex"},
    {"symbol": "^GSPC", "name": "S&P 500"},
]

TRENDING_UNIVERSE_SYMBOLS = [
    "TCS.NS",
    "INFY.NS",
    "RELIANCE.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "ITC.NS",
    "LT.NS",
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",
    "NVDA",
    "JPM",
    "WMT",
    "V",
    "MA",
    "NFLX",
    "AMD",
    "INTC",
    "DIS",
    "UBER",
]

STOCK_LOOKUP = {item["symbol"]: item for item in MASTER_STOCKS}


@dataclass
class StockSnapshot:
    symbol: str
    name: str
    currency: str
    current_price: float
    daily_change: float
    daily_change_pct: float
    week_52_high: float
    week_52_low: float
    market_cap: str
    volume: int
    technical_indicators: dict[str, float]
    historical_prices: list[dict[str, Any]]
    dataframe: pd.DataFrame


class StockDataService:
    def __init__(self) -> None:
        self.history_cache: TTLCache[str, pd.DataFrame] = TTLCache(maxsize=512, ttl=900)
        self.quote_cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=512, ttl=900)
        self.universe_snapshot_cache: TTLCache[str, list[dict[str, Any]]] = TTLCache(maxsize=4, ttl=900)
        self.trending_counter: Counter[str] = Counter()

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return symbol.strip().upper()

    @staticmethod
    def _format_market_cap(value: float | int | None) -> str:
        if not value:
            return "N/A"
        value = float(value)
        for suffix, divisor in [("T", 1e12), ("B", 1e9), ("M", 1e6)]:
            if value >= divisor:
                return f"{value / divisor:.2f}{suffix}"
        return f"{value:.0f}"

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def _fetch_history(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        key = f"{symbol}:{period}"
        if key in self.history_cache:
            return self.history_cache[key].copy()

        ticker = yf.Ticker(symbol)
        history_timeout = 8.0 if period in {"1y", "2y", "max"} else 5.0
        finished, raw_df, error = self._run_with_timeout(
            lambda: ticker.history(period=period, interval="1d", auto_adjust=False),
            timeout_sec=history_timeout,
        )
        if not finished:
            raise RuntimeError(f"Market data request timed out for symbol: {symbol}")
        if error is not None:
            raise RuntimeError(f"Market data request failed for symbol {symbol}: {error}")

        df = raw_df
        if df is None or df.empty:
            raise ValueError(f"No data found for symbol: {symbol}")

        df = df.reset_index()
        if "Date" not in df.columns:
            raise ValueError(f"Unexpected data format from yfinance for symbol: {symbol}")

        cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
        df = df[cols].copy()

        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna().reset_index(drop=True)
        if df.empty:
            raise ValueError(f"No clean data available for symbol: {symbol}")

        self.history_cache[key] = df
        return df.copy()

    @staticmethod
    def _with_indicators(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        close = out["Close"]

        out["ma_50"] = close.rolling(50).mean()
        out["ma_200"] = close.rolling(200).mean()

        rsi = RSIIndicator(close=close, window=14)
        out["rsi"] = rsi.rsi()

        macd = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
        out["macd"] = macd.macd()
        out["macd_signal"] = macd.macd_signal()

        bb = BollingerBands(close=close, window=20, window_dev=2)
        out["bb_upper"] = bb.bollinger_hband()
        out["bb_middle"] = bb.bollinger_mavg()
        out["bb_lower"] = bb.bollinger_lband()

        return out

    @staticmethod
    def _history_records(df: pd.DataFrame) -> list[dict[str, Any]]:
        records = []
        for _, row in df.iterrows():
            records.append(
                {
                    "date": row["Date"].strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 4),
                    "high": round(float(row["High"]), 4),
                    "low": round(float(row["Low"]), 4),
                    "close": round(float(row["Close"]), 4),
                    "volume": int(row["Volume"]),
                }
            )
        return records

    def get_stock_snapshot(self, symbol: str) -> StockSnapshot:
        symbol = self._normalize_symbol(symbol)
        self.trending_counter[symbol] += 1

        base_df = self._fetch_history(symbol, period="1y")
        df = self._with_indicators(base_df)

        if len(df) < 220:
            raise ValueError("Not enough data points to compute indicators reliably.")

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        current_price = float(latest["Close"])
        daily_change = current_price - float(prev["Close"])
        daily_change_pct = (daily_change / float(prev["Close"])) * 100.0 if float(prev["Close"]) else 0.0

        trailing = df.tail(252)
        week_52_high = float(trailing["High"].max())
        week_52_low = float(trailing["Low"].min())

        ticker = yf.Ticker(symbol)
        fast_info = getattr(ticker, "fast_info", None)
        market_cap = self._format_market_cap(getattr(fast_info, "market_cap", None))
        currency = getattr(fast_info, "currency", None) or ("INR" if symbol.endswith(".NS") else "USD")

        details = STOCK_LOOKUP.get(symbol, {"name": symbol, "exchange": "N/A"})
        technicals = {
            "rsi": round(float(latest.get("rsi", 0.0)), 4),
            "macd": round(float(latest.get("macd", 0.0)), 4),
            "macd_signal": round(float(latest.get("macd_signal", 0.0)), 4),
            "ma_50": round(float(latest.get("ma_50", 0.0)), 4),
            "ma_200": round(float(latest.get("ma_200", 0.0)), 4),
            "bollinger_upper": round(float(latest.get("bb_upper", 0.0)), 4),
            "bollinger_middle": round(float(latest.get("bb_middle", 0.0)), 4),
            "bollinger_lower": round(float(latest.get("bb_lower", 0.0)), 4),
        }

        six_months = df.tail(126)

        return StockSnapshot(
            symbol=symbol,
            name=details["name"],
            currency=currency,
            current_price=round(current_price, 4),
            daily_change=round(daily_change, 4),
            daily_change_pct=round(daily_change_pct, 4),
            week_52_high=round(week_52_high, 4),
            week_52_low=round(week_52_low, 4),
            market_cap=market_cap,
            volume=int(latest["Volume"]),
            technical_indicators=technicals,
            historical_prices=self._history_records(six_months),
            dataframe=df,
        )

    def get_history(self, symbol: str, period: str = "1y") -> list[dict[str, Any]]:
        symbol = self._normalize_symbol(symbol)
        self.trending_counter[symbol] += 1

        df = self._fetch_history(symbol, period=period)
        return self._history_records(df)

    def search_stocks(self, query: str) -> list[dict[str, str]]:
        q = query.strip().lower()
        if not q:
            return MASTER_STOCKS[:10]

        matches = [
            item
            for item in MASTER_STOCKS
            if q in item["symbol"].lower() or q in item["name"].lower() or q in item["exchange"].lower()
        ]
        return matches[:20]

    def _build_quote_snapshot(
        self,
        symbol: str,
        latest_close: float,
        prev_close: float,
        volume: int,
    ) -> dict[str, Any]:
        change = latest_close - prev_close
        change_pct = (change / prev_close) * 100.0 if prev_close else 0.0
        meta = STOCK_LOOKUP.get(symbol, {"name": symbol, "exchange": "N/A"})
        return {
            "symbol": symbol,
            "name": meta["name"],
            "exchange": meta["exchange"],
            "price": round(float(latest_close), 4),
            "daily_change": round(float(change), 4),
            "daily_change_pct": round(float(change_pct), 4),
            "volume": int(volume),
        }

    def _snapshot_from_frame(self, symbol: str, frame: pd.DataFrame) -> dict[str, Any] | None:
        df = frame.copy()
        df.columns = [str(c).strip() for c in df.columns]

        if "Close" not in df.columns and "Adj Close" in df.columns:
            df["Close"] = df["Adj Close"]
        if "Close" not in df.columns:
            return None
        if "Volume" not in df.columns:
            df["Volume"] = 0

        close_series = pd.to_numeric(df["Close"], errors="coerce").dropna()
        if len(close_series) < 2:
            return None

        latest_close = float(close_series.iloc[-1])
        prev_close = float(close_series.iloc[-2])

        volume_series = pd.to_numeric(df["Volume"], errors="coerce").dropna()
        volume = int(volume_series.iloc[-1]) if len(volume_series) else 0

        return self._build_quote_snapshot(symbol, latest_close, prev_close, volume)

    def _cached_history_snapshot(self, symbol: str) -> dict[str, Any] | None:
        for period in ("1mo", "1y"):
            key = f"{symbol}:{period}"
            cached_df = self.history_cache.get(key)
            if cached_df is None or cached_df.empty:
                continue
            snapshot = self._snapshot_from_frame(symbol, cached_df)
            if snapshot:
                return snapshot
        return None

    @staticmethod
    def _run_with_timeout(func, timeout_sec: float) -> tuple[bool, Any, Exception | None]:
        done = threading.Event()
        state: dict[str, Any] = {"value": None, "error": None}

        def _worker() -> None:
            try:
                state["value"] = func()
            except Exception as exc:
                state["error"] = exc
            finally:
                done.set()

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        finished = done.wait(timeout_sec)
        if not finished:
            return False, None, None
        return True, state["value"], state["error"]

    def _fetch_quote_snapshots(self, symbols: list[str], timeout_sec: float = 3.0) -> dict[str, dict[str, Any]]:
        normalized = [self._normalize_symbol(s) for s in symbols if s]
        if not normalized:
            return {}

        unique_symbols = list(dict.fromkeys(normalized))

        def _download_payload() -> list[dict[str, Any]]:
            try:
                df = yf.download(
                    unique_symbols,
                    period="5d",
                    interval="1d",
                    auto_adjust=False,
                    progress=False,
                    threads=False,
                )
                if df is None or df.empty:
                    return []

                data_list: list[dict[str, Any]] = []

                if not isinstance(df.columns, pd.MultiIndex):
                    # Single symbol — simple column names
                    sym = unique_symbols[0]
                    close = pd.to_numeric(df.get("Close", pd.Series(dtype=float)), errors="coerce").dropna()
                    vol = pd.to_numeric(df.get("Volume", pd.Series(dtype=float)), errors="coerce").dropna()
                    if len(close) >= 2:
                        data_list.append({
                            "symbol": sym,
                            "price": float(close.iloc[-1]),
                            "prev_close": float(close.iloc[-2]),
                            "volume": int(vol.iloc[-1]) if len(vol) > 0 else 0,
                        })
                else:
                    # Multiple symbols — MultiIndex columns (field, symbol)
                    close_df = df["Close"] if "Close" in df else pd.DataFrame()
                    vol_df = df["Volume"] if "Volume" in df else pd.DataFrame()
                    for sym in unique_symbols:
                        try:
                            if sym not in close_df.columns:
                                continue
                            close = pd.to_numeric(close_df[sym], errors="coerce").dropna()
                            if len(close) < 2:
                                continue
                            vol = pd.to_numeric(vol_df[sym], errors="coerce").dropna() if sym in vol_df.columns else pd.Series(dtype=float)
                            data_list.append({
                                "symbol": sym,
                                "price": float(close.iloc[-1]),
                                "prev_close": float(close.iloc[-2]),
                                "volume": int(vol.iloc[-1]) if len(vol) > 0 else 0,
                            })
                        except Exception:
                            continue

                return data_list
            except Exception:
                return []

        finished, results, _ = self._run_with_timeout(_download_payload, timeout_sec=max(timeout_sec, 5.0))
        if not finished or not results:
            return {}

        snapshots: dict[str, dict[str, Any]] = {}
        for row in results:
            symbol = self._normalize_symbol(row.get("symbol") or "")
            if not symbol:
                continue

            price_raw = row.get("price")
            prev_raw = row.get("prev_close")
            volume_raw = row.get("volume")

            try:
                price = float(price_raw)
            except Exception:
                continue

            try:
                prev_close = float(prev_raw)
                if prev_close == 0.0:
                    prev_close = price
            except Exception:
                prev_close = price

            try:
                volume = int(float(volume_raw))
            except Exception:
                volume = 0

            snapshot = self._build_quote_snapshot(symbol, price, prev_close, volume)
            snapshots[symbol] = snapshot

        return snapshots

    def _get_quote_snapshot(self, symbol: str) -> dict[str, Any]:
        symbol = self._normalize_symbol(symbol)
        key = f"{symbol}:quote:1mo"
        cached = self.quote_cache.get(key)
        if cached:
            return dict(cached)

        quote_data = self._fetch_quote_snapshots([symbol], timeout_sec=1.5)
        quick_snapshot = quote_data.get(symbol)
        if quick_snapshot:
            self.quote_cache[key] = quick_snapshot
            return dict(quick_snapshot)

        df = self._fetch_history(symbol, period="1mo")
        snapshot = self._snapshot_from_frame(symbol, df)
        if not snapshot:
            raise ValueError(f"Not enough quote history for symbol: {symbol}")
        self.quote_cache[key] = snapshot
        return dict(snapshot)

    def _build_fallback_snapshots(self, limit: int = 12) -> list[dict[str, Any]]:
        snapshots: list[dict[str, Any]] = []
        seen: set[str] = set()

        seed_symbols: list[str] = [symbol for symbol, _ in self.trending_counter.most_common(limit)]
        seed_symbols.extend(TRENDING_UNIVERSE_SYMBOLS)

        for symbol in seed_symbols:
            if symbol in seen:
                continue
            cached = self.quote_cache.get(f"{symbol}:quote:1mo")
            if cached:
                snapshots.append(dict(cached))
                seen.add(symbol)
                if len(snapshots) >= limit:
                    break
                continue

            hist_snapshot = self._cached_history_snapshot(symbol)
            if hist_snapshot:
                snapshots.append(hist_snapshot)
                seen.add(symbol)
                if len(snapshots) >= limit:
                    break

        if len(snapshots) < limit:
            for item in MASTER_STOCKS:
                if item["symbol"] in seen:
                    continue
                snapshots.append(
                    {
                        "symbol": item["symbol"],
                        "name": item["name"],
                        "exchange": item["exchange"],
                        "price": None,
                        "daily_change": None,
                        "daily_change_pct": None,
                        "volume": 0,
                        "data_unavailable": True,
                    }
                )
                seen.add(item["symbol"])
                if len(snapshots) >= limit:
                    break

        return snapshots

    def _get_universe_snapshots(self) -> list[dict[str, Any]]:
        cache_key = "universe:1mo"
        cached = self.universe_snapshot_cache.get(cache_key)
        if cached:
            return [dict(item) for item in cached]

        universe_symbols = [s for s in TRENDING_UNIVERSE_SYMBOLS if s in STOCK_LOOKUP]
        
        quote_batch = self._fetch_quote_snapshots(universe_symbols, timeout_sec=15.0)
        
        snapshots: list[dict[str, Any]] = []
        seen: set[str] = set()

        for symbol in universe_symbols:
            snapshot = quote_batch.get(symbol)
            if snapshot:
                snapshots.append(snapshot)
                self.quote_cache[f"{symbol}:quote:1mo"] = snapshot
                seen.add(symbol)

        if len(snapshots) < len(universe_symbols):
            for symbol in universe_symbols:
                if symbol in seen:
                    continue
                cached_quote = self.quote_cache.get(f"{symbol}:quote:1mo")
                if cached_quote:
                    snapshots.append(dict(cached_quote))
                    seen.add(symbol)
                    continue
                cached_hist = self._cached_history_snapshot(symbol)
                if cached_hist:
                    snapshots.append(cached_hist)
                    seen.add(symbol)

        for symbol in universe_symbols:
            if symbol not in seen:
                meta = STOCK_LOOKUP.get(symbol, {"name": symbol, "exchange": "Unknown"})
                snapshots.append({
                    "symbol": symbol, "name": meta["name"], "exchange": meta["exchange"],
                    "price": None, "daily_change": None, "daily_change_pct": None,
                    "volume": 0, "data_unavailable": True,
                })
                seen.add(symbol)

        if not snapshots:
            snapshots = self._build_fallback_snapshots(limit=12)

        self.universe_snapshot_cache[cache_key] = snapshots
        return [dict(item) for item in snapshots]

    def get_trending(self, limit: int = 10) -> list[dict[str, Any]]:
        universe_snapshots = self._get_universe_snapshots()
        snapshot_by_symbol = {item["symbol"]: item for item in universe_snapshots}

        if not universe_snapshots:
            return []

        # Recently viewed symbols (personalized)
        recent_snapshots: list[dict[str, Any]] = []
        for symbol, _ in self.trending_counter.most_common(limit * 3):
            item = snapshot_by_symbol.get(symbol)
            if item:
                recent_snapshots.append(item)

        # Top movers by absolute daily % change and most active by volume.
        movers = sorted(
            universe_snapshots,
            key=lambda row: abs(self._safe_float(row.get("daily_change_pct"), 0.0)),
            reverse=True,
        )
        active = sorted(
            universe_snapshots,
            key=lambda row: int(self._safe_float(row.get("volume"), 0.0)),
            reverse=True,
        )

        recent_quota = 2 if limit >= 5 else 1
        movers_quota = max(1, min(6, limit - recent_quota))
        active_quota = max(0, limit - recent_quota - movers_quota)

        out: list[dict[str, Any]] = []
        seen: set[str] = set()

        def add_from(source: list[dict[str, Any]], count: int) -> None:
            nonlocal out
            for item in source:
                if len(out) >= limit or count <= 0:
                    break
                symbol = item.get("symbol")
                if not symbol or symbol in seen:
                    continue
                seen.add(symbol)
                out.append(item)
                count -= 1

        # Hybrid mix: recently viewed + movers + active
        add_from(recent_snapshots, recent_quota)
        add_from(movers, movers_quota)
        add_from(active, active_quota)

        # Fill any remaining slots from movers then active.
        if len(out) < limit:
            add_from(movers, limit - len(out))
        if len(out) < limit:
            add_from(active, limit - len(out))

        # Last fallback from full universe snapshots.
        if len(out) < limit:
            add_from(universe_snapshots, limit - len(out))

        return out[:limit]

    def get_market_overview(self) -> list[dict[str, Any]]:
        items = []
        for idx in MARKET_OVERVIEW_SYMBOLS:
            symbol = idx["symbol"]
            try:
                df = self._fetch_history(symbol, period="1mo")
                if len(df) < 2:
                    continue
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                change = float(latest["Close"] - prev["Close"])
                change_pct = (change / float(prev["Close"])) * 100.0 if float(prev["Close"]) else 0.0

                items.append(
                    {
                        "symbol": symbol,
                        "name": idx["name"],
                        "value": round(float(latest["Close"]), 2),
                        "daily_change": round(change, 2),
                        "daily_change_pct": round(change_pct, 2),
                    }
                )
            except Exception:
                continue
        return items
