from typing import Any, Dict, List
from .base_agent import BaseAgent
from services.news_service import news_service
from services.llm_service import llm_service


class SentimentAgent(BaseAgent):
    """
    Agent specialized in analyzing market sentiment from multiple sources.
    Combines news sentiment, social indicators, and market signals.
    """

    def __init__(self):
        super().__init__(
            name="Sentiment Analysis Agent",
            agent_type="sentiment"
        )

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive sentiment analysis.

        Args:
            data: Must contain 'symbol' and 'news_data' (from NewsMonitorAgent)
        """
        symbol = data.get("symbol", "")
        news_data = data.get("news_data", {})
        stock_data = data.get("stock_data", {})

        # Get news sentiment
        news_sentiment = news_data.get("news_sentiment_score", 0)
        news_count = news_data.get("news_count", 0)

        # Analyze market signals (volume, price action)
        market_sentiment = self._analyze_market_signals(stock_data)

        # Combine sentiments with weights
        combined_sentiment = self._combine_sentiments(
            news_sentiment=news_sentiment,
            market_sentiment=market_sentiment["score"],
            news_weight=0.6,
            market_weight=0.4
        )

        # Determine overall sentiment
        sentiment_label = self._score_to_label(combined_sentiment)

        # Generate detailed analysis
        analysis = self._generate_sentiment_analysis(
            news_sentiment=news_sentiment,
            market_sentiment=market_sentiment,
            combined_sentiment=combined_sentiment,
            news_count=news_count
        )

        # Calculate confidence
        confidence = self._calculate_confidence(news_count, stock_data)

        result = {
            "overall_sentiment": sentiment_label,
            "sentiment_score": round(combined_sentiment, 3),
            "news_sentiment": round(news_sentiment, 3),
            "market_sentiment": market_sentiment,
            "confidence": round(confidence, 2),
            "analysis": analysis,
            "key_findings": self._extract_findings(
                news_sentiment, market_sentiment, combined_sentiment
            ),
            "risk_factors": self._identify_sentiment_risks(
                news_sentiment, market_sentiment, combined_sentiment
            ),
            "signal": self._sentiment_to_signal(combined_sentiment)
        }

        # LLM-enhanced analysis
        if llm_service.is_available():
            llm_result = await self._llm_analyze(
                system_prompt="You are a market sentiment analyst. Analyze sentiment from news and market signals.",
                user_prompt=f"Stock: {symbol}\nNews sentiment: {news_sentiment:.3f}\nMarket signals: {market_sentiment}\nCombined sentiment: {combined_sentiment:.3f}\nNews count: {news_count}",
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis": {"type": "string"},
                        "signal": {"type": "string", "enum": ["strong_buy", "buy", "hold", "sell", "strong_sell"]},
                        "confidence": {"type": "number"},
                        "key_findings": {"type": "array", "items": {"type": "string"}},
                        "risk_factors": {"type": "array", "items": {"type": "string"}}
                    }
                }
            )
            if llm_result:
                llm_result = llm_service.validate_agent_result(llm_result)
                result["analysis"] = llm_result.get("analysis", result["analysis"])
                result["signal"] = llm_result.get("signal", result["signal"])
                result["confidence"] = llm_result.get("confidence", result["confidence"])
                result["key_findings"] = llm_result.get("key_findings", result["key_findings"])
                result["risk_factors"] = llm_result.get("risk_factors", result["risk_factors"])
                result["llm_enhanced"] = True

        return result

    def _analyze_market_signals(self, stock_data: Dict) -> Dict[str, Any]:
        """Analyze market-based sentiment signals."""
        if not stock_data or "error" in stock_data:
            return {"score": 0, "signals": [], "analysis": "Insufficient market data"}

        signals = []
        score = 0

        # Price change signal
        change_percent = stock_data.get("change_percent", 0)
        if change_percent > 2:
            signals.append("Strong positive price momentum")
            score += 0.3
        elif change_percent > 0:
            signals.append("Positive price movement")
            score += 0.15
        elif change_percent < -2:
            signals.append("Strong negative price momentum")
            score -= 0.3
        elif change_percent < 0:
            signals.append("Negative price movement")
            score -= 0.15

        # Volume signal
        volume = stock_data.get("volume", 0)
        avg_volume = stock_data.get("avg_volume", volume)
        if avg_volume > 0:
            volume_ratio = volume / avg_volume
            if volume_ratio > 1.5:
                signals.append("Above-average trading volume indicates high interest")
                score += 0.1
            elif volume_ratio < 0.5:
                signals.append("Below-average volume suggests low conviction")
                score -= 0.05

        # 52-week position
        current_price = stock_data.get("current_price", 0)
        high_52w = stock_data.get("high_52w", 0)
        low_52w = stock_data.get("low_52w", 0)

        if high_52w > low_52w > 0:
            position = (current_price - low_52w) / (high_52w - low_52w)
            if position > 0.9:
                signals.append("Trading near 52-week high - potential overbought")
                score += 0.1
            elif position < 0.1:
                signals.append("Trading near 52-week low - potential oversold")
                score -= 0.1

        analysis = self._generate_market_analysis(signals, change_percent)

        return {
            "score": max(min(score, 1), -1),
            "signals": signals,
            "analysis": analysis,
            "price_change": change_percent
        }

    def _combine_sentiments(
        self,
        news_sentiment: float,
        market_sentiment: float,
        news_weight: float = 0.6,
        market_weight: float = 0.4
    ) -> float:
        """Combine multiple sentiment sources with weights."""
        combined = (news_sentiment * news_weight) + (market_sentiment * market_weight)
        return max(min(combined, 1), -1)

    def _score_to_label(self, score: float) -> str:
        """Convert numeric score to sentiment label."""
        if score > 0.3:
            return "bullish"
        elif score > 0.1:
            return "slightly_bullish"
        elif score < -0.3:
            return "bearish"
        elif score < -0.1:
            return "slightly_bearish"
        return "neutral"

    def _sentiment_to_signal(self, score: float) -> str:
        """Convert sentiment score to trading signal."""
        if score > 0.4:
            return "strong_buy"
        elif score > 0.15:
            return "buy"
        elif score < -0.4:
            return "strong_sell"
        elif score < -0.15:
            return "sell"
        return "hold"

    def _generate_market_analysis(
        self, signals: List[str], price_change: float
    ) -> str:
        """Generate analysis from market signals."""
        if not signals:
            return "Insufficient market signals for sentiment analysis."

        analysis = "Market sentiment indicators show: "
        analysis += ". ".join(signals) + "."

        if price_change > 3:
            analysis += " The strong price appreciation suggests bullish momentum."
        elif price_change < -3:
            analysis += " The significant price decline indicates bearish pressure."

        return analysis

    def _calculate_confidence(
        self, news_count: int, stock_data: Dict
    ) -> float:
        """Calculate confidence in sentiment analysis."""
        confidence = 0.5  # Base confidence

        # More news = higher confidence
        if news_count > 10:
            confidence += 0.2
        elif news_count > 5:
            confidence += 0.1

        # Available market data increases confidence
        if stock_data and "error" not in stock_data:
            confidence += 0.15

        return min(confidence, 0.95)

    def _generate_sentiment_analysis(
        self,
        news_sentiment: float,
        market_sentiment: Dict,
        combined_sentiment: float,
        news_count: int
    ) -> str:
        """Generate comprehensive sentiment analysis text."""
        if news_count == 0:
            return "Insufficient data for comprehensive sentiment analysis."

        analysis = f"Based on analysis of {news_count} news sources and market signals: "

        if combined_sentiment > 0.3:
            analysis += "Overall sentiment is strongly bullish. "
        elif combined_sentiment > 0.1:
            analysis += "Sentiment is moderately positive. "
        elif combined_sentiment < -0.3:
            analysis += "Overall sentiment is strongly bearish. "
        elif combined_sentiment < -0.1:
            analysis += "Sentiment is moderately negative. "
        else:
            analysis += "Sentiment is neutral/mixed. "

        analysis += f"News sentiment score: {news_sentiment:.2f}. "
        analysis += f"Market signal score: {market_sentiment.get('score', 0):.2f}."

        return analysis

    def _extract_findings(
        self,
        news_sentiment: float,
        market_sentiment: Dict,
        combined: float
    ) -> List[str]:
        """Extract key findings from sentiment analysis."""
        findings = []

        if news_sentiment > 0.3:
            findings.append("Positive news sentiment is supporting the stock")
        elif news_sentiment < -0.3:
            findings.append("Negative news sentiment is weighing on the stock")

        market_signals = market_sentiment.get("signals", [])
        findings.extend(market_signals[:3])

        if combined > 0.3:
            findings.append("Combined sentiment indicators suggest bullish outlook")
        elif combined < -0.3:
            findings.append("Combined sentiment indicators suggest bearish outlook")

        return findings[:5]

    def _identify_sentiment_risks(
        self,
        news_sentiment: float,
        market_sentiment: Dict,
        combined: float
    ) -> List[str]:
        """Identify risk factors from sentiment analysis."""
        risks = []

        if abs(news_sentiment) > 0.5:
            risks.append("Extreme news sentiment may indicate overreaction")

        if combined > 0.6:
            risks.append("Very high positive sentiment could signal contrarian risk")
        elif combined < -0.6:
            risks.append("Very high negative sentiment could indicate panic selling")

        price_change = market_sentiment.get("price_change", 0)
        if abs(price_change) > 5:
            risks.append("Significant price volatility detected")

        return risks[:3]
