document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');

    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Send message on Enter (but allow new lines with Shift+Enter)
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Send message on button click
    sendButton.addEventListener('click', sendMessage);

    async function getAIResponse(message) {
        try {
            const response = await fetch('http://localhost:5000/get_response', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ message })
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('API Yanıt:', errorText);
                throw new Error(`API Hatası (${response.status}): ${errorText}`);
            }

            const data = await response.json();
            console.log('API Yanıtı:', data);

            if (!data.response) {
                console.error('Geçersiz API yanıtı:', data);
                throw new Error('API yanıtı beklenen formatta değil');
            }

            return data.response;
        } catch (error) {
            console.error('API Hatası:', error);
            throw error;
        }
    }

    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Kullanıcı mesajını sohbete ekle
        addMessage(message, 'user');

        // Input'u temizle ve butonu devre dışı bırak
        chatInput.value = '';
        chatInput.style.height = 'auto';
        sendButton.disabled = true;

        try {
            // Yazıyor göstergesi ekle
            const typingIndicator = addTypingIndicator();

            // AI yanıtını al
            const aiResponse = await getAIResponse(message);

            // Yazıyor göstergesini kaldır
            typingIndicator.remove();

            // AI yanıtını sohbete ekle
            addMessage(aiResponse, 'assistant');
        } catch (error) {
            console.error('Mesaj gönderme hatası:', error);
            addMessage('Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.', 'assistant');
        } finally {
            sendButton.disabled = false;
            chatInput.focus();
        }
    }

    function addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        typingDiv.innerHTML = `
            <div class="assistant-avatar">
                <img src="patibox-assistant.png" alt="PatiboxAI Assistant">
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return typingDiv;
    }

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        let messageHTML = '';
        if (sender === 'assistant') {
            messageHTML = `
                <div class="assistant-avatar">
                    <img src="patibox-assistant.png" alt="PatiboxAI Assistant">
                </div>
            `;
        }

        messageHTML += `
            <div class="message-content">
                <p>${text}</p>
            </div>
        `;

        messageDiv.innerHTML = messageHTML;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}); 