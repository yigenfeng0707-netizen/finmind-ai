# FinMind AI - UCWS Singapore Hackathon 2026 Submission

**Track:** Agent
**Status:** Production-deployed
**License:** MIT (Fully Open Source)
**Submission Date:** June 5, 2026

---

## Elevator Pitch (1 sentence)

FinMind AI is the first **free, transparent, multi-agent** financial analysis platform that delivers institutional-grade stock analysis in 3 seconds.

---

## Short Description (300 words)

**FinMind AI** is an autonomous multi-agent financial analysis system that democratizes institutional-grade investment research through transparent, risk-first AI. Built in 30 days, it coordinates four specialized AI agents—News Monitor, Sentiment Analyzer, Technical Analyzer, and Risk Assessor—working in parallel to deliver clear, explainable stock analysis in under 3 seconds.

**The Problem:** Professional financial analysis costs $24,000/year (Bloomberg Terminal), is fragmented across dozens of platforms, and offers no transparency into *how* recommendations are made. 99% of investors are locked out.

**Our Solution:** Four AI agents collaborate like a real analyst team. They scan global news, quantify market sentiment, calculate technical indicators, and quantify downside risk—then converge on a single recommendation with a confidence score, target price, and stop-loss level. Every reasoning step is visible. No black boxes.

**Why It Matters for the Agent Track:** We demonstrate a production-grade multi-agent architecture with specialization, coordination, transparency, and risk-first design. We tell you when *not* to invest—not just chase returns.

**Tech Stack:** Python, FastAPI, async orchestration, Yahoo Finance + NewsAPI, deployed on Vercel serverless, fully open source under MIT License.

**Traction:** Live demo at finmind-ai-beta.vercel.app. AAPL analysis returns "Strong Buy, 70% confidence, target $209.33, stop-loss $191.28" in 2.5 seconds. Production-ready, not a prototype.

**Market:** $50B+ AI-in-finance market. Freemium: $0 / $49 / $299 per month.

**Try it. Star it. Ship it.** github.com/yigenfeng0707-netizen/finmind-ai

---

## Project Information

| Field | Value |
|-------|-------|
| **Project Name** | FinMind AI |
| **Track** | Agent (AI Multi-Agent) |
| **Team** | FinMind AI (Solo Developer) |
| **Submission Date** | June 5, 2026 |
| **License** | MIT (Open Source) |
| **Live Demo** | https://finmind-ai-beta.vercel.app |
| **Source Code** | https://github.com/yigenfeng0707-netizen/finmind-ai |
| **Demo Video** | https://youtu.be/LShNCoXBa4E |
| **Contact Email** | yigen.feng0707@gmail.com |

---

## Tagline Options

Choose from:
1. **"Bloomberg for the 99%, not the 1%."**
2. **"Autonomous Multi-Agent Financial Analysis"**
3. **"4 AI Agents. 1 Click. Done."**
4. **"Risk-First AI for Smarter Investing"**

---

## Technical Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              FinMind AI - Multi-Agent Platform              │
├─────────────────────────────────────────────────────────────┤
│  Frontend (HTML5/CSS3/JavaScript)                           │
│  - Interactive Dashboard                                    │
│  - Real-time Analysis Display                               │
│  - Responsive Design (Mobile + Desktop)                     │
├─────────────────────────────────────────────────────────────┤
│  API Layer (FastAPI + Python 3.11)                          │
│  - RESTful Endpoints (/analyze/{symbol}, /agents, etc.)     │
│  - Async Processing                                         │
│  - CORS-secured                                             │
├─────────────────────────────────────────────────────────────┤
│  Agent Orchestrator                                         │
│  - Task Coordination & Parallel Execution                   │
│  - Result Aggregation & Conflict Resolution                 │
│  - Confidence Scoring                                       │
├─────────────────────────────────────────────────────────────┤
│  Specialized AI Agents                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  News    │ │Sentiment │ │Technical │ │   Risk   │       │
│  │ Monitor  │ │ Analysis │ │ Analysis │ │Assessment│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  Real-time  Sentiment     RSI/MACD/      Volatility         │
│  news scan  scoring       Bollinger      risk metrics       │
├─────────────────────────────────────────────────────────────┤
│  Data Sources                                               │
│  - Yahoo Finance API (Real-time Market Data)                │
│  - NewsAPI (Global Financial News)                          │
│  - Mock Fallback (Reliability Layer)                        │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML5, CSS3, JavaScript | Responsive dashboard with real-time updates |
| **Backend** | Python 3.11, FastAPI, Uvicorn | Async high-performance API |
| **AI/ML** | OpenAI API, TextBlob, TA-Lib | NLP, sentiment, technical analysis |
| **Data** | Yahoo Finance, NewsAPI | Real-time market data, news feeds |
| **Deployment** | Vercel Serverless, Docker | Global CDN, containerization |
| **Testing** | Pytest | 24 unit tests, 100% pass rate |
| **License** | MIT | Fully open source |

---

## Core Features (Innovation)

### 1. Multi-Agent Collaboration
Four specialized agents (News, Sentiment, Technical, Risk) work in parallel, coordinated by an orchestrator that aggregates signals, resolves conflicts, and produces a unified recommendation.

### 2. Transparent Reasoning (Glass Box)
Every recommendation comes with a complete reasoning chain. Users see which agent said what, how signals were weighted, and why the final call was made. **No black boxes.**

### 3. Risk-First Design
We don't sell dreams. Every recommendation includes:
- Confidence score (0-100%)
- Target price
- Stop-loss level
- Risk warnings
- Position sizing guidance

This makes FinMind AI suitable for retail investors, financial advisors, and institutions with fiduciary obligations.

### 4. Production-Grade Deployment
Not a hackathon prototype. Fully deployed on Vercel serverless with:
- Real-time data
- 99%+ uptime
- Global CDN
- API documentation
- Comprehensive tests

### 5. Open Source & Extensible
MIT-licensed on GitHub. Modular design means new agents (crypto, ESG, options) can be added easily.

---

## Business Model

### Target Customers
1. **Retail investors** (primary, free tier) - Need professional analysis, can't afford Bloomberg
2. **Active traders** (Pro tier) - Want unlimited analyses + advanced indicators
3. **Financial advisors** (Enterprise) - Need audit trails, API access
4. **Small funds** (Enterprise) - White-label, custom models

### Pricing

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0/month | 3 analyses/day, full transparency, open source |
| **Pro** | $49/month | Unlimited analyses, advanced indicators, alerts |
| **Enterprise** | $299/month | API access, white-label, custom agents, SLA |

### Market Size
- **TAM**: $300B+ global fintech market
- **SAM**: $50B+ AI-in-finance tools
- **SOM**: $5B+ retail + small institutional segment

### Competitive Advantage
1. **Only free, open-source multi-agent financial platform**
2. **Only platform with full reasoning transparency**
3. **Risk-first design** (institutional grade)
4. **Real-time data** (not delayed)
5. **MIT license** (no vendor lock-in)

---

## Demo Flow (5 minutes)

### 1. Hook (30s)
"Bloomberg costs $24,000 per year. FinMind AI is free. Here's how."

### 2. Live Demo (2 min)
- Enter "AAPL" in dashboard
- Show 4 agents analyzing in parallel (animated progress bars)
- Result appears: "Strong Buy, 70% confidence, $209.33 target, $191.28 stop-loss"
- Expand reasoning chain to show glass-box transparency

### 3. Innovation (1 min)
- Multi-agent architecture
- Transparent reasoning
- Risk-first design

### 4. Business (1 min)
- $50B market
- $0/$49/$299 freemium model
- 30% community voting = critical metric

### 5. CTA (30s)
- Live URL: finmind-ai-beta.vercel.app
- GitHub: github.com/yigenfeng0707-netizen/finmind-ai
- "Try it. Star it. Ship it."

---

## Future Roadmap

### Short-term (3 months)
- Real-time streaming data
- Multi-language UI (English, Chinese, Spanish)
- Mobile app (iOS + Android)
- Additional technical indicators

### Mid-term (6 months)
- Cryptocurrency support
- Social media sentiment (Twitter, Reddit)
- Developer API (with rate limits)
- Webhook integrations

### Long-term (12 months)
- Institutional platform
- Global market coverage
- White-label solution
- Custom agent training
- Compliance reporting

---

## Team

**FinMind AI** is built by a solo full-stack developer passionate about democratizing access to professional financial analysis. The project embodies the principle that **AI should be transparent, risk-aware, and accessible to everyone**—not just the 1%.

### Core Philosophy
- **Risk-first**: Protect capital before chasing returns
- **Glass-box**: Show your work, build trust through transparency
- **Open source**: Community-driven, no vendor lock-in
- **Production-grade**: Real product, not a demo

---

## Contact Information

- **Project Homepage**: https://github.com/yigenfeng0707-netizen/finmind-ai
- **Live Demo**: https://finmind-ai-beta.vercel.app
- **Demo Video (YouTube)**: https://youtu.be/LShNCoXBa4E
- **Contact Email**: yigen.feng0707@gmail.com

---

## Appendix A: Installation Guide

```bash
# Clone the repository
git clone https://github.com/yigenfeng0707-netizen/finmind-ai.git
cd finmind-ai

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Start the server
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Access the app
open http://localhost:8000
```

Or use Docker:
```bash
docker-compose up
```

## Appendix B: API Documentation

Once running, visit `http://localhost:8000/docs` for full OpenAPI documentation.

**Example API call:**
```bash
curl -X GET "https://finmind-ai-beta.vercel.app/api/v1/analyze/AAPL"
```

**Response:**
```json
{
  "symbol": "AAPL",
  "signal": "Strong Buy",
  "confidence": 0.70,
  "target_price": 209.33,
  "stop_loss": 191.28,
  "agents": {
    "news": {"signal": "Bullish", "score": 0.65},
    "sentiment": {"signal": "Positive", "score": 0.62},
    "technical": {"signal": "Buy", "score": 0.71},
    "risk": {"signal": "Medium", "score": 0.50}
  },
  "reasoning": [...]
}
```

## Appendix C: Demo Videos

- **YouTube / Bilibili** (16:9, 80s): https://youtu.be/LShNCoXBa4E
- **Xiaohongshu** (1:1, 30s): social_media/xiaohongshu/
- **Douyin** (9:16, 15s + 30s versions): douyin_wechat_videos/
- **WeChat Channels** (9:16, 30s): douyin_wechat_videos/

## Appendix D: Project Assets

- **Logo**: `submission_assets/logo_512x512.png`
- **Dashboard Screenshot**: `submission_assets/screenshot_dashboard.png`
- **Results Screenshot**: `submission_assets/screenshot_results.png`
- **Architecture Diagram**: `submission_assets/screenshot_architecture.png`

---

## Why FinMind AI Will Win

1. **Production-deployed**, not a demo
2. **Open source** (MIT) - judges can verify everything
3. **Real differentiation**: Only free multi-agent financial platform with glass-box transparency
4. **Strong community appeal**: Retail investors + developers both benefit
5. **Complete deliverables**: 15-slide pitch deck, demo videos, full documentation, social media content
6. **Clear business model**: $50B+ market, proven freemium pricing

**This is what AI agents should look like: specialized, coordinated, transparent, and accountable.**
