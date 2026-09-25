# VoiceDub AI - AI-Powered Video Translation 🎙️🌐

VoiceDub AI is a full-stack application that allows users to translate videos into multiple global languages while maintaining a natural voice. The platform features a professional end-to-end workflow from video upload to final dubbed export, powered by a **local-first AI pipeline** for privacy and zero-cost operation.

## ✨ Key Features

- **Local AI Processing**: A complete pipeline that runs on your own hardware—no expensive API keys required.
- **Native Voice Synthesis**: Generates translated speech in multiple languages using high-quality synthesis.
- **Advanced Upload System**: 
  - Drag-and-drop interface with client-side video validation.
  - Instant local video previews.
- **Interactive AI Configurator**: 
  - Source and target language selection.
  - Voice style and subtitle toggles.
- **Dynamic Visuals**: An interactive, rotating AI visualization system featuring orbiting user avatars and a central wave-frequency ball.
- **Multi-Stage Processing Pipeline**: A real asynchronous sequence: *Upload $\rightarrow$ Extract $\rightarrow$ Transcribe $\rightarrow$ Translate $\rightarrow$ Synthesize $\rightarrow$ Merge*.
- **Comparison Suite**: Side-by-side video playback to compare original and translated content.
- **Dynamic Theming**: Full Light and Dark mode support with persistence.
- **Integrated Info System**: Glassmorphism modal system providing detailed product, company, and support information.

## 📺 Demo

Experience the AI translation pipeline in action.

| Original Video | Translated Video (Hindi) |
| :---: | :---: |
| [▶️ Watch Original](dummy%20for%20AT.mp4) | [▶️ Watch Translated](translated.mp4) |

**Description:** The original video is processed through the AI pipeline to translate the audio into **Hindi** while maintaining synchronization and natural flow.

## 🛠️ Technical Stack

- **Frontend**: HTML5, CSS3 (Glassmorphism), and JavaScript (ES6+).
- **Backend**: FastAPI (Python) for high-performance orchestration.
- **Database**: MongoDB for job tracking and metadata.
- **Local AI Models**: 
  - **Transcription**: OpenAI Whisper (Local)
  - **Translation**: Argos Translate (Offline)
  - **Voice**: gTTS (Google Text-to-Speech)
- **Media Engine**: FFmpeg for audio/video manipulation.

## 🚀 Getting Started

### 1. Prerequisites
- Install **Python 3.x**
- Install **MongoDB** (running on `localhost:27017`)
- Install **FFmpeg** (must be added to your system PATH)

### 2. Backend Setup
```bash
# Navigate to backend folder
cd backend

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

### 3. Frontend Launch
Simply open `index.html` in any modern web browser.

## 📂 Project Structure

- `index.html`: The main entry point containing the UI structure.
- `style.css`: Global styles, theme definitions, and AI visual animations.
- `script.js`: Interactive logic, info modal management, and backend API communication.
- `backend/main.py`: FastAPI server and local AI pipeline logic.
- `PROJECT_DOCUMENTATION.md`: Detailed technical documentation.

---
*Built to showcase the power of local AI for video localization.*
