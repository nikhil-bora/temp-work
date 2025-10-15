// FinOps Agent - Frontend JavaScript

let ws = null;
let conversationHistory = [];
let currentConversationId = null;  // Track current conversation for isolation
let sessionId = 'session_' + Date.now();  // Unique session ID per browser tab
let activeToolExecutions = {};  // Track active tool executions to update them properly

console.log('[INIT] FinOps Agent starting...');
console.log('[INIT] Session ID:', sessionId);

// Initialize WebSocket connection
function initWebSocket() {
    console.log('[WS] Initializing WebSocket connection...');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    console.log('[WS] Connecting to:', wsUrl);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('[WS] ✓ WebSocket connected successfully');
    };

    ws.onmessage = (event) => {
        console.log('[WS] Message received:', event.data);
        const data = JSON.parse(event.data);
        console.log('[WS] Parsed data:', data);
        handleAgentResponse(data);
    };

    ws.onerror = (error) => {
        console.error('[WS] ✗ WebSocket error:', error);
        addSystemMessage('Connection error. Please refresh the page.');
    };

    ws.onclose = () => {
        console.log('[WS] Connection closed. Reconnecting in 3 seconds...');
        setTimeout(initWebSocket, 3000); // Reconnect after 3 seconds
    };
}

// Send message to agent
async function sendMessage() {
    console.log('[CHAT] sendMessage() called');
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    console.log('[CHAT] Message:', message);

    if (!message) {
        console.log('[CHAT] Empty message, ignoring');
        return;
    }

    // If starting a new conversation (no currentConversationId), clear the chat first
    if (!currentConversationId) {
        console.log('[CHAT] No active conversation - clearing chat window');
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.innerHTML = '';
    }

    // Hide welcome screen
    const welcomeScreen = document.getElementById('welcomeScreen');
    if (welcomeScreen) {
        console.log('[CHAT] Hiding welcome screen');
        welcomeScreen.remove();
    }

    // Add user message to chat
    console.log('[CHAT] Adding user message to UI');
    addMessage('user', message);
    input.value = '';
    input.style.height = 'auto';

    // Disable send button
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    sendBtn.textContent = 'Thinking...';

    try {
        // Send to backend via HTTP POST with conversation ID
        console.log('[API] Sending POST request to /api/chat');
        console.log('[API] Conversation ID:', currentConversationId);
        console.log('[API] Session ID:', sessionId);

        // Get selected context IDs
        const contextIds = window.getSelectedContextIds ? window.getSelectedContextIds() : [];
        console.log('[API] Selected context IDs:', contextIds);

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message,
                conversation_id: currentConversationId,
                session_id: sessionId,
                context_ids: contextIds
            })
        });

        console.log('[API] Response status:', response.status);

        if (!response.ok) {
            throw new Error('Failed to send message');
        }

        const data = await response.json();
        console.log('[API] Response data:', data);

        // Store conversation ID for this conversation
        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
            console.log('[CHAT] ✓ Using conversation:', currentConversationId);
            updateConversationIdDisplay();
        }

        console.log('[CHAT] Waiting for WebSocket response...');
        // Response will come via WebSocket
    } catch (error) {
        console.error('[CHAT] ✗ Error:', error);
        addSystemMessage('Error sending message. Please try again.');
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
    }
}

// Handle agent response
function handleAgentResponse(data) {
    console.log('[RESPONSE] handleAgentResponse() called');
    console.log('[RESPONSE] Data type:', data.type);
    console.log('[RESPONSE] Message conversation_id:', data.conversation_id);
    console.log('[RESPONSE] Current conversation_id:', currentConversationId);

    // Filter out messages from other conversations
    if (data.conversation_id && currentConversationId && data.conversation_id !== currentConversationId) {
        console.log('[RESPONSE] ⚠ Ignoring message from different conversation');
        console.log('[RESPONSE] Message is for:', data.conversation_id);
        console.log('[RESPONSE] Current conversation:', currentConversationId);
        return;
    }

    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = false;
    sendBtn.textContent = 'Send';

    if (data.type === 'tool_call') {
        console.log('[TOOL] Tool call detected:', data.tool_name, 'Status:', data.status);
        // Show tool execution
        addToolExecution(data.tool_name, data.status, data.result);
    } else if (data.type === 'text_response') {
        console.log('[RESPONSE] Text response received, length:', data.content.length);
        // Show agent text response
        addMessage('agent', data.content);
    } else if (data.type === 'error') {
        console.error('[RESPONSE] ✗ Error received:', data.message);
        addSystemMessage(`Error: ${data.message}`);
    } else if (data.type === 'complete') {
        // Conversation turn complete
        console.log('[RESPONSE] ✓ Agent response complete');
    } else {
        console.warn('[RESPONSE] Unknown message type:', data.type);
    }
}

// Add message to chat
function addMessage(role, content) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = role === 'user' ? 'U' : 'AI';
    const author = role === 'user' ? 'You' : 'FinOps Agent';
    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-author">${author}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-text">${formatMessage(content)}</div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    conversationHistory.push({ role, content, time });
}

// Add system message
function addSystemMessage(content) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-text" style="color: var(--text-muted); font-style: italic;">
                ${content}
            </div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add tool execution indicator
function addToolExecution(toolName, status, result) {
    console.log('[TOOL] addToolExecution():', toolName, status);

    const messagesContainer = document.getElementById('chatMessages');

    // Check if this is a chart creation
    if (toolName === 'create_visualization' && status === 'completed' && result) {
        console.log('[TOOL] Chart creation detected');
        try {
            const chartData = typeof result === 'string' ? JSON.parse(result) : result;
            console.log('[TOOL] Chart data:', chartData);
            if (chartData.url || chartData.filename) {
                console.log('[TOOL] Adding chart message to UI');
                addChartMessage(chartData);
                // Remove the spinner for this tool if it exists
                if (activeToolExecutions[toolName]) {
                    console.log('[TOOL] Removing spinner for', toolName);
                    const existingDiv = document.getElementById(activeToolExecutions[toolName]);
                    if (existingDiv) {
                        existingDiv.remove();
                    }
                    delete activeToolExecutions[toolName];
                }
                return;
            }
        } catch (e) {
            console.error('[TOOL] ✗ Error parsing chart data:', e);
        }
    }

    let toolDiv;

    if (status === 'started') {
        console.log('[TOOL] Creating tool execution indicator');
        // Create new tool execution div
        const toolId = `tool-${toolName}-${Date.now()}`;
        console.log('[TOOL] Tool ID:', toolId);

        toolDiv = document.createElement('div');
        toolDiv.className = 'tool-execution';
        toolDiv.id = toolId;
        toolDiv.innerHTML = `
            <div class="tool-header">
                <div class="tool-spinner"></div>
                <span>Executing: ${formatToolName(toolName)}</span>
            </div>
        `;
        messagesContainer.appendChild(toolDiv);

        // Track this tool execution
        activeToolExecutions[toolName] = toolId;
        console.log('[TOOL] Active tool executions:', Object.keys(activeToolExecutions));
    } else {
        console.log('[TOOL] Updating existing tool execution');
        // Find existing tool execution div
        if (activeToolExecutions[toolName]) {
            const existingId = activeToolExecutions[toolName];
            console.log('[TOOL] Found active execution ID:', existingId);
            toolDiv = document.getElementById(existingId);
        }

        // If not found, create a new one (shouldn't happen but safety net)
        if (!toolDiv) {
            console.warn('[TOOL] ⚠️  Tool div not found, creating new one');
            const toolId = `tool-${toolName}-${Date.now()}`;
            toolDiv = document.createElement('div');
            toolDiv.className = 'tool-execution';
            toolDiv.id = toolId;
            messagesContainer.appendChild(toolDiv);
        }

        // Update the content based on status
        if (status === 'completed') {
            console.log('[TOOL] ✓ Tool completed:', toolName);
            toolDiv.innerHTML = `
                <div class="tool-header">
                    <span>✓ ${formatToolName(toolName)}</span>
                </div>
                <div class="tool-result">${formatToolResult(result)}</div>
            `;
            // Remove from active tracking
            delete activeToolExecutions[toolName];
            console.log('[TOOL] Removed from active tracking. Remaining:', Object.keys(activeToolExecutions));
        } else if (status === 'error') {
            console.error('[TOOL] ✗ Tool failed:', toolName);
            toolDiv.innerHTML = `
                <div class="tool-header" style="color: var(--accent-coral);">
                    <span>✗ ${formatToolName(toolName)} failed</span>
                </div>
                <div class="tool-result" style="color: var(--accent-coral);">${result}</div>
            `;
            // Remove from active tracking
            delete activeToolExecutions[toolName];
        }
    }

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Format message content (markdown-like)
function formatMessage(content) {
    // Basic markdown formatting
    content = content.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
    content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    content = content.replace(/\n/g, '<br>');
    return content;
}

// Format tool name
function formatToolName(toolName) {
    return toolName
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

// Format tool result
function formatToolResult(result) {
    if (typeof result === 'string' && result.length > 200) {
        return result.substring(0, 200) + '... (truncated)';
    }
    return result;
}

// Send quick query
function sendQuickQuery(query) {
    const input = document.getElementById('chatInput');
    input.value = query;
    sendMessage();
}

// Start a new conversation (no confirmation needed)
function clearHistory() {
    // Clear UI
    conversationHistory = [];
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = `
        <div class="welcome-screen" id="welcomeScreen">
            <div class="welcome-icon">💰</div>
            <h1 class="welcome-title">Welcome to FinOps Agent</h1>
            <p class="welcome-subtitle">Ask me anything about your AWS costs and usage</p>

            <div class="example-queries">
                <div class="example-query" onclick="sendQuickQuery('What were my top 5 services by cost last month?')">
                    What were my top 5 services by cost last month?
                </div>
                <div class="example-query" onclick="sendQuickQuery('Show me EC2 costs grouped by instance type')">
                    Show me EC2 costs grouped by instance type
                </div>
                <div class="example-query" onclick="sendQuickQuery('Find underutilized instances and calculate savings')">
                    Find underutilized instances and calculate savings
                </div>
                <div class="example-query" onclick="sendQuickQuery('Analyze costs by tags')">
                    Analyze costs by tags
                </div>
            </div>
        </div>
    `;

    // Create new conversation on backend
    fetch('/api/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
    })
    .then(res => res.json())
    .then(data => {
        // Start a brand new conversation (complete isolation)
        currentConversationId = data.conversation_id;
        console.log('Started new conversation:', currentConversationId);
        updateConversationIdDisplay();

        // Show brief success message
        addSystemMessage('✨ New conversation started');
    })
    .catch(error => {
        console.error('Error starting new conversation:', error);
        addSystemMessage('Failed to start new conversation');
    });
}

// Add chart message with inline preview
function addChartMessage(chartData) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message chart';

    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const chartUrl = chartData.url || `/charts/${chartData.filename}`;

    messageDiv.innerHTML = `
        <div class="message-avatar">📊</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-author">Chart Created</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="chart-preview-container">
                <div class="chart-info">
                    <div class="chart-title">${chartData.title || 'Visualization'}</div>
                    ${chartData.description ? `<div class="chart-description">${chartData.description}</div>` : ''}
                </div>
                <div class="chart-iframe-wrapper">
                    <iframe src="${chartUrl}" class="chart-iframe" frameborder="0"></iframe>
                </div>
                <div class="chart-actions">
                    <button onclick="window.open('${chartUrl}', '_blank')" class="btn-chart-action">
                        🔍 Open Full Size
                    </button>
                    <button onclick="window.open('/api/charts-page', '_blank')" class="btn-chart-action">
                        📊 View All Charts
                    </button>
                </div>
            </div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Handle Enter key
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Load a conversation from history
async function loadConversation(conversationId) {
    try {
        // Fetch conversation from backend
        const response = await fetch(`/api/conversations/${conversationId}`);
        if (!response.ok) {
            throw new Error('Failed to load conversation');
        }

        const conversation = await response.json();

        // Clear current chat
        conversationHistory = [];
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.innerHTML = '';

        // Remove welcome screen if present
        const welcomeScreen = document.getElementById('welcomeScreen');
        if (welcomeScreen) {
            welcomeScreen.remove();
        }

        // Set as current conversation
        currentConversationId = conversationId;
        updateConversationIdDisplay();

        // Load all messages into chat UI
        conversation.messages.forEach(msg => {
            if (msg.role === 'user') {
                addMessage('user', msg.content);
            } else if (msg.role === 'assistant') {
                addMessage('agent', msg.content);
            } else if (msg.role === 'tool') {
                // Check if this is a chart creation tool
                if (msg.tool_name === 'create_visualization') {
                    try {
                        // Parse chart data from tool output
                        let chartData;
                        if (typeof msg.tool_output === 'string') {
                            chartData = JSON.parse(msg.tool_output);
                        } else {
                            chartData = msg.tool_output;
                        }

                        // Display chart if we have the data
                        if (chartData && (chartData.url || chartData.filename)) {
                            addChartMessage(chartData);
                        } else {
                            // Fallback to regular tool display
                            addToolExecution(msg.tool_name, 'completed', msg.tool_output);
                        }
                    } catch (e) {
                        console.error('Error parsing chart data:', e);
                        // Fallback to regular tool display
                        addToolExecution(msg.tool_name, 'completed', msg.tool_output);
                    }
                } else {
                    // Regular tool execution display
                    addToolExecution(msg.tool_name, 'completed', msg.tool_output);
                }
            }
        });

        console.log('Loaded conversation:', conversationId);
        return true;
    } catch (error) {
        console.error('Error loading conversation:', error);
        addSystemMessage('Failed to load conversation. Please try again.');
        return false;
    }
}

// Update conversation ID display in sidebar
function updateConversationIdDisplay() {
    const display = document.getElementById('conversationIdDisplay');
    const dashboardBtn = document.getElementById('createDashboardBtn');

    if (display) {
        if (currentConversationId) {
            // Show shortened ID for better UX
            const shortId = currentConversationId.replace('conv_', '');
            display.textContent = shortId;
            display.title = currentConversationId;  // Full ID on hover

            // Enable dashboard button
            if (dashboardBtn) {
                dashboardBtn.disabled = false;
            }
        } else {
            display.textContent = 'Not started';

            // Disable dashboard button
            if (dashboardBtn) {
                dashboardBtn.disabled = true;
            }
        }
    }
}

// Auto-resize textarea
document.getElementById('chatInput')?.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

// Check URL for conversation ID to load
function checkForConversationInURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const conversationId = urlParams.get('conversation_id');

    if (conversationId) {
        // Load the conversation
        loadConversation(conversationId);

        // Clean up URL without page reload
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    document.getElementById('chatInput').focus();
    updateConversationIdDisplay();

    // Check if we should load a specific conversation
    checkForConversationInURL();
});
