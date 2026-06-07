from typing import Any, Dict, List
from .base_agent import BaseAgent
from services.market_data import market_data_service
from services.llm_service import llm_service


class FundamentalAgent(BaseAgent):
    """
    Agent specialized in fundamental analysis of stocks.
    Analyzes PE, PB, ROE, revenue growth, earnings, and valuation metrics.
    """

    def __init__(self):
        super().__init__(
            name="Fundamental Analysis Agent",
            agent_type="fundamental"
        )

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform fundamental analysis on a stock.

        Args:
            data: Must contain 'symbol' and optionally 'stock_data'
        """
        symbol = data.get("symbol", "")
        stock_data = data.get("stock_data", {})

        # Extract fundamental metrics from stock data
        metrics = self._extract_metrics(stock_data)

        # Analyze valuation
        valuation = self._analyze_valuation(metrics)

        # Analyze profitability
        profitability = self._analyze_profitability(metrics)

        # Analyze growth
        growth = self._analyze_growth(metrics, stock_data)

        # Determine overall fundamental signal
        signal = self._determine_fundamental_signal(valuation, profitability, growth)

        # Calculate confidence
        confidence = self._calculate_confidence(metrics)

        # Generate analysis text
        analysis = self._generate_analysis(metrics, valuation, profitability, growth)

        # Extract key findings and risk factors
        key_findings = self._extract_key_findings(metrics, valuation, profitability, growth)
        risk_factors = self._identify_risk_factors(metrics)

        result = {
            "summary": analysis,
            "metrics": metrics,
            "valuation": valuation,
            "profitability": profitability,
            "growth": growth,
            "signal": signal,
            "confidence": round(confidence, 2),
            "key_findings": key_findings,
            "risk_factors": risk_factors
        }

        # LLM-enhanced analysis
        if llm_service.is_available():
            llm_result = await self._llm_analyze(
                system_prompt="You are a fundamental analysis expert. Analyze the company's financial health based on valuation, profitability, and growth metrics.",
                user_prompt=f"Stock: {symbol}\nMetrics: {metrics}\nValuation: {valuation}\nProfitability: {profitability}\nGrowth: {growth}",
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

    def _extract_metrics(self, stock_data: Dict) -> Dict[str, Any]:
        """Extract fundamental metrics from stock data."""
        return {
            "pe_ratio": stock_data.get("pe_ratio"),
            "market_cap": stock_data.get("market_cap"),
            "dividend_yield": stock_data.get("dividend_yield"),
            "beta": stock_data.get("beta"),
            "high_52w": stock_data.get("high_52w"),
            "low_52w": stock_data.get("low_52w"),
            "current_price": stock_data.get("current_price"),
            "sector": stock_data.get("sector", "Unknown"),
        }

    def _analyze_valuation(self, metrics: Dict) -> Dict[str, Any]:
        """Analyze stock valuation metrics."""
        assessment = "neutral"
        details = []

        pe = metrics.get("pe_ratio")
        if pe is not None:
            if pe < 0:
                assessment = "negative"
                details.append(f"Negative P/E ratio ({pe:.1f}) indicates losses")
            elif pe < 15:
                assessment = "positive"
                details.append(f"Low P/E ratio ({pe:.1f}) suggests undervaluation")
            elif pe < 25:
                details.append(f"Moderate P/E ratio ({pe:.1f}) is within normal range")
            elif pe < 40:
                assessment = "cautious"
                details.append(f"Elevated P/E ratio ({pe:.1f}) may indicate overvaluation")
            else:
                assessment = "negative"
                details.append(f"Very high P/E ratio ({pe:.1f}) suggests significant overvaluation")

        # 52-week range analysis
        high = metrics.get("high_52w")
        low = metrics.get("low_52w")
        current = metrics.get("current_price")
        if high and low and current and low > 0:
            position = (current - low) / (high - low)
            if position > 0.9:
                details.append(f"Trading near 52-week high ({position:.0%} of range)")
            elif position < 0.2:
                details.append(f"Trading near 52-week low ({position:.0%} of range) - potential value")

        # Dividend yield
        div_yield = metrics.get("dividend_yield")
        if div_yield is not None and div_yield > 0:
            if div_yield > 0.04:
                details.append(f"High dividend yield ({div_yield:.1%}) provides income cushion")
            elif div_yield > 0.02:
                details.append(f"Moderate dividend yield ({div_yield:.1%})")

        return {"assessment": assessment, "details": details}

    def _analyze_profitability(self, metrics: Dict) -> Dict[str, Any]:
        """Analyze profitability indicators."""
        assessment = "neutral"
        details = []

        # Use sector as a proxy for typical profitability
        sector = metrics.get("sector", "")
        high_margin_sectors = ["Technology", "Healthcare", "Financials"]
        low_margin_sectors = ["Energy", "Utilities", "Consumer Staples"]

        if sector in high_margin_sectors:
            details.append(f"{sector} sector typically has higher profit margins")
        elif sector in low_margin_sectors:
            details.append(f"{sector} sector typically has lower profit margins")

        # Market cap as size/profitability proxy
        market_cap = metrics.get("market_cap")
        if market_cap:
            if market_cap > 200_000_000_000:  # > $200B
                details.append("Large-cap company with established profitability")
                assessment = "positive"
            elif market_cap > 10_000_000_000:  # > $10B
                details.append("Mid-to-large-cap with reasonable profitability expectations")
            elif market_cap > 2_000_000_000:  # > $2B
                details.append("Mid-cap company - profitability may vary")
            else:
                details.append("Small-cap company - higher profitability uncertainty")
                assessment = "cautious"

        return {"assessment": assessment, "details": details}

    def _analyze_growth(self, metrics: Dict, stock_data: Dict) -> Dict[str, Any]:
        """Analyze growth indicators."""
        assessment = "neutral"
        details = []

        # Use price momentum as a growth proxy
        current = metrics.get("current_price")
        high_52w = metrics.get("high_52w")
        low_52w = metrics.get("low_52w")

        if current and high_52w and low_52w and low_52w > 0:
            range_pct = ((high_52w - low_52w) / low_52w) * 100
            if range_pct > 80:
                details.append(f"High 52-week range ({range_pct:.0f}%) suggests significant growth volatility")
            elif range_pct > 40:
                details.append(f"Moderate 52-week range ({range_pct:.0f}%)")
            else:
                details.append(f"Low 52-week range ({range_pct:.0f}%) suggests stability")

        # Sector growth outlook
        sector = metrics.get("sector", "")
        growth_sectors = ["Technology", "Healthcare", "Consumer Cyclical"]
        if sector in growth_sectors:
            details.append(f"{sector} sector has favorable growth outlook")
            assessment = "positive"

        return {"assessment": assessment, "details": details}

    def _determine_fundamental_signal(
        self, valuation: Dict, profitability: Dict, growth: Dict
    ) -> str:
        """Determine overall fundamental signal."""
        scores = {"positive": 1, "neutral": 0, "cautious": -0.5, "negative": -1}

        val_score = scores.get(valuation.get("assessment", "neutral"), 0)
        prof_score = scores.get(profitability.get("assessment", "neutral"), 0)
        growth_score = scores.get(growth.get("assessment", "neutral"), 0)

        # Weighted average: valuation 40%, profitability 35%, growth 25%
        total = val_score * 0.4 + prof_score * 0.35 + growth_score * 0.25

        if total > 0.5:
            return "strong_buy"
        elif total > 0.15:
            return "buy"
        elif total < -0.5:
            return "strong_sell"
        elif total < -0.15:
            return "sell"
        return "hold"

    def _calculate_confidence(self, metrics: Dict) -> float:
        """Calculate confidence in fundamental analysis."""
        confidence = 0.4  # Base confidence for fundamental analysis

        # More metrics available = higher confidence
        available = sum(1 for v in metrics.values() if v is not None)
        confidence += min(available * 0.05, 0.2)

        # Having PE ratio significantly increases confidence
        if metrics.get("pe_ratio") is not None:
            confidence += 0.1

        # Having market cap data
        if metrics.get("market_cap") is not None:
            confidence += 0.1

        return min(confidence, 0.85)

    def _generate_analysis(
        self, metrics: Dict, valuation: Dict, profitability: Dict, growth: Dict
    ) -> str:
        """Generate fundamental analysis text."""
        analysis = "Fundamental Analysis: "

        pe = metrics.get("pe_ratio")
        if pe is not None:
            if pe > 0:
                analysis += f"P/E ratio of {pe:.1f} suggests "
                if pe < 15:
                    analysis += "the stock may be undervalued. "
                elif pe < 25:
                    analysis += "fair valuation. "
                else:
                    analysis += "premium valuation. "
            else:
                analysis += "Negative earnings (loss-making). "

        val_details = valuation.get("details", [])
        if val_details:
            analysis += val_details[0] + ". "

        prof_details = profitability.get("details", [])
        if prof_details:
            analysis += prof_details[0] + ". "

        return analysis

    def _extract_key_findings(
        self, metrics: Dict, valuation: Dict, profitability: Dict, growth: Dict
    ) -> List[str]:
        """Extract key findings from fundamental analysis."""
        findings = []

        pe = metrics.get("pe_ratio")
        if pe is not None:
            if pe < 15 and pe > 0:
                findings.append(f"Low P/E ratio ({pe:.1f}) suggests potential undervaluation")
            elif pe > 40:
                findings.append(f"High P/E ratio ({pe:.1f}) indicates premium valuation")

        div = metrics.get("dividend_yield")
        if div and div > 0.03:
            findings.append(f"Attractive dividend yield of {div:.1%}")

        for detail in valuation.get("details", [])[:2]:
            findings.append(detail)

        for detail in growth.get("details", [])[:1]:
            findings.append(detail)

        return findings[:5]

    def _identify_risk_factors(self, metrics: Dict) -> List[str]:
        """Identify fundamental risk factors."""
        risks = []

        pe = metrics.get("pe_ratio")
        if pe is not None and pe < 0:
            risks.append("Company is currently loss-making (negative P/E)")

        market_cap = metrics.get("market_cap")
        if market_cap and market_cap < 2_000_000_000:
            risks.append("Small-cap stock carries higher fundamental risk")

        beta = metrics.get("beta")
        if beta and beta > 1.5:
            risks.append(f"High beta ({beta:.2f}) indicates above-average volatility")

        return risks[:3]
