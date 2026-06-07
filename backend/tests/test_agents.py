"""Unit tests for AI agents."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# Test BaseAgent
class TestBaseAgent:
    def test_base_agent_initialization(self):
        from agents.base_agent import BaseAgent
        
        class ConcreteAgent(BaseAgent):
            async def analyze(self, data):
                return {"test": True}
        
        agent = ConcreteAgent("Test Agent", "test")
        assert agent.name == "Test Agent"
        assert agent.agent_type == "test"
        assert agent.is_running is False
        assert agent.execution_count == 0
        assert agent.error_count == 0

    def test_get_status(self):
        from agents.base_agent import BaseAgent
        
        class ConcreteAgent(BaseAgent):
            async def analyze(self, data):
                return {"test": True}
        
        agent = ConcreteAgent("Test Agent", "test")
        status = agent.get_status()
        assert status["name"] == "Test Agent"
        assert status["type"] == "test"
        assert status["success_rate"] == 0

    @pytest.mark.asyncio
    async def test_execute_success(self):
        from agents.base_agent import BaseAgent
        
        class ConcreteAgent(BaseAgent):
            async def analyze(self, data):
                return {"result": "ok"}
        
        agent = ConcreteAgent("Test Agent", "test")
        result = await agent.execute({"input": "test"})
        assert result["status"] == "success"
        assert result["result"]["result"] == "ok"
        assert agent.execution_count == 1

    @pytest.mark.asyncio
    async def test_execute_error(self):
        from agents.base_agent import BaseAgent
        
        class FailingAgent(BaseAgent):
            async def analyze(self, data):
                raise ValueError("Test error")
        
        agent = FailingAgent("Fail Agent", "fail")
        result = await agent.execute({"input": "test"})
        assert result["status"] == "error"
        assert agent.error_count == 1


# Test TechnicalAgent
class TestTechnicalAgent:
    @pytest.mark.asyncio
    async def test_technical_agent_initialization(self):
        from agents.technical_agent import TechnicalAgent
        agent = TechnicalAgent()
        assert agent.name == "Technical Analysis Agent"
        assert agent.agent_type == "technical"

    @pytest.mark.asyncio
    async def test_signal_to_numeric(self):
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()
        assert orch._signal_to_numeric("strong_buy") == 1.0
        assert orch._signal_to_numeric("buy") == 0.5
        assert orch._signal_to_numeric("hold") == 0
        assert orch._signal_to_numeric("sell") == -0.5
        assert orch._signal_to_numeric("strong_sell") == -1.0

    @pytest.mark.asyncio
    async def test_numeric_to_signal(self):
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()
        assert orch._numeric_to_signal(0.8) == "strong_buy"
        assert orch._numeric_to_signal(0.3) == "buy"
        assert orch._numeric_to_signal(0) == "hold"
        assert orch._numeric_to_signal(-0.3) == "sell"
        assert orch._numeric_to_signal(-0.8) == "strong_sell"


# Test RiskAgent
class TestRiskAgent:
    @pytest.mark.asyncio
    async def test_risk_agent_initialization(self):
        from agents.risk_agent import RiskAgent
        agent = RiskAgent()
        assert agent.name == "Risk Assessment Agent"
        assert agent.agent_type == "risk"

    def test_score_to_risk_level(self):
        from agents.risk_agent import RiskAgent
        agent = RiskAgent()
        assert agent._score_to_risk_level(0.8) == "critical"
        assert agent._score_to_risk_level(0.65) == "high"
        assert agent._score_to_risk_level(0.5) == "medium"
        assert agent._score_to_risk_level(0.3) == "low"

    def test_risk_to_signal(self):
        from agents.risk_agent import RiskAgent
        agent = RiskAgent()
        assert agent._risk_to_signal("low") == "hold"
        assert agent._risk_to_signal("medium") == "hold"
        assert agent._risk_to_signal("high") == "sell"
        assert agent._risk_to_signal("critical") == "strong_sell"


# Test SentimentAgent
class TestSentimentAgent:
    @pytest.mark.asyncio
    async def test_sentiment_agent_initialization(self):
        from agents.sentiment_agent import SentimentAgent
        agent = SentimentAgent()
        assert agent.name == "Sentiment Analysis Agent"
        assert agent.agent_type == "sentiment"

    def test_score_to_label(self):
        from agents.sentiment_agent import SentimentAgent
        agent = SentimentAgent()
        assert agent._score_to_label(0.5) == "bullish"
        assert agent._score_to_label(0.2) == "slightly_bullish"
        assert agent._score_to_label(0) == "neutral"
        assert agent._score_to_label(-0.2) == "slightly_bearish"
        assert agent._score_to_label(-0.5) == "bearish"

    def test_sentiment_to_signal(self):
        from agents.sentiment_agent import SentimentAgent
        agent = SentimentAgent()
        assert agent._sentiment_to_signal(0.5) == "strong_buy"
        assert agent._sentiment_to_signal(0.2) == "buy"
        assert agent._sentiment_to_signal(0) == "hold"
        assert agent._sentiment_to_signal(-0.2) == "sell"
        assert agent._sentiment_to_signal(-0.5) == "strong_sell"


# Test NewsMonitorAgent
class TestNewsMonitorAgent:
    @pytest.mark.asyncio
    async def test_news_agent_initialization(self):
        from agents.news_monitor_agent import NewsMonitorAgent
        agent = NewsMonitorAgent()
        assert agent.name == "News Monitor Agent"
        assert agent.agent_type == "news_monitor"

    def test_determine_signal(self):
        from agents.news_monitor_agent import NewsMonitorAgent
        agent = NewsMonitorAgent()
        assert agent._determine_signal(0.5, {}) == "buy"
        assert agent._determine_signal(-0.5, {}) == "sell"
        assert agent._determine_signal(0, {}) == "hold"


# Test Orchestrator
class TestOrchestrator:
    def test_orchestrator_initialization(self):
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()
        assert "news" in orch.agents
        assert "sentiment" in orch.agents
        assert "technical" in orch.agents
        assert "risk" in orch.agents

    def test_get_agent_status(self):
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()
        status = orch.get_agent_status()
        assert len(status) == 4
        assert all("name" in s for s in status.values())

    def test_risk_to_signal(self):
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()
        assert orch._risk_to_signal("low") == "buy"
        assert orch._risk_to_signal("medium") == "hold"
        assert orch._risk_to_signal("high") == "sell"
        assert orch._risk_to_signal("critical") == "strong_sell"
