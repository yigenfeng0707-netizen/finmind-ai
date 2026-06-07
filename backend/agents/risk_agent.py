from typing import Any, Dict, List
from .base_agent import BaseAgent
import numpy as np
from services.llm_service import llm_service


class RiskAgent(BaseAgent):
    """
    Agent specialized in assessing and quantifying investment risks.
    Analyzes volatility, market risk, news risk, and provides risk scores.
    """

    def __init__(self):
        super().__init__(
            name="Risk Assessment Agent",
            agent_type="risk"
        )

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive risk assessment.

        Args:
            data: Must contain 'symbol', 'stock_data', 'technical_data', 'sentiment_data'
        """
        symbol = data.get("symbol", "")
        stock_data = data.get("stock_data", {})
        technical_data = data.get("technical_data", {})
        sentiment_data = data.get("sentiment_data", {})

        # Calculate different risk components
        volatility_risk = self._calculate_volatility_risk(stock_data, technical_data)
        market_risk = self._calculate_market_risk(stock_data)
        news_risk = self._calculate_news_risk(sentiment_data)
        liquidity_risk = self._calculate_liquidity_risk(stock_data)

        # Calculate overall risk score
        overall_risk_score = self._calculate_overall_risk(
            volatility_risk,
            market_risk,
            news_risk,
            liquidity_risk
        )

        # Determine risk level
        risk_level = self._score_to_risk_level(overall_risk_score)

        # Generate risk warnings
        risk_warnings = self._generate_risk_warnings(
            volatility_risk, market_risk, news_risk, liquidity_risk, stock_data
        )

        # Generate risk mitigations
        risk_mitigations = self._generate_mitigations(risk_level, risk_warnings)

        # Generate analysis
        analysis = self._generate_risk_analysis(
            risk_level, overall_risk_score, volatility_risk,
            market_risk, news_risk, liquidity_risk
        )

        result = {
            "overall_risk": risk_level,
            "risk_score": round(overall_risk_score, 3),
            "volatility_risk": round(volatility_risk, 3),
            "market_risk": round(market_risk, 3),
            "news_risk": round(news_risk, 3),
            "liquidity_risk": round(liquidity_risk, 3),
            "risk_warnings": risk_warnings,
            "risk_mitigations": risk_mitigations,
            "analysis": analysis,
            "key_findings": self._extract_findings(
                risk_level, volatility_risk, market_risk, news_risk
            ),
            "signal": self._risk_to_signal(risk_level)
        }

        # LLM-enhanced analysis
        if llm_service.is_available():
            llm_result = await self._llm_analyze(
                system_prompt="You are a risk assessment expert. Evaluate the investment risk comprehensively.",
                user_prompt=f"Stock: {symbol}\nVolatility risk: {volatility_risk:.3f}\nMarket risk: {market_risk:.3f}\nNews risk: {news_risk:.3f}\nLiquidity risk: {liquidity_risk:.3f}\nOverall risk: {overall_risk_score:.3f} ({risk_level})\nRisk warnings: {risk_warnings}",
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis": {"type": "string"},
                        "signal": {"type": "string", "enum": ["strong_buy", "buy", "hold", "sell", "strong_sell"]},
                        "key_findings": {"type": "array", "items": {"type": "string"}},
                        "risk_warnings": {"type": "array", "items": {"type": "string"}},
                        "risk_mitigations": {"type": "array", "items": {"type": "string"}}
                    }
                }
            )
            if llm_result:
                llm_result = llm_service.validate_agent_result(llm_result)
                result["analysis"] = llm_result.get("analysis", result["analysis"])
                result["signal"] = llm_result.get("signal", result["signal"])
                result["key_findings"] = llm_result.get("key_findings", result["key_findings"])
                result["risk_warnings"] = llm_result.get("risk_warnings", result["risk_warnings"])
                result["risk_mitigations"] = llm_result.get("risk_mitigations", result["risk_mitigations"])
                result["llm_enhanced"] = True

        return result

    def _calculate_volatility_risk(
        self, stock_data: Dict, technical_data: Dict
    ) -> float:
        """Calculate risk based on price volatility."""
        risk = 0.5  # Base risk

        # Check ATR (Average True Range)
        atr = technical_data.get("atr_14")
        current_price = stock_data.get("current_price", 0)

        if atr and current_price and current_price > 0:
            volatility_percent = (atr / current_price) * 100
            if volatility_percent > 4:
                risk = 0.9
            elif volatility_percent > 3:
                risk = 0.7
            elif volatility_percent > 2:
                risk = 0.6
            elif volatility_percent > 1:
                risk = 0.4
            else:
                risk = 0.3

        # Check 52-week range position
        high_52w = stock_data.get("high_52w")
        low_52w = stock_data.get("low_52w")
        current = stock_data.get("current_price", 0)

        if high_52w and low_52w and current:
            range_percent = ((high_52w - low_52w) / low_52w) * 100 if low_52w else 0
            if range_percent > 100:
                risk = min(risk + 0.2, 1.0)
            elif range_percent > 50:
                risk = min(risk + 0.1, 1.0)

        return risk

    def _calculate_market_risk(self, stock_data: Dict) -> float:
        """Calculate market-related risk."""
        risk = 0.5

        # Beta indicates market sensitivity
        beta = stock_data.get("beta")
        if beta:
            if beta > 2:
                risk = 0.9
            elif beta > 1.5:
                risk = 0.75
            elif beta > 1:
                risk = 0.6
            elif beta > 0.5:
                risk = 0.4
            else:
                risk = 0.3

        # Sector risk (simplified)
        sector = stock_data.get("sector", "")
        high_risk_sectors = ["Technology", "Cryptocurrency", "Biotechnology"]
        if sector in high_risk_sectors:
            risk = min(risk + 0.1, 1.0)

        return risk

    def _calculate_news_risk(self, sentiment_data: Dict) -> float:
        """Calculate risk based on news sentiment."""
        risk = 0.5

        sentiment_score = sentiment_data.get("sentiment_score", 0)
        news_count = sentiment_data.get("news_count", 0)

        # High negative sentiment increases risk
        if sentiment_score < -0.5:
            risk = 0.85
        elif sentiment_score < -0.3:
            risk = 0.7
        elif sentiment_score < -0.1:
            risk = 0.6
        elif sentiment_score > 0.3:
            risk = 0.35
        elif sentiment_score > 0.5:
            risk = 0.3

        # Low news coverage = uncertainty risk
        if news_count < 3:
            risk = min(risk + 0.15, 1.0)

        return risk

    def _calculate_liquidity_risk(self, stock_data: Dict) -> float:
        """Calculate liquidity risk based on trading volume."""
        risk = 0.3  # Default low risk

        volume = stock_data.get("volume", 0)
        market_cap = stock_data.get("market_cap", 0)

        # Low volume = high liquidity risk
        if volume < 100000:
            risk = 0.8
        elif volume < 500000:
            risk = 0.6
        elif volume < 1000000:
            risk = 0.5
        elif volume < 5000000:
            risk = 0.4

        # Small cap stocks have higher liquidity risk
        if market_cap:
            if market_cap < 100_000_000:  # < $100M
                risk = min(risk + 0.3, 1.0)
            elif market_cap < 1_000_000_000:  # < $1B
                risk = min(risk + 0.15, 1.0)

        return risk

    def _calculate_overall_risk(
        self,
        volatility: float,
        market: float,
        news: float,
        liquidity: float
    ) -> float:
        """Calculate weighted overall risk score."""
        # Weighted average
        weights = {
            "volatility": 0.35,
            "market": 0.25,
            "news": 0.25,
            "liquidity": 0.15
        }

        overall = (
            volatility * weights["volatility"] +
            market * weights["market"] +
            news * weights["news"] +
            liquidity * weights["liquidity"]
        )

        return min(max(overall, 0), 1)

    def _score_to_risk_level(self, score: float) -> str:
        """Convert risk score to risk level."""
        if score >= 0.75:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        return "low"

    def _generate_risk_warnings(
        self,
        volatility: float,
        market: float,
        news: float,
        liquidity: float,
        stock_data: Dict
    ) -> List[str]:
        """Generate specific risk warnings."""
        warnings = []

        if volatility > 0.7:
            warnings.append("HIGH VOLATILITY: Price swings significantly - expect large moves")
        elif volatility > 0.5:
            warnings.append("Moderate volatility: Price shows notable fluctuations")

        if market > 0.7:
            warnings.append("HIGH MARKET SENSITIVITY: Stock moves strongly with market")
        elif market > 0.5:
            warnings.append("Above-average market correlation")

        if news > 0.7:
            warnings.append("NEGATIVE NEWS SENTIMENT: Recent news coverage is bearish")
        elif news > 0.5:
            warnings.append("Mixed news sentiment: Uncertainty in media coverage")

        if liquidity > 0.6:
            warnings.append("LIQUIDITY RISK: Low trading volume may cause slippage")

        # Company-specific risks
        beta = stock_data.get("beta")
        if beta and beta > 1.5:
            warnings.append(f"High beta ({beta:.2f}): Amplified market movements")

        return warnings

    def _generate_mitigations(self, risk_level: str, warnings: List[str]) -> List[str]:
        """Generate risk mitigation suggestions."""
        mitigations = []

        if risk_level in ["high", "critical"]:
            mitigations.append("Consider using stop-loss orders to limit downside")
            mitigations.append("Reduce position size to manage risk exposure")

        if any("VOLATILITY" in w for w in warnings):
            mitigations.append("Consider options strategies for hedging")
            mitigations.append("Avoid over-leveraging positions")

        if any("LIQUIDITY" in w for w in warnings):
            mitigations.append("Use limit orders instead of market orders")
            mitigations.append("Consider scaling in/out of positions gradually")

        if any("NEWS" in w for w in warnings):
            mitigations.append("Monitor news closely for developments")
            mitigations.append("Consider waiting for news clarity before entering")

        if not mitigations:
            mitigations.append("Standard risk management practices apply")
            mitigations.append("Maintain diversified portfolio allocation")

        return mitigations

    def _generate_risk_analysis(
        self,
        risk_level: str,
        overall_score: float,
        volatility: float,
        market: float,
        news: float,
        liquidity: float
    ) -> str:
        """Generate comprehensive risk analysis text."""
        analysis = f"Overall risk assessment: {risk_level.upper()} (score: {overall_score:.2f}/1.0). "

        if volatility > 0.6:
            analysis += "Volatility risk is elevated, indicating significant price swings. "
        elif volatility < 0.4:
            analysis += "Volatility is contained, suggesting stable price action. "

        if market > 0.6:
            analysis += "High market sensitivity means the stock will amplify market moves. "
        elif market < 0.4:
            analysis += "Lower market correlation provides some diversification benefit. "

        if news > 0.6:
            analysis += "Negative news sentiment adds uncertainty and downside risk. "
        elif news < 0.4:
            analysis += "News sentiment is favorable, supporting the investment thesis. "

        if liquidity > 0.6:
            analysis += "Liquidity concerns may impact trade execution. "

        # Add recommendation based on risk level
        if risk_level == "critical":
            analysis += "CRITICAL: This investment carries substantial risk. Conservative investors should avoid."
        elif risk_level == "high":
            analysis += "HIGH RISK: Suitable only for aggressive investors with high risk tolerance."
        elif risk_level == "medium":
            analysis += "MODERATE RISK: Acceptable for balanced investors with proper position sizing."
        else:
            analysis += "LOW RISK: Suitable for conservative investors seeking stability."

        return analysis

    def _extract_findings(
        self,
        risk_level: str,
        volatility: float,
        market: float,
        news: float
    ) -> List[str]:
        """Extract key risk findings."""
        findings = []

        findings.append(f"Overall risk level: {risk_level}")

        risk_components = [
            ("Volatility", volatility),
            ("Market sensitivity", market),
            ("News sentiment risk", news)
        ]

        for name, score in risk_components:
            if score > 0.7:
                findings.append(f"{name} is HIGH ({score:.2f})")
            elif score < 0.3:
                findings.append(f"{name} is LOW ({score:.2f})")

        return findings[:5]

    def _risk_to_signal(self, risk_level: str) -> str:
        """Convert risk level to trading signal adjustment."""
        signal_map = {
            "low": "hold",
            "medium": "hold",
            "high": "sell",
            "critical": "strong_sell"
        }
        return signal_map.get(risk_level, "hold")
