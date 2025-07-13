# 🎧 Call Analyzer

Transcribe & analyze recorded calls with **OpenAI Whisper** and **Google Gemini** (or any LLM).  
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

<pre>

call-analyzer/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── whisper_module.py
│   ├── gemini_module.py
│   ├── generate_audio.py
│   └── app.py
├── web/
│   └── index.html
├── samples/
│   └── AudioRec.mp3
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md

</pre>

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
