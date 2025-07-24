document.addEventListener('DOMContentLoaded', () => {
    const loadDataBtn = document.getElementById('load-data-btn');
    loadDataBtn.addEventListener('click', loadAllData);
});

function openTab(evt, tabName) {
    let i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tab-link");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

function setStatus(message, isError = false) {
    const statusEl = document.getElementById('status-message');
    statusEl.textContent = message;
    statusEl.className = isError ? 'status-message error' : 'status-message success';
    statusEl.style.display = 'block';
}

async function apiFetch(path, options = {}) {
     const baseUrl = document.getElementById('api-gateway-url').value.trim();
    const apiKey = document.getElementById('api-key').value.trim();

    if (!baseUrl || !apiKey) {
        const message = 'Please provide API Gateway URL and API Key.';
        setStatus(message, true);
        throw new Error(message);
    }

    const headers = {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        ...options.headers,
    };

    try {
        const response = await fetch(`${baseUrl}${path}`, { ...options, headers });
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Request failed: ${response.status} ${response.statusText} - ${errorText}`);
        }
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            return response.json();
        }
        return; 
    } catch (error) {
        console.error('API Fetch Error:', error);
        setStatus(error.message, true);
        throw error;
    }
}

async function loadAllData() {
    setStatus('Loading data...', false);
    await fetchVettedIdeas();
    await fetchDevelopedApks();
    setStatus('Data loaded successfully.', false);
}

async function fetchVettedIdeas() {
    try {
        const data = await apiFetch('/vetted-ideas');
        const ideas = data.ideas || [];
        const tableBody = document.querySelector('#ideas-table tbody');
        tableBody.innerHTML = '';
        if (ideas.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5">No ideas are currently awaiting review.</td></tr>';
            return;
        }
        ideas.forEach(idea => {
            // Base64 encode the SWOT analysis to safely pass it in the onclick handler
            const encodedSwot = btoa(idea.product_spec_and_swot || 'No SWOT analysis available.');
            const row = `<tr>
                <td>${idea.idea_id}</td>
                <td>${idea.description}</td>
                <td>${idea.competition_score !== undefined ? idea.competition_score.toFixed(2) : 'N/A'} / 10.00</td>
                <td><button onclick="showSwot('${encodedSwot}')">View SWOT</button></td>
                <td class="actions">
                    <button onclick="approveIdea('${idea.idea_id}')">Approve</button>
                    <button class="reject" onclick="rejectIdea('${idea.idea_id}')">Reject</button>
                </td>
            </tr>`;
            tableBody.innerHTML += row;
        });
    } catch (error) {
        console.error('Error fetching vetted ideas:', error);
    }
}

// New function to display the SWOT analysis
function showSwot(encodedSwot) {
    // Decode the Base64 string and show it in an alert
    const swotText = atob(encodedSwot);
    alert(swotText);
}

async function fetchDevelopedApks() {
    try {
        const data = await apiFetch('/developed-apks');
        const apks = data.apks || [];
        const tableBody = document.querySelector('#apks-table tbody');
        tableBody.innerHTML = '';
        if (apks.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4">No APKs are currently awaiting review.</td></tr>';
            return;
        }
        apks.forEach(apk => {
            const row = `<tr>
                <td>${apk.idea_id}</td>
                <td>${apk.ceo_feedback || 'N/A'}</td>
                <td><a href="${apk.apk_download_url}" target="_blank" rel="noopener noreferrer">Download APK</a></td>
                <td class="actions">
                    <button onclick="publishApk('${apk.idea_id}')">Publish</button>
                    <button class="revise" onclick="reviseApk('${apk.idea_id}')">Revise</button>
                </td>
            </tr>`;
            tableBody.innerHTML += row;
        });
    } catch (error) {
        console.error('Error fetching developed APKs:', error);
    }
}

async function approveIdea(ideaId) {
    if (!confirm(`Are you sure you want to approve idea ${ideaId} for development?`)) return;
    setStatus(`Approving ${ideaId}...`, false);
    await apiFetch('/approve-idea', { method: 'POST', body: JSON.stringify({ idea_id: ideaId }) });
    setStatus(`Idea ${ideaId} approved and sent for development.`, false);
    fetchVettedIdeas();
}

async function rejectIdea(ideaId) {
    if (!confirm(`Are you sure you want to reject idea ${ideaId}?`)) return;
    setStatus(`Rejecting ${ideaId}...`, false);
    await apiFetch('/reject-idea', { method: 'POST', body: JSON.stringify({ idea_id: ideaId }) });
    setStatus(`Idea ${ideaId} rejected.`, false);
    fetchVettedIdeas();
}

async function publishApk(ideaId) {
    if (!confirm(`Are you sure you want to publish the app for idea ${ideaId}?`)) return;
    setStatus(`Publishing app for ${ideaId}...`, false);
    await apiFetch('/publish-app', { method: 'POST', body: JSON.stringify({ idea_id: ideaId }) });
    setStatus(`App for idea ${ideaId} sent for publishing.`, false);
    fetchDevelopedApks();
}

async function reviseApk(ideaId) {
    const feedback = prompt(`Please provide revision feedback for app ${ideaId}:`);
    if (feedback && feedback.trim() !== '') {
        setStatus(`Requesting revision for ${ideaId}...`, false);
        await apiFetch('/revise-apk', { method: 'POST', body: JSON.stringify({ idea_id: ideaId, feedback: feedback }) });
        setStatus(`Revision requested for app ${ideaId}.`, false);
        fetchDevelopedApks();
    }
}