"""
Voice Agent Microservice - Speech Processing
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import logging
import tempfile
import os

from agents.voice.speech_processor import (
    transcribe_audio, 
    record_and_transcribe, 
    synthesize_speech,
    get_voice_processor
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("voice_agent_service")

app = FastAPI(
    title="Voice Agent - Speech Processing Service",
    description="Microservice for speech-to-text and text-to-speech processing",
    version="1.0.0"
)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str


class TranscribeRequest(BaseModel):
    """Text transcription request"""
    timeout: Optional[float] = 5.0


class TranscribeResponse(BaseModel):
    """Transcription response"""
    text: str
    status: str


class TTSRequest(BaseModel):
    """Text-to-speech request"""
    text: str
    output_file: Optional[str] = None


class TTSResponse(BaseModel):
    """TTS response"""
    message: str
    status: str


class VoiceStatsResponse(BaseModel):
    """Voice stats response"""
    stats: dict
    status: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", service="voice-agent")


@app.post("/stt/microphone", response_model=TranscribeResponse)
async def speech_to_text_microphone(request: TranscribeRequest):
    """Record from microphone and transcribe"""
    try:
        logger.info("Starting microphone transcription...")
        text = record_and_transcribe(timeout=request.timeout)
        
        return TranscribeResponse(
            text=text,
            status="success"
        )
    except Exception as e:
        logger.error(f"Microphone transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stt/file", response_model=TranscribeResponse)
async def speech_to_text_file(file: UploadFile = File(...)):
    """Upload audio file and transcribe"""
    try:
        logger.info(f"Processing uploaded file: {file.filename}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Transcribe
            text = transcribe_audio(tmp_path)
            
            return TranscribeResponse(
                text=text,
                status="success"
            )
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"File transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    try:
        logger.info(f"TTS request: {request.text[:50]}...")
        
        result = synthesize_speech(request.text, request.output_file)
        
        return TTSResponse(
            message=result or "TTS processing completed",
            status="success"
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=VoiceStatsResponse)
async def get_voice_stats():
    """Get voice processor statistics"""
    try:
        processor = get_voice_processor()
        stats = processor.get_voice_stats()
        
        return VoiceStatsResponse(
            stats=stats,
            status="success"
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006) 