import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
import logging
from textblob import TextBlob

from config import NEWSAPI_KEY

logger = logging.getLogger(__name__)


class NewsService:
    """Service for fetching and analyzing financial news."""

    def __init__(self):
        self.newsapi_key = NEWSAPI_KEY
        self.base_url = "https://newsapi.org/v2"

    async def fetch_stock_news(
        self, symbol: str, company_name: str = "", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch news articles related to a specific stock."""
        if not self.newsapi_key:
            return self._get_mock_news(symbol, company_name)

        try:
            query = f"{symbol} stock"
            if company_name:
                query = f"{company_name} OR {symbol}"

            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": limit,
                "apiKey": self.newsapi_key
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/everything", params=params
                )
                data = response.json()

                if data.get("status") == "ok":
                    articles = []
                    for article in data.get("articles", []):
                        # Analyze sentiment
                        title_sentiment = self._analyze_sentiment(
                            article.get("title", "")
                        )
                        desc_sentiment = self._analyze_sentiment(
                            article.get("description", "")
                        )

                        # Combine sentiments
                        combined_score = (
                            title_sentiment["score"] * 0.6 +
                            desc_sentiment["score"] * 0.4
                        )

                        articles.append({
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "source": article.get("source", {}).get("name", "Unknown"),
                            "url": article.get("url", ""),
                            "published_at": article.get("publishedAt", ""),
                            "sentiment": self._score_to_sentiment(combined_score),
                            "sentiment_score": round(combined_score, 3),
                            "relevance_score": 0.8
                        })

                    return articles
                else:
                    return self._get_mock_news(symbol, company_name)

        except Exception as e:
            logger.warning(f"Error fetching news: {e}")
            return self._get_mock_news(symbol, company_name)

    async def fetch_market_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch general market news."""
        if not self.newsapi_key:
            return self._get_mock_market_news()

        try:
            queries = [
                "stock market today",
                "financial markets",
                "investing news"
            ]

            all_articles = []
            for query in queries[:1]:  # Limit to first query to save API calls
                params = {
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": limit,
                    "apiKey": self.newsapi_key
                }

                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/everything", params=params
                    )
                    data = response.json()

                    if data.get("status") == "ok":
                        for article in data.get("articles", []):
                            sentiment = self._analyze_sentiment(
                                article.get("title", "") + " " +
                                (article.get("description") or "")
                            )
                            all_articles.append({
                                "title": article.get("title", ""),
                                "description": article.get("description", ""),
                                "source": article.get("source", {}).get("name", "Unknown"),
                                "url": article.get("url", ""),
                                "published_at": article.get("publishedAt", ""),
                                "sentiment": self._score_to_sentiment(sentiment["score"]),
                                "sentiment_score": round(sentiment["score"], 3),
                                "relevance_score": 0.7
                            })

            return all_articles[:limit]
        except Exception as e:
            logger.warning(f"Error fetching market news: {e}")
            return self._get_mock_market_news()

    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using TextBlob."""
        if not text:
            return {"polarity": 0, "subjectivity": 0, "score": 0}

        blob = TextBlob(text)
        return {
            "polarity": blob.sentiment.polarity,
            "subjectivity": blob.sentiment.subjectivity,
            "score": blob.sentiment.polarity  # -1 to 1
        }

    def _score_to_sentiment(self, score: float) -> str:
        """Convert numeric score to sentiment category."""
        if score > 0.1:
            return "positive"
        elif score < -0.1:
            return "negative"
        return "neutral"

    def _get_mock_news(self, symbol: str, company_name: str) -> List[Dict[str, Any]]:
        """Return mock news when API is unavailable."""
        mock_news = [
            {
                "title": f"{company_name or symbol} Reports Strong Q4 Earnings",
                "description": f"{company_name or symbol} exceeded analyst expectations with record revenue growth.",
                "source": "Financial Times",
                "url": "#",
                "published_at": datetime.now().isoformat(),
                "sentiment": "positive",
                "sentiment_score": 0.65,
                "relevance_score": 0.9
            },
            {
                "title": f"Market Analysts Upgrade {company_name or symbol} to Buy",
                "description": "Multiple Wall Street analysts have upgraded their rating citing strong fundamentals.",
                "source": "Bloomberg",
                "url": "#",
                "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "sentiment": "positive",
                "sentiment_score": 0.55,
                "relevance_score": 0.85
            },
            {
                "title": f"{company_name or symbol} Faces Competitive Pressure",
                "description": "New competitors entering the market could impact future growth.",
                "source": "Reuters",
                "url": "#",
                "published_at": (datetime.now() - timedelta(hours=5)).isoformat(),
                "sentiment": "negative",
                "sentiment_score": -0.35,
                "relevance_score": 0.75
            }
        ]
        return mock_news

    def _get_mock_market_news(self) -> List[Dict[str, Any]]:
        """Return mock market news when API is unavailable."""
        return [
            {
                "title": "Fed Signals Potential Rate Cut in September",
                "description": "Federal Reserve officials hint at possible rate reduction amid cooling inflation.",
                "source": "CNBC",
                "url": "#",
                "published_at": datetime.now().isoformat(),
                "sentiment": "positive",
                "sentiment_score": 0.45,
                "relevance_score": 0.95
            },
            {
                "title": "Tech Stocks Rally on AI Optimism",
                "description": "Major tech companies surge as AI investments show promising returns.",
                "source": "Wall Street Journal",
                "url": "#",
                "published_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                "sentiment": "positive",
                "sentiment_score": 0.55,
                "relevance_score": 0.9
            },
            {
                "title": "Oil Prices Rise on Supply Concerns",
                "description": "Global oil prices increase due to geopolitical tensions.",
                "source": "Financial Times",
                "url": "#",
                "published_at": (datetime.now() - timedelta(hours=3)).isoformat(),
                "sentiment": "neutral",
                "sentiment_score": 0.1,
                "relevance_score": 0.7
            }
        ]


# Singleton instance
news_service = NewsService()
