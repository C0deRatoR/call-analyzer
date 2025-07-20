# 🎧 Call Analyzer

Transcribe & analyze recorded c## 🚀 Quick Start

### Option 1: Web Interface (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/C0deRatoR/call-analyzer.git
cd call-analyzer

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file with your Gemini API key
echo "API_KEY=your_gemini_api_key_here" > .env

# 5. Start the web application
cd src
python app.py

# 6. Open your browser and go to: http://127.0.0.1:5000
```

### Option 2: Command Line Interface

```bash
# Process an audio file directly
python src/main.py samples/university_admission.wav
```

### 🔑 Getting Your Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account  
3. Create a new API key
4. Copy the key and paste it in your `.env` file

### 📁 Supported Audio Formats

- WAV, MP3, M4A, FLAC
- Any format supported by FFmpeg

---

## 📖 How It Works

1. **🎤 Upload Audio**: Use the web interface to upload your audio file
2. **📝 Transcription**: Whisper processes the audio locally and generates a transcript
3. **🤖 AI Analysis**: Gemini analyzes the transcript to provide:
   - **Summary**: Key topics and main points discussed
   - **Sentiment**: Emotional tone and mood analysis  
   - **Suggestions**: Alternative counselor responses for better guidance
4. **📊 Results**: View all analysis results in a clean web interface

---

## 🛠️ Development

### Project Structure

- `src/app.py` - Flask web application with file upload and processing endpoints
- `src/main.py` - CLI interface and main processing logic
- `src/whisper_module.py` - Audio transcription using OpenAI Whisper
- `src/gemini_module.py` - AI analysis using Google Gemini API
- `web/index.html` - Clean web interface for uploads and results

### Running in Development Mode

```bash
# Start with debug mode enabled
cd src
python app.py
```

---

## 🔧 Configuration

All configuration is handled through environment variables in the `.env` file:

```env
# Required: Your Google Gemini API key
API_KEY=your_gemini_api_key_here
```

---

## 📋 Requirements

- Python 3.12+
- Virtual environment (recommended)
- Google Gemini API key
- FFmpeg (for audio processing)

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.OpenAI Whisper** and **Google Gemini** (or any LLM).  
Ideal for support, sales, or research teams that need fast insights from audio.

&nbsp;

| 🛠 Tech Stack | 🔖 Status |
|--------------|-----------|
| Python 3.9+  | ![GitHub last commit](https://img.shields.io/github/last-commit/C0deRatoR/call-analyzer?style=flat-square) |
| Whisper CPP / PyTorch | ![Issues](https://img.shields.io/github/issues/C0deRatoR/call-analyzer?style=flat-square) |
| Google Gemini API | ![License](https://img.shields.io/github/license/C0deRatoR/call-analyzer?style=flat-square) |

---

## ✨ Features

- **Accurate transcription** with Whisper (local or API)
- **Summaries & keyword extraction** powered by an LLM (Gemini by default)
- Optional **text‑to‑speech** synthesis for audio demos
- Simple **web interface** (`index.html`) & CLI entry point
- Modular architecture → drop‑in replacement of models or front‑ends

---

## 🗂 Project Layout

```
call-analyzer/
├── src/
│   ├── __init__.py
│   ├── app.py              # Flask web application
│   ├── main.py             # CLI entry point
│   ├── whisper_module.py   # Audio transcription
│   ├── gemini_module.py    # AI analysis (summary, sentiment, suggestions)
│   └── generate_audio.py   # Sample audio generator
├── web/
│   └── index.html          # Web interface
├── samples/
│   └── university_admission.wav  # Sample audio file
├── venv/                   # Virtual environment
├── uploads/                # Uploaded files storage
├── requirements.txt        # Python dependencies
├── .env                   # API keys (create this!)
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/C0deRatoR/call-analyzer.git
cd call-analyzer

# 2. Install dependencies (preferably in a venv)
pip install -r requirements.txt

# 3. Transcribe & analyze an audio file
python src/main.py samples/AudioRec.mp3
