class ChatInterface {
    constructor() {
        this.chatOutput = document.getElementById('chatOutput');
        this.userInput = document.getElementById('userInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.currentMessageContainer = null;
        this.sessionId = crypto.randomUUID();

        // Event listeners
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.clearBtn.addEventListener('click', () => this.clearChat());
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    appendMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        messageDiv.textContent = text;
        this.chatOutput.appendChild(messageDiv);
        this.chatOutput.scrollTop = this.chatOutput.scrollHeight;
        return messageDiv;
    }

    clearChat() {
        while (this.chatOutput.firstChild) {
            this.chatOutput.removeChild(this.chatOutput.firstChild);
        }
        
        fetch('http://localhost:8080/retrieve/conversation/clear', {
            method: 'POST',
            headers: {
                'X-Session-ID': this.sessionId
            }
        }).catch(error => {
            console.error('Error clearing chat history:', error);
        });
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message) return;

        // Append user message
        this.appendMessage(message, true);
        this.userInput.value = '';

        // Create container for assistant's response
        this.currentMessageContainer = this.appendMessage('');
        const loadingSpan = document.createElement('span');
        loadingSpan.className = 'loading';
        this.currentMessageContainer.appendChild(loadingSpan);

        try {
            const url = new URL('http://localhost:8080/retrieve/search');
            url.searchParams.append('query', message);
            url.searchParams.append('search_type', 'focused');

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Session-ID': this.sessionId
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Create a container for the response
            const responseContainer = document.createElement('div');
            responseContainer.className = 'response-container';

            // Add the answer
            const answerDiv = document.createElement('div');
            answerDiv.className = 'answer';
            answerDiv.textContent = data.answer;
            responseContainer.appendChild(answerDiv);

            // Add citations if present
            if (data.citations && data.citations.length > 0) {
                data.citations.forEach(citation => {
                    const citationDiv = document.createElement('div');
                    citationDiv.className = 'citation';
                    let citationText = `Source: ${citation.document}`;
                    if (citation.date) {
                        citationText += ` (${citation.date})`;
                    }
                    if (citation.section) {
                        citationText += ` - ${citation.section}`;
                    }
                    citationDiv.textContent = citationText;
                    responseContainer.appendChild(citationDiv);
                });
            }

            // Replace the current message container content with the response container
            this.currentMessageContainer.textContent = '';
            this.currentMessageContainer.appendChild(responseContainer);

            // Ensure the chat container scrolls to the latest message
            this.chatOutput.scrollTop = this.chatOutput.scrollHeight;

        } catch (error) {
            console.error('Error:', error);
            this.currentMessageContainer.textContent = `Error: ${error.message}`;
        } finally {
            const loadingSpan = this.currentMessageContainer.querySelector('.loading');
            if (loadingSpan) {
                loadingSpan.remove();
            }
        }
    }
}

// Initialize chat interface when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new ChatInterface();
}); 