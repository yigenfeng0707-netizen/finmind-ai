from typing import Any, Dict, List
from .base_agent import BaseAgent
from services.market_data import market_data_service
from services.llm_service import llm_service


class TechnicalAgent(BaseAgent):
    """
    Agent specialized in technical analysis of stock price and indicators.
    Analyzes price patterns, moving averages, RSI, MACD, and other technical indicators.
    """

    def __init__(self):
        super().__init__(
            name="Technical Analysis Agent",
            agent_type="technical"
        )

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform technical analysis on a stock.

        Args:
            data: Must contain 'symbol' and optionally 'stock_data'
        """
        symbol = data.get("symbol", "")

        # Fetch technical indicators
        indicators = await market_data_service.calculate_technical_indicators(symbol)

        if "error" in indicators:
            return {
                "summary": "Unable to perform technical analysis",
                "indicators": {},
                "signals": [],
                "analysis": indicators["error"],
                "signal": "hold",
                "confidence": 0.3
            }

        # Analyze each indicator
        signals = self._analyze_indicators(indicators)

        # Determine overall technical signal
        signal = self._determine_technical_signal(signals)

        # Calculate confidence
        confidence = self._calculate_confidence(indicators, signals)

        # Generate comprehensive analysis
        analysis = self._generate_technical_analysis(indicators, signals)

        # Identify support and resistance levels
        support_resistance = self._identify_support_resistance(indicators)

        result = {
            "summary": analysis,
            "indicators": indicators,
            "signals": signals,
            "support_resistance": support_resistance,
            "signal": signal,
            "confidence": round(confidence, 2),
            "key_findings": self._extract_key_findings(indicators, signals),
            "risk_factors": self._identify_risk_factors(indicators, signals)
        }

        # LLM-enhanced analysis
        if llm_service.is_available():
            llm_result = await self._llm_analyze(
                system_prompt="You are a technical analysis expert. Analyze the technical indicators and provide trading insights.",
                user_prompt=f"Stock: {symbol}\nIndicators: {indicators}\nSignals: {signals}\nSupport/Resistance: {support_resistance}",
                output_schema={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "signal": {"type": "string", "enum": ["strong_buy", "buy", "hold", "sell", "strong_sell"]},
                        "confidence": {"type": "number"},
                        "key_findings": {"type": "array", "items": {"type": "string"}},
                        "risk_factors": {"type": "array", "items": {"type": "string"}}
                    }
                }
            )
            if llm_result:
                llm_result = llm_service.validate_agent_result(llm_result)
                result["summary"] = llm_result.get("summary", result["summary"])
                result["signal"] = llm_result.get("signal", result["signal"])
                result["confidence"] = llm_result.get("confidence", result["confidence"])
                result["key_findings"] = llm_result.get("key_findings", result["key_findings"])
                result["risk_factors"] = llm_result.get("risk_factors", result["risk_factors"])
                result["llm_enhanced"] = True

        return result

    def _analyze_indicators(self, indicators: Dict) -> List[Dict]:
        """Analyze each technical indicator and generate signals."""
        signals = []

        # RSI Analysis
        rsi = indicators.get("rsi_14")
        if rsi is not None:
            if rsi > 70:
                signals.append({
                    "indicator": "RSI",
                    "value": rsi,
                    "signal": "overbought",
                    "interpretation": f"RSI at {rsi:.1f} indicates overbought conditions",
                    "strength": "strong"
                })
            elif rsi < 30:
                signals.append({
                    "indicator": "RSI",
                    "value": rsi,
                    "signal": "oversold",
                    "interpretation": f"RSI at {rsi:.1f} indicates oversold conditions",
                    "strength": "strong"
                })
            elif rsi > 60:
                signals.append({
                    "indicator": "RSI",
                    "value": rsi,
                    "signal": "bullish",
                    "interpretation": f"RSI at {rsi:.1f} shows bullish momentum",
                    "strength": "moderate"
                })
            elif rsi < 40:
                signals.append({
                    "indicator": "RSI",
                    "value": rsi,
                    "signal": "bearish",
                    "interpretation": f"RSI at {rsi:.1f} shows bearish momentum",
                    "strength": "moderate"
                })
            else:
                signals.append({
                    "indicator": "RSI",
                    "value": rsi,
                    "signal": "neutral",
                    "interpretation": f"RSI at {rsi:.1f} is in neutral territory",
                    "strength": "weak"
                })

        # MACD Analysis
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        if macd is not None and macd_signal is not None:
            macd_diff = macd - macd_signal
            if macd_diff > 0:
                signals.append({
                    "indicator": "MACD",
                    "value": macd,
                    "signal": "bullish",
                    "interpretation": "MACD above signal line indicates bullish momentum",
                    "strength": "strong" if macd_diff > 0.5 else "moderate"
                })
            else:
                signals.append({
                    "indicator": "MACD",
                    "value": macd,
                    "signal": "bearish",
                    "interpretation": "MACD below signal line indicates bearish momentum",
                    "strength": "strong" if macd_diff < -0.5 else "moderate"
                })

        # Moving Average Analysis
        current_price = indicators.get("current_price")
        sma_20 = indicators.get("sma_20")
        sma_50 = indicators.get("sma_50")

        if current_price and sma_20:
            if current_price > sma_20:
                signals.append({
                    "indicator": "SMA_20",
                    "value": sma_20,
                    "signal": "bullish",
                    "interpretation": "Price above 20-day SMA indicates short-term uptrend",
                    "strength": "moderate"
                })
            else:
                signals.append({
                    "indicator": "SMA_20",
                    "value": sma_20,
                    "signal": "bearish",
                    "interpretation": "Price below 20-day SMA indicates short-term downtrend",
                    "strength": "moderate"
                })

        if current_price and sma_50:
            if current_price > sma_50:
                signals.append({
                    "indicator": "SMA_50",
                    "value": sma_50,
                    "signal": "bullish",
                    "interpretation": "Price above 50-day SMA indicates medium-term uptrend",
                    "strength": "strong"
                })
            else:
                signals.append({
                    "indicator": "SMA_50",
                    "value": sma_50,
                    "signal": "bearish",
                    "interpretation": "Price below 50-day SMA indicates medium-term downtrend",
                    "strength": "strong"
                })

        # Bollinger Bands Analysis
        bb_upper = indicators.get("bollinger_upper")
        bb_lower = indicators.get("bollinger_lower")
        position = indicators.get("price_position")

        if position == "overbought":
            signals.append({
                "indicator": "Bollinger",
                "value": bb_upper,
                "signal": "overbought",
                "interpretation": "Price at upper Bollinger Band suggests overbought",
                "strength": "strong"
            })
        elif position == "oversold":
            signals.append({
                "indicator": "Bollinger",
                "value": bb_lower,
                "signal": "oversold",
                "interpretation": "Price at lower Bollinger Band suggests oversold",
                "strength": "strong"
            })

        return signals

    def _determine_technical_signal(self, signals: List[Dict]) -> str:
        """Determine overall technical signal from multiple indicators."""
        if not signals:
            return "hold"

        bullish_count = sum(1 for s in signals if s["signal"] in ["bullish", "oversold"])
        bearish_count = sum(1 for s in signals if s["signal"] in ["bearish", "overbought"])

        # Weight by strength
        bullish_score = sum(
            1.5 if s["strength"] == "strong" else 1
            for s in signals if s["signal"] in ["bullish", "oversold"]
        )
        bearish_score = sum(
            1.5 if s["strength"] == "strong" else 1
            for s in signals if s["signal"] in ["bearish", "overbought"]
        )

        total_score = bullish_score + bearish_score
        if total_score == 0:
            return "hold"

        bullish_ratio = bullish_score / total_score

        if bullish_ratio > 0.7:
            return "strong_buy"
        elif bullish_ratio > 0.55:
            return "buy"
        elif bullish_ratio < 0.3:
            return "strong_sell"
        elif bullish_ratio < 0.45:
            return "sell"
        return "hold"

    def _calculate_confidence(
        self, indicators: Dict, signals: List[Dict]
    ) -> float:
        """Calculate confidence in technical analysis."""
        confidence = 0.5

        # More indicators available = higher confidence
        available_indicators = sum(
            1 for v in indicators.values()
            if v is not None and not isinstance(v, str)
        )
        confidence += min(available_indicators * 0.05, 0.2)

        # Strong signals increase confidence
        strong_signals = sum(
            1 for s in signals if s.get("strength") == "strong"
        )
        confidence += min(strong_signals * 0.05, 0.2)

        return min(confidence, 0.9)

    def _generate_technical_analysis(
        self, indicators: Dict, signals: List[Dict]
    ) -> str:
        """Generate comprehensive technical analysis text."""
        current_price = indicators.get("current_price", 0)
        analysis = f"Technical analysis of price at ${current_price:.2f}: "

        # Summarize key signals
        bullish_signals = [s for s in signals if s["signal"] in ["bullish", "oversold"]]
        bearish_signals = [s for s in signals if s["signal"] in ["bearish", "overbought"]]

        if bullish_signals:
            analysis += f"Bullish indicators: {', '.join(s['indicator'] for s in bullish_signals)}. "
        if bearish_signals:
            analysis += f"Bearish indicators: {', '.join(s['indicator'] for s in bearish_signals)}. "

        # Add specific insights
        rsi = indicators.get("rsi_14")
        if rsi:
            if rsi > 70:
                analysis += "RSI indicates overbought conditions - consider taking profits. "
            elif rsi < 30:
                analysis += "RSI indicates oversold conditions - potential buying opportunity. "

        sma_20 = indicators.get("sma_20")
        sma_50 = indicators.get("sma_50")
        if sma_20 and sma_50:
            if sma_20 > sma_50:
                analysis += "Short-term MA above long-term MA confirms uptrend. "
            else:
                analysis += "Short-term MA below long-term MA suggests downtrend. "

        return analysis

    def _identify_support_resistance(self, indicators: Dict) -> Dict:
        """Identify potential support and resistance levels."""
        current_price = indicators.get("current_price", 0)
        bb_upper = indicators.get("bollinger_upper")
        bb_lower = indicators.get("bollinger_lower")
        sma_20 = indicators.get("sma_20")
        sma_50 = indicators.get("sma_50")

        support = []
        resistance = []

        if bb_lower and current_price:
            support.append({"level": bb_lower, "type": "Bollinger Lower Band"})
        if sma_20 and current_price:
            if sma_20 < current_price:
                support.append({"level": sma_20, "type": "20-day SMA"})
            else:
                resistance.append({"level": sma_20, "type": "20-day SMA"})

        if sma_50 and current_price:
            if sma_50 < current_price:
                support.append({"level": sma_50, "type": "50-day SMA"})
            else:
                resistance.append({"level": sma_50, "type": "50-day SMA"})

        if bb_upper and current_price:
            resistance.append({"level": bb_upper, "type": "Bollinger Upper Band"})

        return {
            "support": sorted(support, key=lambda x: x["level"], reverse=True),
            "resistance": sorted(resistance, key=lambda x: x["level"])
        }

    def _extract_key_findings(self, indicators: Dict, signals: List[Dict]) -> List[str]:
        """Extract key findings from technical analysis."""
        findings = []

        rsi = indicators.get("rsi_14")
        if rsi:
            if rsi > 70:
                findings.append(f"RSI at {rsi:.1f} indicates overbought conditions")
            elif rsi < 30:
                findings.append(f"RSI at {rsi:.1f} indicates oversold conditions")

        sma_20 = indicators.get("sma_20")
        sma_50 = indicators.get("sma_50")
        if sma_20 and sma_50:
            if sma_20 > sma_50:
                findings.append("Golden cross pattern - short-term MA above long-term MA")
            else:
                findings.append("Death cross pattern - short-term MA below long-term MA")

        position = indicators.get("price_position")
        if position == "overbought":
            findings.append("Price at upper Bollinger Band - potential reversal zone")
        elif position == "oversold":
            findings.append("Price at lower Bollinger Band - potential bounce zone")

        return findings[:5]

    def _identify_risk_factors(self, indicators: Dict, signals: List[Dict]) -> List[str]:
        """Identify risk factors from technical analysis."""
        risks = []

        rsi = indicators.get("rsi_14")
        if rsi and rsi > 80:
            risks.append("Extremely overbought RSI - high correction risk")
        elif rsi and rsi < 20:
            risks.append("Extremely oversold RSI - continued downside risk")

        atr = indicators.get("atr_14")
        current_price = indicators.get("current_price")
        if atr and current_price:
            volatility = (atr / current_price) * 100
            if volatility > 3:
                risks.append(f"High volatility ({volatility:.1f}%) increases trading risk")

        return risks[:3]
