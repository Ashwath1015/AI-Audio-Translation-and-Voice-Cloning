import os
os.environ["COQUI_TOS_AGREED"] = "1"

# Windows-specific fix for NotImplementedError with asyncio subprocesses
import asyncio
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import shutil
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import requests
from gtts import gTTS
import edge_tts
import torch


# Fix for PyTorch 2.6+ weights_only security error
# Coqui TTS uses many custom classes. We allow them by adding them to the safe list.
try:
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import XttsAudioConfig
    from TTS.config.shared_configs import BaseDatasetConfig
    torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig])
except ImportError:
    pass

try:
    from TTS.api import TTS
    HAS_TTS = True
except ImportError:
    print("\n⚠️ TTS (Coqui) not installed. Voice cloning will be disabled. Falling back to gTTS.")
    HAS_TTS = False
import whisper
from deep_translator import GoogleTranslator, MyMemoryTranslator
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

load_dotenv()

app = FastAPI(title="VoiceDub AI Backend (Local Edition)")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "voicedub_db")
UPLOAD_DIR = Path(os.getenv("UPLOAD_FOLDER", "uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)

# Create a downloads folder for the final processed videos
DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Serve the downloads folder so the frontend can play the videos
app.mount("/downloads", StaticFiles(directory=DOWNLOADS_DIR), name="downloads")

# Database Connection
client_mongo = AsyncIOMotorClient(MONGODB_URL)
db = client_mongo[DATABASE_NAME]

# Pydantic Models
class FallbackToEdgeTTS(Exception):
    """Custom exception to trigger edge-tts fallback in the main async loop."""
    def __init__(self, voice):
        self.voice = voice
        super().__init__()

class TranslationRequest(BaseModel):
    source_lang: str
    target_lang: str
    voice_style: str
    voice_cloning: bool
    add_subtitles: bool

class VideoStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    result_url: Optional[str] = None

import traceback

# --- LOCAL AI MODELS ---
# Load NLLB-200 for local translation (distilled 600M version for efficiency)
print("\n" + "="*50)
print("Loading local translation model (NLLB-200)...")
print("Note: First run will download ~600MB-1GB of data.")
print("="*50)

translation_model = None
translation_tokenizer = None
try:
    model_name = "facebook/nllb-200-distilled-600M"
    translation_tokenizer = AutoTokenizer.from_pretrained(model_name)
    # Use CUDA if available for translation
    device = "cuda" if torch.cuda.is_available() else "cpu"
    translation_model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
    print(f"✅ Local translation model loaded successfully on {device}.")
except Exception as e:
    print("\n❌ ERROR LOADING LOCAL TRANSLATION MODEL")
    print(f"Error details: {e}")
    traceback.print_exc()
    print("\nPossible fixes:")
    print("1. Check your internet connection for the initial download.")
    print("2. Ensure you have at least 2GB of free disk space.")
    print("3. Ensure you have at least 4GB of available RAM.")
    print("="*50 + "\n")

async def detect_gender(audio_path: str):
    """
    Detects speaker gender using a more robust median pitch analysis.
    Returns 'Male' or 'Female'.
    """
    def run_detection():
        try:
            from librosa import load
            import numpy as np
            import librosa

            y, sr = load(audio_path)
            # Use piptrack to find pitches across the audio
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

            # For each time frame, find the pitch with the maximum magnitude
            # This gives us a sequence of dominant pitches over time
            dominant_pitches = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0: # Filter out silence/zero pitch
                    dominant_pitches.append(pitch)

            if not dominant_pitches:
                return "Female" # Default fallback

            # Use the median pitch to avoid outliers (e.g., noise or high-pitched accents)
            median_f0 = np.median(dominant_pitches)
            print(f"Gender Detection: Median pitch = {median_f0:.2f}Hz")

            # Typical pitch ranges: Male (~85-155Hz), Female (~165-255Hz)
            # Lowered threshold to 150Hz to be more inclusive of higher male voices
            if median_f0 < 150:
                return "Male"
            else:
                return "Female"
        except Exception as e:
            print(f"Gender detection error: {e}")
            return "Female" # Default fallback

    return await asyncio.to_thread(run_detection)

def get_edge_tts_voice(target_lang: str, gender: str):
    """
    Maps target language and detected gender to an edge-tts voice string.
    """
    # Expanded mapping for common languages
    # Format: { "lang_clean": { "Male": "voice_name", "Female": "voice_name" } }
    voice_map = {
        "english": {"Male": "en-US-GuyNeural", "Female": "en-US-JennyNeural"},
        "spanish": {"Male": "es-ES-AlvaroNeural", "Female": "es-ES-ElviraNeural"},
        "hindi": {"Male": "hi-IN-MadhurNeural", "Female": "hi-IN-SwararaNeural"},
        "french": {"Male": "fr-FR-HenriNeural", "Female": "fr-FR-DeniseNeural"},
        "german": {"Male": "de-DE-DennisNeural", "Female": "de-DE-ChristaNeural"},
        "tamil": {"Male": "ta-IN-ValluvarNeural", "Female": "ta-IN-PallaviNeural"},
        "arabic": {"Male": "ar-EG-ShakirNeural", "Female": "ar-EG-SalmaNeural"},
        "chinese": {"Male": "zh-CN-YunxiNeural", "Female": "zh-CN-XiaoxiaoNeural"},
        "japanese": {"Male": "ja-JP-KeitaNeural", "Female": "ja-JP-NanamiNeural"},
        "portuguese": {"Male": "pt-BR-AntonioNeural", "Female": "pt-BR-FranciscaNeural"},
        "russian": {"Male": "ru-RU-DmitryNeural", "Female": "ru-RU-SvetlanaNeural"},
    }

    lang_clean = target_lang.lower().split(' ')[0]

    # 1. Try to get from our curated map
    if lang_clean in voice_map:
        return voice_map[lang_clean].get(gender, voice_map[lang_clean]["Female"])

    # 2. Heuristic fallback: try to construct a common edge-tts voice pattern
    # Many voices follow the pattern: {lang-region}-{Gender}Neural
    # This is a best-effort fallback.
    try:
        # Map clean name to ISO code for fallback attempt
        iso_map = {
            "arabic": "ar-SA", "chinese": "zh-CN", "japanese": "ja-JP",
            "portuguese": "pt-BR", "russian": "ru-RU"
        }
        iso_code = iso_map.get(lang_clean, "en-US")
        # Note: This is a guess; not all languages follow this naming convention
        # Returning English as the safe final fallback
        return voice_map["english"].get(gender, voice_map["english"]["Female"])
    except:
        return voice_map["english"]["Female"]

async def extract_audio(file_path: str):
    """Extracts audio from video using FFmpeg via subprocess.run to avoid Windows asyncio issues."""
    def run_ffmpeg():
        import subprocess
        audio_path = file_path.rsplit('.', 1)[0] + ".mp3"
        try:
            subprocess.run(
                ['ffmpeg', '-i', file_path, '-q:a', '0', '-map', 'a', audio_path, '-y'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            return audio_path
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg extraction error: {e}")
            raise e

    return await asyncio.to_thread(run_ffmpeg)

async def transcribe_audio(audio_path: str):
    """Transcribes audio using local OpenAI Whisper."""
    def run_whisper():
        try:
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language='en')
            text = result.get("text", "").strip()
            print(f"Whisper transcription result: '{text}'")
            return text
        except Exception as e:
            print(f"Whisper error: {e}")
            return ""

    return await asyncio.to_thread(run_whisper)

async def translate_text(text: str, target_lang: str):
    """Translates text using Meta NLLB-200 local model via direct model calls."""
    if translation_model is None or translation_tokenizer is None:
        raise Exception("Local translation model is not loaded.")

    def get_target_code():
        lang_map = {
            "spanish": "spa_Latn",
            "hindi": "hin_Deva",
            "french": "fra_Latn",
            "german": "deu_Latn",
            "tamil": "tam_Taml"
        }
        target_lang_clean = target_lang.lower().split(' ')[0]
        return lang_map.get(target_lang_clean, "eng_Latn"), target_lang_clean

    target_code, target_lang_clean = get_target_code()
    print(f"Translating to: {target_lang_clean} (code: {target_code})")

    import re
    chunks = re.split(r'(?<=[.!?]) +', text)
    translated_chunks = []

    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue

        try:
            def do_translate():
                # 1. Set the tokenizer to English for the input
                translation_tokenizer.src_lang = "eng_Latn"

                # 2. Tokenize the input and move to the same device as the model
                inputs = translation_tokenizer(chunk, return_tensors="pt").to(translation_model.device)

                # 3. Generate translation with the specific target language token
                translated_tokens = translation_model.generate(
                    **inputs,
                    forced_bos_token_id=translation_tokenizer.convert_tokens_to_ids(target_code),
                    max_length=128
                )

                # 4. Decode and return
                return translation_tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]

            translated = await asyncio.to_thread(do_translate)
            translated_chunks.append(translated)
            print(f"Chunk {i+1}/{len(chunks)} translated locally to {target_lang_clean}.")
        except Exception as e:
            print(f"Local translation error on chunk {i+1}: {e}")
            translated_chunks.append(chunk)

    return " ".join(translated_chunks)

async def clone_voice(original_audio_path: str, translated_text: str, output_path: str, target_lang: str = "en", gender: str = "Female"):
    print("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("!!! THIS IS A TEST: THE CODE IS DEFINITELY UPDATED !!!")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n")
    """Generates audio using AI Voice Cloning (XTTS v2) if available, otherwise falls back to edge-tts."""

    # Force gender detection inside if not provided or to ensure accuracy
    print(f"DEBUG: Performing internal gender detection for audio: {original_audio_path}")
    detected_gender = await detect_gender(original_audio_path)
    print(f"DEBUG: Internal gender detection result: {detected_gender}")

    # Use the detected gender over the passed parameter for better accuracy
    gender = detected_gender

    if not HAS_TTS:
        print("\n❌ VOICE CLONING DISABLED: TTS library not detected. Falling back to edge-tts.")
        try:
            voice = get_edge_tts_voice(target_lang, gender)
            communicate = edge_tts.Communicate(translated_text, voice)
            await communicate.save(output_path)
            print(f"✅ edge-tts Fallback successful ({gender}).")
        except Exception as e:
            print(f"edge-tts Fallback error: {e}")
            # Final ultimate fallback to gTTS if edge-tts fails
            try:
                from gtts import gTTS
                tts = gTTS(text=translated_text, lang=target_lang.lower().split(' ')[0][:2])
                tts.save(output_path)
                print("✅ gTTS Ultimate Fallback successful.")
            except Exception as g_e:
                print(f"❌ All synthesis options failed: {g_e}")
                raise e
        return

    def run_cloning():
        try:
            if not translated_text or translated_text.strip() == "":
                raise ValueError("No text provided for speech synthesis")

            print("\n🚀 Starting Voice Cloning Process...")
            # Initialize TTS with XTTS v2 model
            device = "cuda" if torch.cuda.is_available() else "cpu"
            tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            print(f"Using device: {device} for voice cloning")

            # Mapping for XTTS language codes
            # ONLY include languages officially supported by XTTS v2 to avoid crashes (like 'cutlet' error)
            lang_map = {
                "english": "en",
                "spanish": "es",
                "french": "fr",
                "german": "de",
                "italian": "it",
                "portuguese": "pt",
                "polish": "pl",
                "turkish": "tr",
                "russian": "ru",
                "dutch": "nl",
                "chinese": "zh",
                "japanese": "ja",
                "korean": "ko",
                "hindi": "hi",
                "arabic": "ar"
            }
            target_lang_clean = target_lang.lower().split(' ')[0]
            lang_code = lang_map.get(target_lang_clean, "en")

            # Check if language is supported by XTTS v2 to avoid crash
            if hasattr(tts, 'languages') and lang_code not in tts.languages:
                print(f"⚠️ Language {lang_code} not supported for cloning. Falling back to edge-tts.")
                raise NotImplementedError(f"Language {lang_code} not supported by XTTS v2")
            elif not hasattr(tts, 'languages') and lang_code == "ta": # Specific known unsupported
                print(f"⚠️ Language {lang_code} not supported for cloning. Falling back to edge-tts.")
                raise NotImplementedError(f"Language {lang_code} not supported by XTTS v2")

            print(f"Cloning voice using language code: {lang_code}")

            # Generate voice cloning output
            tts.tts_to_file(
                text=translated_text,
                speaker_wav=original_audio_path,
                language=lang_code,
                file_path=output_path
            )
            print(f"✅ Voice cloning complete. File saved to: {output_path}")
        except (Exception, AssertionError) as e:
            print(f"\nℹ️ Voice cloning not available for this language/setup: {e}")
            print("Falling back to edge-tts for seamless playback...")
            try:
                # edge-tts Fallback
                voice = get_edge_tts_voice(target_lang, gender)

                # Since run_cloning is executed in asyncio.to_thread,
                # we are in a separate thread. We should not try to get the event loop
                # and run_until_complete here.
                # Instead, we will raise a custom exception that the outer async
                # function can catch and handle using its own event loop.
                raise FallbackToEdgeTTS(voice)
            except FallbackToEdgeTTS as f_e:
                raise f_e
            except Exception as fallback_e:
                print(f"❌ Both cloning and fallback failed: {fallback_e}")
                raise e

    try:
        await asyncio.to_thread(run_cloning)
    except FallbackToEdgeTTS as f_e:
        print(f"Executing edge-tts fallback with voice: {f_e.voice}")
        try:
            communicate = edge_tts.Communicate(translated_text, f_e.voice)
            await communicate.save(output_path)
            print(f"✅ edge-tts Fallback successful ({gender}).")
        except Exception as fallback_e:
            print(f"❌ edge-tts fallback failed: {fallback_e}")
            # Ultimate fallback to gTTS
            try:
                from gtts import gTTS
                tts = gTTS(text=translated_text, lang=target_lang.lower().split(' ')[0][:2])
                tts.save(output_path)
                print("✅ gTTS Ultimate Fallback successful.")
            except Exception as g_e:
                print(f"❌ All synthesis options failed: {g_e}")
                raise fallback_e

async def merge_audio_video(video_path: str, audio_path: str, output_path: str):
    """Merges the translated audio back into the video using subprocess.run to avoid Windows asyncio issues."""
    def run_merge():
        import subprocess
        try:
            subprocess.run(
                ['ffmpeg', '-i', video_path, '-i', audio_path,
                 '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0',
                 '-shortest', '-y', output_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg merge error: {e}")
            raise e

    return await asyncio.to_thread(run_merge)

# --- API ENDPOINTS ---

@app.get("/")
async def root():
    return {"message": "VoiceDub AI Backend (Local) is running"}

@app.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_lang: str = Form("auto"),
    target_lang: str = Form("english"),
    voice_style: str = Form("original"),
    voice_cloning: bool = Form(True),
    add_subtitles: bool = Form(False),
    gender_override: Optional[str] = Form(None)
):
    print(f"RECEIVED REQUEST: source={source_lang}, target={target_lang}, style={voice_style}, override={gender_override}")


    file_path = UPLOAD_DIR / f"{datetime.now().timestamp()}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    job_id = str(datetime.now().timestamp())
    job_data = {
        "job_id": job_id,
        "filename": file.filename,
        "file_path": str(file_path),
        "source_lang": source_lang,
        "target_lang": target_lang,
        "voice_style": voice_style,
        "voice_cloning": voice_cloning,
        "add_subtitles": add_subtitles,
        "gender_override": gender_override,
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now(timezone.utc)
    }
    await db.jobs.insert_one(job_data)

    background_tasks.add_task(process_video_pipeline, job_id)

    return {
        "job_id": job_id,
        "message": "Video uploaded successfully. Local processing started.",
        "status": "pending"
    }

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    job = await db.jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "status": job["status"],
        "progress": job["progress"],
        "result_url": job.get("result_url"),
        "original_text": job.get("original_text"),
        "translated_text": job.get("translated_text")
    }

@app.get("/jobs")
async def list_jobs():
    jobs = await db.jobs.find().to_list(100)
    return jobs

async def process_video_pipeline(job_id: str):
    """The Local AI Processing Pipeline."""
    try:
        job = await db.jobs.find_one({"job_id": job_id})
        if not job: return

        video_path = job["file_path"]
        target_lang = job["target_lang"]

        # 1. Audio Extraction
        await db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "Extracting audio...", "progress": 10}})
        audio_path = await extract_audio(video_path)

        # FORCE Gender Detection
        print(f"DEBUG: Starting gender detection for job {job_id} using audio: {audio_path}")
        gender = await detect_gender(audio_path)
        print(f"DEBUG: Gender detection finished. Result: {gender} for job {job_id}")
        await db.jobs.update_one({"job_id": job_id}, {"$set": {"gender": gender}})

        # 2. Transcription
        await db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "Transcribing speech (Local)...", "progress": 30}})
        original_text = await transcribe_audio(audio_path)
        await db.jobs.update_one({"job_id": job_id}, {"$set": {"original_text": original_text}})

        # 3. Translation
        await db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "Translating text (Local)...", "progress": 50}})
        try:
            translated_text = await translate_text(original_text, target_lang)
            await db.jobs.update_one({"job_id": job_id}, {"$set": {"translated_text": translated_text}})
        except Exception as e:
            print(f"Critical translation failure for job {job_id}: {e}")
            raise Exception(f"Translation failed: {str(e)}")

        # 4. Voice Synthesis
        await db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "Generating voice (Local)...", "progress": 70}})
        translated_audio_path = video_path.rsplit('.', 1)[0] + "_translated.mp3"

        # Final Safety Net:
        tts_text = ""
        if translated_text and translated_text.strip():
            tts_text = translated_text
        elif original_text and original_text.strip():
            tts_text = original_text
        else:
            print(f"Warning: No text found for job {job_id}. Using safety fallback.")
            tts_text = "No speech detected in this video."

        await clone_voice(audio_path, tts_text, translated_audio_path, target_lang, gender=gender)

        # 5. Merging
        await db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "Merging audio with video...", "progress": 90}})
        final_filename = f"final_{job_id}.mp4"
        final_video_path = DOWNLOADS_DIR / final_filename
        await merge_audio_video(video_path, translated_audio_path, str(final_video_path))

        # Finalize
        await db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "completed", "progress": 100, "result_url": f"/downloads/{final_filename}"}}
        )

    except Exception as e:
        print(f"CRITICAL Error processing job {job_id}: {str(e)}")
        traceback.print_exc()
        await db.jobs.update_one({"job_id": job_id}, {"$set": {"status": f"Error: {str(e)}", "progress": 0}})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
