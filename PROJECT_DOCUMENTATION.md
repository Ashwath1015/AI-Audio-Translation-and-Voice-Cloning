# Project Documentation: VoiceDub AI

## 📌 Project Overview
**VoiceDub AI** is a professional AI-powered video translation service. The core value proposition is the ability to translate a video into any language while maintaining a native voice through advanced voice synthesis.

The project has evolved from a frontend demo into a full-stack application with a real-time AI processing pipeline, now optimized for local execution to ensure privacy and zero-cost operation.

---

## 🚀 Features & Functionality

### 1. Hero & Landing Experience
- **Dynamic Visual System**: 
  - **Wave Ball**: A central, pulsing orb utilizing overlapping rotating layers to simulate voice frequency waves.
  - **User Orbit**: A coordinated system of 6 rotating user avatars with paired voice logos, symbolizing global connectivity and translation.
- **How it Works**: A 3-step instructional guide (Upload $\rightarrow$ Translate $\rightarrow$ Sync).
- **Theming**: Full Light/Dark mode support with persistence.
- **Information Modals**: A dynamic content system that populates a glassmorphism modal based on footer link interactions (Pricing, Features, API, About, Privacy, Terms, Help, Contact, Status).

### 2. Advanced Upload System
- **File Upload**: Drag-and-drop support with client-side validation (MP4, MOV, WebM) and instant local previews.
- **Backend Integration**: Videos are uploaded to a FastAPI server and stored for processing.

### 3. Options Panel (The AI Configurator)
- **Language Routing**: Support for global languages. To ensure stability and high-quality voice cloning, the system is restricted to officially supported XTTS v2 languages.
- **AI Toggles**: Voice Synthesis and Subtitle options.
- **Legal Consent**: Mandatory confirmation for voice synthesis permissions.

### 4. Local AI Processing Pipeline
The application implements a professional asynchronous pipeline running entirely on local hardware, fully optimized for **NVIDIA GPU (CUDA)** acceleration:

1. **Audio Extraction**: `FFmpeg` extracts the audio track from the source video.
2. **Transcription**: `Local OpenAI Whisper` converts speech to text.
3. **Translation**: `Meta NLLB-200` (Local Model) provides high-quality translation for 200+ languages.
4. **Voice Cloning (Zero-Shot TTS)**: 
   - Uses `Coqui XTTS v2` to analyze the original speaker's voice and synthesize translated text.
   - **Language Restriction**: The pipeline now strictly uses languages supported by XTTS v2 to prevent runtime errors.
   - **Smart Chunking**: Implements sentence-by-sentence synthesis to bypass the 400-token limit of XTTS v2.
   - **Seamless Fallback**: Automatically falls back to `edge-tts` or `gTTS` for unsupported languages.
5. **Merging**: `FFmpeg` merges the cloned/synthesized audio back into the original video.

### 5. Result & Export Screen
- **Comparison View**: Side-by-side playback of original vs. translated videos.
- **Real Exports**: Ability to download the processed video and subtitles.

---

## 🛠 Technical Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JS | User interface, AI visual animations, and API polling logic. |
| **Backend** | FastAPI (Python 3.10) | Pipeline orchestration and API management. |
| **Database** | MongoDB | Job tracking and metadata storage. |
| **AI Models** | Whisper, NLLB-200, XTTS v2 | Local Transcription, Translation, and Voice Cloning. |
| **Hardware Accel**| NVIDIA CUDA | GPU acceleration for faster inference. |
| **Media Processing**| FFmpeg, Pydub | Audio extraction, merging, and chunking. |

---

## 📂 File Structure
- `index.html`: Entry point, UI structure, and modal containers.
- `style.css`: Visual styling, glassmorphism definitions, and complex AI animations.
- `script.js`: Frontend logic, modal content mapping, and backend API communication.
- `backend/main.py`: FastAPI server and Local AI pipeline logic.
- `backend/requirements.txt`: Python dependencies.
- `backend/.env`: Database configuration.

---

## 📝 Implementation Notes
- **Environment Requirements**: Must use **Python 3.10** due to `TTS` library constraints.
- **Visual Logic**: The orbiting visual uses CSS variables and `calc()` for precise geometric placement and synchronous rotation.
- **Security Fixes**: Implements `torch.serialization` safe-globals and environment variables (`COQUI_TOS_AGREED`) for PyTorch 2.6+ security.
- **GPU Acceleration**: Offloads NLLB-200 and XTTS v2 to the GPU to reduce processing time.
- **Asynchronous Workflow**: Uses `asyncio.to_thread` to ensure CPU/GPU-bound AI models do not block the FastAPI event loop.
- **Robustness**: Implemented a hybrid voice synthesis system (XTTS $\rightarrow$ edge-tts $\rightarrow$ gTTS) to handle diverse language support without failure.
