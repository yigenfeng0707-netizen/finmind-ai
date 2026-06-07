"""
FinMind AI - Vercel Deployment Entry Point
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Import the app from backend
from main import app as backend_app

# Create Vercel-compatible app
app = FastAPI(
    title="FinMind AI",
    description="Autonomous Multi-Agent Financial Analysis System",
    version="1.0.0",
)

# Copy middleware from backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include backend routes
app.include_router(backend_app.router)

# Landing page
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
        .feature-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 30px; transition: transform 0.3s; }
        .feature-card:hover { transform: translateY(-5px); border-color: #00d4ff; }
        .feature-title { font-size: 20px; margin-bottom: 15px; color: #00d4ff; }
        .feature-desc { color: #aaa; line-height: 1.6; }
        .demo-section { background: rgba(255,255,255,0.05); border-radius: 20px; padding: 40px; margin-bottom: 60px; }
        .demo-title { font-size: 28px; margin-bottom: 30px; text-align: center; }
        .demo-input { display: flex; gap: 15px; margin-bottom: 30px; }
        .demo-input input { flex: 1; padding: 15px 20px; border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; background: rgba(255,255,255,0.1); color: #fff; font-size: 16px; }
        .demo-input button { padding: 15px 30px; background: linear-gradient(90deg, #00d4ff, #7b2cbf); border: none; border-radius: 10px; color: #fff; font-size: 16px; font-weight: bold; cursor: pointer; }
        .demo-input button:hover { transform: scale(1.05); }
        .demo-result { background: rgba(0,0,0,0.3); border-radius: 10px; padding: 20px; min-height: 200px; font-family: monospace; white-space: pre-wrap; color: #00ff88; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 30px; margin-bottom: 60px; }
        .stat-card { text-align: center; padding: 30px; background: rgba(255,255,255,0.05); border-radius: 16px; }
        .stat-number { font-size: 48px; font-weight: bold; color: #00d4ff; }
        .stat-label { color: #aaa; font-size: 14px; margin-top: 10px; }
        .cta { text-align: center; padding: 40px; }
        .cta-button { display: inline-block; padding: 15px 40px; background: linear-gradient(90deg, #00d4ff, #7b2cbf); border-radius: 30px; color: #fff; text-decoration: none; font-size: 18px; font-weight: bold; }
        .cta-button:hover { transform: scale(1.05); }
        .footer { text-align: center; padding: 40px; color: #666; font-size: 14px; }
        @media (max-width: 768px) { .stats { grid-template-columns: repeat(2, 1fr); } .demo-input { flex-direction: column; } }
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
            <div class="feature-card">
                <div class="feature-title">News Intelligence</div>
                <div class="feature-desc">Real-time monitoring of financial news with AI-powered sentiment analysis.</div>
            </div>
            <div class="feature-card">
                <div class="feature-title">Sentiment Analysis</div>
                <div class="feature-desc">Deep analysis of market sentiment combining news and social signals.</div>
            </div>
            <div class="feature-card">
                <div class="feature-title">Technical Analysis</div>
                <div class="feature-desc">RSI, MACD, Bollinger Bands, and pattern recognition.</div>
            </div>
            <div class="feature-card">
                <div class="feature-title">Risk Assessment</div>
                <div class="feature-desc">Comprehensive risk quantification with volatility metrics.</div>
            </div>
        </div>

        <div class="demo-section">
            <div class="demo-title">Try It Now</div>
            <div class="demo-input">
                <input type="text" id="stockInput" placeholder="Enter stock symbol (e.g., AAPL, TSLA)">
                <button onclick="analyzeStock()">Analyze</button>
            </div>
            <div class="demo-result" id="demoResult">Analysis results will appear here...</div>
        </div>

        <div class="stats">
            <div class="stat-card"><div class="stat-number">4</div><div class="stat-label">AI Agents</div></div>
            <div class="stat-card"><div class="stat-number">10+</div><div class="stat-label">Indicators</div></div>
            <div class="stat-card"><div class="stat-number">3s</div><div class="stat-label">Analysis Time</div></div>
            <div class="stat-card"><div class="stat-number">100%</div><div class="stat-label">Transparent</div></div>
        </div>

        <div class="cta">
            <a href="/docs" class="cta-button">View API Documentation</a>
        </div>

        <div class="footer">
            <p>FinMind AI - UCWS Singapore Hackathon 2026</p>
        </div>
    </div>

    <script>
        async function analyzeStock() {
            const symbol = document.getElementById('stockInput').value.toUpperCase();
            const resultDiv = document.getElementById('demoResult');
            if (!symbol) { resultDiv.textContent = 'Please enter a stock symbol'; return; }
            resultDiv.textContent = 'Analyzing ' + symbol + '...';
            try {
                const response = await fetch('/api/v1/analyze/' + symbol);
                const data = await response.json();
                if (data.status === 'success') {
                    const rec = data.recommendation || {};
                    let result = '=== ' + data.company_name + ' (' + symbol + ') ===\\n\\n';
                    result += 'Price: $' + data.current_price + '\\n';
                    result += 'Change: ' + data.change_percent + '%\\n\\n';
                    result += 'RECOMMENDATION: ' + (rec.signal || 'HOLD').toUpperCase() + '\\n';
                    result += 'Confidence: ' + ((rec.confidence || 0.5) * 100).toFixed(0) + '%\\n';
                    result += 'Target: $' + (rec.target_price || 'N/A') + '\\n';
                    result += 'Stop Loss: $' + (rec.stop_loss || 'N/A') + '\\n\\n';
                    result += 'Reasoning:\\n' + (rec.reasoning || 'Analysis completed.');
                    resultDiv.textContent = result;
                } else {
                    resultDiv.textContent = 'Error: ' + (data.error || 'Analysis failed');
                }
            } catch (error) { resultDiv.textContent = 'Error: ' + error.message; }
        }
        document.getElementById('stockInput').addEventListener('keypress', function(e) { if (e.key === 'Enter') analyzeStock(); });
    </script>
</body>
</html>"""
