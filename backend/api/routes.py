from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, List
from datetime import datetime
import uuid
import re
import logging

from models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    ChatRequest,
    ChatResponse,
    MarketOverview
)
from agents.orchestrator import orchestrator
from services.market_data import market_data_service
from services.news_service import news_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Input validation
SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,5}$')


@router.get("/api/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": "FinMind AI API",
        "version": "1.0.0",
        "description": "Autonomous Multi-Agent Financial Analysis System",
        "status": "operational",
        "endpoints": {
            "analysis": "/api/v1/analyze",
            "market_overview": "/api/v1/market-overview",
            "stock_news": "/api/v1/stock-news",
            "chat": "/api/v1/chat",
            "chart_data": "/api/v1/chart-data/{symbol}",
            "backtest": "/api/v1/backtest/{symbol}",
            "health": "/api/v1/health"
        }
    }


@router.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_stock(request: AnalysisRequest):
    """
    Perform comprehensive analysis on a stock symbol.

    This endpoint triggers all AI agents to analyze the stock from multiple
    perspectives: news, sentiment, technical, and risk.
    """
    try:
        request_id = str(uuid.uuid4())

        # Validate symbol
        if not SYMBOL_PATTERN.match(request.symbol.upper()):
            raise HTTPException(status_code=400, detail="Invalid stock symbol. Use 1-5 uppercase letters (e.g., AAPL).")

        # Run comprehensive analysis
        result = await orchestrator.analyze_stock(
            symbol=request.symbol.upper(),
            analysis_type=request.analysis_type
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Analysis failed")
            )

        return AnalysisResponse(
            request_id=request_id,
            symbol=request.symbol.upper(),
            status="completed",
            recommendation=result.get("recommendation"),
            processing_time=result.get("processing_time", 0),
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Internal analysis error")


@router.get("/api/v1/analyze/{symbol}")
async def analyze_stock_get(symbol: str, analysis_type: str = "comprehensive"):
    """
    GET endpoint for quick stock analysis.
    Useful for quick queries and demos.
    """
    if not SYMBOL_PATTERN.match(symbol.upper()):
        raise HTTPException(status_code=400, detail="Invalid stock symbol. Use 1-5 uppercase letters (e.g., AAPL).")
    try:
        result = await orchestrator.analyze_stock(
            symbol=symbol.upper(),
            analysis_type=analysis_type
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Analysis failed")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal analysis error")


@router.get("/api/v1/market-overview")
async def get_market_overview():
    """Get market overview with major indices and sector performance."""
    try:
        # Get market indices
        market_data = await market_data_service.get_market_overview()

        # Get sector performance
        sector_data = await market_data_service.get_sector_performance()

        # Get market news
        market_news = await news_service.fetch_market_news(limit=10)

        return {
            "status": "success",
            "indices": market_data.get("indices", []),
            "sectors": sector_data.get("sectors", []),
            "market_news": market_news,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Market overview failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")


@router.get("/api/v1/stock/{symbol}")
async def get_stock_data(symbol: str):
    """Get basic stock data and information."""
    try:
        stock_data = await market_data_service.get_stock_data(symbol.upper())

        if "error" in stock_data:
            raise HTTPException(status_code=400, detail=stock_data["error"])

        return {
            "status": "success",
            "data": stock_data,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock data failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock data")


@router.get("/api/v1/stock/{symbol}/technical")
async def get_technical_analysis(symbol: str):
    """Get technical analysis for a stock."""
    try:
        indicators = await market_data_service.calculate_technical_indicators(
            symbol.upper()
        )

        if "error" in indicators:
            raise HTTPException(status_code=400, detail=indicators["error"])

        return {
            "status": "success",
            "symbol": symbol.upper(),
            "indicators": indicators,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Technical analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate technical indicators")


@router.get("/api/v1/stock/{symbol}/news")
async def get_stock_news(symbol: str, limit: int = 10):
    """Get news articles for a stock."""
    try:
        # First get stock info for company name
        stock_data = await market_data_service.get_stock_data(symbol.upper())
        company_name = stock_data.get("name", symbol) if "error" not in stock_data else symbol

        news = await news_service.fetch_stock_news(
            symbol=symbol.upper(),
            company_name=company_name,
            limit=limit
        )

        return {
            "status": "success",
            "symbol": symbol.upper(),
            "news_count": len(news),
            "articles": news,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"News fetch failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")


@router.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with the AI financial agent powered by LLM.
    Supports natural language queries about stocks and markets.
    """
    try:
        from services.llm_service import llm_service

        message = request.message.strip()
        if not message:
            return ChatResponse(
                response="Please ask a question about a stock or the market.",
                suggestions=["Analyze AAPL", "How is TSLA doing?", "Market overview"],
                related_stocks=[],
                confidence=0.5
            )

        # Extract stock symbols from message
        symbol_pattern = r'\b([A-Z]{1,5})\b'
        potential_symbols = re.findall(symbol_pattern, message.upper())
        stock_symbols = [s for s in potential_symbols if len(s) <= 5][:3]

        # Check for company names
        company_keywords = {
            "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
            "amazon": "AMZN", "tesla": "TSLA", "nvidia": "NVDA",
            "meta": "META", "netflix": "NFLX", "jpmorgan": "JPM",
            "johnson": "JNJ", "visa": "V", "walmart": "WMT"
        }
        message_lower = message.lower()
        for company, symbol in company_keywords.items():
            if company in message_lower and symbol not in stock_symbols:
                stock_symbols.append(symbol)

        # Gather context data
        context_parts = []
        analyzed_stocks = []

        for symbol in stock_symbols[:2]:  # Limit to 2 stocks for context
            try:
                stock_data = await market_data_service.get_stock_data(symbol)
                if "error" not in stock_data:
                    context_parts.append(
                        f"{symbol} ({stock_data.get('name', '')}): "
                        f"Price ${stock_data.get('current_price', 'N/A')}, "
                        f"Change {stock_data.get('change_percent', 0):+.2f}%, "
                        f"PE {stock_data.get('pe_ratio', 'N/A')}, "
                        f"Market Cap {stock_data.get('market_cap', 'N/A')}"
                    )
                    analyzed_stocks.append(symbol)
            except Exception:
                pass

        # Get market overview if no specific stock mentioned
        if not analyzed_stocks:
            try:
                market_data = await market_data_service.get_market_overview()
                for idx in market_data.get("indices", [])[:3]:
                    context_parts.append(
                        f"{idx.get('name', '')}: {idx.get('change_percent', 0):+.2f}%"
                    )
            except Exception:
                pass

        context = "\n".join(context_parts) if context_parts else "No real-time data available."

        # Use LLM for response if available
        if llm_service.is_available():
            try:
                llm_response = await llm_service.generate(
                    system_prompt=(
                        "You are FinMind AI, a professional financial analyst assistant. "
                        "Answer questions about stocks, markets, and investments based on the provided data. "
                        "Be concise, professional, and include specific numbers when available. "
                        "Always mention that this is AI analysis, not financial advice. "
                        "If asked about a stock, provide price, key metrics, and brief outlook."
                    ),
                    user_prompt=f"User question: {message}\n\nCurrent market data:\n{context}",
                    temperature=0.4,
                    max_tokens=800,
                )

                if llm_response:
                    suggestions = []
                    if analyzed_stocks:
                        suggestions = [
                            f"Detailed analysis of {analyzed_stocks[0]}",
                            f"Risk assessment for {analyzed_stocks[0]}",
                            "Compare with another stock"
                        ]
                    else:
                        suggestions = [
                            "Analyze AAPL",
                            "How is the market today?",
                            "Tell me about NVDA"
                        ]

                    return ChatResponse(
                        response=llm_response,
                        suggestions=suggestions,
                        related_stocks=analyzed_stocks,
                        confidence=0.85
                    )
            except Exception as e:
                logger.warning(f"LLM chat failed, using fallback: {e}")

        # Fallback: rule-based response
        if analyzed_stocks:
            result = await orchestrator.analyze_stock(
                symbol=analyzed_stocks[0],
                analysis_type="quick"
            )
            recommendation = result.get("recommendation", {})
            response_text = f"Based on analysis of {analyzed_stocks[0]}:\n\n"
            response_text += f"Recommendation: {recommendation.get('signal', 'hold').upper()}\n"
            response_text += f"Confidence: {recommendation.get('confidence', 0.5):.0%}\n\n"
            response_text += recommendation.get("reasoning", "Analysis completed.")
        else:
            response_text = "I can help you analyze stocks and markets. Try asking about a specific stock like 'What do you think about AAPL?' or 'Analyze TSLA'."

        return ChatResponse(
            response=response_text,
            suggestions=["Analyze AAPL", "Market overview", "Tell me about NVDA"],
            related_stocks=analyzed_stocks,
            confidence=0.6
        )

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        return ChatResponse(
            response="I encountered an error. Please try again.",
            suggestions=["Try again", "Analyze AAPL"],
            related_stocks=[],
            confidence=0.3
        )


@router.get("/api/v1/chart-data/{symbol}")
async def get_chart_data(symbol: str, period: str = "6mo"):
    """Get chart data for TradingView Lightweight Charts visualization."""
    if not SYMBOL_PATTERN.match(symbol.upper()):
        raise HTTPException(status_code=400, detail="Invalid stock symbol. Use 1-5 uppercase letters (e.g., AAPL).")
    try:
        chart_data = await market_data_service.get_chart_data(
            symbol.upper(), period=period
        )

        if chart_data.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=chart_data.get("error", "Failed to get chart data")
            )

        return chart_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chart data failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chart data")


@router.get("/api/v1/backtest/{symbol}")
async def run_backtest(symbol: str, period: str = "1y", strategy: str = "combined"):
    """Run backtesting simulation on historical data."""
    if not SYMBOL_PATTERN.match(symbol.upper()):
        raise HTTPException(status_code=400, detail="Invalid stock symbol. Use 1-5 uppercase letters (e.g., AAPL).")
    try:
        from services.backtest_service import backtest_service

        result = await backtest_service.run_backtest(
            symbol=symbol.upper(),
            period=period,
            strategy=strategy
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Backtest failed")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to run backtest")


@router.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    agent_status = orchestrator.get_agent_status()

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": agent_status,
        "version": "1.0.0"
    }


@router.get("/api/v1/agents/status")
async def get_agents_status():
    """Get status of all AI agents."""
    return {
        "status": "success",
        "agents": orchestrator.get_agent_status(),
        "timestamp": datetime.now().isoformat()
    }


@router.websocket("/ws/analysis/{symbol}")
async def websocket_analysis(websocket: WebSocket, symbol: str):
    """WebSocket endpoint for real-time analysis progress."""
    from services.ws_manager import ws_manager

    channel = f"analysis:{symbol.upper()}"
    await ws_manager.connect(websocket, channel)
    try:
        while True:
            # Keep connection alive, client can send ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel)
    except Exception:
        ws_manager.disconnect(websocket, channel)


@router.get("/api/v1/history")
async def get_analysis_history(symbol: Optional[str] = None, limit: int = 50):
    """Get analysis history."""
    try:
        from services.database_service import db_service
        history = db_service.get_analysis_history(symbol=symbol, limit=limit)
        return {"status": "success", "history": history}
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis history")


@router.get("/api/v1/compare")
async def compare_stocks(symbols: str = "AAPL,MSFT,GOOGL"):
    """Compare multiple stocks side by side."""
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if len(symbol_list) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 comma-separated symbols")
    if len(symbol_list) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 symbols for comparison")

    try:
        results = []
        for sym in symbol_list:
            if not SYMBOL_PATTERN.match(sym):
                continue
            stock_data = await market_data_service.get_stock_data(sym)
            if "error" not in stock_data:
                indicators = await market_data_service.calculate_technical_indicators(sym)
                results.append({
                    "symbol": sym,
                    "name": stock_data.get("name", sym),
                    "price": stock_data.get("current_price"),
                    "change_pct": stock_data.get("change_percent"),
                    "market_cap": stock_data.get("market_cap"),
                    "pe_ratio": stock_data.get("pe_ratio"),
                    "dividend_yield": stock_data.get("dividend_yield"),
                    "beta": stock_data.get("beta"),
                    "rsi": indicators.get("rsi_14"),
                    "signal": indicators.get("price_position", "unknown"),
                })

        # Rank by different metrics
        rankings = {}
        if results:
            by_return = sorted(results, key=lambda x: x.get("change_pct", 0) or 0, reverse=True)
            rankings["best_performer"] = by_return[0]["symbol"] if by_return else None
            by_pe = sorted([r for r in results if r.get("pe_ratio") and r["pe_ratio"] > 0], key=lambda x: x["pe_ratio"])
            rankings["best_value"] = by_pe[0]["symbol"] if by_pe else None

        return {
            "status": "success",
            "comparison": results,
            "rankings": rankings,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare stocks")


@router.get("/api/v1/stats")
async def get_analysis_stats():
    """Get analysis statistics."""
    try:
        from services.database_service import db_service
        stats = db_service.get_analysis_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.get("/api/v1/export/{symbol}")
async def export_analysis_pdf(symbol: str):
    """Export analysis results as a formatted HTML report (printable to PDF)."""
    if not SYMBOL_PATTERN.match(symbol.upper()):
        raise HTTPException(status_code=400, detail="Invalid stock symbol")

    try:
        result = await orchestrator.analyze_stock(
            symbol=symbol.upper(),
            analysis_type="comprehensive"
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))

        recommendation = result.get("recommendation", {})
        agent_results = result.get("agent_results", {})

        # Build HTML report
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>FinMind AI - {symbol.upper()} Analysis Report</title>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; color: #1a1a2e; }}
    h1 {{ color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
    h2 {{ color: #333; margin-top: 30px; }}
    .header {{ text-align: center; margin-bottom: 30px; }}
    .header p {{ color: #666; }}
    .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
    .metric {{ background: #f5f7fa; padding: 15px; border-radius: 8px; text-align: center; }}
    .metric-value {{ font-size: 24px; font-weight: bold; color: #0066cc; }}
    .metric-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
    .signal {{ display: inline-block; padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 18px; }}
    .signal-buy {{ background: #d1fae5; color: #059669; }}
    .signal-sell {{ background: #fee2e2; color: #dc2626; }}
    .signal-hold {{ background: #fef3c7; color: #d97706; }}
    .signal-strong_buy {{ background: #a7f3d0; color: #047857; }}
    .signal-strong_sell {{ background: #fecaca; color: #b91c1c; }}
    .section {{ margin: 20px 0; padding: 15px; background: #f9fafb; border-radius: 8px; border-left: 4px solid #0066cc; }}
    .section h3 {{ margin: 0 0 10px; color: #0066cc; }}
    .findings li {{ margin: 5px 0; color: #374151; }}
    .footer {{ text-align: center; margin-top: 40px; color: #9ca3af; font-size: 12px; border-top: 1px solid #e5e7eb; padding-top: 20px; }}
    @media print {{ body {{ padding: 20px; }} }}
</style>
</head>
<body>
<div class="header">
    <h1>FinMind AI Analysis Report</h1>
    <p>{result.get('company_name', symbol.upper())} ({symbol.upper()})</p>
    <p>Generated: {result.get('timestamp', '')}</p>
</div>

<div style="text-align: center; margin: 20px 0;">
    <span class="signal signal-{recommendation.get('signal', 'hold')}">
        {recommendation.get('signal', 'hold').replace('_', ' ').upper()}
    </span>
    <p style="margin-top:10px; color:#666;">Confidence: {recommendation.get('confidence', 0.5):.0%}</p>
</div>

<div class="metrics">
    <div class="metric">
        <div class="metric-value">${result.get('current_price', 'N/A')}</div>
        <div class="metric-label">Current Price</div>
    </div>
    <div class="metric">
        <div class="metric-value">${recommendation.get('target_price', 'N/A')}</div>
        <div class="metric-label">Target Price</div>
    </div>
    <div class="metric">
        <div class="metric-value">${recommendation.get('stop_loss', 'N/A')}</div>
        <div class="metric-label">Stop Loss</div>
    </div>
</div>

<div class="section">
    <h3>Analysis Summary</h3>
    <p>{recommendation.get('reasoning', 'No reasoning available.').replace(chr(10), '<br>')}</p>
</div>
"""

        # Add agent sections
        agent_sections = {
            "news": ("News Monitor", agent_results.get("news", {})),
            "sentiment": ("Sentiment Analysis", agent_results.get("sentiment", {})),
            "technical": ("Technical Analysis", agent_results.get("technical", {})),
            "fundamental": ("Fundamental Analysis", agent_results.get("fundamental", {})),
            "risk": ("Risk Assessment", agent_results.get("risk", {})),
        }

        for key, (name, data) in agent_sections.items():
            if data and isinstance(data, dict):
                findings = data.get("key_findings", [])
                findings_html = "".join(f"<li>{f}</li>" for f in findings[:3]) if findings else "<li>No specific findings</li>"
                
                html += f"""
<div class="section">
    <h3>{name} — {data.get('signal', 'hold').replace('_', ' ').upper()}</h3>
    <p>{data.get('summary', data.get('analysis', 'Analysis completed.'))}</p>
    <ul class="findings">{findings_html}</ul>
</div>
"""

        html += f"""
<div class="footer">
    <p>FinMind AI - Autonomous Multi-Agent Financial Analysis System</p>
    <p>This report is generated by AI and should not be considered financial advice.</p>
    <p>Processing time: {result.get('processing_time', 0)}s</p>
</div>
</body>
</html>"""

        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export report")


@router.get("/api/v1/analyze-stream/{symbol}")
async def analyze_stock_stream(symbol: str, analysis_type: str = "comprehensive"):
    """Stream analysis results via Server-Sent Events (SSE)."""
    if not SYMBOL_PATTERN.match(symbol.upper()):
        raise HTTPException(status_code=400, detail="Invalid stock symbol. Use 1-5 uppercase letters (e.g., AAPL).")

    async def event_generator():
        import json
        from datetime import datetime

        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': f'Starting analysis for {symbol.upper()}...'})}\n\n"

            # Fetch stock data
            stock_data = await market_data_service.get_stock_data(symbol.upper())
            if "error" in stock_data:
                yield f"data: {json.dumps({'type': 'error', 'message': stock_data['error']})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'stock_data', 'data': {'symbol': symbol.upper(), 'name': stock_data.get('name', ''), 'price': stock_data.get('current_price'), 'change_pct': stock_data.get('change_percent')}})}\n\n"

            # Run analysis with progress
            result = await orchestrator.analyze_stock(
                symbol=symbol.upper(),
                analysis_type=analysis_type
            )

            # Send agent results one by one
            agent_results = result.get("agent_results", {})
            agent_names = {
                "news": "News Monitor",
                "sentiment": "Sentiment Analysis",
                "technical": "Technical Analysis",
                "fundamental": "Fundamental Analysis",
                "risk": "Risk Assessment"
            }

            for key, agent_data in agent_results.items():
                if agent_data and isinstance(agent_data, dict):
                    yield f"data: {json.dumps({'type': 'agent_result', 'agent': key, 'name': agent_names.get(key, key), 'signal': agent_data.get('signal', 'hold'), 'confidence': agent_data.get('confidence', 0.5), 'llm_enhanced': agent_data.get('llm_enhanced', False)})}\n\n"

            # Send final recommendation
            recommendation = result.get("recommendation", {})
            yield f"data: {json.dumps({'type': 'recommendation', 'signal': recommendation.get('signal', 'hold'), 'confidence': recommendation.get('confidence', 0.5), 'target_price': recommendation.get('target_price'), 'stop_loss': recommendation.get('stop_loss'), 'reasoning': recommendation.get('reasoning', ''), 'llm_enhanced': recommendation.get('llm_enhanced', False)})}\n\n"

            # Send completion
            yield f"data: {json.dumps({'type': 'complete', 'processing_time': result.get('processing_time', 0)})}\n\n"

        except Exception as e:
            logger.error(f"Stream analysis failed for {symbol}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
