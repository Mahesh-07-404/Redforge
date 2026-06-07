// RedForge Web Dashboard Application Logic

let socket = null;
let activeSessionId = null;
let currentAgentMessageElement = null;
let currentAgentMessageBody = null;
let isRunningAgent = false;

// DOM Elements
const wsDot = document.getElementById('ws-dot');
const wsStatusText = document.getElementById('ws-status-text');
const sessionList = document.getElementById('session-list');
const toolStatusList = document.getElementById('tool-status-list');
const headerSessionTitle = document.getElementById('header-session-title');
const headerAutonomyBadge = document.getElementById('header-autonomy-badge');
const headerTargetBadge = document.getElementById('header-target-badge');

const statSessions = document.getElementById('stat-sessions');
const statCritical = document.getElementById('stat-critical');
const statHigh = document.getElementById('stat-high');
const statFindings = document.getElementById('stat-findings');

const chatHistory = document.getElementById('chat-history');
const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');

const findingsList = document.getElementById('findings-list');
const findingsCount = document.getElementById('findings-count');

// Modal Elements
const modalOverlay = document.getElementById('modal-overlay');
const btnNewSession = document.getElementById('btn-new-session');
const btnModalClose = document.getElementById('btn-modal-close');
const btnCancelSession = document.getElementById('btn-cancel-session');
const btnStartSession = document.getElementById('btn-start-session');
const sessionModeInput = document.getElementById('session-mode');
const sessionTargetInput = document.getElementById('session-target');
const sessionAutonomyInput = document.getElementById('session-autonomy');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
    loadSessions();
    loadStats();
    loadToolsStatus();
    
    // Poll stats and tools status every 10 seconds
    setInterval(loadStats, 10000);
    setInterval(loadToolsStatus, 15000);
    
    // Modal Event Listeners
    btnNewSession.addEventListener('click', () => modalOverlay.classList.add('open'));
    btnModalClose.addEventListener('click', closeModal);
    btnCancelSession.addEventListener('click', closeModal);
    btnStartSession.addEventListener('click', createNewSession);
    
    // Chat Event Listeners
    btnSend.addEventListener('click', sendUserMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendUserMessage();
    });
});

function closeModal() {
    modalOverlay.classList.remove('open');
    sessionTargetInput.value = '';
}

// WebSocket Connection
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    wsStatusText.innerText = 'Connecting...';
    wsDot.className = 'ws-dot';
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
        console.log('WebSocket connection established.');
        wsStatusText.innerText = 'Connected';
        wsDot.classList.add('connected');
        
        // Subscribe to events
        socket.send(JSON.stringify({
            type: 'subscribe',
            events: ['chat', 'findings', 'command']
        }));
    };
    
    socket.onclose = () => {
        console.log('WebSocket connection closed. Retrying in 3 seconds...');
        wsStatusText.innerText = 'Disconnected';
        wsDot.className = 'ws-dot';
        setTimeout(connectWebSocket, 3000);
    };
    
    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleServerMessage(data);
    };
}

// Handle incoming websocket events
function handleServerMessage(data) {
    console.log('WS Event received:', data);
    
    switch(data.type) {
        case 'connected':
            console.log('Registered with session welcome token:', data.session_id);
            break;
            
        case 'session_created':
            closeModal();
            loadSessions().then(() => {
                selectSession(data.session.id);
            });
            break;
            
        case 'user_message':
            if (data.session_id === activeSessionId) {
                appendUserMessage(data.content);
                // Clear active running message elements
                currentAgentMessageElement = null;
                currentAgentMessageBody = null;
                isRunningAgent = true;
                setChatControlsState(true); // Disable inputs while thinking
            }
            break;
            
        case 'token':
            if (data.session_id === activeSessionId) {
                streamAgentToken(data.content);
            }
            break;
            
        case 'agent_message':
            if (data.session_id === activeSessionId) {
                finalizeAgentMessage(data.content);
                isRunningAgent = false;
                setChatControlsState(false);
            }
            break;
            
        case 'tool_start':
            if (data.session_id === activeSessionId) {
                appendToolExecution(data.call_id, data.tool, data.command);
            }
            break;
            
        case 'tool_end':
            if (data.session_id === activeSessionId) {
                updateToolExecution(data.call_id, data.success, data.result, data.error);
            }
            break;
            
        case 'finding_created':
            loadStats();
            if (activeSessionId) {
                loadFindings(activeSessionId);
            }
            break;
            
        case 'confirmation_required':
            if (data.session_id === activeSessionId) {
                appendConfirmationRequest(data.message, data.tool_calls);
                isRunningAgent = false;
                setChatControlsState(true); // Disable manual chat input, force approval button
            }
            break;
            
        case 'run_end':
            if (data.session_id === activeSessionId) {
                isRunningAgent = false;
                setChatControlsState(false);
            }
            break;
            
        case 'error':
            if (data.session_id === activeSessionId) {
                appendErrorMessage(data.message);
                isRunningAgent = false;
                setChatControlsState(false);
            }
            break;
    }
}

// REST Requests
async function loadSessions() {
    try {
        const response = await fetch('/sessions');
        const data = await response.json();
        
        sessionList.innerHTML = '';
        
        if (data.sessions.length === 0) {
            sessionList.innerHTML = '<div class="no-findings" style="padding: 10px; font-size: 0.8rem;">No active sessions</div>';
            return;
        }
        
        data.sessions.forEach(session => {
            const item = document.createElement('div');
            item.className = `session-item ${session.id === activeSessionId ? 'active' : ''}`;
            item.dataset.id = session.id;
            
            const truncatedTarget = session.metadata.target ? session.metadata.target : 'No target';
            
            item.innerHTML = `
                <div class="session-header-row">
                    <span class="session-mode-badge ${session.mode}">${session.mode}</span>
                    <span class="session-date">${formatTime(session.created_at)}</span>
                </div>
                <div class="session-target" title="${truncatedTarget}">${truncatedTarget}</div>
            `;
            
            item.addEventListener('click', () => selectSession(session.id));
            sessionList.appendChild(item);
        });
    } catch (e) {
        console.error('Failed to load sessions:', e);
    }
}

async function loadStats() {
    try {
        const response = await fetch('/stats');
        const data = await response.json();
        
        statSessions.innerText = data.total_sessions;
        statCritical.innerText = data.findings_by_severity.critical + data.findings_by_severity.high;
        statHigh.innerText = data.findings_by_severity.medium;
        statFindings.innerText = data.total_findings;
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

async function loadToolsStatus() {
    try {
        const response = await fetch('/tools');
        const data = await response.json();
        
        toolStatusList.innerHTML = '';
        
        Object.keys(data).forEach(tool => {
            const toolInfo = data[tool];
            const item = document.createElement('div');
            item.className = 'tool-status-item';
            
            item.innerHTML = `
                <div class="tool-info">
                    <div class="tool-status-indicator ${toolInfo.available ? 'online' : 'offline'}"></div>
                    <span class="tool-name">${tool}</span>
                </div>
                <span class="tool-version" title="${toolInfo.path}">${toolInfo.version !== 'Unknown' ? toolInfo.version.substring(0, 12) : 'active'}</span>
            `;
            toolStatusList.appendChild(item);
        });
    } catch (e) {
        console.error('Failed to load tools status:', e);
    }
}

async function selectSession(sessionId) {
    activeSessionId = sessionId;
    
    // Update active visual state in sidebar
    document.querySelectorAll('.session-item').forEach(item => {
        if (item.dataset.id === sessionId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // Fetch session details
    try {
        const res = await fetch(`/sessions/${sessionId}`);
        const session = await res.json();
        
        // Update header info
        headerSessionTitle.innerText = `${session.mode.toUpperCase()} Pentest Session`;
        
        headerAutonomyBadge.style.display = 'inline-block';
        headerAutonomyBadge.innerText = `Autonomy: ${session.metadata.autonomy.toUpperCase()}`;
        
        headerTargetBadge.style.display = 'inline-block';
        headerTargetBadge.innerText = `Target: ${session.metadata.target || 'None'}`;
        
        // Enable controls
        setChatControlsState(false);
        
        // Load messages history
        loadMessages(sessionId);
        
        // Load findings
        loadFindings(sessionId);
        
    } catch (e) {
        console.error('Failed to select session:', e);
    }
}

async function loadMessages(sessionId) {
    try {
        const res = await fetch(`/sessions/${sessionId}/messages`);
        const data = await res.json();
        
        chatHistory.innerHTML = '';
        
        if (data.messages.length === 0) {
            chatHistory.innerHTML = `
                <div class="no-findings" style="height: 100%;">
                    <div class="no-findings-icon">🚀</div>
                    <div style="font-weight: 600; color: var(--text-primary);">Agent Ready</div>
                    <div style="font-size: 0.85rem;">Send an instruction below (e.g. "Run port scanning") to kick off the pentest workflow.</div>
                </div>
            `;
            return;
        }
        
        data.messages.forEach(msg => {
            if (msg.role === 'user') {
                appendUserMessage(msg.content);
            } else if (msg.role === 'assistant') {
                // If it's a final assistant message, add it
                appendAgentMessage(msg.content);
            }
        });
        
        scrollToBottom();
    } catch (e) {
        console.error('Failed to load messages:', e);
    }
}

async function loadFindings(sessionId) {
    try {
        const res = await fetch(`/findings?target=${encodeURIComponent(sessionTargetInput.value)}`);
        const data = await res.json();
        
        findingsList.innerHTML = '';
        findingsCount.innerText = data.findings.length;
        
        if (data.findings.length === 0) {
            findingsList.innerHTML = `
                <div class="no-findings">
                    <div class="no-findings-icon">🛡️</div>
                    <div style="font-weight: 600; color: var(--text-primary);">No Findings Yet</div>
                    <div style="font-size: 0.85rem;">Discovered vulnerabilities will appear here in real-time.</div>
                </div>
            `;
            return;
        }
        
        data.findings.forEach(finding => {
            const card = document.createElement('div');
            card.className = 'finding-card';
            
            card.innerHTML = `
                <div class="finding-header">
                    <span class="finding-title">${finding.title}</span>
                    <span class="finding-sev-badge ${finding.severity}">${finding.severity}</span>
                </div>
                <div class="finding-meta">
                    <span>Category: ${finding.category}</span>
                    <span>Target: ${finding.target || 'N/A'}</span>
                </div>
                <div class="finding-desc">${finding.description || ''}</div>
            `;
            findingsList.appendChild(card);
        });
    } catch (e) {
        console.error('Failed to load findings:', e);
    }
}

// Modal actions
function createNewSession() {
    const mode = sessionModeInput.value;
    const target = sessionTargetInput.value.trim();
    const autonomy = sessionAutonomyInput.value;
    
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: 'session_create',
            mode: mode,
            target: target,
            autonomy: autonomy
        }));
    } else {
        alert('Server connection is offline. Unable to create session.');
    }
}

// Chat UI manipulations
function setChatControlsState(disabled) {
    chatInput.disabled = disabled;
    btnSend.disabled = disabled;
    if (!disabled) {
        chatInput.focus();
        chatInput.placeholder = "Type your instruction or message...";
    } else {
        chatInput.placeholder = isRunningAgent ? "Agent is reasoning... Please wait." : "Action required above.";
    }
}

function appendUserMessage(content) {
    // Remove "Ready" helper page if visible
    const helper = chatHistory.querySelector('.no-findings');
    if (helper) helper.remove();
    
    const container = document.createElement('div');
    container.className = 'message user';
    
    container.innerHTML = `
        <div class="message-sender">
            <span>You</span>
        </div>
        <div class="message-bubble">
            <p>${escapeHtml(content)}</p>
        </div>
    `;
    chatHistory.appendChild(container);
    scrollToBottom();
}

function appendAgentMessage(content) {
    const helper = chatHistory.querySelector('.no-findings');
    if (helper) helper.remove();
    
    const container = document.createElement('div');
    container.className = 'message agent';
    
    container.innerHTML = `
        <div class="message-sender">
            <span>RedForge Agent</span>
        </div>
        <div class="message-bubble">
            <div class="message-body">${parseMarkdown(content)}</div>
        </div>
    `;
    chatHistory.appendChild(container);
    scrollToBottom();
}

function streamAgentToken(token) {
    const helper = chatHistory.querySelector('.no-findings');
    if (helper) helper.remove();
    
    if (!currentAgentMessageElement) {
        currentAgentMessageElement = document.createElement('div');
        currentAgentMessageElement.className = 'message agent';
        currentAgentMessageElement.innerHTML = `
            <div class="message-sender">
                <span>RedForge Agent</span>
            </div>
            <div class="message-bubble">
                <div class="message-body">
                    <span class="token-stream"></span><span class="cursor-blink"></span>
                </div>
            </div>
        `;
        chatHistory.appendChild(currentAgentMessageElement);
        currentAgentMessageBody = currentAgentMessageElement.querySelector('.token-stream');
        currentAgentMessageBody.dataset.raw = "";
    }
    
    const rawContent = currentAgentMessageBody.dataset.raw + token;
    currentAgentMessageBody.dataset.raw = rawContent;
    currentAgentMessageBody.innerHTML = parseMarkdown(rawContent);
    scrollToBottom();
}

function finalizeAgentMessage(content) {
    if (currentAgentMessageElement) {
        const blinker = currentAgentMessageElement.querySelector('.cursor-blink');
        if (blinker) blinker.remove();
        
        const body = currentAgentMessageElement.querySelector('.message-body');
        body.innerHTML = parseMarkdown(content);
        
        currentAgentMessageElement = null;
        currentAgentMessageBody = null;
    } else {
        appendAgentMessage(content);
    }
    scrollToBottom();
}

function appendErrorMessage(errorMsg) {
    const container = document.createElement('div');
    container.className = 'message agent';
    container.innerHTML = `
        <div class="message-sender" style="color: var(--color-error);">
            <span>System Error</span>
        </div>
        <div class="message-bubble" style="border-color: rgba(255, 23, 68, 0.3); background: rgba(255, 23, 68, 0.02);">
            <div class="message-body" style="color: var(--color-error); font-weight: 500;">
                ${escapeHtml(errorMsg)}
            </div>
        </div>
    `;
    chatHistory.appendChild(container);
    scrollToBottom();
}

function appendToolExecution(callId, tool, command) {
    const container = document.createElement('div');
    container.className = 'tool-execution-block';
    container.id = `tool-${callId}`;
    
    container.innerHTML = `
        <div class="tool-block-header">
            <div class="tool-run-info">
                <div class="tool-spinner"></div>
                <span>Executing tool: <strong class="tool-command">${escapeHtml(tool)}</strong></span>
            </div>
            <span class="tool-version">ID: ${callId}</span>
        </div>
        <div class="tool-block-body">
            <div class="tool-output" style="color: var(--text-muted);">Command: ${escapeHtml(command)}\nRunning...</div>
        </div>
    `;
    chatHistory.appendChild(container);
    scrollToBottom();
}

function updateToolExecution(callId, success, result, error) {
    const element = document.getElementById(`tool-${callId}`);
    if (!element) return;
    
    // Remove spinner
    const spinner = element.querySelector('.tool-spinner');
    if (spinner) spinner.remove();
    
    // Add success/error indicator
    const headerRow = element.querySelector('.tool-run-info');
    const indicator = document.createElement('span');
    indicator.style.marginRight = '8px';
    indicator.innerHTML = success ? 
        '<span style="color: var(--color-success); font-weight: bold;">✓</span>' : 
        '<span style="color: var(--color-error); font-weight: bold;">✗</span>';
    headerRow.insertBefore(indicator, headerRow.firstChild);
    
    element.classList.add(success ? 'success' : 'error');
    
    const body = element.querySelector('.tool-block-body');
    
    let displayOutput = "";
    if (error) {
        displayOutput = `<span class="tool-error">${escapeHtml(error)}</span>`;
    } else {
        const stdout = result.output || "";
        displayOutput = `<span class="tool-output">${escapeHtml(stdout)}</span>`;
    }
    
    const cmdStr = result.command ? `Command: ${escapeHtml(result.command)}\n\n` : '';
    body.innerHTML = `
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 8px;">Duration: ${result.duration_s || 0}s | Return Code: ${result.returncode !== undefined ? result.returncode : 0}</div>
        <pre style="margin: 0; padding: 0; font-family: inherit;">${cmdStr}${displayOutput}</pre>
    `;
    scrollToBottom();
}

function appendConfirmationRequest(message, toolCalls) {
    const container = document.createElement('div');
    container.className = 'confirmation-block';
    
    let cmdDetails = "";
    toolCalls.forEach(call => {
        if (call.tool === 'bash') {
            cmdDetails += `bash command:\n${call.command}\n`;
        } else if (call.tool === 'python') {
            cmdDetails += `python script:\n${call.code}\n`;
        } else {
            cmdDetails += `${call.tool} tool execution: ${JSON.stringify(call)}\n`;
        }
    });
    
    container.innerHTML = `
        <div class="confirm-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-top: 1px;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            Approval Needed
        </div>
        <div style="font-size: 0.85rem; line-height: 1.4;">${escapeHtml(message)}</div>
        <pre class="confirm-command">${escapeHtml(cmdDetails.trim())}</pre>
        <div class="confirm-actions">
            <button class="btn-approve" onclick="submitApproval(true, this)">Approve and Run</button>
            <button class="btn-reject" onclick="submitApproval(false, this)">Deny Action</button>
        </div>
    `;
    chatHistory.appendChild(container);
    scrollToBottom();
}

function submitApproval(approved, buttonElement) {
    // Disable actions
    const parent = buttonElement.closest('.confirmation-block');
    parent.style.opacity = '0.7';
    parent.querySelectorAll('button').forEach(btn => btn.disabled = true);
    
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: approved ? 'approve' : 'reject',
            session_id: activeSessionId
        }));
        
        isRunningAgent = true;
        setChatControlsState(true);
    }
}

function sendUserMessage() {
    const text = chatInput.value.trim();
    if (!text || !activeSessionId) return;
    
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: 'message',
            session_id: activeSessionId,
            content: text
        }));
        
        chatInput.value = '';
    }
}

// Helpers
function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function parseMarkdown(text) {
    if (!text) return "";
    let html = text.toString();
    
    // Escaping code markers temporarily
    const codeBlocks = [];
    html = html.replace(/```([\s\S]*?)```/g, (match, p1) => {
        const id = `__CODE_BLOCK_${codeBlocks.length}__`;
        codeBlocks.push(`<pre class="tool-output" style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: var(--radius-md); font-family: var(--font-mono); border: 1px solid var(--border-color); overflow-x: auto; margin: 10px 0;"><code>${escapeHtml(p1.trim())}</code></pre>`);
        return id;
    });
    
    // Escape standard tags
    html = escapeHtml(html);
    
    // Put code blocks back
    codeBlocks.forEach((block, idx) => {
        html = html.replace(`__CODE_BLOCK_${idx}__`, block);
    });
    
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Headings
    html = html.replace(/^### (.*$)/gim, '<h3 style="margin: 12px 0 6px 0; font-weight: 700; color: #fff;">$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 style="margin: 16px 0 8px 0; font-weight: 700; color: #fff;">$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1 style="margin: 20px 0 10px 0; font-weight: 800; color: #fff;">$1</h1>');
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code style="font-family: var(--font-mono); background: rgba(255,255,255,0.06); padding: 2px 4px; border-radius: var(--radius-sm); font-size: 0.85em; color: var(--color-info);">$1</code>');
    
    // Bullet lists
    html = html.replace(/^\s*-\s+(.*$)/gim, '<li style="margin-left: 20px; margin-bottom: 4px;">$1</li>');
    html = html.replace(/^\s*\*\s+(.*$)/gim, '<li style="margin-left: 20px; margin-bottom: 4px;">$1</li>');
    
    // Clean list items wrap
    html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul style="margin: 10px 0;">$1</ul>');
    html = html.replace(/<\/ul>\s*<ul style="margin: 10px 0;">/g, '');
    
    // Newlines to breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

function scrollToBottom() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
}
