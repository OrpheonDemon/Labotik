// Global Chatbot Widget Script - LabTik

(function() {
    const API_URL = "http://127.0.0.1:8000";
    const TIMEOUT_MS = 180000; // 180 seconds for medgemma cold-start
    let conversationHistory = [];
    let userRole = null;
    let patientId = null;
    let currentController = null; // Active AbortController reference

    // Helper: JWT Decoder
    function decodeJwt(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (e) {
            console.error("Error decoding JWT:", e);
            return null;
        }
    }

    // Helper: Get Auth headers
    function getAuthHeaders() {
        const token = sessionStorage.getItem('access_token') || localStorage.getItem('access_token');
        return token ? { 
            'Authorization': `Bearer ${token}`,
            'X-Access-Token': token,
            'Content-Type': 'application/json'
        } : { 'Content-Type': 'application/json' };
    }

    // Init Chatbot
    document.addEventListener("DOMContentLoaded", function() {
        const token = sessionStorage.getItem('access_token') || localStorage.getItem('access_token');
        if (!token) {
            // No authenticated user, do not render chatbot
            return;
        }

        const payload = decodeJwt(token);
        if (!payload) return;

        userRole = payload.rol;
        
        // If logged in as patient, pre-fill and lock patient context
        if (userRole === 'paciente') {
            patientId = payload.id_usuario;
        }

        // Render Widget HTML
        createChatbotDOM();
        
        // Initialize patient select if user has a clinical role
        if (['medico', 'laboratorista', 'administrador'].includes(userRole)) {
            loadPatientsSelector();
        } else {
            // Hide patient context selector if patient or general user
            const contextPanel = document.getElementById('chatbotContextPanel');
            if (contextPanel) contextPanel.style.display = 'none';
        }

        // Event Listeners
        const triggerBtn = document.getElementById('chatbotTriggerBtn');
        const container = document.getElementById('chatbotContainer');
        const closeBtn = document.getElementById('chatbotCloseBtn');
        const form = document.getElementById('chatbotForm');

        triggerBtn.addEventListener('click', () => {
            container.classList.toggle('show');
            triggerBtn.classList.toggle('active');
            if (container.classList.contains('show')) {
                document.getElementById('chatbotInput').focus();
            }
        });

        closeBtn.addEventListener('click', () => {
            container.classList.remove('show');
            triggerBtn.classList.remove('active');
        });

        form.addEventListener('submit', handleFormSubmit);
    });

    function createChatbotDOM() {
        // Floating button
        const btn = document.createElement('button');
        btn.id = 'chatbotTriggerBtn';
        btn.className = 'chatbot-trigger-btn';
        btn.innerHTML = '<i class="fas fa-comment-medical"></i>';
        document.body.appendChild(btn);

        // Chat Container
        const container = document.createElement('div');
        container.id = 'chatbotContainer';
        container.className = 'chatbot-container';
        
        container.innerHTML = `
            <div class="chatbot-header">
                <div class="chatbot-header-title">
                    <i class="fas fa-brain"></i>
                    <div>
                        <h4>Asistente Clínico IA</h4>
                        <div class="chatbot-header-status">
                            <span class="chatbot-dot"></span> MedGemma Activo
                        </div>
                    </div>
                </div>
                <button id="chatbotCloseBtn" class="chatbot-header-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <div id="chatbotContextPanel" class="chatbot-context-panel">
                <select id="chatbotPatientSelect" class="chatbot-context-select">
                    <option value="">-- Sin paciente (Consulta General) --</option>
                </select>
            </div>
            
            <div id="chatbotMessages" class="chatbot-messages">
                <div class="chatbot-welcome-card" id="chatbotWelcomeCard">
                    <i class="fas fa-robot"></i>
                    <h5>¡Hola! Soy MedGemma</h5>
                    <p>Puedo ayudarte a interpretar análisis clínicos, explicar biomarcadores y responder dudas médicas de laboratorio. ¿De qué deseas hablar hoy?</p>
                    
                    <button class="chatbot-suggested-btn" onclick="window.sendChatbotSuggested('¿Qué significa hemoglobina baja?')">
                        <i class="fas fa-question-circle"></i> ¿Qué significa hemoglobina baja?
                    </button>
                    <button class="chatbot-suggested-btn" onclick="window.sendChatbotSuggested('¿Cuáles son los valores normales de glucosa?')">
                        <i class="fas fa-question-circle"></i> Valores normales de glucosa
                    </button>
                    <button class="chatbot-suggested-btn" onclick="window.sendChatbotSuggested('¿Para qué sirve el examen de TSH?')">
                        <i class="fas fa-question-circle"></i> ¿Para qué sirve el examen de TSH?
                    </button>
                </div>
            </div>
            
            <div class="chatbot-footer">
                <form id="chatbotForm" class="chatbot-form" autocomplete="off">
                    <input type="text" id="chatbotInput" class="chatbot-input" placeholder="Pregunta sobre laboratorio o enfermedades..." required>
                    <button type="submit" class="chatbot-send-btn">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </form>
            </div>
        `;

        document.body.appendChild(container);
    }

    async function loadPatientsSelector() {
        const select = document.getElementById('chatbotPatientSelect');
        if (!select) return;

        try {
            const response = await fetch(`${API_URL}/pacientes?limit=100`, {
                headers: getAuthHeaders()
            });
            if (response.ok) {
                const pacientes = await response.json();
                pacientes.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id_paciente;
                    opt.textContent = `Paciente: ${p.nombre} ${p.apellido_paterno} (${p.id_paciente})`;
                    select.appendChild(opt);
                });
            }
        } catch (error) {
            console.error("Error loading patients for chatbot context:", error);
        }

        select.addEventListener('change', function() {
            patientId = this.value || null;
            if (patientId) {
                addMessage('assistant', `Se ha seleccionado el contexto clínico del paciente.`);
            } else {
                addMessage('assistant', `Contexto de paciente removido. Consultas generales.`);
            }
        });
    }

    // Global helper for suggested questions
    window.sendChatbotSuggested = function(question) {
        const input = document.getElementById('chatbotInput');
        if (input) {
            input.value = question;
            document.getElementById('chatbotForm').dispatchEvent(new Event('submit', { cancelable: true }));
        }
    };

    function handleFormSubmit(e) {
        e.preventDefault();
        const input = document.getElementById('chatbotInput');
        const question = input.value.trim();
        if (!question) return;

        input.value = '';
        
        // Hide welcome card
        const welcome = document.getElementById('chatbotWelcomeCard');
        if (welcome) welcome.style.display = 'none';

        // Add user message
        addMessage('user', question);
        
        // Show typing indicator with progressive status
        showTypingIndicator();

        // Disable form while processing
        setFormEnabled(false);

        // Send to backend
        sendChatRequest(question);
    }

    function sendChatRequest(question, isRetry = false) {
        const payload = {
            question: question,
            patient_id: patientId
        };

        // Create AbortController with extended timeout for medgemma
        const controller = new AbortController();
        currentController = controller;

        const timeoutId = setTimeout(() => {
            controller.abort();
        }, TIMEOUT_MS);

        // Progressive status messages
        const statusTimers = startProgressiveStatus();

        let bubbleElement = null;
        let streamedText = "";

        fetch(`${API_URL}/ai/smart-chat-stream`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(payload),
            signal: controller.signal
        })
        .then(async response => {
            clearTimeout(timeoutId);
            clearProgressiveStatus(statusTimers);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = "";

            removeTypingIndicator();
            setFormEnabled(true);
            currentController = null;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                
                // Keep the last partial line in the buffer
                buffer = lines.pop();

                for (const line of lines) {
                    const cleanLine = line.trim();
                    if (!cleanLine.startsWith("data:")) continue;

                    try {
                        const jsonData = JSON.parse(cleanLine.substring(5).trim());
                        if (jsonData.error) {
                            if (bubbleElement) {
                                bubbleElement.innerHTML = renderMarkdown(`⚠️ ${jsonData.error}`);
                            } else {
                                addMessage('assistant', `⚠️ ${jsonData.error}`);
                            }
                            return;
                        }

                        if (jsonData.token) {
                            streamedText += jsonData.token;
                            
                            if (!bubbleElement) {
                                bubbleElement = createEmptyAssistantBubble();
                            }
                            
                            bubbleElement.innerHTML = renderMarkdown(streamedText);
                            
                            const time = document.createElement('div');
                            time.className = 'chatbot-time';
                            time.textContent = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
                            bubbleElement.appendChild(time);
                            
                            const container = document.getElementById('chatbotMessages');
                            container.scrollTop = container.scrollHeight;
                        }
                    } catch (e) {
                        console.error("Error parsing streaming line:", e, cleanLine);
                    }
                }
            }
        })
        .catch(err => {
            clearTimeout(timeoutId);
            clearProgressiveStatus(statusTimers);
            removeTypingIndicator();
            setFormEnabled(true);
            currentController = null;
            console.error("Chatbot API Error:", err);
            
            if (err.name === 'AbortError') {
                addMessageWithRetry(
                    '⏳ La consulta tardó más de lo esperado. El modelo MedGemma puede necesitar tiempo para inicializarse la primera vez.',
                    question
                );
            } else if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
                addMessage('assistant', '🔌 No se pudo conectar con el servidor. Verifica que FastAPI esté ejecutándose en el puerto 8000 y que Ollama esté activo.');
            } else {
                addMessage('assistant', `❌ Error inesperado: ${err.message}. Intenta de nuevo.`);
            }
        });
    }

    function createEmptyAssistantBubble() {
        const container = document.getElementById('chatbotMessages');
        const row = document.createElement('div');
        row.className = 'chatbot-msg-row assistant';

        const bubble = document.createElement('div');
        bubble.className = 'chatbot-bubble';
        bubble.innerHTML = '<span class="chatbot-typing"><span></span><span></span><span></span></span>';

        row.appendChild(bubble);
        container.appendChild(row);
        container.scrollTop = container.scrollHeight;
        return bubble;
    }

    function setFormEnabled(enabled) {
        const input = document.getElementById('chatbotInput');
        const sendBtn = document.querySelector('.chatbot-send-btn');
        if (input) {
            input.disabled = !enabled;
            input.placeholder = enabled 
                ? 'Pregunta sobre laboratorio o enfermedades...' 
                : 'Procesando consulta...';
        }
        if (sendBtn) sendBtn.disabled = !enabled;
    }

    function cancelCurrentRequest() {
        if (currentController) {
            currentController.abort();
            currentController = null;
        }
    }

    function renderMarkdown(text) {
        // Convert markdown-like patterns to HTML
        let html = text
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')  // **bold**
            .replace(/\*(.+?)\*/g, '<em>$1</em>')              // *italic*
            .replace(/^\s*[-•]\s+(.+)/gm, '<li>$1</li>')       // bullet lists
            .replace(/^\s*\d+\.\s+(.+)/gm, '<li>$1</li>')     // numbered lists
            .replace(/\n/g, '<br>');                             // newlines
        
        // Wrap consecutive <li> in <ul>
        html = html.replace(/(<li>.*?<\/li>(?:<br>)?)+/g, (match) => {
            return '<ul class="chatbot-list">' + match.replace(/<br>/g, '') + '</ul>';
        });
        
        return html;
    }

    function addMessage(sender, text) {
        const container = document.getElementById('chatbotMessages');
        const row = document.createElement('div');
        row.className = `chatbot-msg-row ${sender}`;

        const bubble = document.createElement('div');
        bubble.className = 'chatbot-bubble';
        
        bubble.innerHTML = renderMarkdown(text);

        const time = document.createElement('div');
        time.className = 'chatbot-time';
        time.textContent = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });

        bubble.appendChild(time);
        row.appendChild(bubble);
        container.appendChild(row);

        // Auto-scroll
        container.scrollTop = container.scrollHeight;
    }

    function addMessageWithRetry(text, originalQuestion) {
        const container = document.getElementById('chatbotMessages');
        const row = document.createElement('div');
        row.className = 'chatbot-msg-row assistant';

        const bubble = document.createElement('div');
        bubble.className = 'chatbot-bubble';
        bubble.innerHTML = renderMarkdown(text);

        const retryBtn = document.createElement('button');
        retryBtn.className = 'chatbot-retry-btn';
        retryBtn.innerHTML = '<i class="fas fa-redo"></i> Reintentar';
        retryBtn.addEventListener('click', () => {
            row.remove();
            showTypingIndicator();
            setFormEnabled(false);
            sendChatRequest(originalQuestion, true);
        });

        const time = document.createElement('div');
        time.className = 'chatbot-time';
        time.textContent = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });

        bubble.appendChild(retryBtn);
        bubble.appendChild(time);
        row.appendChild(bubble);
        container.appendChild(row);
        container.scrollTop = container.scrollHeight;
    }

    function showTypingIndicator() {
        const container = document.getElementById('chatbotMessages');
        const row = document.createElement('div');
        row.className = 'chatbot-msg-row assistant';
        row.id = 'chatbotTypingIndicator';

        const bubble = document.createElement('div');
        bubble.className = 'chatbot-bubble';
        bubble.innerHTML = `
            <div class="chatbot-typing">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <div class="chatbot-typing-status" id="chatbotTypingStatus">Procesando...</div>
            <button class="chatbot-cancel-btn" id="chatbotCancelBtn" title="Cancelar">
                <i class="fas fa-times-circle"></i> Cancelar
            </button>
        `;

        row.appendChild(bubble);
        container.appendChild(row);
        container.scrollTop = container.scrollHeight;

        // Bind cancel button
        const cancelBtn = document.getElementById('chatbotCancelBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                cancelCurrentRequest();
            });
        }
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('chatbotTypingIndicator');
        if (indicator) indicator.remove();
    }

    function startProgressiveStatus() {
        const messages = [
            { delay: 5000,  text: 'Conectando con MedGemma...' },
            { delay: 15000, text: 'Analizando tu consulta...' },
            { delay: 30000, text: 'Generando respuesta clínica...' },
            { delay: 60000, text: 'El modelo está procesando (esto puede tardar en la primera consulta)...' },
            { delay: 120000, text: 'Aún procesando, por favor espera...' }
        ];
        
        const timers = messages.map(msg => 
            setTimeout(() => {
                const statusEl = document.getElementById('chatbotTypingStatus');
                if (statusEl) {
                    statusEl.textContent = msg.text;
                    statusEl.classList.add('chatbot-status-pulse');
                    setTimeout(() => statusEl.classList.remove('chatbot-status-pulse'), 500);
                }
            }, msg.delay)
        );
        
        return timers;
    }

    function clearProgressiveStatus(timers) {
        if (timers && Array.isArray(timers)) {
            timers.forEach(t => clearTimeout(t));
        }
    }
})();
