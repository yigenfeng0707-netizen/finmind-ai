# FinMind AI - Project Description (English)

**UCWS Singapore Hackathon 2026 | Agent Track**

---

## Short Description (300 words)

**FinMind AI** is an autonomous multi-agent financial analysis system that democratizes institutional-grade investment research through transparent, risk-first AI. Built in 30 days, it coordinates four specialized AI agents—News Monitor, Sentiment Analyzer, Technical Analyzer, and Risk Assessor—working in parallel to deliver clear, explainable stock analysis in under 3 seconds.

**The Problem:** Professional financial analysis costs $24,000/year (Bloomberg Terminal), is fragmented across dozens of platforms, and offers no transparency into *how* recommendations are made. 99% of investors are locked out.

**Our Solution:** Four AI agents collaborate like a real analyst team. They scan global news, quantify market sentiment, calculate technical indicators, and quantify downside risk—then converge on a single recommendation with a confidence score, target price, and stop-loss level. Every reasoning step is visible. No black boxes. No "just trust me."

**Why It Matters for the Agent Track:** We demonstrate a production-grade multi-agent architecture with:
- **Specialization**: Each agent has a focused domain (news, sentiment, technical, risk)
- **Coordination**: An orchestrator aggregates signals, resolves conflicts, and weighs evidence
- **Transparency**: Every decision comes with a full reasoning chain users can audit
- **Risk-first design**: We tell you when *not* to invest—not just chase returns

**Tech Stack:** Python, FastAPI, async orchestration, Yahoo Finance + NewsAPI integration, deployed on Vercel serverless, fully open source under MIT License.

**Traction:** Live demo at finmind-ai-beta.vercel.app. AAPL analysis returns "Strong Buy, 70% confidence, target $209.33, stop-loss $191.28" in 2.5 seconds. Production-ready, not a prototype.

**Market:** $50B+ AI-in-finance market. Freemium model: $0 / $49 / $299 per month. Built to scale from retail investors to institutional clients.

**Try it. Star it. Ship it.** github.com/yigenfeng0707-netizen/finmind-ai

---

## Long Description (Full Pitch)

### What We Built

FinMind AI is a real-time, multi-agent financial analysis platform that processes a single stock ticker and returns a comprehensive investment recommendation—signal, confidence, target price, stop-loss, and full reasoning chain—in under 3 seconds.

### How It Works

**1. Input:** User enters a stock symbol (e.g., AAPL, TSLA, NVDA)

**2. Parallel Analysis:** Four specialized agents work simultaneously:
- **News Agent** scans 50+ global financial news sources, classifies sentiment per article
- **Sentiment Agent** aggregates market mood from news + social signals
- **Technical Agent** computes RSI, MACD, Bollinger Bands, moving averages
- **Risk Agent** quantifies volatility, max drawdown, position sizing

**3. Orchestration:** A central orchestrator weighs each agent's output, resolves conflicts, and synthesizes a final recommendation with confidence scoring

**4. Transparent Output:** Results show:
- Signal (Strong Buy / Buy / Hold / Sell / Strong Sell)
- Confidence (0-100%)
- Target price and stop-loss levels
- Full reasoning chain (which agent said what, why, and how it influenced the final call)

### Why Multi-Agent

Single-LLM approaches are black boxes and unreliable for finance. Our multi-agent design means:
- **Domain expertise**: Each agent is tuned for its specialty
- **Failure isolation**: A bad sentiment score doesn't poison technical analysis
- **Audit trail**: Compliance teams can trace every recommendation
- **Extensibility**: New agents (crypto, options, ESG) plug in easily

### Risk-First Philosophy

We don't sell dreams. Every recommendation includes explicit downside analysis and stop-loss levels. This makes FinMind AI suitable for:
- Retail investors who need to protect their savings
- Financial advisors who must justify recommendations to clients
- Institutions with fiduciary and compliance obligations

### Business Model

Three tiers, freemium-first:
- **Free**: 3 analyses/day, full transparency
- **Pro** ($49/mo): Unlimited analyses, advanced indicators
- **Enterprise** ($299/mo): API access, white-label, custom models

### Tech & Deployment

- **Backend**: Python 3.11 + FastAPI + async orchestration
- **Data**: Yahoo Finance (real-time), NewsAPI (financial news)
- **Frontend**: Modern HTML5/CSS3/JavaScript dashboard
- **Deployment**: Vercel serverless (global CDN, iad1 region)
- **License**: MIT (fully open source)
- **Tests**: 24 unit tests, 100% pass rate

### Live Demo

Visit **https://finmind-ai-beta.vercel.app**
- Enter "AAPL" → Get "Strong Buy, 70% confidence, $209.33 target, $191.28 stop-loss" in 2.5 seconds
- Watch 4 agents analyze in real-time
- Expand the reasoning chain to see how the decision was made

### Open Source

Full source code on GitHub: **github.com/yigenfeng0707-netizen/finmind-ai**
- 100% MIT licensed
- Community contributions welcome
- No vendor lock-in

### Roadmap

- **3 months**: Real-time data, multi-language UI, mobile app
- **6 months**: Crypto + forex, social sentiment, developer API
- **12 months**: Institutional platform, global markets, white-label

### Built for Impact

We didn't just demo a hackathon project. We shipped a **production-deployed**, **open-source** financial analysis platform that anyone can use, audit, and extend. This is what AI agents should look like: specialized, coordinated, transparent, and accountable.

---

## Contact

- **Project**: https://github.com/yigenfeng0707-netizen/finmind-ai
- **Live Demo**: https://finmind-ai-beta.vercel.app
- **Email**: yigen.feng0707@gmail.com
