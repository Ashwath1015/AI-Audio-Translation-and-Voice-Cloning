# Backend Setup Guide

This project uses a Python FastAPI backend to handle video uploads and coordinate the AI translation pipeline.

## 🛠️ Tech Stack
- **Framework**: FastAPI (High performance, asynchronous)
- **Database**: MongoDB (Flexible schema for video metadata)
- **File Storage**: Local `/uploads` directory (for demo) $\rightarrow$ AWS S3 (for production)
- **Task Queue**: Celery + Redis (Required for long-running video processing)

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.10+
- MongoDB installed and running locally (or MongoDB Atlas)
- Redis installed and running (for the task queue)

### 2. Environment Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the `backend` folder:
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=voicedub_db
UPLOAD_FOLDER=uploads
REDIS_URL=redis://localhost:6379/0
```

### 4. Running the Server
```bash
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`.
