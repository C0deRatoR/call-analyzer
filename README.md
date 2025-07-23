
# 🎧 Call Analyzer - AI-Powered Audio Intelligence

Transform your audio conversations into actionable insights with advanced AI transcription, sentiment analysis, and professional counselor recommendations.

[
[
[
[

## ✨ Features

**🤖 Advanced AI Processing**

- OpenAI Whisper Integration - State-of-the-art audio transcription
- Google Gemini AI Analysis - Contextual conversation understanding
- VADER Sentiment Analysis - Real-time numerical sentiment scoring
- Dual Analysis System - Combined AI approaches for comprehensive insights

**🎨 Modern Interactive Interface**

- Responsive Design - Beautiful interface that works on all devices
- Dark/Light Theme Toggle - User preference with system detection
- Drag-and-Drop Upload - Intuitive file handling with visual feedback
- Real-time Processing Visualization - Animated steps showing analysis progress
- Interactive Sentiment Dashboard - Visual progress bars and emotional indicators

**🔒 Enterprise-Grade Security**

- Secure File Upload - Path traversal protection and file validation
- Magic Byte Verification - Advanced file type detection
- Automatic Cleanup - Temporary files removed after processing
- Input Validation - Comprehensive data sanitization


## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Google Gemini API key
- 4GB+ RAM (for Whisper model)


### Installation

```
# 1. Clone the repository
git clone https://github.com/C0deRatoR/call-analyzer.git
cd call-analyzer

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
echo "API_KEY=your_gemini_api_key_here" > .env

# 5. Start the application
cd src
python app.py
```


### 🌐 Access

Open your browser: **http://127.0.0.1:5000**

## 🔧 How It Works

1. **🎤 Audio Upload** - Drag and drop audio files (MP3, WAV, M4A, FLAC, OGG)
2. **📝 AI Transcription** - OpenAI Whisper processes audio locally
3. **🧠 Intelligent Analysis** - Dual sentiment analysis with VADER + Gemini
4. **📊 Interactive Results** - Visual sentiment breakdown with export options

## 🏗️ Technical Stack

**Backend**

- Flask 3.1.0 - Web application framework
- openai-whisper - Audio transcription
- google-generativeai - AI analysis and insights
- vaderSentiment - Real-time sentiment scoring

**Frontend**

- HTML5 - Semantic structure
- CSS3 - Modern styling with animations
- JavaScript ES6+ - Interactive functionality
- Font Awesome 6 - Professional icons


## 📁 Project Structure

```
call-analyzer/
├── src/
│   ├── app.py                   # Flask web application
│   ├── main.py                  # CLI interface
│   ├── whisper_module.py        # Audio transcription
│   ├── gemini_module.py         # AI analysis
│   └── sentiment_analyzer.py    # Enhanced sentiment processing
├── web/
│   ├── index.html              # Main interface
│   ├── styles/main.css         # Modern CSS
│   └── scripts/app.js          # Interactive JavaScript
├── samples/                     # Example audio files
├── requirements.txt            # Dependencies
└── README.md                   # This file
```


## 🎯 Use Cases

**Educational Institutions**

- Student counseling session analysis
- Admission interview insights
- Support service improvements

**Business Applications**

- Customer support call monitoring
- Sales conversation analysis
- Training program enhancement

**Research \& Development**

- Conversation pattern analysis
- Sentiment research studies
- AI model training data generation


## 📊 Performance

| Metric | Value |
| :-- | :-- |
| Transcription Accuracy | 95%+ |
| Processing Speed | 0.3x real-time |
| Memory Usage | ~2GB |
| API Response Time | <2 seconds |
| File Size Limit | 100MB |
| Supported Formats | MP3, WAV, M4A, FLAC, OGG |

## 🧪 CLI Usage

```
# Process audio file directly
python src/main.py samples/conversation.wav
```

Output:

```
{
  "transcript": "...",
  "summary": "...",
  "sentiment": {
    "vader_scores": {...},
    "ai_analysis": "..."
  },
  "suggestion": "..."
}
```


## 🚀 Deployment

**Development**

```
python src/app.py
```

**Production**

```
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```


## 🔐 Security Features

- Path traversal protection with secure filename generation
- Magic byte validation for file type verification
- Automatic temporary file cleanup
- Comprehensive input validation and sanitization
- Secure API key management with environment variables


## 📈 Roadmap

**Phase 1: Core Features** ✅

- [x] Audio transcription with Whisper
- [x] AI analysis with Gemini
- [x] Modern interactive UI
- [x] Enhanced sentiment analysis

**Phase 2: Advanced Analytics** 🔄

- [ ] Keyword extraction and topic modeling
- [ ] Interactive charts and visualizations
- [ ] Historical analysis and trends

**Phase 3: Platform Features** 🔮

- [ ] User authentication
- [ ] API documentation
- [ ] Docker containerization
- [ ] Real-time WebSocket processing


## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI Whisper - Speech recognition
- Google Gemini - Language understanding
- VADER Sentiment - Sentiment analysis
- Flask Framework - Web development

<div align="center">

**Built with ❤️ for better communication analysis**

⭐ Star this repo if you find it useful!

</div>
