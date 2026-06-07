import asyncio
import time
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from .news_monitor_agent import NewsMonitorAgent
from .sentiment_agent import SentimentAgent
from .technical_agent import TechnicalAgent
from .risk_agent import RiskAgent
from .fundamental_agent import FundamentalAgent
from services.market_data import market_data_service
from services.ws_manager import ws_manager
from services.database_service import db_service

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates multiple AI agents to produce comprehensive financial analysis.
    Manages agent lifecycle, data flow, and result aggregation.
    """

    def __init__(self):
        # Initialize agents
        self.news_agent = NewsMonitorAgent()
        self.sentiment_agent = SentimentAgent()
        self.technical_agent = TechnicalAgent()
        self.risk_agent = RiskAgent()
        self.fundamental_agent = FundamentalAgent()

        self.agents = {
            "news": self.news_agent,
            "sentiment": self.sentiment_agent,
            "technical": self.technical_agent,
            "risk": self.risk_agent,
            "fundamental": self.fundamental_agent
        }

    async def analyze_stock(
        self,
        symbol: str,
        company_name: str = "",
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Run comprehensive analysis on a stock using all agents.

        Args:
            symbol: Stock ticker symbol
            company_name: Company name for news search
            analysis_type: Type of analysis (comprehensive, quick, news_only, technical_only)

        Returns:
            Complete analysis result with all agent outputs and final recommendation
        """
        start_time = time.time()

        # Fetch base stock data
        stock_data = await market_data_service.get_stock_data(symbol)
        if "error" in stock_data:
            return {
                "status": "error",
                "error": stock_data["error"],
                "symbol": symbol
            }

        # Add company name to stock data if not present
        if company_name and "name" not in stock_data:
            stock_data["name"] = company_name

        # Run agents based on analysis type - parallelize where possible
        agent_results = {}

        if analysis_type == "comprehensive":
            # Phase 1: Run News, Technical, and Fundamental agents in parallel
            news_task = self.news_agent.execute({
                "symbol": symbol,
                "company_name": stock_data.get("name", company_name),
                "news_count": 10
            })
            technical_task = self.technical_agent.execute({
                "symbol": symbol,
                "stock_data": stock_data
            })
            fundamental_task = self.fundamental_agent.execute({
                "symbol": symbol,
                "stock_data": stock_data
            })

            news_result, technical_result, fundamental_result = await asyncio.gather(
                news_task, technical_task, fundamental_task
            )
            agent_results["news"] = news_result.get("result", {})
            await ws_manager.send_agent_progress(symbol, "News Monitor", "completed", agent_results["news"])
            agent_results["technical"] = technical_result.get("result", {})
            await ws_manager.send_agent_progress(symbol, "Technical Analysis", "completed", agent_results["technical"])
            agent_results["fundamental"] = fundamental_result.get("result", {})
            await ws_manager.send_agent_progress(symbol, "Fundamental Analysis", "completed", agent_results["fundamental"])

            # Phase 2: Run Sentiment agent (depends on news data)
            sentiment_result = await self.sentiment_agent.execute({
                "symbol": symbol,
                "stock_data": stock_data,
                "news_data": agent_results.get("news", {})
            })
            agent_results["sentiment"] = sentiment_result.get("result", {})
            await ws_manager.send_agent_progress(symbol, "Sentiment Analysis", "completed", agent_results["sentiment"])

            # Phase 3: Run Risk agent (depends on all others)
            risk_result = await self.risk_agent.execute({
                "symbol": symbol,
                "stock_data": stock_data,
                "technical_data": agent_results.get("technical", {}),
                "sentiment_data": agent_results.get("sentiment", {})
            })
            agent_results["risk"] = risk_result.get("result", {})
            await ws_manager.send_agent_progress(symbol, "Risk Assessment", "completed", agent_results["risk"])

        elif analysis_type == "news_only":
            news_result = await self.news_agent.execute({
                "symbol": symbol,
                "company_name": stock_data.get("name", company_name),
                "news_count": 10
            })
            agent_results["news"] = news_result.get("result", {})

        elif analysis_type == "technical_only":
            technical_result = await self.technical_agent.execute({
                "symbol": symbol,
                "stock_data": stock_data
            })
            agent_results["technical"] = technical_result.get("result", {})

        elif analysis_type == "sentiment_only":
            # Sentiment agent depends on news data, fetch it first
            news_result = await self.news_agent.execute({
                "symbol": symbol,
                "company_name": stock_data.get("name", company_name),
                "news_count": 10
            })
            agent_results["news"] = news_result.get("result", {})
            
            sentiment_result = await self.sentiment_agent.execute({
                "symbol": symbol,
                "stock_data": stock_data,
                "news_data": agent_results.get("news", {})
            })
            agent_results["sentiment"] = sentiment_result.get("result", {})

        # Generate final recommendation
        recommendation = self._generate_recommendation(
            symbol=symbol,
            stock_data=stock_data,
            agent_results=agent_results
        )

        # LLM-enhanced reasoning
        try:
            llm_reasoning = await self._generate_llm_reasoning(
                symbol, stock_data, agent_results, recommendation.get("reasoning", "")
            )
            if llm_reasoning:
                recommendation["reasoning"] = llm_reasoning
                recommendation["llm_enhanced"] = True
        except Exception as e:
            logger.warning(f"LLM reasoning enhancement failed: {e}")

        processing_time = time.time() - start_time

        # Save to database
        try:
            db_service.save_analysis({
                "symbol": symbol,
                "company_name": stock_data.get("name", ""),
                "current_price": stock_data.get("current_price"),
                "change_percent": stock_data.get("change_percent"),
                "recommendation": recommendation,
                "agent_results": agent_results,
                "processing_time": round(processing_time, 2)
            })
        except Exception as e:
            logger.warning(f"Failed to save analysis to database: {e}")

        await ws_manager.send_analysis_complete(symbol, {
            "recommendation": recommendation,
            "processing_time": round(processing_time, 2)
        })

        return {
            "status": "success",
            "symbol": symbol,
            "company_name": stock_data.get("name", symbol),
            "current_price": stock_data.get("current_price"),
            "change_percent": stock_data.get("change_percent"),
            "agent_results": agent_results,
            "recommendation": recommendation,
            "processing_time": round(processing_time, 2),
            "timestamp": datetime.now().isoformat()
        }

    def _generate_recommendation(
        self,
        symbol: str,
        stock_data: Dict,
        agent_results: Dict
    ) -> Dict[str, Any]:
        """Generate final investment recommendation by combining agent outputs."""

        # Collect signals from each agent
        signals = []
        confidences = []
        key_findings = []
        risk_factors = []

        # News signal
        news_data = agent_results.get("news", {})
        if news_data:
            news_signal = news_data.get("signal", "hold")
            signals.append(self._signal_to_numeric(news_signal))
            confidences.append(news_data.get("confidence", 0.5))
            key_findings.extend(news_data.get("key_findings", []))
            risk_factors.extend(news_data.get("risk_factors", []))

        # Sentiment signal
        sentiment_data = agent_results.get("sentiment", {})
        if sentiment_data:
            sentiment_signal = sentiment_data.get("signal", "hold")
            signals.append(self._signal_to_numeric(sentiment_signal))
            confidences.append(sentiment_data.get("confidence", 0.5))
            key_findings.extend(sentiment_data.get("key_findings", []))
            risk_factors.extend(sentiment_data.get("risk_factors", []))

        # Technical signal
        technical_data = agent_results.get("technical", {})
        if technical_data:
            technical_signal = technical_data.get("signal", "hold")
            signals.append(self._signal_to_numeric(technical_signal))
            confidences.append(technical_data.get("confidence", 0.5))
            key_findings.extend(technical_data.get("key_findings", []))
            risk_factors.extend(technical_data.get("risk_factors", []))

        # Risk signal (inverse - higher risk = more negative signal)
        risk_data = agent_results.get("risk", {})
        if risk_data:
            risk_level = risk_data.get("overall_risk", "medium")
            risk_signal = self._risk_to_signal(risk_level)
            signals.append(self._signal_to_numeric(risk_signal) * 0.5)  # Lower weight
            key_findings.extend(risk_data.get("key_findings", []))
            risk_factors.extend(risk_data.get("risk_warnings", []))

        # Fundamental signal
        fundamental_data = agent_results.get("fundamental", {})
        if fundamental_data:
            fundamental_signal = fundamental_data.get("signal", "hold")
            signals.append(self._signal_to_numeric(fundamental_signal))
            confidences.append(fundamental_data.get("confidence", 0.5))
            key_findings.extend(fundamental_data.get("key_findings", []))
            risk_factors.extend(fundamental_data.get("risk_factors", []))

        # Calculate weighted average signal
        if signals and confidences:
            avg_confidence = sum(confidences) / len(confidences)
            # Weight by confidence
            weighted_signal = sum(
                s * c for s, c in zip(signals, confidences[:len(signals)])
            ) / sum(confidences[:len(signals)]) if confidences else 0
        else:
            avg_confidence = 0.5
            weighted_signal = 0

        # Determine final signal
        final_signal = self._numeric_to_signal(weighted_signal)

        # Calculate stop loss and target price
        current_price = stock_data.get("current_price", 0)
        atr = technical_data.get("indicators", {}).get("atr_14", current_price * 0.02)

        stop_loss = round(current_price - (atr * 2), 2) if atr else round(current_price * 0.95, 2)
        target_price = round(current_price + (atr * 3), 2) if atr else round(current_price * 1.15, 2)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            final_signal, agent_results, key_findings, risk_factors
        )

        return {
            "signal": final_signal,
            "confidence": round(avg_confidence, 2),
            "target_price": target_price,
            "stop_loss": stop_loss,
            "reasoning": reasoning,
            "key_points": key_findings[:5],
            "risk_assessment": risk_data if risk_data else {},
            "agent_analyses": list(agent_results.values())
        }

    def _signal_to_numeric(self, signal: str) -> float:
        """Convert signal string to numeric value."""
        signal_map = {
            "strong_buy": 1.0,
            "buy": 0.5,
            "hold": 0,
            "sell": -0.5,
            "strong_sell": -1.0
        }
        return signal_map.get(signal, 0)

    def _numeric_to_signal(self, value: float) -> str:
        """Convert numeric value to signal string."""
        if value > 0.5:
            return "strong_buy"
        elif value > 0.2:
            return "buy"
        elif value < -0.5:
            return "strong_sell"
        elif value < -0.2:
            return "sell"
        return "hold"

    def _risk_to_signal(self, risk_level: str) -> str:
        """Convert risk level to signal."""
        risk_map = {
            "low": "buy",
            "medium": "hold",
            "high": "sell",
            "critical": "strong_sell"
        }
        return risk_map.get(risk_level, "hold")

    async def _generate_llm_reasoning(
        self,
        symbol: str,
        stock_data: Dict,
        agent_results: Dict,
        rule_based_reasoning: str
    ) -> str:
        """Use LLM to generate enhanced recommendation reasoning."""
        from services.llm_service import llm_service

        if not llm_service.is_available():
            return rule_based_reasoning

        try:
            # Build context from all agent results
            news_data = agent_results.get("news", {})
            sentiment_data = agent_results.get("sentiment", {})
            technical_data = agent_results.get("technical", {})
            risk_data = agent_results.get("risk", {})

            context = f"""Stock: {symbol} ({stock_data.get('name', '')})
Current Price: ${stock_data.get('current_price', 'N/A')}
Change: {stock_data.get('change_percent', 0)}%

News Analysis: {news_data.get('summary', 'N/A')}
News Signal: {news_data.get('signal', 'hold')} (confidence: {news_data.get('confidence', 0.5)})

Sentiment Analysis: {sentiment_data.get('analysis', 'N/A')}
Sentiment Signal: {sentiment_data.get('signal', 'hold')} (confidence: {sentiment_data.get('confidence', 0.5)})
Overall Sentiment: {sentiment_data.get('overall_sentiment', 'neutral')}

Technical Analysis: {technical_data.get('summary', 'N/A')}
Technical Signal: {technical_data.get('signal', 'hold')} (confidence: {technical_data.get('confidence', 0.5)})
Key Indicators: RSI={technical_data.get('indicators', {}).get('rsi_14', 'N/A')}, MACD={technical_data.get('indicators', {}).get('macd', 'N/A')}

Risk Assessment: {risk_data.get('analysis', 'N/A')}
Overall Risk: {risk_data.get('overall_risk', 'medium')} (score: {risk_data.get('risk_score', 0.5)})
Risk Warnings: {risk_data.get('risk_warnings', [])}

Rule-based reasoning: {rule_based_reasoning}"""

            llm_result = await llm_service.generate_structured(
                system_prompt="You are a senior financial analyst. Based on the multi-agent analysis data provided, generate a clear, professional investment recommendation reasoning. Be specific about which factors support the recommendation and which risks to watch. Write in a confident but measured tone. You MUST respond with valid JSON.",
                user_prompt=context,
                output_schema={
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "key_catalysts": {"type": "array", "items": {"type": "string"}},
                        "key_risks": {"type": "array", "items": {"type": "string"}},
                        "time_horizon": {"type": "string"}
                    }
                }
            )

            reasoning = llm_result.get("reasoning", "")
            if reasoning:
                # Enrich with LLM insights
                catalysts = llm_result.get("key_catalysts", [])
                risks = llm_result.get("key_risks", [])
                horizon = llm_result.get("time_horizon", "")

                enhanced = reasoning
                if catalysts:
                    enhanced += "\n\nKey Catalysts:\n"
                    for i, c in enumerate(catalysts[:3], 1):
                        enhanced += f"  {i}. {c}\n"
                if risks:
                    enhanced += "\nKey Risks to Monitor:\n"
                    for i, r in enumerate(risks[:3], 1):
                        enhanced += f"  {i}. {r}\n"
                if horizon:
                    enhanced += f"\nSuggested Time Horizon: {horizon}"

                return enhanced
            return rule_based_reasoning

        except Exception as e:
            logger.warning(f"LLM reasoning generation failed: {e}")
            return rule_based_reasoning

    def _generate_reasoning(
        self,
        signal: str,
        agent_results: Dict,
        key_findings: List[str],
        risk_factors: List[str]
    ) -> str:
        """Generate human-readable reasoning for the recommendation."""
        signal_explanations = {
            "strong_buy": "Strong Buy",
            "buy": "Buy",
            "hold": "Hold",
            "sell": "Sell",
            "strong_sell": "Strong Sell"
        }

        reasoning = f"Based on comprehensive analysis from 5 AI agents, our recommendation is {signal_explanations.get(signal, 'Hold')}.\n\n"

        # Add key positive factors
        if key_findings:
            reasoning += "Key factors supporting this view:\n"
            for i, finding in enumerate(key_findings[:3], 1):
                reasoning += f"{i}. {finding}\n"

        # Add risk considerations
        if risk_factors:
            reasoning += "\nRisk considerations:\n"
            for i, risk in enumerate(risk_factors[:2], 1):
                reasoning += f"{i}. {risk}\n"

        # Add agent-specific insights
        news_sentiment = agent_results.get("sentiment", {}).get("overall_sentiment", "neutral")
        technical_signal = agent_results.get("technical", {}).get("signal", "hold")
        risk_level = agent_results.get("risk", {}).get("overall_risk", "medium")

        fundamental_signal = agent_results.get("fundamental", {}).get("signal", "hold")
        reasoning += f"\nAgent consensus: News sentiment is {news_sentiment}, "
        reasoning += f"technical indicators show {technical_signal}, "
        reasoning += f"risk level is {risk_level}, and fundamental outlook is {fundamental_signal}."

        return reasoning

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        return {
            name: agent.get_status()
            for name, agent in self.agents.items()
        }


# Singleton instance
orchestrator = AgentOrchestrator()
