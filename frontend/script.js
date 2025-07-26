document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('load-data-btn').addEventListener('click', loadAllData);
    document.getElementById('start-discovery-btn').addEventListener('click', startDiscovery);
    
    const modal = document.getElementById('swot-modal');
    const closeBtn = document.querySelector('.close-button');
    closeBtn.onclick = () => modal.style.display = "none";
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    };
    
    setInterval(loadAllData, 30000);
});

function setStatus(message, isError = false, duration = 5000) {
    const statusEl = document.getElementById('status-message');
    statusEl.textContent = message;
    statusEl.className = isError ? 'status-message error' : 'status-message success';
    setTimeout(() => {
        statusEl.textContent = '';
        statusEl.className = 'status-message';
    }, duration);
}

async function apiFetch(path, options = {}) {
    const baseUrl = document.getElementById('api-gateway-url').value.trim();
    const apiKey = document.getElementById('api-key').value.trim();
    if (!baseUrl || !apiKey) {
        throw new Error('API Gateway URL and API Key are required.'); [cite: 2422]
    }

    const headers = {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        ...options.headers,
    };

    const response = await fetch(`${baseUrl}${path}`, { ...options, headers });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.status} - ${errorText}`); [cite: 2425]
    }
    const contentType = response.headers.get("content-type");
    return contentType?.includes("application/json") ? response.json() : null;
}

async function startDiscovery() {
    if (!confirm('This will start the automated discovery pipeline. Proceed?')) return;
    setStatus('Starting discovery cycle...');
    try {
        await apiFetch('/start-discovery', { method: 'POST' });
        setStatus('Discovery cycle started successfully. New ideas will appear shortly.');
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function loadAllData() {
    const baseUrl = document.getElementById('api-gateway-url').value;
    if (!baseUrl) return; // Don't run if config is missing

    try {
        const [ideasData, apksData] = await Promise.all([
            apiFetch('/vetted-ideas'),
            apiFetch('/developed-apks')
        ]);
        const allIdeas = (ideasData?.ideas || []).concat(apksData?.apks || []);
        
        updateKpiOverview(allIdeas);
        renderIdeasTable(ideasData?.ideas || []);
        renderApksTable(apksData?.apks || []);
    } catch (error) {
        setStatus(error.message, true);
    }
}
// Additional UI rendering and action functions are in the holistic context file