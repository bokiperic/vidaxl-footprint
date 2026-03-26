const API = '';
let reviewPage = 1;
let sentimentDoughnutChart = null;
let sentimentTrendChart = null;
let sourceBarChart = null;

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
    loadOverview();
    loadComplaints();
    loadProducts();
    loadTrends();
    loadSources();
    loadInsights();
    loadReviews();
});

// ---- API helpers ----
async function api(path) {
    const res = await fetch(API + path);
    if (res.status === 401) { window.location.href = '/login'; return; }
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

function setStatus(msg) {
    document.getElementById('status-msg').textContent = msg;
    setTimeout(() => { document.getElementById('status-msg').textContent = ''; }, 5000);
}

// ---- Actions ----
async function triggerScrape() {
    const btn = document.getElementById('btn-scrape');
    btn.disabled = true;
    try {
        const data = await (await fetch(API + '/api/v1/scrape/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sources: null })
        })).json();
        setStatus(`Scraping started: ${data.sources?.length || 0} sources`);
    } catch (e) {
        setStatus('Scrape failed: ' + e.message);
    }
    btn.disabled = false;
}

async function triggerAnalysis() {
    const btn = document.getElementById('btn-analyze');
    btn.disabled = true;
    try {
        await (await fetch(API + '/api/v1/analysis/run', { method: 'POST' })).json();
        setStatus('Analysis started in background');
    } catch (e) {
        setStatus('Analysis failed: ' + e.message);
    }
    btn.disabled = false;
}

// ---- Overview / KPI ----
async function loadOverview() {
    try {
        const data = await api('/api/v1/dashboard/overview');
        document.getElementById('kpi-total').textContent = data.total_reviews.toLocaleString();
        document.getElementById('kpi-rating').textContent = data.avg_rating ? `${data.avg_rating}/5.0` : '—';
        document.getElementById('kpi-sentiment').textContent = data.avg_sentiment_score ? `${(data.avg_sentiment_score * 100).toFixed(0)}%` : '—';
        document.getElementById('kpi-sources').textContent = data.active_sources;

        // Sentiment doughnut
        const sc = data.sentiment_counts || {};
        renderSentimentDoughnut(sc.POS || 0, sc.NEU || 0, sc.NEG || 0);
    } catch (e) {
        console.error('Overview load failed:', e);
    }
}

function renderSentimentDoughnut(pos, neu, neg) {
    const ctx = document.getElementById('sentimentDoughnut').getContext('2d');
    if (sentimentDoughnutChart) sentimentDoughnutChart.destroy();

    sentimentDoughnutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [pos, neu, neg],
                backgroundColor: ['#22c55e', '#f59e0b', '#ef4444'],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#e4e4e7', padding: 16 } }
            }
        }
    });
}

// ---- Trends ----
async function loadTrends() {
    try {
        const data = await api('/api/v1/dashboard/trends');
        const monthly = data.monthly || [];
        if (!monthly.length) return;

        const ctx = document.getElementById('sentimentTrend').getContext('2d');
        if (sentimentTrendChart) sentimentTrendChart.destroy();

        sentimentTrendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: monthly.map(m => m.month),
                datasets: [
                    { label: 'Positive', data: monthly.map(m => m.positive), borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,0.1)', fill: true, tension: 0.3 },
                    { label: 'Neutral', data: monthly.map(m => m.neutral), borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,0.1)', fill: true, tension: 0.3 },
                    { label: 'Negative', data: monthly.map(m => m.negative), borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', fill: true, tension: 0.3 },
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: { ticks: { color: '#8b8d98' }, grid: { color: '#2a2d3a' } },
                    y: { ticks: { color: '#8b8d98' }, grid: { color: '#2a2d3a' } }
                },
                plugins: { legend: { labels: { color: '#e4e4e7' } } }
            }
        });
    } catch (e) {
        console.error('Trends load failed:', e);
    }
}

// ---- Complaints ----
async function loadComplaints() {
    try {
        const data = await api('/api/v1/dashboard/complaints');
        const tbody = document.getElementById('complaints-body');
        tbody.innerHTML = '';
        for (const c of (data.complaints || [])) {
            const tr = document.createElement('tr');
            tr.setAttribute('data-testid', 'complaints-row');
            const sourceCell = c.source_url
                ? `<a href="${esc(c.source_url)}" target="_blank" rel="noopener noreferrer" class="complaint-source-link">${esc(c.source_name || 'Source')}</a>`
                : esc(c.source_name || '');

            tr.innerHTML = `
                <td><strong>${esc(c.theme)}</strong></td>
                <td>${c.frequency}</td>
                <td><span class="severity-${esc(c.severity)}">${esc(c.severity)}</span></td>
                <td>${esc(c.category || '')}</td>
                <td><em>"${esc(c.example_quote || '')}"</em></td>
                <td>${sourceCell}</td>
            `;
            tbody.appendChild(tr);
        }
    } catch (e) {
        console.error('Complaints load failed:', e);
    }
}

// ---- Products ----
async function loadProducts() {
    try {
        const data = await api('/api/v1/dashboard/products');
        fillProductTable('best-products-body', data.best || []);
        fillProductTable('worst-products-body', data.worst || []);
    } catch (e) {
        console.error('Products load failed:', e);
    }
}

function fillProductTable(id, items) {
    const tbody = document.getElementById(id);
    tbody.innerHTML = '';
    for (const p of items) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${esc(p.product)}</td><td>${p.avg_rating}</td><td>${p.review_count}</td>`;
        tbody.appendChild(tr);
    }
    if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="3" class="placeholder">No product data yet</td></tr>';
    }
}

// ---- Sources ----
async function loadSources() {
    try {
        const data = await api('/api/v1/dashboard/sources');
        const sources = data.sources || [];
        const withReviews = sources.filter(s => s.review_count > 0);

        const ctx = document.getElementById('sourceChart').getContext('2d');
        if (sourceBarChart) sourceBarChart.destroy();

        sourceBarChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: withReviews.map(s => s.name),
                datasets: [{
                    label: 'Review Count',
                    data: withReviews.map(s => s.review_count),
                    backgroundColor: '#6366f1',
                    borderRadius: 4,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                scales: {
                    x: { ticks: { color: '#8b8d98' }, grid: { color: '#2a2d3a' } },
                    y: { ticks: { color: '#e4e4e7' }, grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });
    } catch (e) {
        console.error('Sources load failed:', e);
    }
}

// ---- Insights ----
async function loadInsights() {
    try {
        const data = await api('/api/v1/dashboard/insights');
        const container = document.getElementById('insights-content');

        if (!data.insights?.recommendations && !data.trends?.trends) {
            container.innerHTML = '<p class="placeholder">Run analysis to generate insights...</p>';
            return;
        }

        let html = '';

        // Trends
        if (data.trends?.trends?.length) {
            html += '<h3 style="margin-bottom:0.5rem">Detected Trends</h3>';
            for (const t of data.trends.trends) {
                const arrow = t.direction === 'up' ? '&#x2191;' : t.direction === 'down' ? '&#x2193;' : '&#x2192;';
                const cls = `trend-arrow-${esc(t.direction)}`;
                html += `<div class="trend-item"><span class="${cls}" style="font-size:1.2rem">${arrow}</span><strong>${esc(t.trend)}</strong><span style="color:var(--text-muted);margin-left:0.5rem">${esc(t.evidence)}</span></div>`;
            }
            html += '<br>';
        }

        // Recommendations
        if (data.insights?.recommendations?.length) {
            html += '<h3 style="margin-bottom:0.5rem">Recommendations</h3>';
            for (const r of data.insights.recommendations) {
                const color = r.priority === 'high' ? 'var(--negative)' : r.priority === 'medium' ? 'var(--neutral)' : 'var(--positive)';
                html += `<div class="recommendation priority-${esc(r.priority)}">
                    <span class="priority-badge" style="background:${color}">${r.priority}</span>
                    <strong>${esc(r.recommendation)}</strong>
                    <div style="color:var(--text-muted);margin-top:0.25rem;font-size:0.8rem">Expected impact: ${esc(r.expected_impact)}</div>
                </div>`;
            }
        }

        container.innerHTML = html || '<p class="placeholder">No insights available</p>';
    } catch (e) {
        console.error('Insights load failed:', e);
    }
}

// ---- Reviews Feed ----
async function loadReviews() {
    try {
        const data = await api(`/api/v1/reviews?page=${reviewPage}&page_size=15`);
        const feed = document.getElementById('reviews-feed');

        for (const r of (data.items || [])) {
            const div = document.createElement('div');
            div.className = 'review-item';
            div.setAttribute('data-testid', 'review-item');

            const stars = r.rating ? '★'.repeat(Math.round(r.rating)) + '☆'.repeat(5 - Math.round(r.rating)) : '';
            const sentBadge = r.sentiment ? `<span class="sentiment-badge sentiment-${esc(r.sentiment)}">${esc(r.sentiment)}</span>` : '';
            const topics = (r.topics || []).map(t => `<span class="topic-tag">${esc(t)}</span>`).join('');

            const sourceName = r.source_name ? `<span class="review-source">${esc(r.source_name)}</span>` : '';
            const sourceLink = r.source_url ? `<a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer" class="review-source-link">Open source</a>` : '';

            div.innerHTML = `
                <div class="review-header">
                    <span class="review-author" data-testid="review-author">${esc(r.author || 'Anonymous')} ${sentBadge}</span>
                    <span class="review-date">${r.review_date || ''}</span>
                </div>
                ${stars || sourceName ? `<div class="review-meta-row">${stars ? `<span class="review-rating">${stars}</span>` : ''}${sourceName}</div>` : ''}
                ${r.title ? `<div class="review-title">${esc(r.title)}</div>` : ''}
                ${r.body ? `<div class="review-body">${esc(r.body?.substring(0, 300))}${(r.body?.length || 0) > 300 ? '...' : ''}</div>` : ''}
                <div class="review-footer">
                    <div class="topics-list">${topics}</div>
                    ${sourceLink}
                </div>
            `;
            feed.appendChild(div);
        }

        const btn = document.getElementById('btn-load-more');
        btn.style.display = (data.items?.length === 15 && data.total > reviewPage * 15) ? 'block' : 'none';
    } catch (e) {
        console.error('Reviews load failed:', e);
    }
}

function loadMoreReviews() {
    reviewPage++;
    loadReviews();
}

// ---- Util ----
function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}
