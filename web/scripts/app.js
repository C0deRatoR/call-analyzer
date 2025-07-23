class CallAnalyzer {
    constructor() {
        this.currentFile = null;
        this.isProcessing = false;
        this.theme = localStorage.getItem('theme') || 'light';
        
        this.initializeElements();
        this.attachEventListeners();
        this.initializeTheme();
        this.setupAnimations();
    }

    initializeElements() {
        // File upload elements
        this.fileDropZone = document.getElementById('fileDropZone');
        this.fileInput = document.getElementById('audioFile');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.getElementById('fileName');
        this.fileSize = document.getElementById('fileSize');
        this.removeFileBtn = document.getElementById('removeFile');
        
        // Form and button elements
        this.uploadForm = document.getElementById('uploadForm');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.btnText = this.analyzeBtn.querySelector('.btn-text');
        this.btnLoader = this.analyzeBtn.querySelector('.btn-loader');
        
        // Processing elements
        this.processingSection = document.getElementById('processingSection');
        this.progressFill = document.getElementById('progressFill');
        this.processingStatus = document.getElementById('processingStatus');
        this.steps = document.querySelectorAll('.step');
        
        // Results elements
        this.resultsSection = document.getElementById('resultsSection');
        this.summaryContent = document.getElementById('summaryContent');
        this.sentimentAnalysis = document.getElementById('sentimentAnalysis');
        this.suggestionsContent = document.getElementById('suggestionsContent');
        
        // Sentiment details
        this.sentimentBadge = document.getElementById('sentimentBadge');
        this.confidenceValue = document.getElementById('confidenceValue');
        this.sentimentDetails = document.getElementById('sentimentDetails');
        this.toggleSentimentDetails = document.getElementById('toggleSentimentDetails');
        
        // Score elements
        this.positiveBar = document.getElementById('positiveBar');
        this.negativeBar = document.getElementById('negativeBar');
        this.neutralBar = document.getElementById('neutralBar');
        this.positiveValue = document.getElementById('positiveValue');
        this.negativeValue = document.getElementById('negativeValue');
        this.neutralValue = document.getElementById('neutralValue');
        this.compoundScore = document.getElementById('compoundScore');
        
        // Emotional indicators
        this.emotionalIndicators = document.getElementById('emotionalIndicators');
        this.indicatorsList = document.getElementById('indicatorsList');
        
        // Action buttons
        this.analyzeAnotherBtn = document.getElementById('analyzeAnother');
        this.exportResultsBtn = document.getElementById('exportResults');
        this.exportSuggestionsBtn = document.getElementById('exportSuggestions');
        
        // Theme toggle
        this.themeToggle = document.getElementById('themeToggle');
    }

    attachEventListeners() {
        // File upload events
        this.fileDropZone.addEventListener('click', () => this.fileInput.click());
        this.fileDropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.fileDropZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.fileDropZone.addEventListener('drop', (e) => this.handleDrop(e));
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.removeFileBtn.addEventListener('click', () => this.removeFile());
        
        // Form submission
        this.uploadForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Sentiment details toggle
        this.toggleSentimentDetails.addEventListener('click', () => this.toggleSentimentDetailsView());
        
        // Action buttons
        this.analyzeAnotherBtn.addEventListener('click', () => this.resetAnalysis());
        this.exportResultsBtn.addEventListener('click', () => this.exportResults());
        this.exportSuggestionsBtn.addEventListener('click', () => this.exportSuggestions());
        
        // Theme toggle
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });
    }

    initializeTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        this.updateThemeIcon();
    }

    setupAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animationDelay = '0s';
                    entry.target.classList.add('fade-in');
                }
            });
        }, observerOptions);

        // Observe elements for animation
        document.querySelectorAll('.result-card').forEach(card => {
            observer.observe(card);
        });
    }

    handleDragOver(e) {
        e.preventDefault();
        this.fileDropZone.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.fileDropZone.classList.remove('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        this.fileDropZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    processFile(file) {
        // Validate file type
        const allowedTypes = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/m4a', 'audio/flac', 'audio/ogg'];
        if (!allowedTypes.includes(file.type) && !this.isAudioFile(file.name)) {
            this.showNotification('Please select a valid audio file (MP3, WAV, M4A, FLAC)', 'error');
            return;
        }

        // Validate file size (100MB limit)
        const maxSize = 100 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showNotification('File size must be less than 100MB', 'error');
            return;
        }

        this.currentFile = file;
        this.displayFileInfo(file);
        this.analyzeBtn.disabled = false;
    }

    isAudioFile(filename) {
        const audioExtensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'];
        return audioExtensions.some(ext => filename.toLowerCase().endsWith(ext));
    }

    displayFileInfo(file) {
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.formatFileSize(file.size);
        this.fileInfo.style.display = 'block';
        this.fileInfo.classList.add('slide-up');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    removeFile() {
        this.currentFile = null;
        this.fileInput.value = '';
        this.fileInfo.style.display = 'none';
        this.analyzeBtn.disabled = true;
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        
        if (!this.currentFile || this.isProcessing) {
            return;
        }

        this.isProcessing = true;
        this.showProcessingState();
        this.simulateProcessingSteps();

        try {
            const formData = new FormData();
            formData.append('audio_file', this.currentFile);

            const response = await fetch('/process_audio', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.displayResults(data);
                this.showCompletedState();
            } else {
                throw new Error(data.error || 'Processing failed');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
            this.resetProcessingState();
        } finally {
            this.isProcessing = false;
        }
    }

    showProcessingState() {
        // Hide upload section and show processing
        document.querySelector('.upload-section').style.display = 'none';
        this.processingSection.style.display = 'block';
        this.resultsSection.style.display = 'none';
        
        // Reset processing state
        this.steps.forEach(step => {
            step.classList.remove('active', 'completed');
        });
        this.progressFill.style.width = '0%';
        this.processingStatus.textContent = 'Preparing analysis...';
        
        // Smooth scroll to processing section
        this.processingSection.scrollIntoView({ behavior: 'smooth' });
    }

    simulateProcessingSteps() {
        const steps = [
            { element: this.steps[0], text: 'Uploading file...', progress: 25 },
            { element: this.steps[1], text: 'Transcribing audio...', progress: 50 },
            { element: this.steps[2], text: 'Analyzing sentiment...', progress: 75 },
            { element: this.steps[3], text: 'Generating insights...', progress: 100 }
        ];

        steps.forEach((step, index) => {
            setTimeout(() => {
                // Mark previous steps as completed
                steps.slice(0, index).forEach(prevStep => {
                    prevStep.element.classList.remove('active');
                    prevStep.element.classList.add('completed');
                });
                
                // Mark current step as active
                step.element.classList.add('active');
                
                // Update progress
                this.progressFill.style.width = `${step.progress}%`;
                this.processingStatus.textContent = step.text;
            }, index * 1000);
        });
    }

    showCompletedState() {
        // Mark all steps as completed
        this.steps.forEach(step => {
            step.classList.remove('active');
            step.classList.add('completed');
        });
        
        this.processingStatus.textContent = 'Analysis complete!';
        
        // Show results after a short delay
        setTimeout(() => {
            this.processingSection.style.display = 'none';
            this.resultsSection.style.display = 'block';
            this.resultsSection.scrollIntoView({ behavior: 'smooth' });
        }, 1000);
    }

    resetProcessingState() {
        this.processingSection.style.display = 'none';
        document.querySelector('.upload-section').style.display = 'block';
    }

    displayResults(data) {
        // Display summary
        this.summaryContent.textContent = data.summary || 'No summary available';
        
        // Display sentiment analysis
        if (data.sentiment) {
            // Gemini analysis
            const geminiAnalysis = data.sentiment.gemini_analysis || 'No sentiment analysis available';
            this.sentimentAnalysis.textContent = geminiAnalysis;
            
            // VADER scores
            if (data.sentiment.detailed_scores) {
                this.displaySentimentScores(data.sentiment.detailed_scores);
            }
        }
        
        // Display suggestions
        this.displaySuggestions(data.suggestion);
        
        // Show results section
        this.resultsSection.style.display = 'block';
        this.resultsSection.classList.add('fade-in');
    }

    displaySentimentScores(detailedScores) {
        const scores = detailedScores.vader_scores;
        const sentimentLabel = detailedScores.sentiment_label || 'neutral';
        const confidence = detailedScores.confidence || 'medium';
        
        // Update sentiment badge and confidence
        this.sentimentBadge.textContent = sentimentLabel.replace('_', ' ');
        this.sentimentBadge.className = `sentiment-badge ${sentimentLabel}`;
        this.confidenceValue.textContent = confidence;
        
        // Update score bars with animation
        this.animateScoreBar(this.positiveBar, this.positiveValue, scores.positive);
        this.animateScoreBar(this.negativeBar, this.negativeValue, scores.negative);
        this.animateScoreBar(this.neutralBar, this.neutralValue, scores.neutral);
        
        // Update compound score
        this.compoundScore.textContent = scores.compound.toFixed(3);
        
        // Display emotional indicators
        if (detailedScores.emotional_indicators && detailedScores.emotional_indicators.length > 0) {
            this.displayEmotionalIndicators(detailedScores.emotional_indicators);
        }
    }

    animateScoreBar(barElement, valueElement, score) {
        const percentage = Math.round(score * 100);
        
        // Animate the bar width
        setTimeout(() => {
            barElement.style.width = `${percentage}%`;
            valueElement.textContent = `${percentage}%`;
        }, 500);
    }

    displayEmotionalIndicators(indicators) {
        this.indicatorsList.innerHTML = '';
        
        indicators.forEach((indicator, index) => {
            const tag = document.createElement('span');
            tag.className = `indicator-tag ${indicator}`;
            tag.textContent = indicator.replace('_', ' ');
            tag.style.animationDelay = `${index * 0.1}s`;
            tag.classList.add('fade-in');
            this.indicatorsList.appendChild(tag);
        });
        
        this.emotionalIndicators.style.display = 'block';
    }

    displaySuggestions(suggestions) {
        if (!suggestions) {
            this.suggestionsContent.innerHTML = '<p>No suggestions available</p>';
            return;
        }

        if (typeof suggestions === 'string') {
            // Parse suggestions if they contain numbered points or bullet points
            const lines = suggestions.split('\n').filter(line => line.trim());
            const listItems = lines
                .filter(line => /^\d+\./.test(line.trim()) || line.includes('*') || line.includes('•'))
                .map(line => line.replace(/^[\d\.\*\•\s]+/, '').trim())
                .filter(line => line.length > 0);
            
            if (listItems.length > 0) {
                this.suggestionsContent.innerHTML = '<ol>' + 
                    listItems.map(item => `<li>${item}</li>`).join('') + 
                    '</ol>';
            } else {
                this.suggestionsContent.innerHTML = `<p>${suggestions}</p>`;
            }
        } else {
            this.suggestionsContent.innerHTML = '<p>No suggestions available</p>';
        }
    }

    toggleSentimentDetailsView() {
        const isVisible = this.sentimentDetails.style.display !== 'none';
        this.sentimentDetails.style.display = isVisible ? 'none' : 'block';
        
        const icon = this.toggleSentimentDetails.querySelector('i');
        icon.className = isVisible ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
        
        if (!isVisible) {
            this.sentimentDetails.classList.add('slide-up');
        }
    }

    resetAnalysis() {
        // Reset all sections
        this.resultsSection.style.display = 'none';
        this.processingSection.style.display = 'none';
        document.querySelector('.upload-section').style.display = 'block';
        
        // Reset file upload
        this.removeFile();
        
        // Reset sentiment details
        this.sentimentDetails.style.display = 'none';
        this.emotionalIndicators.style.display = 'none';
        
        // Scroll to top
        document.querySelector('.upload-section').scrollIntoView({ behavior: 'smooth' });
    }

    exportResults() {
        const summaryText = this.summaryContent.textContent;
        const sentimentText = this.sentimentAnalysis.textContent;
        const suggestionsText = this.suggestionsContent.textContent;
        
        const results = `Call Analysis Results
========================

Summary:
${summaryText}

Sentiment Analysis:
${sentimentText}

AI Suggestions:
${suggestionsText}

Generated on: ${new Date().toLocaleString()}
`;
        
        this.downloadTextFile(results, 'call-analysis-results.txt');
    }

    exportSuggestions() {
        const suggestionsText = this.suggestionsContent.textContent;
        const content = `AI Counselor Suggestions
========================

${suggestionsText}

Generated on: ${new Date().toLocaleString()}
`;
        
        this.downloadTextFile(content, 'counselor-suggestions.txt');
    }

    downloadTextFile(content, filename) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        this.showNotification('File downloaded successfully!', 'success');
    }

    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', this.theme);
        localStorage.setItem('theme', this.theme);
        this.updateThemeIcon();
    }

    updateThemeIcon() {
        const icon = this.themeToggle.querySelector('i');
        icon.className = this.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + U to trigger file upload
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            if (!this.isProcessing) {
                this.fileInput.click();
            }
        }
        
        // Ctrl/Cmd + Enter to start analysis
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (this.currentFile && !this.isProcessing) {
                this.uploadForm.dispatchEvent(new Event('submit'));
            }
        }
        
        // Escape to reset analysis
        if (e.key === 'Escape') {
            if (this.resultsSection.style.display !== 'none') {
                this.resetAnalysis();
            }
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Add styles
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: type === 'error' ? 'var(--error)' : type === 'success' ? 'var(--success)' : 'var(--info)',
            color: 'white',
            padding: '1rem 1.5rem',
            borderRadius: '0.5rem',
            boxShadow: 'var(--shadow-lg)',
            zIndex: '1000',
            animation: 'slideInRight 0.3s ease-out',
            maxWidth: '400px'
        });
        
        document.body.appendChild(notification);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    getNotificationIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            default: return 'info-circle';
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CallAnalyzer();
});

// Add notification animations to CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
`;
document.head.appendChild(style);
