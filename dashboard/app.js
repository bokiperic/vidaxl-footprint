const API = '';
let reviewPage = 1;
let sentimentDoughnutChart = null;
let sentimentTrendChart = null;
let sourceBarChart = null;
let dateRangeStart = null;
let dateRangeEnd = null;

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
    loadAllData();
    document.addEventListener('click', (e) => {
        const popup = document.getElementById('date-picker-popup');
        const btn = document.getElementById('btn-date-filter');
        if (!popup.contains(e.target) && e.target !== btn) {
            popup.classList.add('hidden');
        }
    });
    // Set max attribute to current month to prevent future selection
    const maxMonth = currentMonth();
    document.getElementById('date-start').setAttribute('max', maxMonth);
    document.getElementById('date-end').setAttribute('max', maxMonth);

    // Toggle placeholder visibility on month inputs + click anywhere to open picker
    for (const id of ['date-start', 'date-end']) {
        const input = document.getElementById(id);
        const placeholder = document.getElementById(id + '-placeholder');
        input.addEventListener('change', () => {
            if (input.value) {
                placeholder.classList.add('has-value');
                input.classList.add('has-value');
            } else {
                placeholder.classList.remove('has-value');
                input.classList.remove('has-value');
            }
        });
        // Make the whole wrap area open the picker on click
        input.parentElement.addEventListener('click', () => {
            try { input.showPicker(); } catch (_) { input.focus(); }
        });
    }
});

function loadAllData() {
    loadOverview();
    loadComplaints();
    loadProducts();
    loadTrends();
    loadSources();
    loadInsights();
    loadWebMentions();
    reviewPage = 1;
    document.getElementById('reviews-feed').innerHTML = '';
    loadReviews();
}

// ---- Date Range ----
function dateParams() {
    let params = '';
    if (dateRangeStart) params += `&start_date=${dateRangeStart}-01`;
    if (dateRangeEnd) {
        // end of month: use last day
        const [y, m] = dateRangeEnd.split('-').map(Number);
        const lastDay = new Date(y, m, 0).getDate();
        params += `&end_date=${dateRangeEnd}-${String(lastDay).padStart(2, '0')}`;
    }
    return params;
}

function toggleDatePicker() {
    document.getElementById('date-picker-popup').classList.toggle('hidden');
}

function currentMonth() {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function syncInputVisuals(id, value) {
    const input = document.getElementById(id);
    const placeholder = document.getElementById(id + '-placeholder');
    input.value = value || '';
    if (value) {
        input.classList.add('has-value');
        placeholder.classList.add('has-value');
    } else {
        input.classList.remove('has-value');
        placeholder.classList.remove('has-value');
    }
}

function applyDateRange() {
    let start = document.getElementById('date-start').value || null;
    let end = document.getElementById('date-end').value || null;

    // Clamp future dates to current month
    const max = currentMonth();
    if (start && start > max) start = max;
    if (end && end > max) end = max;

    // Only "To" selected without "From" → clear both (All Time)
    if (!start && end) {
        start = null;
        end = null;
    }

    // Only "From" selected without "To" → default "To" to current month
    if (start && !end) {
        end = currentMonth();
    }

    // If "From" is after "To", swap them
    if (start && end && start > end) {
        [start, end] = [end, start];
    }

    dateRangeStart = start;
    dateRangeEnd = end;
    syncInputVisuals('date-start', start);
    syncInputVisuals('date-end', end);
    updateDateLabel();
    document.getElementById('date-picker-popup').classList.add('hidden');
    loadAllData();
}

function clearDateRange() {
    dateRangeStart = null;
    dateRangeEnd = null;
    syncInputVisuals('date-start', null);
    syncInputVisuals('date-end', null);
    updateDateLabel();
    document.getElementById('date-picker-popup').classList.add('hidden');
    loadAllData();
}

function updateDateLabel() {
    const label = document.getElementById('date-range-label');
    if (!dateRangeStart && !dateRangeEnd) {
        label.textContent = 'All Time';
        return;
    }
    const fmt = (v) => {
        const [y, m] = v.split('-');
        const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        return `${months[parseInt(m)-1]} ${y}`;
    };
    const s = dateRangeStart ? fmt(dateRangeStart) : '...';
    const e = dateRangeEnd ? fmt(dateRangeEnd) : '...';
    label.textContent = `${s} – ${e}`;
}

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
        const data = await api('/api/v1/dashboard/overview?' + dateParams());
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
        const data = await api('/api/v1/dashboard/trends?' + dateParams());
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
        const data = await api('/api/v1/dashboard/complaints?' + dateParams());
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
        const data = await api('/api/v1/dashboard/products?' + dateParams());
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
        const data = await api('/api/v1/dashboard/sources?' + dateParams());
        const sources = data.sources || [];
        const withItems = sources.filter(s => s.item_count > 0);

        const ctx = document.getElementById('sourceChart').getContext('2d');
        if (sourceBarChart) sourceBarChart.destroy();

        const labels = withItems.map(s => {
            if (s.source_type === 'web_search') return s.name + ' (Web)';
            return s.name;
        });

        sourceBarChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Reviews',
                        data: withItems.map(s => s.review_count),
                        backgroundColor: '#6366f1',
                        borderRadius: 4,
                    },
                    {
                        label: 'Articles',
                        data: withItems.map(s => s.article_count),
                        backgroundColor: '#8b5cf6',
                        borderRadius: 4,
                    },
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                scales: {
                    x: { stacked: true, ticks: { color: '#8b8d98' }, grid: { color: '#2a2d3a' } },
                    y: { stacked: true, ticks: { color: '#e4e4e7' }, grid: { display: false } }
                },
                plugins: { legend: { labels: { color: '#e4e4e7' } } }
            }
        });
    } catch (e) {
        console.error('Sources load failed:', e);
    }
}

// ---- Insights ----
async function loadInsights() {
    try {
        const data = await api('/api/v1/dashboard/insights?' + dateParams());
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

// ---- Web Mentions ----
async function loadWebMentions() {
    try {
        const data = await api('/api/v1/dashboard/web-mentions?' + dateParams());
        const feed = document.getElementById('web-mentions-feed');
        const mentions = data.mentions || [];

        if (!mentions.length) {
            feed.innerHTML = '<p class="placeholder">No web mentions yet. Run scraping to discover brand mentions across the web.</p>';
            return;
        }

        feed.innerHTML = '';
        for (const m of mentions) {
            const div = document.createElement('div');
            div.className = 'review-item';

            const sentBadge = m.sentiment ? `<span class="sentiment-badge sentiment-${esc(m.sentiment)}">${esc(m.sentiment)}</span>` : '';
            const sourceBadge = `<span class="topic-tag">${esc(m.source_name)}</span>`;

            div.innerHTML = `
                <div class="review-header">
                    <span>${sourceBadge} ${sentBadge}</span>
                    <span class="review-date">${m.published_date || ''}</span>
                </div>
                ${m.title ? `<div class="review-title"><a href="${esc(m.url)}" target="_blank" rel="noopener noreferrer" style="color:var(--accent)">${esc(m.title)}</a></div>` : ''}
                ${m.body ? `<div class="review-body">${esc(m.body)}${m.body.length >= 300 ? '...' : ''}</div>` : ''}
            `;
            feed.appendChild(div);
        }
    } catch (e) {
        console.error('Web mentions load failed:', e);
    }
}

// ---- Reviews Feed ----
async function loadReviews() {
    try {
        const data = await api(`/api/v1/reviews?page=${reviewPage}&page_size=15${dateParams()}`);
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

async function loadMoreReviews() {
    const btn = document.getElementById('btn-load-more');
    btn.classList.add('loading');
    btn.textContent = 'Loading...';
    reviewPage++;
    await loadReviews();
    btn.classList.remove('loading');
    btn.textContent = 'Load More';
}

// ---- Util ----
function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}
