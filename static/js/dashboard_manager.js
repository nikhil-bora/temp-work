// Dashboard Management for Chat

function showCreateDashboardModal() {
    const modal = document.getElementById('dashboardModal');
    modal.style.display = 'flex';
}

function closeDashboardModal() {
    const modal = document.getElementById('dashboardModal');
    modal.style.display = 'none';
    document.getElementById('dashboardForm').reset();
}

async function submitDashboard(event) {
    event.preventDefault();

    const name = document.getElementById('dashboardName').value;
    const description = document.getElementById('dashboardDescription').value;

    try {
        const response = await fetch('/api/dashboards', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                description,
                conversation_id: currentConversationId
            })
        });

        if (!response.ok) {
            throw new Error('Failed to create dashboard');
        }

        const dashboard = await response.json();
        console.log('Dashboard created:', dashboard);

        // Close modal
        closeDashboardModal();

        // Show success message
        if (typeof addSystemMessage === 'function') {
            addSystemMessage(` Dashboard "${name}" created successfully!`);
        }

        // Open dashboard in new tab
        window.open(`/api/dashboard/${dashboard.id}/view`, '_blank');

    } catch (error) {
        console.error('Error creating dashboard:', error);
        alert('Failed to create dashboard. Please try again.');
    }
}
