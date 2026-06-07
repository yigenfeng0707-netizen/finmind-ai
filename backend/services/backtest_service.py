import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False


class BacktestService:
    """Service for backtesting trading strategies based on FinMind AI signals."""

    def __init__(self):
        self.initial_capital = 100000
        self.position_size_pct = 0.1  # 10% of capital per trade

    async def run_backtest(
        self,
        symbol: str,
        period: str = "1y",
        strategy: str = "combined"
    ) -> Dict[str, Any]:
        """
        Run a backtest simulation on historical data.

        Args:
            symbol: Stock ticker symbol
            period: Historical period (3mo, 6mo, 1y, 2y)
            strategy: Strategy type (combined, technical, sentiment, momentum)

        Returns:
            Backtest results with performance metrics
        """
        try:
            # Fetch historical data
            df = await self._fetch_historical_data(symbol, period)
            if df is None or df.empty:
                return {"status": "error", "error": "No historical data available"}

            # Calculate indicators
            df = self._calculate_indicators(df)

            # Generate signals based on strategy
            df = self._generate_signals(df, strategy)

            # Simulate trades
            trades = self._simulate_trades(df)

            # Calculate performance metrics
            metrics = self._calculate_metrics(trades, df)

            # Generate equity curve
            equity_curve = self._generate_equity_curve(trades, df)

            return {
                "status": "success",
                "symbol": symbol.upper(),
                "period": period,
                "strategy": strategy,
                "initial_capital": self.initial_capital,
                "metrics": metrics,
                "trades": trades[:50],  # Limit to 50 trades for response size
                "equity_curve": equity_curve,
                "total_trades": len(trades),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Backtest failed for {symbol}: {e}")
            return {"status": "error", "error": str(e)}

    async def _fetch_historical_data(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """Fetch historical price data."""
        if not YF_AVAILABLE:
            return self._generate_mock_data(period)

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval="1d")
            if df.empty:
                return self._generate_mock_data(period)
            return df
        except Exception as e:
            logger.warning(f"Failed to fetch data: {e}")
            return self._generate_mock_data(period)

    def _generate_mock_data(self, period: str) -> pd.DataFrame:
        """Generate mock historical data for testing."""
        period_map = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
        days = period_map.get(period, 365)

        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        np.random.seed(42)

        base_price = 150
        returns = np.random.normal(0.0003, 0.015, days)
        prices = base_price * (1 + returns).cumprod()

        df = pd.DataFrame({
            'Open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
            'High': prices * (1 + np.random.uniform(0, 0.02, days)),
            'Low': prices * (1 - np.random.uniform(0, 0.02, days)),
            'Close': prices,
            'Volume': np.random.uniform(10000000, 50000000, days).astype(int)
        }, index=dates)

        return df

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for signal generation."""
        df = df.copy()

        # Moving averages
        df['SMA_20'] = SMAIndicator(close=df['Close'], window=20).sma_indicator()
        df['SMA_50'] = SMAIndicator(close=df['Close'], window=50).sma_indicator()

        # RSI
        df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()

        # MACD
        macd = MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()

        # Bollinger Bands
        bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Lower'] = bb.bollinger_lband()

        # ATR
        df['ATR'] = AverageTrueRange(
            high=df['High'], low=df['Low'], close=df['Close'], window=14
        ).average_true_range()

        return df

    def _generate_signals(self, df: pd.DataFrame, strategy: str) -> pd.DataFrame:
        """Generate buy/sell signals based on strategy."""
        df = df.copy()
        df['Signal'] = 0  # 0=hold, 1=buy, -1=sell

        if strategy == "technical":
            df = self._technical_signals(df)
        elif strategy == "momentum":
            df = self._momentum_signals(df)
        elif strategy == "sentiment":
            df = self._sentiment_proxy_signals(df)
        else:  # combined
            df = self._combined_signals(df)

        return df

    def _technical_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals based on technical indicators."""
        for i in range(1, len(df)):
            buy_score = 0
            sell_score = 0

            # RSI signals
            rsi = df['RSI'].iloc[i]
            if not pd.isna(rsi):
                if rsi < 30:
                    buy_score += 2
                elif rsi < 40:
                    buy_score += 1
                elif rsi > 70:
                    sell_score += 2
                elif rsi > 60:
                    sell_score += 1

            # MACD signals
            macd = df['MACD'].iloc[i]
            macd_signal = df['MACD_Signal'].iloc[i]
            if not pd.isna(macd) and not pd.isna(macd_signal):
                if macd > macd_signal:
                    buy_score += 1
                else:
                    sell_score += 1

            # SMA crossover
            sma20 = df['SMA_20'].iloc[i]
            sma50 = df['SMA_50'].iloc[i]
            prev_sma20 = df['SMA_20'].iloc[i-1]
            prev_sma50 = df['SMA_50'].iloc[i-1]

            if not pd.isna(sma20) and not pd.isna(sma50) and not pd.isna(prev_sma20) and not pd.isna(prev_sma50):
                if sma20 > sma50 and prev_sma20 <= prev_sma50:
                    buy_score += 2  # Golden cross
                elif sma20 < sma50 and prev_sma20 >= prev_sma50:
                    sell_score += 2  # Death cross

            # Determine signal
            if buy_score >= 3:
                df.iloc[i, df.columns.get_loc('Signal')] = 1
            elif sell_score >= 3:
                df.iloc[i, df.columns.get_loc('Signal')] = -1

        return df

    def _momentum_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals based on momentum strategy."""
        df['Momentum'] = df['Close'].pct_change(20)

        for i in range(1, len(df)):
            momentum = df['Momentum'].iloc[i]
            if pd.isna(momentum):
                continue

            if momentum > 0.05:
                df.iloc[i, df.columns.get_loc('Signal')] = 1
            elif momentum < -0.05:
                df.iloc[i, df.columns.get_loc('Signal')] = -1

        return df

    def _sentiment_proxy_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals simulating sentiment-based strategy using price action proxy."""
        for i in range(1, len(df)):
            # Use price change patterns as sentiment proxy
            recent_change = (df['Close'].iloc[i] - df['Close'].iloc[max(0, i-5):i].mean()) / df['Close'].iloc[max(0, i-5):i].mean()

            if recent_change > 0.03:
                df.iloc[i, df.columns.get_loc('Signal')] = 1
            elif recent_change < -0.03:
                df.iloc[i, df.columns.get_loc('Signal')] = -1

        return df

    def _combined_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals combining multiple strategies."""
        df_tech = self._technical_signals(df.copy())
        df_mom = self._momentum_signals(df.copy())

        for i in range(len(df)):
            combined = df_tech['Signal'].iloc[i] + df_mom['Signal'].iloc[i]
            if combined >= 2:
                df.iloc[i, df.columns.get_loc('Signal')] = 1
            elif combined <= -2:
                df.iloc[i, df.columns.get_loc('Signal')] = -1
            else:
                df.iloc[i, df.columns.get_loc('Signal')] = 0

        return df

    def _simulate_trades(self, df: pd.DataFrame) -> List[Dict]:
        """Simulate trades based on signals."""
        trades = []
        position = 0  # Number of shares
        entry_price = 0
        entry_date = None
        capital = self.initial_capital

        for i in range(len(df)):
            signal = df['Signal'].iloc[i]
            price = float(df['Close'].iloc[i])
            date = df.index[i]

            if signal == 1 and position == 0:
                # Buy
                shares = int((capital * self.position_size_pct) / price)
                if shares > 0:
                    position = shares
                    entry_price = price
                    entry_date = date
                    capital -= shares * price

            elif signal == -1 and position > 0:
                # Sell
                exit_price = price
                pnl = (exit_price - entry_price) * position
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                capital += position * exit_price

                trades.append({
                    "entry_date": entry_date.strftime('%Y-%m-%d') if entry_date else "",
                    "exit_date": date.strftime('%Y-%m-%d'),
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "shares": position,
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl_pct, 2),
                    "type": "long"
                })

                position = 0
                entry_price = 0
                entry_date = None

        # Close any open position at end
        if position > 0:
            exit_price = float(df['Close'].iloc[-1])
            pnl = (exit_price - entry_price) * position
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            capital += position * exit_price

            trades.append({
                "entry_date": entry_date.strftime('%Y-%m-%d') if entry_date else "",
                "exit_date": df.index[-1].strftime('%Y-%m-%d'),
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "shares": position,
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "type": "long"
            })

        return trades

    def _calculate_metrics(self, trades: List[Dict], df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate backtest performance metrics."""
        if not trades:
            return {
                "total_return": 0,
                "total_return_pct": 0,
                "win_rate": 0,
                "avg_win_pct": 0,
                "avg_loss_pct": 0,
                "max_drawdown_pct": 0,
                "sharpe_ratio": 0,
                "profit_factor": 0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0
            }

        winning = [t for t in trades if t['pnl'] > 0]
        losing = [t for t in trades if t['pnl'] <= 0]

        total_pnl = sum(t['pnl'] for t in trades)
        total_return_pct = (total_pnl / self.initial_capital) * 100

        win_rate = (len(winning) / len(trades)) * 100 if trades else 0
        avg_win = np.mean([t['pnl_pct'] for t in winning]) if winning else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losing]) if losing else 0

        # Max drawdown
        cumulative_pnl = np.cumsum([t['pnl'] for t in trades])
        peak = np.maximum.accumulate(cumulative_pnl)
        drawdown = peak - cumulative_pnl
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        max_drawdown_pct = (max_drawdown / self.initial_capital) * 100

        # Sharpe ratio (simplified)
        daily_returns = df['Close'].pct_change().dropna()
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0

        # Profit factor
        gross_profit = sum(t['pnl'] for t in winning) if winning else 0
        gross_loss = abs(sum(t['pnl'] for t in losing)) if losing else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        return {
            "total_return": round(total_pnl, 2),
            "total_return_pct": round(total_return_pct, 2),
            "win_rate": round(win_rate, 1),
            "avg_win_pct": round(float(avg_win), 2),
            "avg_loss_pct": round(float(avg_loss), 2),
            "max_drawdown_pct": round(float(max_drawdown_pct), 2),
            "sharpe_ratio": round(float(sharpe), 2),
            "profit_factor": round(float(profit_factor), 2),
            "total_trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing)
        }

    def _generate_equity_curve(self, trades: List[Dict], df: pd.DataFrame) -> List[Dict]:
        """Generate equity curve data points."""
        curve = []
        capital = self.initial_capital
        trade_idx = 0

        for i in range(len(df)):
            date_str = df.index[i].strftime('%Y-%m-%d')

            # Apply trade PnL when trade is closed
            while trade_idx < len(trades) and trades[trade_idx]['exit_date'] == date_str:
                capital += trades[trade_idx]['pnl']
                trade_idx += 1

            curve.append({
                "date": date_str,
                "equity": round(capital, 2)
            })

        return curve


# Singleton instance
backtest_service = BacktestService()
