from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import time
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Try to import yfinance, but handle gracefully if not available
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange


class MarketDataService:
    """Service for fetching and processing market data from Yahoo Finance."""

    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = 300  # 5 minutes
        self.use_mock = not YF_AVAILABLE

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self.cache and key in self.cache_timestamps:
            if time.time() - self.cache_timestamps[key] < self.cache_ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.cache_timestamps[key]
        return None

    def _set_cache(self, key: str, value: Any):
        """Set cache value with timestamp."""
        self.cache[key] = value
        self.cache_timestamps[key] = time.time()

    async def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch current stock data and basic info."""
        cache_key = f"stock_{symbol.upper()}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        if self.use_mock:
            return self._get_mock_stock_data(symbol)

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get current price data
            hist = ticker.history(period="1d")
            if hist.empty:
                return self._get_mock_stock_data(symbol)

            current_price = hist['Close'].iloc[-1]
            prev_close = info.get('previousClose', current_price)
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close else 0

            result = {
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", symbol)),
                "current_price": round(float(current_price), 2),
                "change": round(float(change), 2),
                "change_percent": round(float(change_percent), 2),
                "volume": int(hist['Volume'].iloc[-1]),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "high_52w": info.get("fiftyTwoWeekHigh"),
                "low_52w": info.get("fiftyTwoWeekLow"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "sector": info.get("sector"),
                "industry": info.get("industry")
            }
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.warning(f"Yahoo Finance error: {e}, using mock data")
            return self._get_mock_stock_data(symbol)

    async def get_historical_data(
        self, symbol: str, period: str = "3mo", interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch historical price data."""
        if self.use_mock:
            return self._get_mock_historical_data()

        try:
            ticker = yf.Ticker(symbol)
            return ticker.history(period=period, interval=interval)
        except Exception as e:
            logger.warning(f"Error fetching historical data: {e}")
            return self._get_mock_historical_data()

    async def calculate_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """Calculate technical indicators for a stock."""
        try:
            df = await self.get_historical_data(symbol, period="6mo")

            if df.empty:
                return self._get_mock_technical_indicators()

            # Simple Moving Averages
            sma_20 = SMAIndicator(close=df['Close'], window=20).sma_indicator()
            sma_50 = SMAIndicator(close=df['Close'], window=50).sma_indicator()

            # RSI
            rsi = RSIIndicator(close=df['Close'], window=14).rsi()

            # MACD
            macd = MACD(close=df['Close'])
            macd_line = macd.macd()
            macd_signal = macd.macd_signal()

            # Bollinger Bands
            bollinger = BollingerBands(close=df['Close'], window=20, window_dev=2)
            bb_upper = bollinger.bollinger_hband()
            bb_lower = bollinger.bollinger_lband()

            # ATR
            atr = AverageTrueRange(
                high=df['High'], low=df['Low'], close=df['Close'], window=14
            ).average_true_range()

            # Get latest values
            indicators = {
                "sma_20": round(float(sma_20.iloc[-1]), 2) if not pd.isna(sma_20.iloc[-1]) else None,
                "sma_50": round(float(sma_50.iloc[-1]), 2) if not pd.isna(sma_50.iloc[-1]) else None,
                "rsi_14": round(float(rsi.iloc[-1]), 2) if not pd.isna(rsi.iloc[-1]) else None,
                "macd": round(float(macd_line.iloc[-1]), 4) if not pd.isna(macd_line.iloc[-1]) else None,
                "macd_signal": round(float(macd_signal.iloc[-1]), 4) if not pd.isna(macd_signal.iloc[-1]) else None,
                "bollinger_upper": round(float(bb_upper.iloc[-1]), 2) if not pd.isna(bb_upper.iloc[-1]) else None,
                "bollinger_lower": round(float(bb_lower.iloc[-1]), 2) if not pd.isna(bb_lower.iloc[-1]) else None,
                "atr_14": round(float(atr.iloc[-1]), 2) if not pd.isna(atr.iloc[-1]) else None,
                "current_price": round(float(df['Close'].iloc[-1]), 2),
                "price_position": self._get_price_position(
                    df['Close'].iloc[-1], bb_upper.iloc[-1], bb_lower.iloc[-1]
                )
            }

            return indicators
        except Exception as e:
            logger.warning(f"Error calculating indicators: {e}")
            return self._get_mock_technical_indicators()

    def _get_price_position(self, price: float, upper: float, lower: float) -> str:
        """Determine price position within Bollinger Bands."""
        if pd.isna(upper) or pd.isna(lower):
            return "unknown"
        if price >= upper:
            return "overbought"
        elif price <= lower:
            return "oversold"
        else:
            position = (price - lower) / (upper - lower)
            if position > 0.8:
                return "near_upper"
            elif position < 0.2:
                return "near_lower"
            return "middle"

    async def get_market_overview(self) -> Dict[str, Any]:
        """Get overall market overview with major indices."""
        indices = [
            {"symbol": "^GSPC", "name": "S&P 500"},
            {"symbol": "^DJI", "name": "Dow Jones"},
            {"symbol": "^IXIC", "name": "NASDAQ"},
            {"symbol": "^VIX", "name": "VIX (Volatility)"}
        ]

        market_data = []
        for idx in indices:
            data = await self.get_stock_data(idx["symbol"])
            if "error" not in data:
                data["name"] = idx["name"]
                market_data.append(data)

        return {"indices": market_data, "timestamp": datetime.now()}

    async def get_sector_performance(self) -> Dict[str, Any]:
        """Get sector ETF performance."""
        sector_etfs = [
            {"symbol": "XLK", "name": "Technology"},
            {"symbol": "XLF", "name": "Financials"},
            {"symbol": "XLV", "name": "Healthcare"},
            {"symbol": "XLE", "name": "Energy"},
            {"symbol": "XLI", "name": "Industrials"}
        ]

        sectors = []
        for sector in sector_etfs:
            data = await self.get_stock_data(sector["symbol"])
            if "error" not in data:
                sectors.append({
                    "symbol": sector["symbol"],
                    "name": sector["name"],
                    "change_percent": data.get("change_percent", 0)
                })

        sectors.sort(key=lambda x: x["change_percent"], reverse=True)
        return {"sectors": sectors, "timestamp": datetime.now()}

    async def get_chart_data(self, symbol: str, period: str = "6mo") -> Dict[str, Any]:
        """Get chart data formatted for TradingView Lightweight Charts."""
        try:
            df = await self.get_historical_data(symbol, period=period)

            if df.empty:
                return {"status": "error", "error": "No historical data available"}

            # Calculate indicators on the full dataframe
            sma_20 = SMAIndicator(close=df['Close'], window=20).sma_indicator()
            sma_50 = SMAIndicator(close=df['Close'], window=50).sma_indicator()
            rsi = RSIIndicator(close=df['Close'], window=14).rsi()
            bollinger = BollingerBands(close=df['Close'], window=20, window_dev=2)
            bb_upper = bollinger.bollinger_hband()
            bb_lower = bollinger.bollinger_lband()

            # Format candlestick data
            candles = []
            volume_data = []
            sma20_data = []
            sma50_data = []
            bb_upper_data = []
            bb_lower_data = []
            rsi_data = []

            for i in range(len(df)):
                timestamp = int(df.index[i].timestamp())

                candles.append({
                    "time": timestamp,
                    "open": round(float(df['Open'].iloc[i]), 2),
                    "high": round(float(df['High'].iloc[i]), 2),
                    "low": round(float(df['Low'].iloc[i]), 2),
                    "close": round(float(df['Close'].iloc[i]), 2)
                })

                vol = int(df['Volume'].iloc[i]) if not pd.isna(df['Volume'].iloc[i]) else 0
                close = float(df['Close'].iloc[i])
                prev_close = float(df['Close'].iloc[i-1]) if i > 0 else close
                volume_data.append({
                    "time": timestamp,
                    "value": vol,
                    "color": "rgba(0, 255, 136, 0.5)" if close >= prev_close else "rgba(255, 71, 87, 0.5)"
                })

                if not pd.isna(sma_20.iloc[i]):
                    sma20_data.append({"time": timestamp, "value": round(float(sma_20.iloc[i]), 2)})
                if not pd.isna(sma_50.iloc[i]):
                    sma50_data.append({"time": timestamp, "value": round(float(sma_50.iloc[i]), 2)})
                if not pd.isna(bb_upper.iloc[i]):
                    bb_upper_data.append({"time": timestamp, "value": round(float(bb_upper.iloc[i]), 2)})
                if not pd.isna(bb_lower.iloc[i]):
                    bb_lower_data.append({"time": timestamp, "value": round(float(bb_lower.iloc[i]), 2)})
                if not pd.isna(rsi.iloc[i]):
                    rsi_data.append({"time": timestamp, "value": round(float(rsi.iloc[i]), 2)})

            return {
                "status": "success",
                "symbol": symbol.upper(),
                "candles": candles,
                "volume": volume_data,
                "sma20": sma20_data,
                "sma50": sma50_data,
                "bb_upper": bb_upper_data,
                "bb_lower": bb_lower_data,
                "rsi": rsi_data
            }

        except Exception as e:
            logger.warning(f"Error getting chart data: {e}")
            return {"status": "error", "error": str(e)}

    def _get_mock_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Return mock stock data for testing."""
        mock_data = {
            "AAPL": {"name": "Apple Inc.", "price": 198.50, "change": 2.35, "change_pct": 1.20, "sector": "Technology"},
            "TSLA": {"name": "Tesla Inc.", "price": 245.80, "change": -5.20, "change_pct": -2.07, "sector": "Consumer Cyclical"},
            "GOOGL": {"name": "Alphabet Inc.", "price": 178.25, "change": 1.85, "change_pct": 1.05, "sector": "Technology"},
            "MSFT": {"name": "Microsoft Corp.", "price": 445.60, "change": 3.40, "change_pct": 0.77, "sector": "Technology"},
            "NVDA": {"name": "NVIDIA Corp.", "price": 875.40, "change": 15.60, "change_pct": 1.81, "sector": "Technology"},
            "AMZN": {"name": "Amazon.com Inc.", "price": 186.90, "change": -1.20, "change_pct": -0.64, "sector": "Consumer Cyclical"},
            "META": {"name": "Meta Platforms", "price": 505.20, "change": 8.70, "change_pct": 1.75, "sector": "Technology"},
            "JPM": {"name": "JPMorgan Chase", "price": 198.40, "change": 2.10, "change_pct": 1.07, "sector": "Financials"}
        }

        data = mock_data.get(symbol.upper(), {
            "name": f"{symbol} Corp.",
            "price": 150.00,
            "change": 1.50,
            "change_pct": 1.01,
            "sector": "Unknown"
        })

        return {
            "symbol": symbol.upper(),
            "name": data["name"],
            "current_price": data["price"],
            "change": data["change"],
            "change_percent": data["change_pct"],
            "volume": int(np.random.uniform(5000000, 50000000)),
            "market_cap": int(np.random.uniform(100000000000, 2000000000000)),
            "pe_ratio": round(np.random.uniform(15, 35), 2),
            "high_52w": round(data["price"] * 1.3, 2),
            "low_52w": round(data["price"] * 0.7, 2),
            "dividend_yield": round(np.random.uniform(0, 0.03), 4),
            "beta": round(np.random.uniform(0.8, 1.5), 2),
            "sector": data["sector"],
            "industry": "Technology"
        }

    def _get_mock_historical_data(self) -> pd.DataFrame:
        """Return mock historical data for testing."""
        dates = pd.date_range(end=datetime.now(), periods=120, freq='D')
        np.random.seed(42)

        # Generate realistic-looking price data
        base_price = 150
        returns = np.random.normal(0.0005, 0.02, 120)
        prices = base_price * (1 + returns).cumprod()

        df = pd.DataFrame({
            'Open': prices * (1 + np.random.uniform(-0.01, 0.01, 120)),
            'High': prices * (1 + np.random.uniform(0, 0.02, 120)),
            'Low': prices * (1 - np.random.uniform(0, 0.02, 120)),
            'Close': prices,
            'Volume': np.random.uniform(10000000, 50000000, 120).astype(int)
        }, index=dates)

        return df

    def _get_mock_technical_indicators(self) -> Dict[str, Any]:
        """Return mock technical indicators for testing."""
        current_price = 198.50
        return {
            "sma_20": round(current_price * 0.98, 2),
            "sma_50": round(current_price * 0.95, 2),
            "rsi_14": round(np.random.uniform(40, 70), 2),
            "macd": round(np.random.uniform(-1, 1), 4),
            "macd_signal": round(np.random.uniform(-1, 1), 4),
            "bollinger_upper": round(current_price * 1.05, 2),
            "bollinger_lower": round(current_price * 0.95, 2),
            "atr_14": round(current_price * 0.02, 2),
            "current_price": current_price,
            "price_position": "middle"
        }


# Singleton instance
market_data_service = MarketDataService()
