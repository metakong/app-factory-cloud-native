document.addEventListener('DOMContentLoaded', () => {
    // Initial setup
    document.getElementById('load-data-btn').addEventListener('click', loadAllData);
    document.getElementById('start-discovery-btn').addEventListener('click', startDiscovery);

    // Modal setup
    const modal = document.getElementById('swot-modal');
    const closeBtn = document.querySelector('.close-button');
    closeBtn.onclick = () => modal.style.display = "none";
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    };
    
    // Auto-refresh data every 30 seconds
    setInterval(loadAllData, 30000);
});

// --- API & State Management ---

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
        throw new Error('API Gateway URL and API Key are required.');
    }

    const headers = {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        ...options.headers,
    };

    const response = await fetch(`${baseUrl}${path}`, { ...options, headers });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.status} - ${errorText}`);
    }
    const contentType = response.headers.get("content-type");
    return contentType?.includes("application/json") ? response.json() : null;
}

// --- CORE ACTIONS ---

async function startDiscovery() {
    if (!confirm('This will start the automated discovery pipeline. Proceed?')) return;
    setStatus('Starting discovery cycle...');
    try {
        await apiFetch('/start-discovery', { method: 'POST' });
        setStatus('Discovery cycle started successfully. New ideas will appear shortly.');
    } catch (error) {
        setStatus(error.message, true);
        console.error('Error starting discovery cycle:', error);
    }
}

async function loadAllData() {
    const baseUrl = document.getElementById('api-gateway-url').value;
    if (!baseUrl) return; // Don't run if config is missing

    console.log("Refreshing dashboard data...");
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
        console.error('Error loading data:', error);
    }
}

// --- UI RENDERING ---

function openTab(evt, tabName) {
    document.querySelectorAll(".tab-content").forEach(tc => tc.style.display = "none");
    document.querySelectorAll(".tab-link").forEach(tl => tl.classList.remove("active"));
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.classList.add("active");
}

function updateKpiOverview(allIdeas) {
    const funnelData = {
        'PENDING_VETTING': 0,
        'PENDING_CEO_APPROVAL': 0,
        'PENDING_BUILD': 0,
        'PUBLISHED': 0,
    };

    allIdeas.forEach(idea => {
        if (funnelData.hasOwnProperty(idea.status)) {
            funnelData[idea.status]++;
        }
    });

    const chartOptions = {
        chart: { type: 'bar', height: 350, toolbar: { show: false } },
        series: [{ name: 'Ideas', data: Object.values(funnelData) }],
        xaxis: { categories: Object.keys(funnelData), labels: { style: { colors: '#e0e0e0' }}},
        yaxis: { labels: { style: { colors: '#e0e0e0' }}},
        grid: { borderColor: '#38383a' },
        plotOptions: { bar: { horizontal: false, columnWidth: '50%', distributed: true } },
        legend: { show: false }
    };
    
    const chartContainer = document.querySelector("#funnel-chart");
    chartContainer.innerHTML = ''; // Clear previous chart
    const chart = new ApexCharts(chartContainer, chartOptions);
    chart.render();
}

function renderIdeasTable(ideas) {
    const tableBody = document.querySelector('#ideas-table tbody');
    tableBody.innerHTML = '';
    if (ideas.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7">No ideas are currently awaiting review.</td></tr>';
        return;
    }
    ideas.forEach(idea => {
        const encodedSwot = btoa(idea.product_spec_and_swot || 'No product brief available.');
        tableBody.innerHTML += `
            <tr>
                <td><span class="status-indicator status-${idea.status}"></span>${idea.status}</td>
                <td>${idea.description}</td>
                <td>${idea.source_subreddit || 'N/A'}</td>
                <td>${idea.community_validation_score || 'N/A'}</td>
                <td>${(idea.competition_score !== undefined ? idea.competition_score.toFixed(2) : 'N/A')} / 10</td>
                <td><button onclick="showSwotModal('${encodedSwot}')">View Brief</button></td>
                <td class="actions">
                    <button onclick="approveIdea('${idea.idea_id}')">Approve</button>
                    <button class="reject" onclick="rejectIdea('${idea.idea_id}')">Reject</button>
                </td>
            </tr>`;
    });
}

function renderApksTable(apks) {
    const tableBody = document.querySelector('#apks-table tbody');
    tableBody.innerHTML = '';
    if (apks.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7">No apps are published or in development.</td></tr>';
        return;
    }
    apks.forEach(apk => {
        tableBody.innerHTML += `
            <tr>
                <td><span class="status-indicator status-${apk.status}"></span>${apk.status}</td>
                <td>${apk.description || apk.idea_id}</td>
                <td>${apk.downloads || 'N/A'}</td>
                <td>${apk.rating || 'N/A'}</td>
                <td>${apk.revenue || '$0.00'}</td>
                <td class="actions">
                    ${apk.apk_download_url ? `<a href="${apk.apk_download_url}" target="_blank" class="button-link">Test APK</a>` : ''}
                    ${apk.repo_url ? `<a href="${apk.repo_url}" target="_blank" class="button-link">Repo</a>` : ''}
                </td>
                <td class="actions">
                    ${apk.status === 'PENDING_CEO_TESTING' ? `
                        <button onclick="publishApk('${apk.idea_id}')">Publish</button>
                        <button class="revise" onclick="reviseApk('${apk.idea_id}')">Revise</button>
                    ` : 'No actions'}
                </td>
            </tr>`;
    });
}

function showSwotModal(encodedSwot) {
    const swotText = atob(encodedSwot);
    document.getElementById('swot-text').textContent = swotText;
    document.getElementById('swot-modal').style.display = 'block';
}


// --- BUTTON ACTIONS (APPROVE, REJECT, ETC.) ---

async function approveIdea(ideaId) {
    if (!confirm(`Approve idea ${ideaId} for development?`)) return;
    setStatus(`Approving ${ideaId}...`);
    try {
        await apiFetch('/approve-idea', { method: 'POST', body: JSON.stringify({ idea_id: ideaId }) });
        setStatus(`Idea ${ideaId} approved and sent for development.`);
        loadAllData();
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function rejectIdea(ideaId) {
    if (!confirm(`Are you sure you want to reject idea ${ideaId}?`)) return;
    setStatus(`Rejecting ${ideaId}...`);
    try {
        await apiFetch('/reject-idea', { method: 'POST', body: JSON.stringify({ idea_id: ideaId }) });
        setStatus(`Idea ${ideaId} rejected.`);
        loadAllData();
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function publishApk(ideaId) {
    if (!confirm(`Publish the app for idea ${ideaId}? This will send it to the internal test track on the Play Store.`)) return;
    setStatus(`Publishing app for ${ideaId}...`);
    try {
        await apiFetch('/publish-app', { method: 'POST', body: JSON.stringify({ idea_id: ideaId }) });
        setStatus(`App for idea ${ideaId} sent for publishing.`);
        loadAllData();
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function reviseApk(ideaId) {
    const feedback = prompt(`Please provide concise revision feedback for app ${ideaId}:`);
    if (feedback?.trim()) {
        setStatus(`Requesting revision for ${ideaId}...`);
        try {
            await apiFetch('/revise-apk', { method: 'POST', body: JSON.stringify({ idea_id: ideaId, feedback: feedback }) });
            setStatus(`Revision requested for app ${ideaId}.`);
            loadAllData();
        } catch(error) {
            setStatus(error.message, true);
        }
    }
}