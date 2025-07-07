// Cloud Functions API URL'si - Bu URL'i Cloud Functions deploy ettikten sonra güncelleyin
const API_URL = 'https://YOUR_REGION-YOUR_PROJECT_ID.cloudfunctions.net/ptiboxmain';

let sessionId = null;

// DOM elementlerini al
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');

// Mesaj gönderme fonksiyonu
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Kullanıcı mesajını ekle
    addMessage(message, 'user');
    messageInput.value = '';
    sendButton.disabled = true;

    // Typing indicator ekle
    const typingIndicator = addTypingIndicator();

    try {
        // API'ye mesaj gönder
        const response = await fetch(`${API_URL}/get_response`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        // Typing indicator'ı kaldır
        typingIndicator.remove();

        if (response.ok) {
            const data = await response.json();
            
            // Session ID'yi kaydet
            if (data.session_id) {
                sessionId = data.session_id;
            }

            // Bot yanıtını ekle
            addMessage(data.response, 'bot');
        } else {
            throw new Error('API yanıt vermedi');
        }
    } catch (error) {
        console.error('Hata:', error);
        typingIndicator.remove();
        addMessage('Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.', 'bot');
    } finally {
        sendButton.disabled = false;
        messageInput.focus();
    }
}

// Mesaj ekleme fonksiyonu
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageText = document.createElement('p');
    messageText.textContent = text;
    
    messageContent.appendChild(messageText);
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    
    // Otomatik scroll
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Typing indicator ekleme fonksiyonu
function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message';
    
    const typingContent = document.createElement('div');
    typingContent.className = 'typing-indicator';
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'typing-dot';
        typingContent.appendChild(dot);
    }
    
    typingDiv.appendChild(typingContent);
    chatMessages.appendChild(typingDiv);
    
    // Otomatik scroll
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return typingDiv;
}

// Event listeners
sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Input focus
messageInput.focus();

// Sayfa yüklendiğinde session ID oluştur
window.addEventListener('load', () => {
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}); 