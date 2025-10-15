// Custom Context Management

let selectedContextIds = [];

// Load contexts on page load
async function loadContexts() {
    try {
        const response = await fetch('/api/contexts');
        const contexts = await response.json();

        const contextList = document.getElementById('contextList');

        if (contexts.length === 0) {
            contextList.innerHTML = '<div style="font-size: 0.75rem; color: var(--text-secondary); padding: 0.5rem; text-align: center;">No contexts available</div>';
            return;
        }

        contextList.innerHTML = '';

        contexts.forEach(context => {
            const contextItem = document.createElement('div');
            contextItem.className = 'context-item';
            contextItem.style.cssText = `
                padding: 0.5rem;
                background: var(--bg-secondary);
                border-radius: 6px;
                margin-bottom: 0.5rem;
                cursor: pointer;
                border: 2px solid transparent;
                transition: all 0.2s;
            `;

            const isSelected = selectedContextIds.includes(context.id);
            if (isSelected) {
                contextItem.style.borderColor = 'var(--primary-blue)';
                contextItem.style.background = 'rgba(0, 85, 254, 0.08)';
            }

            const typeIcon = context.type === 'image' ? '🖼️ ' : '📄 ';

            contextItem.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="font-size: 0.8125rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem;">
                            ${isSelected ? '✓ ' : ''}${typeIcon}${escapeHtml(context.name)}
                        </div>
                        ${context.description ? `<div style="font-size: 0.6875rem; color: var(--text-secondary);">${escapeHtml(context.description)}</div>` : ''}
                        <div style="font-size: 0.625rem; color: var(--text-muted); margin-top: 0.25rem;">
                            ${context.type === 'image' ? 'Image • ' : ''}${formatBytes(context.size)}
                        </div>
                    </div>
                    <button onclick="event.stopPropagation(); deleteContext('${context.id}')" style="background: none; border: none; color: var(--accent-coral); cursor: pointer; font-size: 0.875rem; padding: 0.25rem;">
                        🗑️
                    </button>
                </div>
            `;

            contextItem.onclick = () => toggleContextSelection(context.id);
            contextList.appendChild(contextItem);
        });

    } catch (error) {
        console.error('Error loading contexts:', error);
    }
}

function toggleContextSelection(contextId) {
    const index = selectedContextIds.indexOf(contextId);
    if (index > -1) {
        selectedContextIds.splice(index, 1);
    } else {
        selectedContextIds.push(contextId);
    }
    loadContexts(); // Refresh display
    updateSelectedContextsBar(); // Update chat input bar
}

async function updateSelectedContextsBar() {
    const bar = document.getElementById('selectedContextsBar');
    const textEl = document.getElementById('selectedContextsText');

    if (selectedContextIds.length === 0) {
        bar.style.display = 'none';
        return;
    }

    try {
        const response = await fetch('/api/contexts');
        const allContexts = await response.json();

        const selectedNames = selectedContextIds
            .map(id => {
                const ctx = allContexts.find(c => c.id === id);
                return ctx ? ctx.name : null;
            })
            .filter(n => n);

        textEl.textContent = selectedNames.join(', ');
        bar.style.display = 'flex';
    } catch (error) {
        console.error('Error updating context bar:', error);
    }
}

function clearContextSelection() {
    selectedContextIds = [];
    loadContexts();
    updateSelectedContextsBar();
}

function showAddContextModal() {
    document.getElementById('contextModal').style.display = 'flex';
    switchTab('text'); // Default to text tab
}

function closeContextModal() {
    document.getElementById('contextModal').style.display = 'none';
    document.getElementById('contextForm').reset();
    document.getElementById('fileUploadForm').reset();
}

function switchTab(tab) {
    const textTab = document.getElementById('textTab');
    const fileTab = document.getElementById('fileTab');
    const contextForm = document.getElementById('contextForm');
    const fileUploadForm = document.getElementById('fileUploadForm');

    if (tab === 'text') {
        textTab.style.borderBottomColor = 'var(--primary-blue)';
        textTab.style.color = 'var(--primary-blue)';
        fileTab.style.borderBottomColor = 'transparent';
        fileTab.style.color = 'var(--text-secondary)';
        contextForm.style.display = 'block';
        fileUploadForm.style.display = 'none';
    } else {
        fileTab.style.borderBottomColor = 'var(--primary-blue)';
        fileTab.style.color = 'var(--primary-blue)';
        textTab.style.borderBottomColor = 'transparent';
        textTab.style.color = 'var(--text-secondary)';
        fileUploadForm.style.display = 'block';
        contextForm.style.display = 'none';
    }
}

async function submitContext(event) {
    event.preventDefault();

    const name = document.getElementById('contextName').value.trim();
    const description = document.getElementById('contextDescription').value.trim();
    const content = document.getElementById('contextContent').value.trim();

    if (!name || !content) {
        alert('Name and content are required');
        return;
    }

    try {
        const response = await fetch('/api/contexts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, description, content })
        });

        if (response.ok) {
            closeContextModal();
            loadContexts();
        } else {
            const error = await response.json();
            alert(`Error: ${error.error}`);
        }
    } catch (error) {
        console.error('Error creating context:', error);
        alert('Failed to create context');
    }
}

async function submitFileContext(event) {
    event.preventDefault();

    const fileInput = document.getElementById('contextFile');
    const name = document.getElementById('fileName').value.trim();
    const description = document.getElementById('fileDescription').value.trim();

    if (!fileInput.files || fileInput.files.length === 0) {
        alert('Please select a file');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);
    if (description) formData.append('description', description);

    try {
        const response = await fetch('/api/contexts/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            closeContextModal();
            loadContexts();
        } else {
            const error = await response.json();
            alert(`Error: ${error.error}`);
        }
    } catch (error) {
        console.error('Error uploading context file:', error);
        alert('Failed to upload context file');
    }
}

async function deleteContext(contextId) {
    if (!confirm('Are you sure you want to delete this context?')) {
        return;
    }

    try {
        const response = await fetch(`/api/contexts/${contextId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            // Remove from selected if it was selected
            const index = selectedContextIds.indexOf(contextId);
            if (index > -1) {
                selectedContextIds.splice(index, 1);
                updateSelectedContextsBar();
            }
            loadContexts();
        } else {
            alert('Failed to delete context');
        }
    } catch (error) {
        console.error('Error deleting context:', error);
        alert('Failed to delete context');
    }
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export selectedContextIds for use in app.js
window.getSelectedContextIds = () => selectedContextIds;

// Load contexts on page load
loadContexts();
