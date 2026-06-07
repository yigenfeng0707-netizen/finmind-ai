from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from config import APP_NAME, DEBUG
from api.routes import router

# Configure structured logging
import logging
import json
import sys

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)

# Apply JSON logging in production
if not DEBUG:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)

# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    description="Autonomous Multi-Agent Financial Analysis System - UCWS Singapore Hackathon 2026",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - restricted to known origins
ALLOWED_ORIGINS = [
    "https://finmind-ai-beta.vercel.app",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Rate limiting middleware
from middleware.rate_limiter import RateLimiter
app.add_middleware(RateLimiter, requests_per_minute=60, burst=10)

# Include API routes
app.include_router(router)


# Root endpoint with landing page
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Serve the landing page."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinMind AI - Autonomous Financial Analysis</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%);
            color: #fff;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 60px;
        }
        .logo {
            font-size: 48px;
            font-weight: bold;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }
        .tagline {
            font-size: 24px;
            color: #aaa;
            margin-bottom: 30px;
        }
        .badge {
            display: inline-block;
            background: rgba(0, 212, 255, 0.2);
            border: 1px solid #00d4ff;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            margin-bottom: 30px;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            margin-bottom: 60px;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 30px;
            transition: transform 0.3s, border-color 0.3s;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            border-color: #00d4ff;
        }
        .feature-icon {
            font-size: 40px;
            margin-bottom: 20px;
        }
        .feature-title {
            font-size: 20px;
            margin-bottom: 15px;
            color: #00d4ff;
        }
        .feature-desc {
            color: #aaa;
            line-height: 1.6;
        }
        .demo-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 60px;
        }
        .demo-title {
            font-size: 28px;
            margin-bottom: 30px;
            text-align: center;
        }
        .demo-input {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
        }
        .demo-input input {
            flex: 1;
            padding: 15px 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            font-size: 16px;
        }
        .demo-input input::placeholder {
            color: #666;
        }
        .demo-input button {
            padding: 15px 30px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            border: none;
            border-radius: 10px;
            color: #fff;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .demo-input button:hover {
            transform: scale(1.05);
        }
        .demo-result {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            min-height: 200px;
            font-family: monospace;
            white-space: pre-wrap;
            color: #00ff88;
        }
        .agents-viz {
            display: none;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        .agents-viz.active { display: grid; }
        .agent-card {
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s;
        }
        .agent-card.active { border-color: #00d4ff; box-shadow: 0 0 20px rgba(0, 212, 255, 0.3); }
        .agent-card.done { border-color: #00ff88; }
        .agent-icon { font-size: 32px; margin-bottom: 10px; }
        .agent-name { font-size: 14px; color: #aaa; margin-bottom: 10px; }
        .agent-status { font-size: 12px; color: #666; }
        .agent-card.active .agent-status { color: #00d4ff; }
        .agent-card.done .agent-status { color: #00ff88; }
        .progress-bar {
            height: 4px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
            margin-top: 10px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            transition: width 0.5s;
        }
        @media (max-width: 768px) {
            .stats { grid-template-columns: repeat(2, 1fr); }
            .demo-input { flex-direction: column; }
            .agents-viz { grid-template-columns: repeat(2, 1fr); }
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 30px;
            margin-bottom: 60px;
        }
        .stat-card {
            text-align: center;
            padding: 30px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
        }
        .stat-number {
            font-size: 48px;
            font-weight: bold;
            color: #00d4ff;
            margin-bottom: 10px;
        }
        .stat-label {
            color: #aaa;
            font-size: 14px;
        }
        .cta {
            text-align: center;
            padding: 40px;
        }
        .cta-button {
            display: inline-block;
            padding: 15px 40px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            border-radius: 30px;
            color: #fff;
            text-decoration: none;
            font-size: 18px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .cta-button:hover {
            transform: scale(1.05);
        }
        .footer {
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 14px;
        }
        @media (max-width: 768px) {
            .stats { grid-template-columns: repeat(2, 1fr); }
            .demo-input { flex-direction: column; }
        }
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
                <div class="feature-desc">Real-time monitoring of financial news with AI-powered sentiment analysis across multiple sources.</div>
            </div>
            <div class="feature-card">
                <div class="feature-title">Sentiment Analysis</div>
                <div class="feature-desc">Deep analysis of market sentiment combining news, social signals, and market indicators.</div>
            </div>
            <div class="feature-card">
                <div class="feature-title">Technical Analysis</div>
                <div class="feature-desc">Advanced technical indicators including RSI, MACD, Bollinger Bands, and pattern recognition.</div>
            </div>
            <div class="feature-card">
                <div class="feature-title">Risk Assessment</div>
                <div class="feature-desc">Comprehensive risk quantification with volatility, market, and news risk metrics.</div>
            </div>
        </div>

        <div class="demo-section">
            <div class="demo-title">Try It Now</div>
            <div class="demo-input">
                <input type="text" id="stockInput" placeholder="Enter stock symbol (e.g., AAPL, TSLA, GOOGL)">
                <button onclick="analyzeStock()">Analyze</button>
            </div>
            
            <div class="agents-viz" id="agentsViz">
                <div class="agent-card" id="agent1">
                    <div class="agent-icon">📰</div>
                    <div class="agent-name">News Monitor</div>
                    <div class="agent-status">Waiting...</div>
                    <div class="progress-bar"><div class="progress-fill"></div></div>
                </div>
                <div class="agent-card" id="agent2">
                    <div class="agent-icon">💭</div>
                    <div class="agent-name">Sentiment Analysis</div>
                    <div class="agent-status">Waiting...</div>
                    <div class="progress-bar"><div class="progress-fill"></div></div>
                </div>
                <div class="agent-card" id="agent3">
                    <div class="agent-icon">📊</div>
                    <div class="agent-name">Technical Analysis</div>
                    <div class="agent-status">Waiting...</div>
                    <div class="progress-bar"><div class="progress-fill"></div></div>
                </div>
                <div class="agent-card" id="agent4">
                    <div class="agent-icon">⚠️</div>
                    <div class="agent-name">Risk Assessment</div>
                    <div class="agent-status">Waiting...</div>
                    <div class="progress-bar"><div class="progress-fill"></div></div>
                </div>
            </div>
            
            <div class="demo-result" id="demoResult">
Analysis results will appear here...

Click "Analyze" to see the AI agents in action!
            </div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">4</div>
                <div class="stat-label">AI Agents</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">10+</div>
                <div class="stat-label">Indicators</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">Real-time</div>
                <div class="stat-label">Analysis</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">100%</div>
                <div class="stat-label">Transparent</div>
            </div>
        </div>

        <div class="cta">
            <a href="/docs" class="cta-button">View API Documentation</a>
        </div>

        <div class="footer">
            <p>FinMind AI - Built for UCWS Singapore Hackathon 2026</p>
            <p>Multi-Agent Architecture | Transparent AI | Real-Time Analysis</p>
        </div>
    </div>

    <script>
        let analyzing = false;

        function resetAgents() {
            for (let i = 1; i <= 4; i++) {
                const card = document.getElementById(`agent${i}`);
                card.classList.remove('active', 'done');
                card.querySelector('.agent-status').textContent = 'Waiting...';
                card.querySelector('.progress-fill').style.width = '0%';
            }
        }

        function setAgentStatus(id, status, progress) {
            const card = document.getElementById(`agent${id}`);
            card.classList.add('active');
            card.classList.remove('done');
            card.querySelector('.agent-status').textContent = status;
            card.querySelector('.progress-fill').style.width = progress + '%';
        }

        function setAgentDone(id) {
            const card = document.getElementById(`agent${id}`);
            card.classList.remove('active');
            card.classList.add('done');
            card.querySelector('.agent-status').textContent = 'Complete!';
            card.querySelector('.progress-fill').style.width = '100%';
        }

        async function analyzeStock() {
            if (analyzing) return;
            analyzing = true;

            const symbol = document.getElementById('stockInput').value.toUpperCase();
            const resultDiv = document.getElementById('demoResult');
            const vizDiv = document.getElementById('agentsViz');

            if (!symbol) {
                resultDiv.textContent = 'Please enter a stock symbol';
                analyzing = false;
                return;
            }

            resetAgents();
            vizDiv.classList.add('active');
            resultDiv.textContent = `Initializing analysis for ${symbol}...`;

            // Simulate agent progress
            const agentSteps = [
                { id: 1, status: 'Scanning financial news...', delay: 800 },
                { id: 1, status: 'Analyzing 15 news articles...', delay: 1200 },
                { id: 2, status: 'Processing sentiment signals...', delay: 600 },
                { id: 2, status: 'Aggregating social indicators...', delay: 1000 },
                { id: 3, status: 'Calculating technical indicators...', delay: 700 },
                { id: 3, status: 'Analyzing price patterns...', delay: 1100 },
                { id: 4, status: 'Evaluating risk metrics...', delay: 500 },
                { id: 4, status: 'Generating risk profile...', delay: 900 },
            ];

            let progress = 0;
            const stepPromise = (async () => {
                for (const step of agentSteps) {
                    await new Promise(r => setTimeout(r, step.delay));
                    progress += 12;
                    setAgentStatus(step.id, step.status, Math.min(progress, 100));
                }
            })();

            try {
                const response = await fetch(`/api/v1/analyze/${symbol}`);
                const data = await response.json();

                await stepPromise;
                for (let i = 1; i <= 4; i++) setAgentDone(i);

                if (data.status === 'success') {
                    const rec = data.recommendation || {};
                    let result = `=== ${data.company_name} (${symbol}) ===\\n\\n`;
                    result += `Current Price: $${data.current_price}\\n`;
                    result += `Change: ${data.change_percent > 0 ? '+' : ''}${data.change_percent}%\\n\\n`;
                    result += `RECOMMENDATION: ${(rec.signal || 'HOLD').toUpperCase()}\\n`;
                    result += `Confidence: ${((rec.confidence || 0.5) * 100).toFixed(0)}%\\n`;
                    result += `Target: $${rec.target_price || 'N/A'}\\n`;
                    result += `Stop Loss: $${rec.stop_loss || 'N/A'}\\n\\n`;
                    result += `ANALYSIS:\\n${rec.reasoning || 'Analysis completed.'}\\n\\n`;
                    result += `Processing Time: ${data.processing_time}s`;
                    resultDiv.textContent = result;
                } else {
                    resultDiv.textContent = `Error: ${data.error || 'Analysis failed'}`;
                }
            } catch (error) {
                resultDiv.textContent = `Error: ${error.message}`;
            }

            analyzing = false;
        }

        document.getElementById('stockInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') analyzeStock();
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG
    )
