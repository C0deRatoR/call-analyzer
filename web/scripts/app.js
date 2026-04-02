class CallAnalyzer {
    constructor() {
        this.currentFile = null;
        this.isProcessing = false;
        this.theme = localStorage.getItem('theme') || 'light';
        this.charts = {}; // store Chart.js instances
        this.lastData = null; // store last result for re-rendering charts on tab switch
        
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
        
        // Transcript elements
        this.transcriptTurns = document.getElementById('transcriptTurns');
        this.toggleTranscriptBtn = document.getElementById('toggleTranscript');
        this.languageBadge = document.getElementById('languageBadge');

        // Emotion elements
        this.dominantEmotionBadge = document.getElementById('dominantEmotionBadge');
        this.emotionDistribution = document.getElementById('emotionDistribution');
        this.emotionTimeline = document.getElementById('emotionTimeline');
        this.emotionTimelineSection = document.getElementById('emotionTimelineSection');
        this.toggleEmotionBtn = document.getElementById('toggleEmotionDetails');

        // Keyword elements
        this.keywordTags = document.getElementById('keywordTags');
        this.keywordMethodBadge = document.getElementById('keywordMethodBadge');
        
        // Action buttons
        this.analyzeAnotherBtn = document.getElementById('analyzeAnother');
        this.exportResultsBtn = document.getElementById('exportResults');
        this.exportSuggestionsBtn = document.getElementById('exportSuggestions');
        
        // Theme toggle
        this.themeToggle = document.getElementById('themeToggle');

        // Tab elements
        this.tabCards = document.getElementById('tabCards');
        this.tabDashboard = document.getElementById('tabDashboard');
        this.dashboardTab = document.getElementById('dashboardTab');
        this.cardsTab = document.querySelector('.results-section .container > .result-card, .results-section .container');
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
        
        // Transcript toggle
        this.toggleTranscriptBtn.addEventListener('click', () => this.toggleTranscriptView());

        // Emotion timeline toggle
        this.toggleEmotionBtn.addEventListener('click', () => this.toggleEmotionTimeline());

        // Tab switching
        this.tabCards.addEventListener('click', () => this.switchTab('cards'));
        this.tabDashboard.addEventListener('click', () => this.switchTab('dashboard'));
        
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
        this.lastData = data; // store for chart re-render

        // Display transcript
        if (data.diarized_turns && data.diarized_turns.length > 0) {
            this.displayTranscript(data.diarized_turns, data.language);
        } else if (data.transcript) {
            this.transcriptTurns.innerHTML = `<p class="plain-transcript">${data.transcript}</p>`;
        }
        // Display emotions
        if (data.emotions && !data.emotions.error) {
            this.displayEmotions(data.emotions);
        }

        // Display keywords
        if (data.keywords && data.keywords.keywords && data.keywords.keywords.length > 0) {
            this.displayKeywords(data.keywords);
        }

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
        
        this.resultsSection.style.display = 'block';
        this.resultsSection.classList.add('fade-in');

        // Default to cards tab, render charts in background
        this.switchTab('cards');
        setTimeout(() => this.renderDashboardCharts(data), 600);
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

    displayTranscript(turns, language) {
        this.transcriptTurns.innerHTML = '';

        // Show detected language badge
        if (language && language !== 'unknown') {
            this.languageBadge.textContent = language.toUpperCase();
            this.languageBadge.style.display = 'inline-block';
        }

        turns.forEach((turn, index) => {
            const turnEl = document.createElement('div');
            const speakerClass = turn.speaker.toLowerCase().replace(/\s+/g, '-');
            turnEl.className = `transcript-turn ${speakerClass}`;
            turnEl.style.animationDelay = `${index * 0.05}s`;

            const mins = Math.floor(turn.start / 60);
            const secs = Math.floor(turn.start % 60);
            const timestamp = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

            turnEl.innerHTML = `
                <div class="turn-header">
                    <span class="speaker-label ${speakerClass}">${turn.speaker}</span>
                    <div class="turn-meta">
                        ${turn.emotion ? `<span class="emotion-tag emotion-${turn.emotion.primary_emotion}">${this.getEmotionEmoji(turn.emotion.primary_emotion)} ${turn.emotion.primary_emotion}</span>` : ''}
                        <span class="turn-timestamp">${timestamp}</span>
                    </div>
                </div>
                <p class="turn-text">${turn.text}</p>
            `;
            this.transcriptTurns.appendChild(turnEl);
        });
    }

    toggleTranscriptView() {
        const isCollapsed = this.transcriptTurns.classList.contains('collapsed');
        this.transcriptTurns.classList.toggle('collapsed');

        const icon = this.toggleTranscriptBtn.querySelector('i');
        icon.className = isCollapsed ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
    }

    getEmotionEmoji(emotion) {
        const emojis = {
            joy: '😊', anger: '😠', sadness: '😢', fear: '😰',
            surprise: '😮', disgust: '🤢', neutral: '😐', unknown: '❓'
        };
        return emojis[emotion] || '❓';
    }

    getEmotionColor(emotion) {
        const colors = {
            joy: '#22c55e', anger: '#ef4444', sadness: '#3b82f6',
            fear: '#a855f7', surprise: '#f59e0b', disgust: '#84cc16',
            neutral: '#6b7280', unknown: '#9ca3af'
        };
        return colors[emotion] || '#6b7280';
    }

    displayEmotions(emotions) {
        // Dominant emotion badge
        const dominant = emotions.dominant_emotion || 'unknown';
        this.dominantEmotionBadge.textContent = `${this.getEmotionEmoji(dominant)} ${dominant}`;
        this.dominantEmotionBadge.className = `emotion-badge emotion-${dominant}`;

        // Distribution bars
        this.emotionDistribution.innerHTML = '';
        const distribution = emotions.emotion_distribution || {};
        Object.entries(distribution).forEach(([emotion, ratio]) => {
            const percentage = Math.round(ratio * 100);
            const color = this.getEmotionColor(emotion);
            const bar = document.createElement('div');
            bar.className = 'emotion-bar-item';
            bar.innerHTML = `
                <div class="emotion-bar-label">
                    <span>${this.getEmotionEmoji(emotion)} ${emotion}</span>
                    <span class="emotion-bar-value">${percentage}%</span>
                </div>
                <div class="emotion-bar-track">
                    <div class="emotion-bar-fill" style="width: 0%; background: ${color};"></div>
                </div>
            `;
            this.emotionDistribution.appendChild(bar);
            // Animate bar fill
            setTimeout(() => {
                bar.querySelector('.emotion-bar-fill').style.width = `${percentage}%`;
            }, 300);
        });

        // Timeline
        const timeline = emotions.emotion_timeline || [];
        if (timeline.length > 0) {
            this.emotionTimeline.innerHTML = '';
            timeline.forEach((item, i) => {
                const dot = document.createElement('div');
                dot.className = `timeline-dot emotion-${item.emotion}`;
                dot.style.animationDelay = `${i * 0.08}s`;
                const mins = Math.floor(item.start / 60);
                const secs = Math.floor(item.start % 60);
                dot.innerHTML = `
                    <span class="timeline-emoji">${this.getEmotionEmoji(item.emotion)}</span>
                    <span class="timeline-speaker">${item.speaker}</span>
                    <span class="timeline-time">${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}</span>
                `;
                this.emotionTimeline.appendChild(dot);
            });
        }
    }

    toggleEmotionTimeline() {
        const section = this.emotionTimelineSection;
        const isVisible = section.style.display !== 'none';
        section.style.display = isVisible ? 'none' : 'block';
        const icon = this.toggleEmotionBtn.querySelector('i');
        icon.className = isVisible ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
    }

    displayKeywords(keywordsData) {
        this.keywordTags.innerHTML = '';

        // Show method badge
        if (keywordsData.method) {
            this.keywordMethodBadge.textContent = keywordsData.method === 'keybert' ? 'KeyBERT' : 'TF-IDF';
            this.keywordMethodBadge.style.display = 'inline-block';
        }

        const keywords = keywordsData.keywords || [];
        const maxScore = keywords.length > 0 ? keywords[0].score : 1;

        keywords.forEach((kw, index) => {
            const tag = document.createElement('span');
            tag.className = 'keyword-tag';
            tag.style.animationDelay = `${index * 0.06}s`;

            // Scale font size by relevance (0.8rem to 1.15rem)
            const relativeScore = kw.score / maxScore;
            const fontSize = 0.8 + relativeScore * 0.35;
            tag.style.fontSize = `${fontSize}rem`;

            // Higher scores get more opaque gradient
            const opacity = 0.08 + relativeScore * 0.12;
            tag.style.background = `rgba(59, 130, 246, ${opacity})`;

            const scorePercent = Math.round(kw.score * 100);
            tag.innerHTML = `
                <span class="keyword-text">${kw.keyword}</span>
                <span class="keyword-score">${scorePercent}%</span>
            `;
            tag.title = `Relevance: ${scorePercent}%`;
            this.keywordTags.appendChild(tag);
        });
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

    async exportResults() {
        if (!this.lastData) {
            this.showNotification('No analysis data to export', 'warning');
            return;
        }

        const btn = this.exportResultsBtn;
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating PDF...';
        btn.disabled = true;

        try {
            const response = await fetch('/export_pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.lastData)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'PDF generation failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'call-analysis-report.pdf';
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            this.showNotification('PDF report downloaded!', 'success');

        } catch (error) {
            console.error('PDF export error:', error);
            this.showNotification(`PDF export failed: ${error.message}. Falling back to text export.`, 'warning');
            this._exportFallbackText();
        } finally {
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        }
    }

    _exportFallbackText() {
        const summaryText = this.summaryContent.textContent;
        const sentimentText = this.sentimentAnalysis.textContent;
        const suggestionsText = this.suggestionsContent.textContent;
        const results = `Call Analysis Results\n========================\n\nSummary:\n${summaryText}\n\nSentiment Analysis:\n${sentimentText}\n\nAI Suggestions:\n${suggestionsText}\n\nGenerated: ${new Date().toLocaleString()}\n`;
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
        // Re-render charts with updated theme colors
        if (this.lastData && this.dashboardTab && this.dashboardTab.style.display !== 'none') {
            this.renderDashboardCharts(this.lastData);
        }
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

    // ===== TAB SWITCHING =====

    switchTab(tab) {
        const allCards = document.querySelectorAll('.results-section .result-card');
        const actionBtns = document.getElementById('actionButtons');

        if (tab === 'cards') {
            allCards.forEach(c => c.style.display = 'block');
            this.dashboardTab.style.display = 'none';
            if (actionBtns) actionBtns.style.display = 'flex';
            this.tabCards.classList.add('active');
            this.tabDashboard.classList.remove('active');
        } else {
            allCards.forEach(c => c.style.display = 'none');
            this.dashboardTab.style.display = 'block';
            if (actionBtns) actionBtns.style.display = 'none';
            this.tabDashboard.classList.add('active');
            this.tabCards.classList.remove('active');
            // Re-render charts whenever we switch to dashboard
            if (this.lastData) this.renderDashboardCharts(this.lastData);
        }
    }

    // ===== CHART RENDERING =====

    destroyCharts() {
        Object.values(this.charts).forEach(c => { if (c) c.destroy(); });
        this.charts = {};
    }

    getChartDefaults() {
        const isDark = this.theme === 'dark';
        return {
            textColor: isDark ? '#cbd5e1' : '#1e293b',
            gridColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
            bgCard: isDark ? '#1e293b' : '#ffffff',
        };
    }

    renderDashboardCharts(data) {
        this.destroyCharts();
        const defaults = this.getChartDefaults();
        Chart.defaults.color = defaults.textColor;
        Chart.defaults.font.family = "'Inter', sans-serif";

        if (data.sentiment && data.sentiment.detailed_scores) {
            this.renderSentimentPie(data.sentiment.detailed_scores, defaults);
        }
        if (data.emotions && !data.emotions.error) {
            this.renderEmotionBar(data.emotions, defaults);
            this.renderEmotionTimeline(data.emotions, defaults);
        }
        if (data.keywords && data.keywords.keywords && data.keywords.keywords.length > 0) {
            this.renderKeywordBar(data.keywords.keywords, defaults);
        }
    }

    renderSentimentPie(scores, defaults) {
        const vader = scores.vader_scores;
        const ctx = document.getElementById('sentimentPieChart').getContext('2d');
        this.charts.sentimentPie = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Positive', 'Negative', 'Neutral'],
                datasets: [{
                    data: [
                        Math.round(vader.positive * 100),
                        Math.round(vader.negative * 100),
                        Math.round(vader.neutral * 100)
                    ],
                    backgroundColor: ['#10b981', '#ef4444', '#6b7280'],
                    borderColor: defaults.bgCard,
                    borderWidth: 3,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                animation: { animateRotate: true, duration: 900 },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { padding: 16, font: { size: 13 }, color: defaults.textColor }
                    },
                    tooltip: {
                        callbacks: {
                            label: ctx => ` ${ctx.label}: ${ctx.parsed}%`
                        }
                    }
                },
                cutout: '62%'
            }
        });
    }

    renderEmotionBar(emotions, defaults) {
        const distribution = emotions.emotion_distribution || {};
        const emotionColors = {
            joy: '#22c55e', anger: '#ef4444', sadness: '#3b82f6',
            fear: '#a855f7', surprise: '#f59e0b', disgust: '#84cc16', neutral: '#6b7280'
        };
        const labels = Object.keys(distribution).map(e => `${this.getEmotionEmoji(e)} ${e}`);
        const values = Object.values(distribution).map(v => Math.round(v * 100));
        const bgColors = Object.keys(distribution).map(e => emotionColors[e] || '#6b7280');

        const ctx = document.getElementById('emotionBarChart').getContext('2d');
        this.charts.emotionBar = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Distribution (%)',
                    data: values,
                    backgroundColor: bgColors.map(c => c + 'cc'),
                    borderColor: bgColors,
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                animation: { duration: 900 },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: v => v + '%', color: defaults.textColor },
                        grid: { color: defaults.gridColor }
                    },
                    x: {
                        ticks: { color: defaults.textColor },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y}%` } }
                }
            }
        });
    }

    renderEmotionTimeline(emotions, defaults) {
        const timeline = emotions.emotion_timeline || [];
        if (timeline.length === 0) return;

        const emotionToNum = {
            joy: 6, surprise: 5, neutral: 4, disgust: 3, fear: 2, sadness: 1, anger: 0
        };
        const numToLabel = ['anger', 'sadness', 'fear', 'disgust', 'neutral', 'surprise', 'joy'];
        const emotionColors = {
            joy: '#22c55e', anger: '#ef4444', sadness: '#3b82f6',
            fear: '#a855f7', surprise: '#f59e0b', disgust: '#84cc16', neutral: '#6b7280'
        };

        const timeLabels = timeline.map((item, i) => {
            const m = Math.floor(item.start / 60);
            const s = Math.floor(item.start % 60);
            return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
        });
        const dataPoints = timeline.map(item => emotionToNum[item.emotion] ?? 4);
        const pointColors = timeline.map(item => emotionColors[item.emotion] || '#6b7280');
        const speakers = timeline.map(item => item.speaker);

        const ctx = document.getElementById('emotionTimelineChart').getContext('2d');
        this.charts.emotionTimeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [{
                    label: 'Emotion',
                    data: dataPoints,
                    borderColor: 'rgba(139, 92, 246, 0.8)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: {
                        target: 'origin',
                        above: 'rgba(139, 92, 246, 0.08)'
                    },
                    pointBackgroundColor: pointColors,
                    pointBorderColor: pointColors,
                    pointRadius: 6,
                    pointHoverRadius: 9
                }]
            },
            options: {
                responsive: true,
                animation: { duration: 1000 },
                scales: {
                    y: {
                        min: 0,
                        max: 6,
                        ticks: {
                            stepSize: 1,
                            callback: v => `${this.getEmotionEmoji(numToLabel[v])} ${numToLabel[v]}`,
                            color: defaults.textColor
                        },
                        grid: { color: defaults.gridColor }
                    },
                    x: {
                        ticks: { color: defaults.textColor, maxRotation: 45 },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) => `Time: ${items[0].label}`,
                            label: (ctx) => ` ${speakers[ctx.dataIndex]}: ${this.getEmotionEmoji(numToLabel[ctx.parsed.y])} ${numToLabel[ctx.parsed.y]}`
                        }
                    }
                }
            }
        });
    }

    renderKeywordBar(keywords, defaults) {
        const labels = keywords.map(kw => kw.keyword);
        const values = keywords.map(kw => Math.round(kw.score * 100));
        const intensities = keywords.map((kw, i) => {
            const alpha = Math.round(0.45 + (kw.score / keywords[0].score) * 0.55 * 255).toString(16).padStart(2, '0');
            return `#3b82f6${alpha}`;
        });

        const ctx = document.getElementById('keywordBarChart').getContext('2d');
        this.charts.keywordBar = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Relevance (%)',
                    data: values,
                    backgroundColor: intensities,
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                animation: { duration: 900 },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: v => v + '%', color: defaults.textColor },
                        grid: { color: defaults.gridColor }
                    },
                    y: {
                        ticks: { color: defaults.textColor, font: { size: 13 } },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.x}% relevance` } }
                }
            }
        });
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
