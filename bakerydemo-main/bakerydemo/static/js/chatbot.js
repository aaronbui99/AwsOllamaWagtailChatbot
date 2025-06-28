document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const chatIcon = document.getElementById('chatIcon');
    const chatWindow = document.getElementById('chatWindow');
    const closeChat = document.getElementById('closeChat');
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    
    // Toggle chat window when chat icon is clicked
    chatIcon.addEventListener('click', function() {
        chatWindow.classList.toggle('active');
        if (chatWindow.classList.contains('active')) {
            userInput.focus();
        }
    });
    
    // Close chat window when close button is clicked
    closeChat.addEventListener('click', function() {
        chatWindow.classList.remove('active');
    });
    
    // Send message when send button is clicked
    sendButton.addEventListener('click', sendMessage);
    
    // Send message when Enter key is pressed
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Function to send message
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input field
        userInput.value = '';
        
        // Show loading indicator
        const loadingMessage = addMessage('Thinking...', 'ai', true);
        
        try {
            // Prepare request payload
            const payload = {
                message: message,
                use_bedrock_embeddings: true // Default to using Bedrock embeddings
            };
            
            // Send request to API
            const response = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            // Parse response
            const data = await response.json();
            
            // Remove loading message
            if (loadingMessage) {
                chatMessages.removeChild(loadingMessage);
            }
            
            if (data.error) {
                // Show error message
                addMessage(`Error: ${data.error}`, 'ai');
            } else {
                // Add AI response to chat
                addMessage(data.response, 'ai');
            }
        } catch (error) {
            // Remove loading message
            if (loadingMessage) {
                chatMessages.removeChild(loadingMessage);
            }
            
            // Show error message
            addMessage(`Error: ${error.message}`, 'ai');
        }
    }
    
    // Function to add message to chat
    function addMessage(content, sender, isLoading = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'ai-message'}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isLoading) {
            const loadingSpan = document.createElement('span');
            loadingSpan.className = 'loading-indicator';
            contentDiv.appendChild(loadingSpan);
        }
        
        contentDiv.appendChild(document.createTextNode(content));
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return isLoading ? messageDiv : null;
    }
});