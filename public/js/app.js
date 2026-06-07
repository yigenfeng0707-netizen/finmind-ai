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

async function analyzeStock() {
    const symbol = searchInput.value.trim().toUpperCase();

    if (!symbol) {
        showNotification('Please enter a stock symbol', 'error');
        return;
    }

    // Show loading state
    showLoading('quickAnalysis');
    showLoading('detailedAnalysis');

    // Set all agents to running state
    document.querySelectorAll('.agent-status-badge').forEach(badge => {
        badge.textContent = 'Running...';
        badge.className = 'agent-status-badge running';
    });

    try {
        const response = await fetch(getApiUrl(`/analyze/${symbol}`));
        const data = await response.json();

        if (data.status === 'success') {
            renderQuickAnalysis(data);
            renderDetailedAnalysis(data);
            showLoading('mainChart');
            showLoading('backtestResults');
            connectAnalysisWs(symbol);
            loadChart(symbol);
            loadBacktest(symbol);

            // Add to watchlist if not exists
            if (!watchlist.includes(symbol)) {
                watchlist.push(symbol);
                localStorage.setItem('watchlist', JSON.stringify(watchlist));
            }
        } else {
            showError('quickAnalysis', data.error || 'Analysis failed');
        }
    } catch (error) {
        showError('quickAnalysis', 'Failed to connect to API');
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
                    <p style="color: var(--text-secondary)">${escapeHtml(data.symbol)}</p>
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

            <div style="margin-top: 12px; text-align: right;">
                <button onclick="window.open('/api/v1/export/${data.symbol}', '_blank')" 
                    style="background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple)); 
                           color: white; border: none; padding: 8px 16px; border-radius: 8px; 
                           cursor: pointer; font-size: 13px;">
                    📄 Export Report
                </button>
            </div>

            <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${(rec.confidence || 0.5) * 100}%"></div>
            </div>
        </div>
    `;
}

function renderDetailedAnalysis(data) {
    const container = document.getElementById('detailedAnalysis');
    const agents = data.agent_results || {};

    let agentsHtml = '';

    // News Agent
    if (agents.news) {
        agentsHtml += createAgentResultCard(
            '📰',
            'News Monitor',
            agents.news.signal,
            agents.news.summary,
            agents.news.key_findings
        );
    }

    // Sentiment Agent
    if (agents.sentiment) {
        agentsHtml += createAgentResultCard(
            '💭',
            'Sentiment Analysis',
            agents.sentiment.signal,
            agents.sentiment.analysis,
            agents.sentiment.key_findings
        );
    }

    // Technical Agent
    if (agents.technical) {
        agentsHtml += createAgentResultCard(
            '📈',
            'Technical Analysis',
            agents.technical.signal,
            agents.technical.summary,
            agents.technical.key_findings
        );
    }

    // Risk Agent
    if (agents.risk) {
        agentsHtml += createAgentResultCard(
            '⚠️',
            'Risk Assessment',
            agents.risk.signal,
            agents.risk.analysis,
            agents.risk.risk_warnings
        );
    }

    container.innerHTML = `
        <div class="recommendation-card">
            <div class="recommendation-header">
                <div>
                    <h2>${data.symbol} Analysis</h2>
                    <p style="color: var(--text-secondary)">Processed in ${data.processing_time}s</p>
                </div>
            </div>

            <div class="recommendation-card" style="background: var(--bg-primary); margin-bottom: 20px;">
                <h3 style="margin-bottom: 12px;">Final Recommendation</h3>
                <p style="color: var(--text-secondary); line-height: 1.6;">
                    ${(data.recommendation?.reasoning || 'Analysis completed.').replace(/\n/g, '<br>')}
                </p>
            </div>
        </div>

        <h3 style="margin-bottom: 16px;">Agent Analyses</h3>
        <div class="agent-results">
            ${agentsHtml}
        </div>
    `;
}

function createAgentResultCard(icon, title, signal, analysis, findings) {
    const signalClass = signal ? `signal-${signal}` : '';
    const safeAnalysis = analysis ? String(analysis) : 'Analysis pending...';
    const safeFindings = Array.isArray(findings)
        ? findings.filter(f => f != null).map(f => String(f))
        : [];
    const findingsHtml = safeFindings.length
        ? `<ul style="margin-top: 12px; padding-left: 20px; color: var(--text-secondary);">
            ${safeFindings.slice(0, 3).map(f => `<li style="margin-bottom: 4px;">${escapeHtml(f)}</li>`).join('')}
           </ul>`
        : '';

    return `
        <div class="agent-result-card">
            <div class="agent-result-header">
                <div class="agent-result-title">
                    <span>${icon}</span>
                    ${title}
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

    if (!articles.length) {
        container.innerHTML = '<p class="analysis-placeholder">No news articles found</p>';
        return;
    }

    container.innerHTML = articles.map(article => `
        <div class="news-card">
            <div class="news-header">
                <div class="news-title">${escapeHtml(article.title)}</div>
                <span class="news-sentiment sentiment-${article.sentiment}">
                    ${article.sentiment}
                </span>
            </div>
            <div class="news-description">${escapeHtml(article.description || '')}</div>
            <div class="news-meta">
                <span>${article.source}</span>
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

// WebSocket Analysis Progress
let analysisWs = null;

function connectAnalysisWs(symbol) {
    // Close existing connection
    if (analysisWs) {
        analysisWs.close();
        analysisWs = null;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/analysis/${symbol}`;

    try {
        analysisWs = new WebSocket(wsUrl);

        analysisWs.onopen = () => {
            console.log(`WebSocket connected for ${symbol}`);
        };

        analysisWs.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWsMessage(data);
            } catch (e) {
                console.error('WebSocket message parse error:', e);
            }
        };

        analysisWs.onerror = (error) => {
            console.log('WebSocket error (non-critical, progress updates disabled)');
        };

        analysisWs.onclose = () => {
            analysisWs = null;
        };
    } catch (e) {
        console.log('WebSocket not available, progress updates disabled');
    }
}

function handleWsMessage(data) {
    if (data.type === 'agent_progress') {
        updateAgentProgress(data.agent, data.status, data.result);
    } else if (data.type === 'analysis_complete') {
        updateAnalysisComplete(data.result);
    }
}

function updateAgentProgress(agentName, status, result) {
    // Update agent status cards on dashboard
    const agentCards = document.querySelectorAll('.agent-card');
    const agentMap = {
        'News Monitor': 0,
        'Sentiment Analysis': 1,
        'Technical Analysis': 2,
        'Risk Assessment': 3,
        'Fundamental Analysis': 4
    };
    
    const idx = agentMap[agentName];
    if (idx !== undefined && agentCards[idx]) {
        const card = agentCards[idx];
        const statusBadge = card.querySelector('.agent-status-badge');
        if (statusBadge) {
            if (status === 'completed') {
                statusBadge.textContent = 'Done';
                statusBadge.className = 'agent-status-badge active';
                card.classList.add('pulse-once');
                setTimeout(() => card.classList.remove('pulse-once'), 1000);
            } else if (status === 'running') {
                statusBadge.textContent = 'Running...';
                statusBadge.className = 'agent-status-badge running';
            }
        }
    }
    
    // Update analysis page agent cards
    const agentResultCards = document.querySelectorAll('.agent-result-card');
    agentResultCards.forEach(card => {
        const titleEl = card.querySelector('.agent-result-title');
        if (titleEl && titleEl.textContent.includes(agentName)) {
            const signalEl = card.querySelector('.agent-signal');
            if (signalEl && status === 'completed' && result) {
                const signal = result.signal || 'hold';
                signalEl.textContent = signal.replace('_', ' ');
                signalEl.className = `agent-signal signal-${signal}`;
                
                // Add LLM badge if enhanced
                if (result.llm_enhanced) {
                    const badge = document.createElement('span');
                    badge.className = 'llm-badge';
                    badge.textContent = 'AI Enhanced';
                    badge.style.cssText = 'font-size:10px;background:linear-gradient(90deg,var(--accent-blue),var(--accent-purple));color:white;padding:2px 6px;border-radius:4px;margin-left:8px;';
                    titleEl.appendChild(badge);
                }
            }
        }
    });
    
    // Show progress notification
    if (status === 'completed') {
        showNotification(`${agentName} completed`, 'success');
    }
}

function updateAnalysisComplete(result) {
    showNotification('Analysis complete!', 'success');
}

// Chart Management
let mainChartInstance = null;
let rsiChartInstance = null;
let chartSeries = {};

async function loadChart(symbol) {
    try {
        const response = await fetch(getApiUrl('/chart-data/' + symbol + '?period=6mo'));
        const data = await response.json();

        if (data.status === 'success' && data.candles) {
            renderChart(data);
        }
    } catch (error) {
        console.error('Failed to load chart data:', error);
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
        crosshair: {
            mode: 0,
        },
        rightPriceScale: {
            borderColor: 'rgba(255,255,255,0.1)',
        },
        timeScale: {
            borderColor: 'rgba(255,255,255,0.1)',
            timeVisible: true,
        },
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
    if (data.volume) {
        volumeSeries.setData(data.volume);
    }

    // SMA 20
    if (data.sma20) {
        const sma20Series = mainChartInstance.addLineSeries({
            color: '#ffd93d',
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: false,
        });
        sma20Series.setData(data.sma20);
    }

    // SMA 50
    if (data.sma50) {
        const sma50Series = mainChartInstance.addLineSeries({
            color: '#7b2cbf',
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: false,
        });
        sma50Series.setData(data.sma50);
    }

    // Bollinger Bands
    if (data.bb_upper && data.bb_lower) {
        const bbUpperSeries = mainChartInstance.addLineSeries({
            color: 'rgba(0, 212, 255, 0.3)',
            lineWidth: 1,
            lineStyle: 2,
            priceLineVisible: false,
            lastValueVisible: false,
        });
        bbUpperSeries.setData(data.bb_upper);

        const bbLowerSeries = mainChartInstance.addLineSeries({
            color: 'rgba(0, 212, 255, 0.3)',
            lineWidth: 1,
            lineStyle: 2,
            priceLineVisible: false,
            lastValueVisible: false,
        });
        bbLowerSeries.setData(data.bb_lower);
    }

    // RSI chart
    const rsiContainer = document.getElementById('rsiChart');
    rsiChartInstance = LightweightCharts.createChart(rsiContainer, {
        ...chartOptions,
        width: rsiContainer.clientWidth,
        height: 150,
    });

    if (data.rsi) {
        const rsiSeries = rsiChartInstance.addLineSeries({
            color: '#00d4ff',
            lineWidth: 2,
            priceLineVisible: false,
        });
        rsiSeries.setData(data.rsi);

        // RSI reference lines at 30 and 70
        const rsi30 = rsiChartInstance.addLineSeries({
            color: 'rgba(0, 255, 136, 0.3)',
            lineWidth: 1,
            lineStyle: 2,
            priceLineVisible: false,
            lastValueVisible: false,
        });
        rsi30.setData(data.rsi.map(d => ({ time: d.time, value: 30 })));

        const rsi70 = rsiChartInstance.addLineSeries({
            color: 'rgba(255, 71, 87, 0.3)',
            lineWidth: 1,
            lineStyle: 2,
            priceLineVisible: false,
            lastValueVisible: false,
        });
        rsi70.setData(data.rsi.map(d => ({ time: d.time, value: 70 })));
    }

    // Sync time scales
    mainChartInstance.timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (range) {
            rsiChartInstance.timeScale().setVisibleLogicalRange(range);
        }
    });
    rsiChartInstance.timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (range) {
            mainChartInstance.timeScale().setVisibleLogicalRange(range);
        }
    });

    // Handle resize
    const resizeObserver = new ResizeObserver(entries => {
        for (const entry of entries) {
            const { width } = entry.contentRect;
            mainChartInstance.applyOptions({ width });
            rsiChartInstance.applyOptions({ width });
        }
    });
    resizeObserver.observe(mainContainer);
}

// Backtest
async function loadBacktest(symbol) {
    try {
        const response = await fetch(getApiUrl('/backtest/' + symbol));
        const data = await response.json();

        if (data.status === 'success') {
            renderBacktestResults(data);
        }
    } catch (error) {
        console.error('Failed to load backtest data:', error);
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
            <h3>Strategy Backtest Results (${data.period})</h3>
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
        rightPriceScale: {
            borderColor: 'rgba(255,255,255,0.1)',
        },
        timeScale: {
            borderColor: 'rgba(255,255,255,0.1)',
        },
        width: container.clientWidth,
        height: 200,
    });
    
    const series = chart.addLineSeries({
        color: '#00ff88',
        lineWidth: 2,
        priceLineVisible: false,
    });
    
    // Convert equity data to chart format
    const chartData = equityData.map(d => {
        const date = new Date(d.date);
        return {
            time: Math.floor(date.getTime() / 1000),
            value: d.equity
        };
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
        el.innerHTML = `<div class="analysis-placeholder" style="color: var(--accent-red);">${message}</div>`;
    }
}

function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.getElementById('toastContainer').appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
