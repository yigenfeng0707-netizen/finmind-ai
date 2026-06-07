from typing import Any, Dict, List
from .base_agent import BaseAgent
from services.news_service import news_service
from services.llm_service import llm_service


class NewsMonitorAgent(BaseAgent):
    """
    Agent specialized in monitoring and analyzing financial news.
    Fetches latest news, categorizes by importance, and provides news-based insights.
    """

    def __init__(self):
        super().__init__(
            name="News Monitor Agent",
            agent_type="news_monitor"
        )

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze news for a given stock symbol.

        Args:
            data: Must contain 'symbol' and optionally 'company_name'
        """
        symbol = data.get("symbol", "")
        company_name = data.get("company_name", "")
        news_count = data.get("news_count", 10)

        # Fetch news
        news_articles = await news_service.fetch_stock_news(
            symbol=symbol,
            company_name=company_name,
            limit=news_count
        )

        if not news_articles:
            return {
                "summary": "No significant news found",
                "news_count": 0,
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                "key_headlines": [],
                "news_sentiment_score": 0,
                "analysis": "Insufficient news data for analysis"
            }

        # Analyze sentiment distribution
        sentiment_dist = {"positive": 0, "negative": 0, "neutral": 0}
        total_sentiment_score = 0

        for article in news_articles:
            sentiment = article.get("sentiment", "neutral")
            sentiment_dist[sentiment] = sentiment_dist.get(sentiment, 0) + 1
            total_sentiment_score += article.get("sentiment_score", 0)

        avg_sentiment = total_sentiment_score / len(news_articles)

        # Extract key headlines
        key_headlines = []
        for article in news_articles[:5]:
            key_headlines.append({
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "sentiment": article.get("sentiment", "neutral"),
                "sentiment_score": article.get("sentiment_score", 0)
            })

        # Generate analysis
        analysis = self._generate_analysis(
            news_articles, sentiment_dist, avg_sentiment
        )

        # Determine signal
        signal = self._determine_signal(avg_sentiment, sentiment_dist)

        result = {
            "summary": analysis,
            "news_count": len(news_articles),
            "sentiment_distribution": sentiment_dist,
            "key_headlines": key_headlines,
            "news_sentiment_score": round(avg_sentiment, 3),
            "signal": signal,
            "confidence": min(0.5 + len(news_articles) * 0.05, 0.9),
            "key_findings": self._extract_key_findings(news_articles),
            "risk_factors": self._extract_risk_factors(news_articles)
        }

        # LLM-enhanced analysis
        if llm_service.is_available():
            llm_result = await self._llm_analyze(
                system_prompt="You are a financial news analyst. Analyze the news data and provide insights.",
                user_prompt=f"Stock: {symbol}\nCompany: {company_name}\nNews articles: {key_headlines}\nSentiment distribution: {sentiment_dist}\nAverage sentiment: {avg_sentiment:.3f}",
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
                # Override rule-based results with LLM insights
                result["summary"] = llm_result.get("summary", result["summary"])
                result["signal"] = llm_result.get("signal", result["signal"])
                result["confidence"] = llm_result.get("confidence", result["confidence"])
                result["key_findings"] = llm_result.get("key_findings", result["key_findings"])
                result["risk_factors"] = llm_result.get("risk_factors", result["risk_factors"])
                result["llm_enhanced"] = True

        return result

    def _generate_analysis(
        self,
        articles: List[Dict],
        sentiment_dist: Dict[str, int],
        avg_sentiment: float
    ) -> str:
        """Generate natural language analysis of news."""
        total = len(articles)
        pos_pct = (sentiment_dist.get("positive", 0) / total) * 100
        neg_pct = (sentiment_dist.get("negative", 0) / total) * 100

        if avg_sentiment > 0.3:
            tone = "predominantly positive"
        elif avg_sentiment < -0.3:
            tone = "predominantly negative"
        else:
            tone = "mixed"

        analysis = (
            f"Analysis of {total} recent news articles shows {tone} sentiment "
            f"surrounding this stock. Positive coverage accounts for "
            f"{pos_pct:.0f}% of articles, while negative coverage represents "
            f"{neg_pct:.0f}%. "
        )

        if sentiment_dist.get("positive", 0) > sentiment_dist.get("negative", 0):
            analysis += "The news cycle appears favorable, which could support upward price momentum."
        elif sentiment_dist.get("negative", 0) > sentiment_dist.get("positive", 0):
            analysis += "Negative news sentiment may create headwinds for the stock in the near term."
        else:
            analysis += "Balanced news coverage suggests no clear directional bias from media sentiment."

        return analysis

    def _determine_signal(
        self, avg_sentiment: float, sentiment_dist: Dict[str, int]
    ) -> str:
        """Determine investment signal based on news analysis."""
        if avg_sentiment > 0.4:
            return "buy"
        elif avg_sentiment > 0.15:
            return "hold"  # slightly positive
        elif avg_sentiment < -0.4:
            return "sell"
        elif avg_sentiment < -0.15:
            return "hold"  # slightly negative
        return "hold"

    def _extract_key_findings(self, articles: List[Dict]) -> List[str]:
        """Extract key findings from news articles."""
        findings = []
        positive_count = sum(1 for a in articles if a.get("sentiment") == "positive")
        negative_count = sum(1 for a in articles if a.get("sentiment") == "negative")

        if positive_count > 0:
            findings.append(f"{positive_count} positive news articles identified")
        if negative_count > 0:
            findings.append(f"{negative_count} negative news articles identified")

        # Add top headline as finding
        if articles:
            top_article = max(articles, key=lambda x: abs(x.get("sentiment_score", 0)))
            findings.append(f"Most impactful headline: {top_article.get('title', '')[:100]}")

        return findings[:5]

    def _extract_risk_factors(self, articles: List[Dict]) -> List[str]:
        """Extract risk factors from negative news."""
        risk_factors = []
        for article in articles:
            if article.get("sentiment") == "negative" and article.get("sentiment_score", 0) < -0.3:
                risk_factors.append(f"Negative coverage: {article.get('title', '')[:80]}")
        return risk_factors[:3]
