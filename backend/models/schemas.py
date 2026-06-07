from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalType(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class NewsArticle(BaseModel):
    title: str
    description: Optional[str] = None
    source: str
    url: str
    published_at: datetime
    sentiment: SentimentType = SentimentType.NEUTRAL
    sentiment_score: float = Field(ge=-1.0, le=1.0, default=0.0)
    relevance_score: float = Field(ge=0.0, le=1.0, default=0.5)


class StockData(BaseModel):
    symbol: str
    name: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    technical_indicators: Dict[str, Any] = {}


class TechnicalIndicators(BaseModel):
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr_14: Optional[float] = None
    volume_sma: Optional[float] = None


class AgentAnalysis(BaseModel):
    agent_name: str
    agent_type: str
    analysis: str
    confidence: float = Field(ge=0.0, le=1.0)
    signal: SignalType
    key_findings: List[str] = []
    risk_factors: List[str] = []
    metadata: Dict[str, Any] = {}


class RiskAssessment(BaseModel):
    overall_risk: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    volatility_risk: float = Field(ge=0.0, le=1.0)
    market_risk: float = Field(ge=0.0, le=1.0)
    news_risk: float = Field(ge=0.0, le=1.0)
    risk_warnings: List[str] = []
    risk_mitigations: List[str] = []


class InvestmentRecommendation(BaseModel):
    symbol: str
    company_name: str
    signal: SignalType
    confidence: float = Field(ge=0.0, le=1.0)
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    reasoning: str
    key_points: List[str] = []
    risk_assessment: RiskAssessment
    agent_analyses: List[AgentAnalysis] = []
    timestamp: datetime = Field(default_factory=datetime.now)


class AnalysisRequest(BaseModel):
    symbol: str
    analysis_type: str = "comprehensive"
    include_news: bool = True
    include_technical: bool = True
    include_sentiment: bool = True
    risk_tolerance: str = "moderate"


class AnalysisResponse(BaseModel):
    request_id: str
    symbol: str
    status: str
    recommendation: Optional[InvestmentRecommendation] = None
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)


class MarketOverview(BaseModel):
    indices: List[Dict[str, Any]] = []
    top_gainers: List[StockData] = []
    top_losers: List[StockData] = []
    market_sentiment: SentimentType = SentimentType.NEUTRAL
    news_summary: List[NewsArticle] = []
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    conversation_history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str
    suggestions: List[str] = []
    related_stocks: List[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
