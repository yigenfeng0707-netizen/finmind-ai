"""
FinMind AI - Vercel Deployment Entry Point
All routes defined inline with lazy imports to avoid module-level crashes.
"""
import sys
import os
import logging
from pathlib import Path

# Setup paths BEFORE any backend imports
backend_dir = str(Path(__file__).parent.parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("finmind")

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

app = FastAPI(title="FinMind AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lazy import cache ──────────────────────────────────────────────
_cache = {}

def _get(name: str):
    """Lazy-load and cache backend modules."""
    if name in _cache:
        return _cache[name]
    try:
        if name == "orchestrator":
            from agents.orchestrator import orchestrator
            _cache[name] = orchestrator
        elif name == "market_data":
            from services.market_data import market_data_service
            _cache[name] = market_data_service
        elif name == "news_service":
            from services.news_service import news_service
            _cache[name] = news_service
        elif name == "llm_service":
            from services.llm_service import llm_service
            _cache[name] = llm_service
        elif name == "backtest_service":
            from services.backtest_service import backtest_service
            _cache[name] = backtest_service
        elif name == "db_service":
            from services.database_service import db_service
            _cache[name] = db_service
        elif name == "ws_manager":
            from services.ws_manager import ws_manager
            _cache[name] = ws_manager
        elif name == "schemas":
            from models.schemas import AnalysisRequest, AnalysisResponse, ChatRequest, ChatResponse, MarketOverview
            _cache[name] = {
                "AnalysisRequest": AnalysisRequest,
                "AnalysisResponse": AnalysisResponse,
                "ChatRequest": ChatRequest,
                "ChatResponse": ChatResponse,
                "MarketOverview": MarketOverview,
            }
        return _cache.get(name)
    except Exception as e:
        logger.error(f"Failed to lazy-load module '{name}': {e}")
        _cache[name] = None
        return None


# ── Input validation ───────────────────────────────────────────────
import re
SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,5}$')


# ════════════════════════════════════════════════════════════════════
# ALWAYS-AVAILABLE ENDPOINTS (no backend dependency)
# ════════════════════════════════════════════════════════════════════

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "agents": 5, "version": "1.0.0"}

@app.get("/api/info")
async def api_info():
    return {
        "name": "FinMind AI API",
        "version": "1.0.0",
        "description": "Autonomous Multi-Agent Financial Analysis System",
        "status": "operational",
        "endpoints": {
            "analysis": "/api/v1/analyze",
            "market_overview": "/api/v1/market-overview",
            "stock_news": "/api/v1/stock-news",
            "chart_data": "/api/v1/chart-data/{symbol}",
            "backtest": "/api/v1/backtest/{symbol}",
            "health": "/api/v1/health"
        }
    }

@app.get("/api/v1/diag")
async def diagnostics():
    """Diagnostic endpoint to check which backend modules loaded successfully."""
    results = {}
    for name in ["orchestrator", "market_data", "news_service", "llm_service", "backtest_service", "db_service", "ws_manager"]:
        mod = _get(name)
        results[name] = "ok" if mod is not None else "FAILED"
    results["sys_path"] = sys.path[:5]
    results["backend_dir"] = backend_dir
    results["backend_exists"] = Path(backend_dir).exists()
    return results


# ════════════════════════════════════════════════════════════════════
# ANALYSIS ENDPOINTS
# ════════════════════════════════════════════════════════════════════

@app.get("/api/v1/analyze/{symbol}")
async def analyze_stock_get(symbol: str, analysis_type: str = "comprehensive"):
    """GET endpoint for quick stock analysis."""
    if not SYMBOL_PATTERN.match(symbol.upper()):
        raise HTTPException(status_code=400, detail="Invalid stock symbol. Use 1-5 uppercase letters.")
    orchestrator = _get("orchestrator")
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Analysis engine unavailable. Backend modules failed to load.")
    try:
        result = await orchestrator.analyze_stock(symbol=symbol.upper(), analysis_type=analysis_type)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal analysis error")


@app.post("/api/v1/analyze")
async def analyze_stock_post(request: dict):
    """POST endpoint for stock analysis."""
    symbol = request.get("symbol", "").upper()
    analysis_type = request.get("analysis_type", "comprehensive")
    if not SYMBOL_PATTERN.match(symbol):
        raise HTTPException(status_code=400, detail="Invalid stock symbol. Use 1-5 uppercase letters.")
    orchestrator = _get("orchestrator")
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Analysis engine unavailable.")
    try:
        import uuid
        from datetime import datetime
        result = await orchestrator.analyze_stock(symbol=symbol, analysis_type=analysis_type)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))
        return {
            "request_id": str(uuid.uuid4()),
            "symbol": symbol,
            "status": "completed",
            "recommendation": result.get("recommendation"),
            "processing_time": result.get("processing_time", 0),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Internal analysis error")


# ════════════════════════════════════════════════════════════════════
# MARKET DATA ENDPOINTS
# ════════════════════════════════════════════════════════════════════

@app.get("/api/v1/market-overview")
async def get_market_overview():
    """Get market overview with major indices and sector performance."""
    mds = _get("market_data")
    ns = _get("news_service")
    if mds is None:
        raise HTTPException(status_code=503, detail="Market data service unavailable.")
    try:
        from datetime import datetime
        market_data = await mds.get_market_overview()
        sector_data = await mds.get_sector_performance() if mds else {"sectors": []}
        market_news = await ns.fetch_market_news(limit=10) if ns else []
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


@app.get("/api/v1/stock/{symbol}")
async def get_stock_data(symbol: str):
    """Get basic stock data and information."""
    mds = _get("market_data")
    if mds is None:
        raise HTTPException(status_code=503, detail="Market data service unavailable.")
    try:
        from datetime import datetime
        stock_data = await mds.get_stock_data(symbol.upper())
        if "error" in stock_data:
            raise HTTPException(status_code=400, detail=stock_data["error"])
        return {"status": "success", "data": stock_data, "timestamp": datetime.now().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock data failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock data")


@app.get("/api/v1/stock/{symbol}/technical")
async def get_technical_analysis(symbol: str):
    """Get technical analysis for a stock."""
    mds = _get("market_data")
    if mds is None:
        raise HTTPException(status_code=503, detail="Market data service unavailable.")
    try:
        from datetime import datetime
        indicators = await mds.calculate_technical_indicators(symbol.upper())
        if "error" in indicators:
            raise HTTPException(status_code=400, detail=indicators["error"])
        return {"status": "success", "symbol": symbol.upper(), "indicators": indicators, "timestamp": datetime.now().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Technical analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate technical indicators")


@app.get("/api/v1/stock/{symbol}/news")
async def get_stock_news(symbol: str, limit: int = 10):
    """Get news articles for a stock."""
    mds = _get("market_data")
    ns = _get("news_service")
    if mds is None or ns is None:
        raise HTTPException(status_code=503, detail="Service unavailable.")
    try:
        from datetime import datetime
        stock_data = await mds.get_stock_data(symbol.upper())
        company_name = stock_data.get("name", symbol) if "error" not in stock_data else symbol
        news = await ns.fetch_stock_news(symbol=symbol.upper(), company_name=company_name, limit=limit)
        return {"status": "success", "symbol": symbol.upper(), "news_count": len(news), "articles": news, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"News fetch failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")


# ════════════════════════════════════════════════════════════════════
# CHART & BACKTEST ENDPOINTS
# ════════════════════════════════════════════════════════════════════

@app.get("/api/v1/chart-data/{symbol}")
async def get_chart_data(symbol: str, period: str = "6mo"):
    """Get chart data for TradingView Lightweight Charts visualization."""
    if not SYMBOL_PATTERN.match(symbol.upper()):
        raise HTTPException(status_code=400, detail="Invalid stock symbol.")
    mds = _get("market_data")
    if mds is None:
        raise HTTPException(status_code=503, detail="Market data service unavailable.")
    try:
        chart_data = await mds.get_chart_data(symbol.upper(), period=period)
        if chart_data.get("status") == "error":
            raise HTTPException(status_code=400, detail=chart_data.get("error", "Failed to get chart data"))
        return chart_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chart data failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chart data")


@app.get("/api/v1/backtest/{symbol}")
async def run_backtest(symbol: str, period: str = "1y", strategy: str = "combined"):
    """Run backtesting simulation on historical data."""
    if not SYMBOL_PATTERN.match(symbol.upper()):
        raise HTTPException(status_code=400, detail="Invalid stock symbol.")
    bts = _get("backtest_service")
    if bts is None:
        raise HTTPException(status_code=503, detail="Backtest service unavailable.")
    try:
        result = await bts.run_backtest(symbol=symbol.upper(), period=period, strategy=strategy)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error", "Backtest failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to run backtest")


# ════════════════════════════════════════════════════════════════════
# CHAT ENDPOINT (LLM-powered)
# ════════════════════════════════════════════════════════════════════

@app.post("/api/v1/chat")
async def chat_with_agent(request: dict):
    """Chat with the AI financial agent powered by LLM."""
    message = request.get("message", "").strip()
    if not message:
        return {
            "response": "Please ask a question about a stock or the market.",
            "suggestions": ["Analyze AAPL", "How is TSLA doing?", "Market overview"],
            "related_stocks": [],
            "confidence": 0.5
        }

    llm = _get("llm_service")
    mds = _get("market_data")
    orch = _get("orchestrator")

    try:
        # Extract stock symbols from message
        symbol_pattern = r'\b([A-Z]{1,5})\b'
        potential_symbols = re.findall(symbol_pattern, message.upper())
        stock_symbols = [s for s in potential_symbols if len(s) <= 5][:3]

        # Check for company names
        company_keywords = {
            "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
            "amazon": "AMZN", "tesla": "TSLA", "nvidia": "NVDA",
            "meta": "META", "netflix": "NFLX", "jpmorgan": "JPM",
        }
        message_lower = message.lower()
        for company, sym in company_keywords.items():
            if company in message_lower and sym not in stock_symbols:
                stock_symbols.append(sym)

        # Gather context data
        context_parts = []
        analyzed_stocks = []

        if mds:
            for sym in stock_symbols[:2]:
                try:
                    stock_data = await mds.get_stock_data(sym)
                    if "error" not in stock_data:
                        context_parts.append(
                            f"{sym} ({stock_data.get('name', '')}): "
                            f"Price ${stock_data.get('current_price', 'N/A')}, "
                            f"Change {stock_data.get('change_percent', 0):+.2f}%, "
                            f"PE {stock_data.get('pe_ratio', 'N/A')}"
                        )
                        analyzed_stocks.append(sym)
                except Exception:
                    pass

            if not analyzed_stocks:
                try:
                    market_data = await mds.get_market_overview()
                    for idx in market_data.get("indices", [])[:3]:
                        context_parts.append(f"{idx.get('name', '')}: {idx.get('change_percent', 0):+.2f}%")
                except Exception:
                    pass

        context = "\n".join(context_parts) if context_parts else "No real-time data available."

        # Use LLM for response if available
        if llm and llm.is_available():
            try:
                llm_response = await llm.generate(
                    system_prompt=(
                        "You are FinMind AI, a professional financial analyst assistant. "
                        "Answer questions about stocks, markets, and investments based on the provided data. "
                        "Be concise, professional, and include specific numbers when available. "
                        "Always mention that this is AI analysis, not financial advice."
                    ),
                    user_prompt=f"User question: {message}\n\nCurrent market data:\n{context}",
                    temperature=0.4,
                    max_tokens=800,
                )
                if llm_response:
                    suggestions = (
                        [f"Detailed analysis of {analyzed_stocks[0]}", f"Risk assessment for {analyzed_stocks[0]}", "Compare with another stock"]
                        if analyzed_stocks else ["Analyze AAPL", "How is the market today?", "Tell me about NVDA"]
                    )
                    return {"response": llm_response, "suggestions": suggestions, "related_stocks": analyzed_stocks, "confidence": 0.85}
            except Exception as e:
                logger.warning(f"LLM chat failed, using fallback: {e}")

        # Fallback: rule-based response
        if analyzed_stocks and orch:
            result = await orch.analyze_stock(symbol=analyzed_stocks[0], analysis_type="quick")
            recommendation = result.get("recommendation", {})
            response_text = f"Based on analysis of {analyzed_stocks[0]}:\n\n"
            response_text += f"Recommendation: {recommendation.get('signal', 'hold').upper()}\n"
            response_text += f"Confidence: {recommendation.get('confidence', 0.5):.0%}\n\n"
            response_text += recommendation.get("reasoning", "Analysis completed.")
        else:
            response_text = "I can help you analyze stocks and markets. Try asking about a specific stock like 'What do you think about AAPL?' or 'Analyze TSLA'."

        return {"response": response_text, "suggestions": ["Analyze AAPL", "Market overview", "Tell me about NVDA"], "related_stocks": analyzed_stocks, "confidence": 0.6}

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        return {"response": "I encountered an error. Please try again.", "suggestions": ["Try again", "Analyze AAPL"], "related_stocks": [], "confidence": 0.3}


# ════════════════════════════════════════════════════════════════════
# SSE STREAM ENDPOINT
# ════════════════════════════════════════════════════════════════════

@app.get("/api/v1/analyze-stream/{symbol}")
async def analyze_stock_stream(symbol: str, analysis_type: str = "comprehensive"):
    """Stream analysis results via Server-Sent Events (SSE)."""
    if not SYMBOL_PATTERN.match(symbol.upper()):
        raise HTTPException(status_code=400, detail="Invalid stock symbol.")
    orch = _get("orchestrator")
    mds = _get("market_data")
    if orch is None:
        raise HTTPException(status_code=503, detail="Analysis engine unavailable.")

    async def event_generator():
        import json
        from datetime import datetime
        try:
            yield f"data: {json.dumps({'type': 'status', 'message': f'Starting analysis for {symbol.upper()}...'})}\n\n"

            if mds:
                stock_data = await mds.get_stock_data(symbol.upper())
                if "error" in stock_data:
                    yield f"data: {json.dumps({'type': 'error', 'message': stock_data['error']})}\n\n"
                    return
                yield f"data: {json.dumps({'type': 'stock_data', 'data': {'symbol': symbol.upper(), 'name': stock_data.get('name', ''), 'price': stock_data.get('current_price'), 'change_pct': stock_data.get('change_percent')}})}\n\n"

            result = await orch.analyze_stock(symbol=symbol.upper(), analysis_type=analysis_type)

            agent_results = result.get("agent_results", {})
            agent_names = {"news": "News Monitor", "sentiment": "Sentiment Analysis", "technical": "Technical Analysis", "fundamental": "Fundamental Analysis", "risk": "Risk Assessment"}

            for key, agent_data in agent_results.items():
                if agent_data and isinstance(agent_data, dict):
                    yield f"data: {json.dumps({'type': 'agent_result', 'agent': key, 'name': agent_names.get(key, key), 'signal': agent_data.get('signal', 'hold'), 'confidence': agent_data.get('confidence', 0.5), 'llm_enhanced': agent_data.get('llm_enhanced', False)})}\n\n"

            recommendation = result.get("recommendation", {})
            yield f"data: {json.dumps({'type': 'recommendation', 'signal': recommendation.get('signal', 'hold'), 'confidence': recommendation.get('confidence', 0.5), 'target_price': recommendation.get('target_price'), 'stop_loss': recommendation.get('stop_loss'), 'reasoning': recommendation.get('reasoning', ''), 'llm_enhanced': recommendation.get('llm_enhanced', False)})}\n\n"

            yield f"data: {json.dumps({'type': 'complete', 'processing_time': result.get('processing_time', 0)})}\n\n"

        except Exception as e:
            logger.error(f"Stream analysis failed for {symbol}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


# ════════════════════════════════════════════════════════════════════
# COMPARISON, HISTORY, STATS, EXPORT
# ════════════════════════════════════════════════════════════════════

@app.get("/api/v1/compare")
async def compare_stocks(symbols: str = "AAPL,MSFT,GOOGL"):
    """Compare multiple stocks side by side."""
    mds = _get("market_data")
    if mds is None:
        raise HTTPException(status_code=503, detail="Market data service unavailable.")
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if len(symbol_list) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 comma-separated symbols")
    if len(symbol_list) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 symbols for comparison")
    try:
        from datetime import datetime
        results = []
        for sym in symbol_list:
            if not SYMBOL_PATTERN.match(sym):
                continue
            stock_data = await mds.get_stock_data(sym)
            if "error" not in stock_data:
                indicators = await mds.calculate_technical_indicators(sym)
                results.append({
                    "symbol": sym, "name": stock_data.get("name", sym),
                    "price": stock_data.get("current_price"), "change_pct": stock_data.get("change_percent"),
                    "market_cap": stock_data.get("market_cap"), "pe_ratio": stock_data.get("pe_ratio"),
                    "rsi": indicators.get("rsi_14"), "signal": indicators.get("price_position", "unknown"),
                })
        rankings = {}
        if results:
            by_return = sorted(results, key=lambda x: x.get("change_pct", 0) or 0, reverse=True)
            rankings["best_performer"] = by_return[0]["symbol"] if by_return else None
            by_pe = sorted([r for r in results if r.get("pe_ratio") and r["pe_ratio"] > 0], key=lambda x: x["pe_ratio"])
            rankings["best_value"] = by_pe[0]["symbol"] if by_pe else None
        return {"status": "success", "comparison": results, "rankings": rankings, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare stocks")


@app.get("/api/v1/history")
async def get_analysis_history(symbol: str = None, limit: int = 50):
    """Get analysis history."""
    dbs = _get("db_service")
    if dbs is None:
        return {"status": "success", "history": [], "note": "Database service unavailable in serverless mode"}
    try:
        history = dbs.get_analysis_history(symbol=symbol, limit=limit)
        return {"status": "success", "history": history}
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        return {"status": "success", "history": []}


@app.get("/api/v1/stats")
async def get_analysis_stats():
    """Get analysis statistics."""
    dbs = _get("db_service")
    if dbs is None:
        return {"status": "success", "stats": {"total_analyses": 0, "note": "Database service unavailable in serverless mode"}}
    try:
        stats = dbs.get_analysis_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"status": "success", "stats": {"total_analyses": 0}}


@app.get("/api/v1/export/{symbol}")
async def export_analysis(symbol: str):
    """Export analysis results as a formatted HTML report."""
    if not SYMBOL_PATTERN.match(symbol.upper()):
        raise HTTPException(status_code=400, detail="Invalid stock symbol")
    orch = _get("orchestrator")
    if orch is None:
        raise HTTPException(status_code=503, detail="Analysis engine unavailable.")
    try:
        result = await orch.analyze_stock(symbol=symbol.upper(), analysis_type="comprehensive")
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))

        recommendation = result.get("recommendation", {})
        agent_results = result.get("agent_results", {})

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>FinMind AI - {symbol.upper()} Analysis Report</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; color: #1a1a2e; }}
h1 {{ color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
h2 {{ color: #333; margin-top: 30px; }}
.header {{ text-align: center; margin-bottom: 30px; }}
.metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
.metric {{ background: #f5f7fa; padding: 15px; border-radius: 8px; text-align: center; }}
.metric-value {{ font-size: 24px; font-weight: bold; color: #0066cc; }}
.metric-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
.signal {{ display: inline-block; padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 18px; }}
.signal-buy {{ background: #d1fae5; color: #059669; }}
.signal-sell {{ background: #fee2e2; color: #dc2626; }}
.signal-hold {{ background: #fef3c7; color: #d97706; }}
.section {{ margin: 20px 0; padding: 15px; background: #f9fafb; border-radius: 8px; border-left: 4px solid #0066cc; }}
.footer {{ text-align: center; margin-top: 40px; color: #9ca3af; font-size: 12px; border-top: 1px solid #e5e7eb; padding-top: 20px; }}
</style></head><body>
<div class="header"><h1>FinMind AI Analysis Report</h1>
<p>{result.get('company_name', symbol.upper())} ({symbol.upper()})</p>
<p>Generated: {result.get('timestamp', '')}</p></div>
<div style="text-align: center; margin: 20px 0;">
<span class="signal signal-{recommendation.get('signal', 'hold')}">{recommendation.get('signal', 'hold').replace('_', ' ').upper()}</span>
<p style="margin-top:10px; color:#666;">Confidence: {recommendation.get('confidence', 0.5):.0%}</p></div>
<div class="metrics">
<div class="metric"><div class="metric-value">${result.get('current_price', 'N/A')}</div><div class="metric-label">Current Price</div></div>
<div class="metric"><div class="metric-value">${recommendation.get('target_price', 'N/A')}</div><div class="metric-label">Target Price</div></div>
<div class="metric"><div class="metric-value">${recommendation.get('stop_loss', 'N/A')}</div><div class="metric-label">Stop Loss</div></div></div>
<div class="section"><h3>Analysis Summary</h3><p>{recommendation.get('reasoning', 'No reasoning available.').replace(chr(10), '<br>')}</p></div>"""

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
                html += f"""<div class="section"><h3>{name} — {data.get('signal', 'hold').replace('_', ' ').upper()}</h3>
<p>{data.get('summary', data.get('analysis', 'Analysis completed.'))}</p><ul>{findings_html}</ul></div>"""

        html += f"""<div class="footer"><p>FinMind AI - Autonomous Multi-Agent Financial Analysis System</p>
<p>This report is generated by AI and should not be considered financial advice.</p>
<p>Processing time: {result.get('processing_time', 0)}s</p></div></body></html>"""

        return HTMLResponse(content=html)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export report")


# ════════════════════════════════════════════════════════════════════
# AGENTS STATUS
# ════════════════════════════════════════════════════════════════════

@app.get("/api/v1/agents/status")
async def get_agents_status():
    """Get status of all AI agents."""
    orch = _get("orchestrator")
    if orch is None:
        return {"status": "degraded", "agents": {}, "note": "Orchestrator unavailable"}
    from datetime import datetime
    return {"status": "success", "agents": orch.get_agent_status(), "timestamp": datetime.now().isoformat()}


# ════════════════════════════════════════════════════════════════════
# WEBSOCKET (best-effort in serverless)
# ════════════════════════════════════════════════════════════════════

@app.websocket("/ws/analysis/{symbol}")
async def websocket_analysis(websocket: WebSocket, symbol: str):
    """WebSocket endpoint for real-time analysis progress."""
    wsm = _get("ws_manager")
    if wsm is None:
        await websocket.close(code=1013, reason="WebSocket not available in serverless")
        return
    channel = f"analysis:{symbol.upper()}"
    await wsm.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        wsm.disconnect(websocket, channel)
    except Exception:
        wsm.disconnect(websocket, channel)


# ════════════════════════════════════════════════════════════════════
# LANDING PAGE
# ════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def landing():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinMind AI - Autonomous Financial Analysis</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%); color: #fff; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        .header { text-align: center; margin-bottom: 60px; }
        .logo { font-size: 48px; font-weight: bold; background: linear-gradient(90deg, #00d4ff, #7b2cbf); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .tagline { font-size: 24px; color: #aaa; margin: 20px 0; }
        .badge { display: inline-block; background: rgba(0, 212, 255, 0.2); border: 1px solid #00d4ff; padding: 8px 16px; border-radius: 20px; font-size: 14px; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; margin-bottom: 60px; }
        .feature-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 30px; }
        .feature-title { font-size: 20px; margin-bottom: 15px; color: #00d4ff; }
        .feature-desc { color: #aaa; line-height: 1.6; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 30px; margin-bottom: 60px; }
        .stat-card { text-align: center; padding: 30px; background: rgba(255,255,255,0.05); border-radius: 16px; }
        .stat-number { font-size: 48px; font-weight: bold; color: #00d4ff; }
        .stat-label { color: #aaa; font-size: 14px; margin-top: 10px; }
        .footer { text-align: center; padding: 40px; color: #666; font-size: 14px; }
        @media (max-width: 768px) { .stats { grid-template-columns: repeat(2, 1fr); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">FinMind AI</div>
            <div class="tagline">Autonomous Multi-Agent Financial Analysis</div>
            <div class="badge">UCWS Singapore Hackathon 2026</div>
        </div>
        <div class="features">
            <div class="feature-card"><div class="feature-title">News Intelligence</div><div class="feature-desc">Real-time monitoring of financial news with AI-powered sentiment analysis.</div></div>
            <div class="feature-card"><div class="feature-title">Sentiment Analysis</div><div class="feature-desc">Deep analysis of market sentiment combining news and social signals.</div></div>
            <div class="feature-card"><div class="feature-title">Technical Analysis</div><div class="feature-desc">RSI, MACD, Bollinger Bands, and pattern recognition.</div></div>
            <div class="feature-card"><div class="feature-title">Risk Assessment</div><div class="feature-desc">Comprehensive risk quantification with volatility metrics.</div></div>
            <div class="feature-card"><div class="feature-title">Fundamental Analysis</div><div class="feature-desc">PE/PB ratios, earnings growth, and valuation metrics.</div></div>
        </div>
        <div class="stats">
            <div class="stat-card"><div class="stat-number">5</div><div class="stat-label">AI Agents</div></div>
            <div class="stat-card"><div class="stat-number">15+</div><div class="stat-label">Indicators</div></div>
            <div class="stat-card"><div class="stat-number">3s</div><div class="stat-label">Analysis Time</div></div>
            <div class="stat-card"><div class="stat-number">100%</div><div class="stat-label">Transparent</div></div>
        </div>
        <div class="footer"><p>FinMind AI - UCWS Singapore Hackathon 2026</p></div>
    </div>
</body>
</html>"""
