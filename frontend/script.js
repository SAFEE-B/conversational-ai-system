document.addEventListener('DOMContentLoaded', () => {
    /* ─── Refs ──────────────────────────────────────────── */
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const chatForm = document.getElementById('chat-form');
    const resetBtn = document.getElementById('reset-btn');
    const statusDot = document.getElementById('status-dot');
    const statusLabel = document.getElementById('status-label');
    const menuBtn = document.getElementById('menu-btn');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const sessionList = document.getElementById('session-list');
    const newChatBtn = document.getElementById('new-chat-btn');
    const chatTitle = document.getElementById('chat-title');
    const chips = document.querySelectorAll('.chip');
    const welcomeTime = document.getElementById('welcome-time');
    const voiceBtn = document.getElementById('voice-btn');
    const voiceStopBtn = document.getElementById('voice-stop-btn');

    /* ─── State ─────────────────────────────────────────── */
    // API_BASE and WS_BASE are defined in config.js

    // Persist session list locally (keyed by session_id → title)
    const LOCAL_KEY = 'hf_sessions'; // list of { session_id, title }

    let ws = null;
    let currentSession = null;   // active session_id
    let currentMsg = null;   // DOM element being streamed into
    let isGenerating = false;
    let pendingSessionId = null;  // session_id requested but waiting for server ack
    let isRecording = false;
    let mediaRecorder = null;
    let recordedChunks = [];
    let currentAudio = null;
    // Ensure audio chunks play in order.
    let audioChain = Promise.resolve();
    let audioGenerationId = 0;

    /* ─── Helpers ───────────────────────────────────────── */
    welcomeTime.textContent = formatTime();

    function formatTime(d = new Date()) {
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function stopAudioPlayback() {
        audioGenerationId += 1;
        if (currentAudio) {
            try { currentAudio.pause(); } catch { }
            currentAudio = null;
        }
        audioChain = Promise.resolve();
    }

    function blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                try {
                    const dataUrl = reader.result;
                    const b64 = dataUrl.split(',')[1];
                    resolve(b64);
                } catch (e) {
                    reject(e);
                }
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    function playWavBase64(audioB64) {
        // Creates a standalone WAV data URI and plays it.
        // We chain them so playback stays in order.
        return new Promise((resolve) => {
            const audio = new Audio(`data:audio/wav;base64,${audioB64}`);
            currentAudio = audio;
            audio.onended = () => resolve();
            audio.onerror = () => resolve();
            audio.play().catch(() => resolve());
        });
    }

    function setVoiceButtonsRecording(recording) {
        isRecording = recording;
        if (voiceBtn) voiceBtn.style.display = recording ? 'none' : '';
        if (voiceStopBtn) voiceStopBtn.style.display = recording ? '' : 'none';
        updateSendBtn();
    }

    async function startVoiceCapture() {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        if (isGenerating || isRecording) return;

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            chatBox.appendChild(createMessageElement('error', 'Voice input is not supported in this browser.'));
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            const candidates = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/ogg;codecs=opus',
                'audio/ogg',
            ];
            const mimeType = candidates.find(t => MediaRecorder.isTypeSupported(t)) || '';

            recordedChunks = [];
            mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
            mediaRecorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) recordedChunks.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                try {
                    setVoiceButtonsRecording(false);
                    // Stop the mic tracks.
                    stream.getTracks().forEach(t => t.stop());

                    if (!recordedChunks.length) return;

                    const mime = mediaRecorder.mimeType || 'audio/webm';
                    const blob = new Blob(recordedChunks, { type: mime });
                    const audioB64 = await blobToBase64(blob);
                    const inputExt = mime.includes('webm') ? 'webm' : (mime.includes('ogg') ? 'ogg' : 'webm');

                    // Mark generating to disable text controls while voice is processed.
                    isGenerating = true;
                    updateSendBtn();

                    ws.send(JSON.stringify({ type: 'voice_message', audio_base64: audioB64, input_ext: inputExt }));
                } catch {
                    isGenerating = false;
                    updateSendBtn();
                    chatBox.appendChild(createMessageElement('error', 'Could not send voice audio.'));
                    scrollToBottom();
                }
            };

            setVoiceButtonsRecording(true);
            mediaRecorder.start();
        } catch {
            setVoiceButtonsRecording(false);
            chatBox.appendChild(createMessageElement('error', 'Microphone permission denied.'));
            scrollToBottom();
        }
    }

    function stopVoiceCapture() {
        if (!mediaRecorder) return;
        if (mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
    }

    function setStatus(s) {
        statusDot.className = 'status-pulse ' + s;
        statusLabel.textContent = s === 'connecting' ? 'Connecting…'
            : s === 'connected' ? 'Connected'
                : 'Disconnected · Retrying…';
    }

    function updateSendBtn() {
        sendBtn.disabled = messageInput.value.trim() === '' || isGenerating
            || isRecording
            || !ws || ws.readyState !== WebSocket.OPEN;
    }

    /* ─── Local session store ───────────────────────────── */
    function loadLocalSessions() {
        try { return JSON.parse(localStorage.getItem(LOCAL_KEY)) || []; }
        catch { return []; }
    }

    function saveLocalSession(session_id, title) {
        const list = loadLocalSessions().filter(s => s.session_id !== session_id);
        list.unshift({ session_id, title: title || 'New Chat' });
        // Keep only the 20 most recent
        localStorage.setItem(LOCAL_KEY, JSON.stringify(list.slice(0, 20)));
    }

    function removeLocalSession(session_id) {
        const list = loadLocalSessions().filter(s => s.session_id !== session_id);
        localStorage.setItem(LOCAL_KEY, JSON.stringify(list));
    }

    /* ─── Session sidebar ───────────────────────────────── */
    function renderSessionList() {
        const sessions = loadLocalSessions();
        sessionList.innerHTML = '';

        if (sessions.length === 0) {
            sessionList.innerHTML = '<div class="session-empty">No prior chats yet</div>';
            return;
        }

        sessions.forEach(({ session_id, title }) => {
            const item = document.createElement('div');
            item.className = 'session-item' + (session_id === currentSession ? ' active' : '');
            item.dataset.sid = session_id;
            item.innerHTML = `
                <svg class="session-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                <span class="session-title">${escapeHtml(title)}</span>
                <button class="del-btn" data-sid="${session_id}" title="Delete">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>`;
            item.addEventListener('click', (e) => {
                if (e.target.closest('.del-btn')) return;
                switchSession(session_id);
            });
            item.querySelector('.del-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteSession(session_id);
            });
            sessionList.appendChild(item);
        });
    }

    function escapeHtml(s) {
        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    /* ─── Message elements ──────────────────────────────── */
    function createMessageElement(role, text = '') {
        const wrapper = document.createElement('div');
        wrapper.className = `message ${role}`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'msg-avatar';

        if (role === 'user') {
            // No avatar needed for user in new design
            avatarDiv.style.display = 'none';
        } else if (role === 'error') {
            avatarDiv.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
        } else {
            avatarDiv.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/></svg>`;
        }

        const body = document.createElement('div');
        body.className = 'msg-body';

        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = text;

        const time = document.createElement('span');
        time.className = 'msg-time';
        time.textContent = formatTime();

        body.appendChild(bubble);
        body.appendChild(time);

        wrapper.appendChild(avatarDiv);
        wrapper.appendChild(body);
        return wrapper;
    }

    /* ─── Restore history from server ───────────────────── */
    async function restoreHistory(session_id) {
        try {
            const res = await fetch(`${API_BASE}/history/${session_id}`);
            if (!res.ok) throw new Error('Not found');
            const data = await res.json();

            // Clear chat (keep only welcome msg)
            while (chatBox.children.length > 1) chatBox.removeChild(chatBox.lastChild);

            data.messages.forEach(({ role, content }) => {
                if (role === 'user' || role === 'assistant') {
                    chatBox.appendChild(createMessageElement(role, content));
                }
            });
            scrollToBottom();
        } catch {
            // Session not on server yet (e.g. first connect) - that's fine
        }
    }

    /* ─── Session switching ─────────────────────────────── */
    function switchSession(session_id) {
        closeSidebar();
        reconnectWithSession(session_id);
    }

    async function deleteSession(session_id) {
        removeLocalSession(session_id);
        try { await fetch(`${API_BASE}/sessions/${session_id}`, { method: 'DELETE' }); } catch { }
        if (session_id === currentSession) {
            startNewChat();
        } else {
            renderSessionList();
        }
    }

    /* ─── New chat ──────────────────────────────────────── */
    function startNewChat() {
        currentSession = null;
        while (chatBox.children.length > 1) chatBox.removeChild(chatBox.lastChild);
        chatTitle.textContent = 'HealthFirst Assistant';
        stopVoiceCapture();
        stopAudioPlayback();
        isGenerating = false;
        currentMsg = null;
        closeSidebar();
        reconnectWithSession(null);
    }

    /* ─── WebSocket ─────────────────────────────────────── */
    function reconnectWithSession(session_id) {
        pendingSessionId = session_id;
        if (ws) ws.close();   // will trigger onclose → connect()
    }

    function connect() {
        setStatus('connecting');
        ws = new WebSocket(`${WS_BASE}/ws/chat`);

        ws.onopen = () => {
            // Send init frame with optional session_id to resume
            ws.send(JSON.stringify({ session_id: pendingSessionId || null }));
        };

        ws.onclose = () => {
            setStatus('disconnected');
            sendBtn.disabled = true;
            setTimeout(connect, 3000);
        };

        ws.onerror = (err) => console.error('[WS]', err);

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.type === 'session_init') {
                    currentSession = data.session_id;
                    pendingSessionId = null;
                    setStatus('connected');
                    updateSendBtn();
                    // If we asked for an existing session, reload its history
                    const local = loadLocalSessions().find(s => s.session_id === currentSession);
                    if (local) {
                        chatTitle.textContent = local.title;
                        restoreHistory(currentSession);
                    }
                    renderSessionList();
                    return;
                }

                if (data.type === 'voice_transcript') {
                    // Render the ASR transcript as a user message bubble.
                    if (data.content) {
                        chatBox.appendChild(createMessageElement('user', data.content));
                        scrollToBottom();
                    }
                    return;
                }

                if (data.type === 'audio_chunk') {
                    if (data.audio_base64) {
                        const genId = audioGenerationId;
                        audioChain = audioChain.then(() => {
                            if (genId !== audioGenerationId) return;
                            return playWavBase64(data.audio_base64);
                        });
                    }
                    return;
                }

                if (data.type === 'start') {
                    isGenerating = true;
                    currentMsg = createMessageElement('assistant');
                    currentMsg.querySelector('.bubble').classList.add('streaming');
                    chatBox.appendChild(currentMsg);
                    scrollToBottom();
                }
                else if (data.type === 'token') {
                    if (currentMsg) {
                        currentMsg.querySelector('.bubble').textContent += data.content;
                        scrollToBottom();
                    }
                }
                else if (data.type === 'end') {
                    isGenerating = false;
                    if (currentMsg) {
                        currentMsg.querySelector('.bubble').classList.remove('streaming');
                        currentMsg = null;
                    }
                    // Sync sidebar title after first assistant response
                    refreshSessionMeta();
                    updateSendBtn();
                }
                else if (data.type === 'error') {
                    isGenerating = false;
                    chatBox.appendChild(createMessageElement('error', data.content || 'An error occurred.'));
                    scrollToBottom();
                    updateSendBtn();
                }
                else if (data.type === 'system') {
                    chatBox.appendChild(createMessageElement('system', data.content));
                    scrollToBottom();
                }
            } catch (e) {
                console.error('[WS] parse error', e);
            }
        };
    }

    /* Fetch latest session meta from server and update sidebar */
    async function refreshSessionMeta() {
        if (!currentSession) return;
        try {
            const res = await fetch(`${API_BASE}/sessions`);
            if (!res.ok) return;
            const { sessions } = await res.json();
            const meta = sessions.find(s => s.session_id === currentSession);
            if (meta) {
                saveLocalSession(currentSession, meta.title);
                chatTitle.textContent = meta.title;
                renderSessionList();
            }
        } catch { }
    }

    /* ─── Init ──────────────────────────────────────────── */
    // On first load restore the last used session_id, if any
    const lastSessions = loadLocalSessions();
    pendingSessionId = lastSessions.length ? lastSessions[0].session_id : null;
    connect();

    /* ─── Input resize ──────────────────────────────────── */
    messageInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 130) + 'px';
        updateSendBtn();
    });

    /* ─── Enter to send ─────────────────────────────────── */
    messageInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    /* ─── Submit ────────────────────────────────────────── */
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const content = messageInput.value.trim();
        if (!content || isGenerating || isRecording || !ws || ws.readyState !== WebSocket.OPEN) return;

        chatBox.appendChild(createMessageElement('user', content));
        scrollToBottom();

        ws.send(JSON.stringify({ type: 'message', content }));

        // Persist session locally immediately (title will be updated after response)
        if (currentSession) saveLocalSession(currentSession, chatTitle.textContent);

        messageInput.value = '';
        messageInput.style.height = 'auto';
        sendBtn.disabled = true;
        isGenerating = true;
        messageInput.focus();
    });

    /* ─── Reset ─────────────────────────────────────────── */
    resetBtn.addEventListener('click', () => {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        ws.send(JSON.stringify({ type: 'reset' }));
        while (chatBox.children.length > 1) chatBox.removeChild(chatBox.lastChild);
        chatTitle.textContent = 'HealthFirst Assistant';
        stopVoiceCapture();
        setVoiceButtonsRecording(false);
        stopAudioPlayback();
        isGenerating = false;
        currentMsg = null;
        updateSendBtn();
    });

    /* ─── New chat ──────────────────────────────────────── */
    newChatBtn.addEventListener('click', startNewChat);

    /* ─── Voice controls ───────────────────────────────── */
    if (voiceBtn) voiceBtn.addEventListener('click', startVoiceCapture);
    if (voiceStopBtn) voiceStopBtn.addEventListener('click', stopVoiceCapture);

    /* ─── Chips ─────────────────────────────────────────── */
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            if (isRecording || isGenerating) return;
            messageInput.value = chip.dataset.msg;
            messageInput.dispatchEvent(new Event('input'));
            messageInput.focus();
            closeSidebar();
        });
    });

    /* ─── Sidebar toggle ─────────────────────────────────── */
    function isMobile() { return window.innerWidth <= 680; }

    function openSidebar() { sidebar.classList.add('open'); sidebarOverlay.classList.add('visible'); }
    function closeSidebar() { sidebar.classList.remove('open'); sidebarOverlay.classList.remove('visible'); }

    function toggleSidebar() {
        if (isMobile()) {
            // Mobile: drawer with overlay
            sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
        } else {
            // Desktop: collapse/expand the sidebar panel inline
            sidebar.classList.toggle('collapsed');
        }
    }

    menuBtn.addEventListener('click', toggleSidebar);
    sidebarOverlay.addEventListener('click', closeSidebar);
});
