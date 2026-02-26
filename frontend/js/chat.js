// ── YCCE-AI Chat Logic ────────────────────────────────────
(function () {
    'use strict';

    // Gemini API config (client-side RAG)
    const GEMINI_API_KEY = 'AIzaSyCSUGXTpci6F4pJSwn_LLJXzw8n41dTiwI';
    const GEMINI_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key=${GEMINI_API_KEY}`;

    const SYSTEM_PROMPT = `You are YCCE-AI, an intelligent assistant for Yeshwantrao Chavan College of Engineering (YCCE), Nagpur.
Your job is to answer questions about YCCE using ONLY the context provided below.

Rules:
- Answer in clear, well-formatted paragraphs.
- If the context contains relevant information, synthesize it into a helpful, coherent answer.
- If the context does NOT contain enough information, say so politely and suggest checking the YCCE website.
- Be concise but thorough. Use bullet points for lists.
- Do NOT make up information not present in the context.
- Be friendly and professional.`;

    let accessToken = null;

    // --- Auth Guard ---
    async function requireAuth() {
        const { data: { session } } = await _sb.auth.getSession();
        if (!session) {
            window.location.href = 'index.html';
            return;
        }
        accessToken = session.access_token;
        document.getElementById('user-email').textContent = session.user.email;
    }
    requireAuth();

    // Listen for auth changes
    _sb.auth.onAuthStateChange((event, session) => {
        if (event === 'SIGNED_OUT' || !session) {
            window.location.href = 'index.html';
        } else {
            accessToken = session.access_token;
        }
    });

    // --- DOM ---
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const logoutBtn = document.getElementById('logout-btn');

    // --- Logout ---
    logoutBtn.addEventListener('click', async () => {
        await _sb.auth.signOut();
    });

    // --- Suggestion chips ---
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('chip')) {
            const query = e.target.dataset.query;
            if (query) {
                chatInput.value = query;
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });

    // --- Call Gemini to synthesize answer (with retry for rate limits) ---
    async function callGemini(query, context) {
        const prompt = `Context from YCCE knowledge base:\n---\n${context}\n---\n\nUser Question: ${query}\n\nProvide a helpful, well-formatted answer based on the context above.`;

        const maxRetries = 3;
        for (let attempt = 0; attempt < maxRetries; attempt++) {
            try {
                const resp = await fetch(GEMINI_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        contents: [{ role: 'user', parts: [{ text: prompt }] }],
                        systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
                        generationConfig: { temperature: 0.3, maxOutputTokens: 1024 },
                    }),
                });

                if (resp.status === 429) {
                    const wait = (attempt + 1) * 5000;
                    console.log(`Gemini rate limited (429). Retry ${attempt + 1}/${maxRetries} in ${wait/1000}s...`);
                    await new Promise(r => setTimeout(r, wait));
                    continue;
                }

                const data = await resp.json();
                console.log('Gemini status:', resp.status, 'Has candidates:', !!data?.candidates);

                if (!resp.ok) {
                    console.error('Gemini error:', resp.status, data);
                    return null;
                }

                const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
                if (text) return text;

                if (data?.promptFeedback?.blockReason) {
                    console.error('Gemini blocked:', data.promptFeedback.blockReason);
                    return null;
                }

                return null;
            } catch (err) {
                console.error('Gemini fetch error:', err);
                if (attempt < maxRetries - 1) {
                    await new Promise(r => setTimeout(r, 3000));
                    continue;
                }
                return null;
            }
        }
        return null;
    }

    // --- Send Message ---
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = chatInput.value.trim();
        if (!query) return;

        // Add user message
        addMessage(query, 'user');
        chatInput.value = '';
        sendBtn.disabled = true;

        // Show typing indicator
        const typingId = showTyping();

        try {
            // Step 1: Search the vector DB
            const searchResp = await fetch(`${SUPABASE_URL}/functions/v1/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
                },
                body: JSON.stringify({ query, match_count: 5 }),
            });

            if (!searchResp.ok) {
                throw new Error(`Search failed (${searchResp.status})`);
            }

            const searchData = await searchResp.json();

            if (!searchData.results || searchData.results.length === 0) {
                removeTyping(typingId);
                addMessage("I couldn't find any relevant information about that in the YCCE knowledge base. Try rephrasing your question or visit https://www.ycce.edu directly.", 'ai');
            } else {
                // Step 2: Send chunks + query to Gemini for a proper answer
                const context = searchData.results
                    .map((r, i) => `[Source: ${r.url}]\n${r.content}`)
                    .join('\n\n');

                const aiAnswer = await callGemini(query, context);

                removeTyping(typingId);

                if (aiAnswer) {
                    addAIResponse(aiAnswer, searchData.results);
                } else {
                    // Fallback: Gemini rate-limited, show a helpful summary of raw results
                    const fallbackAnswer = "⚡ AI summarization is temporarily rate-limited. Here's what I found in the YCCE knowledge base:\n\n" +
                        searchData.results.map((r, i) => `${i+1}. ${r.content.substring(0, 200)}...`).join('\n\n');
                    addAIResponse(fallbackAnswer, searchData.results);
                }
            }
        } catch (err) {
            removeTyping(typingId);
            addMessage(`Error: ${err.message}. Please try again.`, 'ai');
        }

        sendBtn.disabled = false;
        chatInput.focus();
    });

    // --- Add User/AI message ---
    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `message ${sender}-message fade-in`;

        if (sender === 'user') {
            div.innerHTML = `
                <div class="message-avatar user-avatar">You</div>
                <div class="message-content"><p>${escapeHtml(text)}</p></div>
            `;
        } else {
            div.innerHTML = `
                <div class="message-avatar ai-avatar">
                    <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
                        <circle cx="16" cy="16" r="14" stroke="#888" stroke-width="2"/>
                        <path d="M10 16 L14 20 L22 12" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="message-content"><p>${escapeHtml(text)}</p></div>
            `;
        }

        chatMessages.appendChild(div);
        scrollToBottom();
    }

    function addAIResponse(answerText, results) {
        const div = document.createElement('div');
        div.className = 'message ai-message fade-in';

        // Convert markdown to HTML
        let answerHtml = formatMarkdown(answerText);

        // Add sources
        let sourcesHtml = '';
        if (results && results.length > 0) {
            const uniqueUrls = [...new Set(results.map(s => s.url))];
            sourcesHtml = `
                <div class="sources">
                    ${uniqueUrls.map(url => {
                        const shortUrl = url.replace('https://ycce.edu/', '').replace('https://www.ycce.edu/', '');
                        return `<a href="${url}" target="_blank" class="source-tag">${shortUrl || 'Homepage'}</a>`;
                    }).join('')}
                </div>
            `;
        }

        div.innerHTML = `
            <div class="message-avatar ai-avatar">
                <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
                    <circle cx="16" cy="16" r="14" stroke="#888" stroke-width="2"/>
                    <path d="M10 16 L14 20 L22 12" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="message-content">
                ${answerHtml}
                ${sourcesHtml}
            </div>
        `;

        chatMessages.appendChild(div);
        scrollToBottom();
    }

    // --- Typing Indicator ---
    function showTyping() {
        const id = 'typing-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'message ai-message fade-in';
        div.innerHTML = `
            <div class="message-avatar ai-avatar">
                <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
                    <circle cx="16" cy="16" r="14" stroke="#888" stroke-width="2"/>
                    <path d="M10 16 L14 20 L22 12" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(div);
        scrollToBottom();
        return id;
    }

    function removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // --- Helpers ---
    function scrollToBottom() {
        const main = document.getElementById('chat-messages');
        main.scrollTop = main.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatMarkdown(text) {
        let html = escapeHtml(text);
        // Bold: **text**
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Italic: *text*
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        // Bullet lists: lines starting with - or *
        html = html.replace(/^[\-\*]\s+(.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
        // Numbered lists
        html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
        // Paragraphs
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');
        html = '<p>' + html + '</p>';
        html = html.replace(/<p>\s*<\/p>/g, '');
        return html;
    }
})();
