class VoiceSearchManager {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.init();
    }

    init() {
        // Check for browser support
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            this.setupSpeechRecognition();
            this.addVoiceSearchButton();
        }
    }

    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
        
        this.recognition.onstart = () => {
            this.isListening = true;
            this.updateVoiceButton('listening');
        };
        
        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            this.handleVoiceQuery(transcript);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.updateVoiceButton('error');
            this.isListening = false;
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            this.updateVoiceButton('idle');
        };
    }

    addVoiceSearchButton() {
        const searchInput = document.querySelector('input[name="keyword"]');
        if (searchInput) {
            const voiceButton = document.createElement('button');
            voiceButton.type = 'button';
            voiceButton.className = 'voice-search-btn';
            voiceButton.innerHTML = '🎤';
            voiceButton.title = 'Voice Search';
            
            voiceButton.addEventListener('click', () => this.toggleVoiceSearch());
            
            // Insert after search input
            searchInput.parentNode.insertBefore(voiceButton, searchInput.nextSibling);
        }
    }

    toggleVoiceSearch() {
        if (this.isListening) {
            this.recognition.stop();
        } else {
            this.recognition.start();
        }
    }

    updateVoiceButton(state) {
        const button = document.querySelector('.voice-search-btn');
        if (!button) return;
        
        switch (state) {
            case 'listening':
                button.innerHTML = '⏸️';
                button.title = 'Stop listening';
                button.classList.add('listening');
                break;
            case 'error':
                button.innerHTML = '❌';
                button.title = 'Voice search error';
                button.classList.add('error');
                setTimeout(() => {
                    button.innerHTML = '🎤';
                    button.title = 'Voice Search';
                    button.classList.remove('error');
                }, 2000);
                break;
            case 'idle':
            default:
                button.innerHTML = '🎤';
                button.title = 'Voice Search';
                button.classList.remove('listening', 'error');
                break;
        }
    }

    handleVoiceQuery(query) {
        // Process voice query and perform search
        const searchInput = document.querySelector('input[name="keyword"]');
        if (searchInput) {
            searchInput.value = query;
            
            // Trigger search
            const searchForm = searchInput.closest('form');
            if (searchForm) {
                searchForm.submit();
            }
        }
        
        // Log voice search for analytics
        this.logVoiceSearch(query);
    }

    logVoiceSearch(query) {
        // Send voice search data to analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'voice_search', {
                'search_term': query,
                'event_category': 'engagement'
            });
        }
    }
}

// Initialize voice search
const voiceSearchManager = new VoiceSearchManager();