// FinMind AI Frontend Application

const API_BASE = '/api/v1';

// API Key management
function getApiKey() {
    return localStorage.getItem('finmind_api_key') || '';
}

function setApiKey(key) {
    localStorage.setItem('finmind_api_key', key);
}

function getApiHeaders() {
    const key = getApiKey();
    const headers = { 'Content-Type': 'application/json' };
    if (key) headers['X-API-Key'] = key;
    return headers;
}

function getApiUrl(endpoint) {
    const key = getApiKey();
    const sep = endpoint.includes('?') ? '&' : '?';
    return key ? `${API_BASE}${endpoint}${sep}api_key=${encodeURIComponent(key)}` : `${API_BASE}${endpoint}`;
}

// Utility: Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// State
let currentPage = 'dashboard';
let watchlist = JSON.parse(localStorage.getItem('watchlist') || '[]');

// DOM Elements
const searchInput = document.getElementById('searchInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const timestampEl = document.getElementById('timestamp');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    updateTimestamp();
    setInterval(updateTimestamp, 60000);
});

function initializeApp() {
    // Restore saved API key
    const savedKey = getApiKey();
    const keyInput = document.getElementById('apiKeyInput');
    if (keyInput && savedKey) keyInput.value = savedKey;

    loadMarketOverview();
    loadNewsFeed();
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            navigateTo(page);
        });
    });

    // Analysis
    analyzeBtn.addEventListener('click', () => analyzeStock());
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') analyzeStock();
    });
}

function navigateTo(page) {
    currentPage = page;

    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });

    // Update pages
    document.querySelectorAll('.page').forEach(p => {
        p.classList.toggle('active', p.id === page);
    });

    // Load page-specific data
    if (page === 'watchlist') loadWatchlist();
    if (page === 'news') loadNewsFeed();
}

function updateTimestamp() {
    const now = new Date();
    timestampEl.textContent = now.toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Theme Toggle
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    document.getElementById('themeToggle').textContent = next === 'light' ? '☀️' : '🌙';
}

// Load saved theme
(function() {
    const saved = localStorage.getItem('theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
        const btn = document.getElementById('themeToggle');
        if (btn) btn.textContent = saved === 'light' ? '☀️' : '🌙';
    }
})();

// API Calls
async function loadMarketOverview() {
    try {
        const response = await fetch(getApiUrl('/market-overview'));
        const data = await response.json();

        if (data.status === 'success') {
            renderIndices(data.indices || []);
        }
    } catch (error) {
        console.error('Failed to load market overview:', error);
    }
}

function renderIndices(indices) {
    const grid = document.getElementById('indicesGrid');

    if (!indices.length) {
        grid.innerHTML = '<p class="analysis-placeholder">Loading market data...</p>';
        return;
    }

    grid.innerHTML = indices.map(index => `
        <div class="index-card">
            <div class="index-name">${escapeHtml(index.name)}</div>
            <div class="index-price">$${formatNumber(index.current_price)}</div>
            <div class="index-change ${index.change_percent >= 0 ? 'positive' : 'negative'}">
                ${index.change_percent >= 0 ? '+' : ''}${index.change_percent.toFixed(2)}%
            </div>
        </div>
    `).join('');
}

// ── Main Analysis Flow ──────────────────────────────────────────
async function analyzeStock() {
    const symbol = searchInput.value.trim().toUpperCase();

    if (!symbol) {
        showNotification('Please enter a stock symbol', 'error');
        return;
    }

    // Set all agents to running state
    setAllAgentStatus('running');
    showLoading('quickAnalysis');

    try {
        showNotification(`Analyzing ${symbol}...`, 'info');

        const response = await fetch(getApiUrl(`/analyze/${symbol}`));
        const data = await response.json();

        if (data.status === 'success') {
            // Update agent statuses from results
            updateAgentStatusesFromResults(data.agent_results || {});

            // Render results on Dashboard
            renderQuickAnalysis(data);

            // Render detailed analysis on Analysis page
            renderDetailedAnalysis(data);

            // Switch to Analysis page to show charts & details
            navigateTo('analysis');

            // Load chart and backtest in parallel
            loadChart(symbol);
            loadBacktest(symbol);

            // Add to watchlist
            if (!watchlist.includes(symbol)) {
                watchlist.push(symbol);
                localStorage.setItem('watchlist', JSON.stringify(watchlist));
            }

            showNotification(`${symbol} analysis complete!`, 'success');
        } else {
            setAllAgentStatus('error');
            showError('quickAnalysis', data.error || data.detail || 'Analysis failed');
            showNotification('Analysis failed: ' + (data.error || data.detail || 'Unknown error'), 'error');
        }
    } catch (error) {
        setAllAgentStatus('error');
        showError('quickAnalysis', 'Failed to connect to API: ' + error.message);
        showNotification('Connection error', 'error');
    }
}

function setAllAgentStatus(status) {
    document.querySelectorAll('.agent-status-badge').forEach(badge => {
        if (status === 'running') {
            badge.textContent = 'Running...';
            badge.className = 'agent-status-badge running';
        } else if (status === 'error') {
            badge.textContent = 'Error';
            badge.className = 'agent-status-badge error';
        }
    });
}

function updateAgentStatusesFromResults(agentResults) {
    const agentMap = {
        'news': 0,
        'sentiment': 1,
        'technical': 2,
        'risk': 3,
        'fundamental': 4
    };

    const badges = document.querySelectorAll('.agent-status-badge');

    for (const [key, idx] of Object.entries(agentMap)) {
        if (agentResults[key] && badges[idx]) {
            const result = agentResults[key];
            badges[idx].textContent = 'Done';
            badges[idx].className = 'agent-status-badge active';
        }
    }
}

function renderQuickAnalysis(data) {
    const container = document.getElementById('quickAnalysis');
    const rec = data.recommendation || {};

    container.innerHTML = `
        <div class="recommendation-card">
            <div class="recommendation-header">
                <div>
                    <h2>${escapeHtml(data.company_name || data.symbol)}</h2>
                    <p style="color: var(--text-secondary)">${escapeHtml(data.symbol)} · ${data.processing_time || 0}s</p>
                </div>
                <div class="recommendation-signal signal-${rec.signal || 'hold'}">
                    ${rec.signal ? rec.signal.replace('_', ' ').toUpperCase() : 'HOLD'}
                </div>
            </div>

            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">$${data.current_price || 'N/A'}</div>
                    <div class="metric-label">Current Price</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value ${data.change_percent >= 0 ? 'positive' : 'negative'}" style="color: ${data.change_percent >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">
                        ${data.change_percent >= 0 ? '+' : ''}${data.change_percent || 0}%
                    </div>
                    <div class="metric-label">Change</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">$${rec.target_price || 'N/A'}</div>
                    <div class="metric-label">Target Price</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${((rec.confidence || 0.5) * 100).toFixed(0)}%</div>
                    <div class="metric-label">Confidence</div>
                </div>
            </div>

            <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${(rec.confidence || 0.5) * 100}%"></div>
            </div>

            ${rec.reasoning ? `
            <div style="margin-top: 16px; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px; border-left: 3px solid var(--accent-blue);">
                <p style="color: var(--text-secondary); line-height: 1.6; font-size: 13px;">
                    ${escapeHtml(rec.reasoning).replace(/\n/g, '<br>')}
                </p>
            </div>` : ''}

            <div style="margin-top: 12px; text-align: right;">
                <button onclick="window.open('/api/v1/export/${data.symbol}', '_blank')"
                    style="background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
                           color: white; border: none; padding: 8px 16px; border-radius: 8px;
                           cursor: pointer; font-size: 13px;">
                    Export Report
                </button>
            </div>
        </div>
    `;
}

function renderDetailedAnalysis(data) {
    const container = document.getElementById('detailedAnalysis');
    const agents = data.agent_results || {};
    const rec = data.recommendation || {};

    let agentsHtml = '';

    // News Agent
    if (agents.news) {
        agentsHtml += createAgentResultCard(
            '📰', 'News Monitor', agents.news.signal,
            agents.news.summary, agents.news.key_findings, agents.news.llm_enhanced
        );
    }

    // Sentiment Agent
    if (agents.sentiment) {
        agentsHtml += createAgentResultCard(
            '💭', 'Sentiment Analysis', agents.sentiment.signal,
            agents.sentiment.analysis, agents.sentiment.key_findings, agents.sentiment.llm_enhanced
        );
    }

    // Technical Agent
    if (agents.technical) {
        agentsHtml += createAgentResultCard(
            '📈', 'Technical Analysis', agents.technical.signal,
            agents.technical.summary, agents.technical.key_findings, agents.technical.llm_enhanced
        );
    }

    // Fundamental Agent
    if (agents.fundamental) {
        agentsHtml += createAgentResultCard(
            '💰', 'Fundamental Analysis', agents.fundamental.signal,
            agents.fundamental.summary, agents.fundamental.key_findings, agents.fundamental.llm_enhanced
        );
    }

    // Risk Agent
    if (agents.risk) {
        agentsHtml += createAgentResultCard(
            '⚠️', 'Risk Assessment', agents.risk.signal,
            agents.risk.analysis, agents.risk.risk_warnings, agents.risk.llm_enhanced
        );
    }

    container.innerHTML = `
        <div class="recommendation-card">
            <div class="recommendation-header">
                <div>
                    <h2>${data.symbol} Analysis</h2>
                    <p style="color: var(--text-secondary)">Processed in ${data.processing_time}s · ${rec.llm_enhanced ? 'AI Enhanced' : 'Rule-based'}</p>
                </div>
                <div class="recommendation-signal signal-${rec.signal || 'hold'}">
                    ${rec.signal ? rec.signal.replace('_', ' ').toUpperCase() : 'HOLD'}
                </div>
            </div>

            <div class="recommendation-card" style="background: var(--bg-primary); margin-bottom: 20px;">
                <h3 style="margin-bottom: 12px;">Final Recommendation</h3>
                <p style="color: var(--text-secondary); line-height: 1.6;">
                    ${(rec.reasoning || 'Analysis completed.').replace(/\n/g, '<br>')}
                </p>
            </div>
        </div>

        <h3 style="margin-bottom: 16px;">Agent Analyses</h3>
        <div class="agent-results">
            ${agentsHtml}
        </div>
    `;
}

function createAgentResultCard(icon, title, signal, analysis, findings, llmEnhanced) {
    const signalClass = signal ? `signal-${signal}` : '';
    const safeAnalysis = analysis ? String(analysis) : 'Analysis pending...';
    const safeFindings = Array.isArray(findings)
        ? findings.filter(f => f != null).map(f => String(f))
        : [];
    const findingsHtml = safeFindings.length
        ? `<ul style="margin-top: 12px; padding-left: 20px; color: var(--text-secondary);">
            ${safeFindings.slice(0, 5).map(f => `<li style="margin-bottom: 4px;">${escapeHtml(f)}</li>`).join('')}
           </ul>`
        : '';
    const llmBadge = llmEnhanced
        ? `<span style="font-size:10px;background:linear-gradient(90deg,var(--accent-blue),var(--accent-purple));color:white;padding:2px 6px;border-radius:4px;margin-left:8px;">AI Enhanced</span>`
        : '';

    return `
        <div class="agent-result-card">
            <div class="agent-result-header">
                <div class="agent-result-title">
                    <span>${icon}</span>
                    ${title}${llmBadge}
                </div>
                <span class="agent-signal ${signalClass}">
                    ${signal ? signal.replace('_', ' ') : 'N/A'}
                </span>
            </div>
            <div class="agent-analysis">
                ${safeAnalysis}
                ${findingsHtml}
            </div>
        </div>
    `;
}

async function loadNewsFeed() {
    const container = document.getElementById('newsFeed');

    try {
        const response = await fetch(getApiUrl('/market-overview'));
        const data = await response.json();

        if (data.status === 'success' && data.market_news) {
            renderNewsFeed(data.market_news);
        } else {
            container.innerHTML = '<p class="analysis-placeholder">No news available</p>';
        }
    } catch (error) {
        container.innerHTML = '<p class="analysis-placeholder">Failed to load news</p>';
    }
}

function renderNewsFeed(articles) {
    const container = document.getElementById('newsFeed');

    if (!articles || !articles.length) {
        container.innerHTML = '<p class="analysis-placeholder">No news articles found</p>';
        return;
    }

    container.innerHTML = articles.map(article => `
        <div class="news-card">
            <div class="news-header">
                <div class="news-title">${escapeHtml(article.title)}</div>
                <span class="news-sentiment sentiment-${article.sentiment || 'neutral'}">
                    ${article.sentiment || 'neutral'}
                </span>
            </div>
            <div class="news-description">${escapeHtml(article.description || '')}</div>
            <div class="news-meta">
                <span>${escapeHtml(article.source || '')}</span>
                <span>${formatTime(article.published_at)}</span>
            </div>
        </div>
    `).join('');
}

function loadWatchlist() {
    const container = document.getElementById('watchlistContainer');

    if (!watchlist.length) {
        container.innerHTML = '<p class="analysis-placeholder">Your watchlist is empty. Analyze a stock to add it.</p>';
        return;
    }

    container.innerHTML = `
        <div class="indices-grid">
            ${watchlist.map(symbol => `
                <div class="index-card" onclick="searchInput.value='${symbol}'; analyzeStock();" style="cursor: pointer;">
                    <div class="index-name">${symbol}</div>
                    <div class="index-price">Click to analyze</div>
                </div>
            `).join('')}
        </div>
    `;
}

// Chart Management
let mainChartInstance = null;
let rsiChartInstance = null;

async function loadChart(symbol) {
    const container = document.getElementById('mainChart');
    if (!container) return;

    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const response = await fetch(getApiUrl('/chart-data/' + symbol + '?period=6mo'));
        const data = await response.json();

        if (data.status === 'success' && data.candles && data.candles.length > 0) {
            renderChart(data);
        } else {
            container.innerHTML = '<p class="analysis-placeholder">Chart data unavailable</p>';
        }
    } catch (error) {
        console.error('Failed to load chart data:', error);
        container.innerHTML = '<p class="analysis-placeholder">Failed to load chart</p>';
    }
}

function renderChart(data) {
    // Clear existing charts
    if (mainChartInstance) {
        mainChartInstance.remove();
        mainChartInstance = null;
    }
    if (rsiChartInstance) {
        rsiChartInstance.remove();
        rsiChartInstance = null;
    }

    const chartOptions = {
        layout: {
            background: { type: 'solid', color: '#1a1a3a' },
            textColor: '#8888aa',
        },
        grid: {
            vertLines: { color: 'rgba(255,255,255,0.05)' },
            horzLines: { color: 'rgba(255,255,255,0.05)' },
        },
        crosshair: { mode: 0 },
        rightPriceScale: { borderColor: 'rgba(255,255,255,0.1)' },
        timeScale: { borderColor: 'rgba(255,255,255,0.1)', timeVisible: true },
    };

    // Main chart
    const mainContainer = document.getElementById('mainChart');
    mainChartInstance = LightweightCharts.createChart(mainContainer, {
        ...chartOptions,
        width: mainContainer.clientWidth,
        height: 400,
    });

    // Candlestick series
    const candleSeries = mainChartInstance.addCandlestickSeries({
        upColor: '#00ff88',
        downColor: '#ff4757',
        borderUpColor: '#00ff88',
        borderDownColor: '#ff4757',
        wickUpColor: '#00ff88',
        wickDownColor: '#ff4757',
    });
    candleSeries.setData(data.candles);

    // Volume series
    const volumeSeries = mainChartInstance.addHistogramSeries({
        color: '#00d4ff',
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
    });
    volumeSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
    });
    if (data.volume) volumeSeries.setData(data.volume);

    // SMA 20
    if (data.sma20 && data.sma20.length) {
        mainChartInstance.addLineSeries({
            color: '#ffd93d', lineWidth: 1, priceLineVisible: false, lastValueVisible: false,
        }).setData(data.sma20);
    }

    // SMA 50
    if (data.sma50 && data.sma50.length) {
        mainChartInstance.addLineSeries({
            color: '#7b2cbf', lineWidth: 1, priceLineVisible: false, lastValueVisible: false,
        }).setData(data.sma50);
    }

    // Bollinger Bands
    if (data.bb_upper && data.bb_lower) {
        mainChartInstance.addLineSeries({
            color: 'rgba(0, 212, 255, 0.3)', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false,
        }).setData(data.bb_upper);
        mainChartInstance.addLineSeries({
            color: 'rgba(0, 212, 255, 0.3)', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false,
        }).setData(data.bb_lower);
    }

    // RSI chart
    const rsiContainer = document.getElementById('rsiChart');
    if (rsiContainer && data.rsi && data.rsi.length) {
        rsiChartInstance = LightweightCharts.createChart(rsiContainer, {
            ...chartOptions,
            width: rsiContainer.clientWidth,
            height: 150,
        });

        rsiChartInstance.addLineSeries({
            color: '#00d4ff', lineWidth: 2, priceLineVisible: false,
        }).setData(data.rsi);

        // RSI reference lines
        rsiChartInstance.addLineSeries({
            color: 'rgba(0, 255, 136, 0.3)', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false,
        }).setData(data.rsi.map(d => ({ time: d.time, value: 30 })));
        rsiChartInstance.addLineSeries({
            color: 'rgba(255, 71, 87, 0.3)', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false,
        }).setData(data.rsi.map(d => ({ time: d.time, value: 70 })));

        // Sync time scales
        mainChartInstance.timeScale().subscribeVisibleLogicalRangeChange(range => {
            if (range) rsiChartInstance.timeScale().setVisibleLogicalRange(range);
        });
        rsiChartInstance.timeScale().subscribeVisibleLogicalRangeChange(range => {
            if (range) mainChartInstance.timeScale().setVisibleLogicalRange(range);
        });
    }

    // Handle resize
    const resizeObserver = new ResizeObserver(entries => {
        for (const entry of entries) {
            const { width } = entry.contentRect;
            if (mainChartInstance) mainChartInstance.applyOptions({ width });
            if (rsiChartInstance) rsiChartInstance.applyOptions({ width });
        }
    });
    resizeObserver.observe(mainContainer);
}

// Backtest
async function loadBacktest(symbol) {
    const container = document.getElementById('backtestResults');
    if (!container) return;

    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const response = await fetch(getApiUrl('/backtest/' + symbol));
        const data = await response.json();

        if (data.status === 'success' && data.metrics) {
            renderBacktestResults(data);
        } else {
            container.innerHTML = '<p class="analysis-placeholder">Backtest data unavailable</p>';
        }
    } catch (error) {
        console.error('Failed to load backtest data:', error);
        container.innerHTML = '<p class="analysis-placeholder">Failed to load backtest</p>';
    }
}

function renderBacktestResults(data) {
    const container = document.getElementById('backtestResults');
    if (!container) return;

    const m = data.metrics;
    const returnClass = m.total_return_pct >= 0 ? 'positive' : 'negative';
    const returnColor = m.total_return_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';

    container.innerHTML = `
        <div class="backtest-card">
            <h3>Strategy Backtest Results (${data.period || '1y'}, ${data.strategy || 'combined'})</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value ${returnClass}" style="color: ${returnColor}">
                        ${m.total_return_pct >= 0 ? '+' : ''}${m.total_return_pct}%
                    </div>
                    <div class="metric-label">Total Return</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${m.win_rate}%</div>
                    <div class="metric-label">Win Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${m.total_trades}</div>
                    <div class="metric-label">Total Trades</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: var(--accent-red)">${m.max_drawdown_pct}%</div>
                    <div class="metric-label">Max Drawdown</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${m.sharpe_ratio}</div>
                    <div class="metric-label">Sharpe Ratio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${m.profit_factor}</div>
                    <div class="metric-label">Profit Factor</div>
                </div>
            </div>
            <div id="equityCurveChart" class="chart-main" style="height: 200px; margin-top: 20px;"></div>
        </div>
    `;

    // Render equity curve if data available
    if (data.equity_curve && data.equity_curve.length > 0 && typeof LightweightCharts !== 'undefined') {
        renderEquityCurve(data.equity_curve);
    }
}

function renderEquityCurve(equityData) {
    const container = document.getElementById('equityCurveChart');
    if (!container) return;

    const chart = LightweightCharts.createChart(container, {
        layout: {
            background: { type: 'solid', color: '#1a1a3a' },
            textColor: '#8888aa',
        },
        grid: {
            vertLines: { color: 'rgba(255,255,255,0.05)' },
            horzLines: { color: 'rgba(255,255,255,0.05)' },
        },
        rightPriceScale: { borderColor: 'rgba(255,255,255,0.1)' },
        timeScale: { borderColor: 'rgba(255,255,255,0.1)' },
        width: container.clientWidth,
        height: 200,
    });

    const series = chart.addLineSeries({
        color: '#00ff88', lineWidth: 2, priceLineVisible: false,
    });

    const chartData = equityData.map(d => {
        const date = new Date(d.date);
        return { time: Math.floor(date.getTime() / 1000), value: d.equity };
    }).filter(d => d.time > 0);

    series.setData(chartData);
}

// Utility Functions
function formatNumber(num) {
    if (typeof num !== 'number') return 'N/A';
    return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
}

function showLoading(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    }
}

function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = `<div class="analysis-placeholder" style="color: var(--accent-red);">${escapeHtml(message)}</div>`;
    }
}

function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    const container = document.getElementById('toastContainer');
    if (container) {
        container.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}
