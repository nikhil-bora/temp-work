// KPI Dashboard JavaScript

let kpis = [];
let templates = [];
let editingKPI = null;
let ws = null;

console.log('[DASHBOARD] Initializing KPI Dashboard');

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('[DASHBOARD] DOM loaded, loading KPIs and templates');
    loadKPIs();
    loadTemplates();
    setupFormHandler();
    initWebSocket();
});

// Initialize WebSocket for real-time updates
function initWebSocket() {
    console.log('[DASHBOARD-WS] Initializing WebSocket connection');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    console.log('[DASHBOARD-WS] Connecting to:', wsUrl);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('[DASHBOARD-WS] ✓ WebSocket connected successfully');
    };

    ws.onmessage = (event) => {
        console.log('[DASHBOARD-WS] Message received:', event.data);
        try {
            const data = JSON.parse(event.data);
            console.log('[DASHBOARD-WS] Parsed data:', data);

            // Handle KPI creation notification
            if (data.type === 'kpi_created') {
                console.log('[DASHBOARD-WS] KPI created notification received:', data.kpi_id);
                console.log('[DASHBOARD-WS] Refreshing KPI list...');

                // Show notification
                showNotification('New KPI created! Refreshing dashboard...');

                // Reload KPIs after short delay to ensure file is saved
                setTimeout(() => {
                    loadKPIs();
                }, 500);
            }
        } catch (e) {
            console.error('[DASHBOARD-WS] Error parsing message:', e);
        }
    };

    ws.onerror = (error) => {
        console.error('[DASHBOARD-WS] ✗ WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('[DASHBOARD-WS] Connection closed. Reconnecting in 3 seconds...');
        setTimeout(initWebSocket, 3000);
    };
}

// Show notification
function showNotification(message) {
    console.log('[DASHBOARD] Showing notification:', message);
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4CAF50;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Load all KPIs
async function loadKPIs() {
    try {
        console.log('[DASHBOARD] Loading KPIs...');
        // Add cache-busting parameter to ensure fresh data
        const response = await fetch(`/api/kpis?t=${Date.now()}`, {
            cache: 'no-store'
        });
        if (!response.ok) throw new Error('Failed to load KPIs');

        kpis = await response.json();
        console.log('[DASHBOARD] Loaded', kpis.length, 'KPIs');
        console.log('[DASHBOARD] KPI IDs:', kpis.map(k => k.id));
        renderKPIs();

        // Auto-refresh KPIs that need it
        kpis.forEach(kpi => {
            if (kpi.last_value === null || needsRefresh(kpi)) {
                refreshKPI(kpi.id);
            }
        });
    } catch (error) {
        console.error('[DASHBOARD] Error loading KPIs:', error);
        showError('Failed to load KPIs');
    }
}

// Load KPI templates
async function loadTemplates() {
    try {
        const response = await fetch('/api/kpis/templates');
        if (!response.ok) throw new Error('Failed to load templates');

        templates = await response.json();
        renderTemplates();
    } catch (error) {
        console.error('Error loading templates:', error);
    }
}

// Render KPI grid
function renderKPIs() {
    const grid = document.getElementById('kpiGrid');

    if (kpis.length === 0) {
        grid.innerHTML = `
            <div class="kpi-loading">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">No KPIs Yet</h3>
                <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Get started by adding your first KPI</p>
                <button class="btn-primary" onclick="showAddKPIModal()">＋ Add KPI</button>
            </div>
        `;
        return;
    }

    grid.innerHTML = kpis.map(kpi => createKPICard(kpi)).join('');
}

// Create KPI card HTML
function createKPICard(kpi) {
    const value = formatKPIValue(kpi.last_value, kpi.format);
    const lastUpdated = kpi.last_updated ? formatTimestamp(kpi.last_updated) : 'Never';
    const isLoading = kpi.last_value === null;

    return `
        <div class="kpi-card size-${kpi.size}" style="border-color: ${kpi.color}20;" data-kpi-id="${kpi.id}">
            <div class="kpi-card-header">
                <div class="kpi-icon" style="background: ${kpi.color}20; color: ${kpi.color};">
                    ${kpi.icon}
                </div>
                <div class="kpi-actions">
                    <button class="kpi-action-btn" onclick="refreshKPI('${kpi.id}')" title="Refresh">
                        🔄
                    </button>
                    <button class="kpi-action-btn" onclick="editKPI('${kpi.id}')" title="Edit">
                        ✏️
                    </button>
                    <button class="kpi-action-btn delete" onclick="deleteKPI('${kpi.id}')" title="Delete">
                        🗑️
                    </button>
                </div>
            </div>
            <div class="kpi-info">
                <div class="kpi-name">${kpi.name}</div>
                <div class="kpi-description">${kpi.description}</div>
            </div>
            <div class="kpi-value" style="color: ${kpi.color};">
                ${isLoading ? '<div class="spinner" style="width: 30px; height: 30px;"></div>' : value}
            </div>
            <div class="kpi-meta">
                <span>Updated ${lastUpdated}</span>
                ${kpi.trend ? `<span class="kpi-trend ${kpi.trend}">${kpi.trend === 'up' ? '↑' : '↓'}</span>` : ''}
            </div>
        </div>
    `;
}

// Format KPI value based on format type
function formatKPIValue(value, format) {
    if (value === null || value === undefined) return '—';

    switch (format) {
        case 'currency':
            return '$' + Number(value).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        case 'number':
            return Number(value).toLocaleString('en-US');
        case 'percentage':
            return Number(value).toFixed(1) + '%';
        case 'text':
            return String(value);
        default:
            return String(value);
    }
}

// Format timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
    if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago';
    return Math.floor(diff / 86400000) + 'd ago';
}

// Check if KPI needs refresh
function needsRefresh(kpi) {
    if (!kpi.last_updated) return true;

    const lastUpdated = new Date(kpi.last_updated);
    const now = new Date();
    const diff = (now - lastUpdated) / 1000;

    return diff > kpi.refresh_interval;
}

// Refresh single KPI
async function refreshKPI(kpiId) {
    const card = document.querySelector(`[data-kpi-id="${kpiId}"]`);
    if (!card) return;

    // Show loading state
    const valueEl = card.querySelector('.kpi-value');
    const originalContent = valueEl.innerHTML;
    valueEl.innerHTML = '<div class="spinner" style="width: 30px; height: 30px;"></div>';

    try {
        const response = await fetch(`/api/kpis/${kpiId}/refresh`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to refresh KPI');

        const result = await response.json();

        // Update KPI in local array
        const kpiIndex = kpis.findIndex(k => k.id === kpiId);
        if (kpiIndex !== -1) {
            kpis[kpiIndex].last_value = result.value;
            kpis[kpiIndex].last_updated = result.updated;
        }

        // Re-render
        renderKPIs();
    } catch (error) {
        console.error('Error refreshing KPI:', error);
        valueEl.innerHTML = originalContent;
        showError(`Failed to refresh ${kpiId}`);
    }
}

// Refresh all KPIs
async function refreshAllKPIs() {
    const promises = kpis.map(kpi => refreshKPI(kpi.id));
    await Promise.all(promises);
}

// Show add KPI modal
function showAddKPIModal() {
    editingKPI = null;
    document.getElementById('modalTitle').textContent = 'Add New KPI';
    document.getElementById('kpiForm').reset();
    document.getElementById('kpiId').value = '';
    document.getElementById('templatesSection').style.display = 'block';
    document.getElementById('kpiModal').classList.add('show');
}

// Show edit KPI modal
function editKPI(kpiId) {
    const kpi = kpis.find(k => k.id === kpiId);
    if (!kpi) return;

    editingKPI = kpi;
    document.getElementById('modalTitle').textContent = 'Edit KPI';
    document.getElementById('kpiId').value = kpi.id;
    document.getElementById('kpiName').value = kpi.name;
    document.getElementById('kpiDescription').value = kpi.description;
    document.getElementById('kpiIcon').value = kpi.icon;
    document.getElementById('kpiColor').value = kpi.color;
    document.getElementById('kpiSize').value = kpi.size;
    document.getElementById('kpiQueryType').value = kpi.query_type;
    document.getElementById('kpiQuery').value = kpi.query;
    document.getElementById('kpiFormat').value = kpi.format;
    document.getElementById('kpiRefreshInterval').value = kpi.refresh_interval;
    document.getElementById('templatesSection').style.display = 'none';

    document.getElementById('kpiModal').classList.add('show');
    updateQueryHelp();
}

// Close KPI modal
function closeKPIModal() {
    document.getElementById('kpiModal').classList.remove('show');
    editingKPI = null;
}

// Setup form handler
function setupFormHandler() {
    document.getElementById('kpiForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const kpiId = document.getElementById('kpiId').value;
        const kpiData = {
            name: document.getElementById('kpiName').value,
            description: document.getElementById('kpiDescription').value,
            icon: document.getElementById('kpiIcon').value,
            color: document.getElementById('kpiColor').value,
            size: document.getElementById('kpiSize').value,
            query_type: document.getElementById('kpiQueryType').value,
            query: document.getElementById('kpiQuery').value,
            format: document.getElementById('kpiFormat').value,
            refresh_interval: parseInt(document.getElementById('kpiRefreshInterval').value)
        };

        try {
            let response;
            if (kpiId) {
                // Update existing KPI
                response = await fetch(`/api/kpis/${kpiId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(kpiData)
                });
            } else {
                // Create new KPI
                response = await fetch('/api/kpis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(kpiData)
                });
            }

            if (!response.ok) throw new Error('Failed to save KPI');

            closeKPIModal();
            loadKPIs();
        } catch (error) {
            console.error('Error saving KPI:', error);
            showError('Failed to save KPI');
        }
    });
}

// Delete KPI
async function deleteKPI(kpiId) {
    if (!confirm('Are you sure you want to delete this KPI?')) return;

    try {
        const response = await fetch(`/api/kpis/${kpiId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete KPI');

        loadKPIs();
    } catch (error) {
        console.error('Error deleting KPI:', error);
        showError('Failed to delete KPI');
    }
}

// Render templates
function renderTemplates() {
    const grid = document.getElementById('templatesGrid');

    grid.innerHTML = templates.map(template => `
        <div class="template-card" onclick='useTemplate(${JSON.stringify(template).replace(/'/g, "&apos;")})'>
            <div class="template-icon">${template.icon}</div>
            <div class="template-name">${template.name}</div>
            <div class="template-description">${template.description}</div>
        </div>
    `).join('');
}

// Use template
function useTemplate(template) {
    document.getElementById('kpiName').value = template.name;
    document.getElementById('kpiDescription').value = template.description;
    document.getElementById('kpiIcon').value = template.icon;
    document.getElementById('kpiColor').value = template.color;
    document.getElementById('kpiQueryType').value = template.query_type;
    document.getElementById('kpiQuery').value = template.query;
    document.getElementById('kpiFormat').value = template.format;

    updateQueryHelp();
}

// Update query help text
function updateQueryHelp() {
    const queryType = document.getElementById('kpiQueryType').value;
    const helpText = document.getElementById('queryHelp');

    switch (queryType) {
        case 'cur':
            helpText.textContent = 'Use {table} placeholder for CUR table name. Query should return a single value.';
            break;
        case 'cost_explorer':
            helpText.textContent = 'Enter the Cost Explorer function name (e.g., get_ri_coverage, get_anomalies_count).';
            break;
        case 'custom':
            helpText.textContent = 'Enter a custom function name that will be called to calculate this KPI.';
            break;
    }
}

// Show error message
function showError(message) {
    // Simple alert for now, can be enhanced with toast notifications
    alert(message);
}

// Close modal when clicking outside
document.getElementById('kpiModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'kpiModal') {
        closeKPIModal();
    }
});
