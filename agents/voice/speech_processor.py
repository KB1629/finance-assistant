"""Voice processing agent with STT and TTS capabilities."""

import os
import io
import logging
import tempfile
from pathlib import Path
from typing import Optional, Union, BinaryIO

import whisper
import speech_recognition as sr
from pydub import AudioSegment
from pydub.playback import play

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("voice.speech_processor")


class VoiceProcessor:
    """Voice processing agent for STT and TTS operations."""

    def __init__(self, whisper_model: str = "base"):
        """Initialize the voice processor.
        
        Args:
            whisper_model: Whisper model size to use (tiny, base, small, medium, large)
        """
        self.whisper_model = whisper_model
        
        # Initialize Whisper model
        logger.info(f"Loading Whisper model: {whisper_model}")
        try:
            self.whisper = whisper.load_model(whisper_model)
            logger.info(f"Successfully loaded Whisper model: {whisper_model}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise
        try:
            with self.microphone as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Microphone calibration complete")
        except Exception as e:
            logger.warning(f"Could not calibrate microphone: {e}")

    def speech_to_text_whisper(self, audio_file: Union[str, Path, BinaryIO]) -> str:
        """Convert speech to text using Whisper.
        
        Args:
            audio_file: Path to audio file or file-like object
            
        Returns:
            Transcribed text
        """
        try:
            logger.info("Starting Whisper transcription...")
            
            # If it's a file-like object, save to temporary file
            if hasattr(audio_file, 'read'):
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(audio_file.read())
                    temp_path = temp_file.name
                
                result = self.whisper.transcribe(temp_path)
                os.unlink(temp_path)  # Clean up temp file
            else:
                result = self.whisper.transcribe(str(audio_file))
            
            text = result["text"].strip()
            logger.info(f"Whisper transcription completed: '{text[:50]}...'")
            return text
            
        except Exception as e:
            logger.error(f"Error in Whisper transcription: {e}")
            return f"Error: Unable to transcribe audio - {str(e)}"

    def speech_to_text_microphone(self, timeout: float = 5.0) -> str:
        """Record from microphone and convert to text.
        
        Args:
            timeout: Maximum time to wait for speech
            
        Returns:
            Transcribed text
        """
        try:
            logger.info("Listening for speech...")
            
            with self.microphone as source:
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
            logger.info("Processing audio...")
            
            # Try Whisper first (higher quality)
            try:
                # Convert audio to wav format for Whisper
                audio_data = io.BytesIO(audio.get_wav_data())
                return self.speech_to_text_whisper(audio_data)
            except Exception as e:
                logger.warning(f"Whisper failed, falling back to Google: {e}")
                
                # Fallback to Google Speech Recognition
                try:
                    text = self.recognizer.recognize_google(audio)
                    logger.info(f"Google transcription: '{text}'")
                    return text
                except sr.UnknownValueError:
                    return "Sorry, I couldn't understand the audio"
                except sr.RequestError as e:
                    return f"Error with speech recognition service: {e}"
                    
        except sr.WaitTimeoutError:
            return "No speech detected within timeout period"
        except Exception as e:
            logger.error(f"Error in microphone transcription: {e}")
            return f"Error: {str(e)}"

    def text_to_speech_simple(self, text: str, output_file: Optional[str] = None) -> Optional[str]:
        """Convert text to speech using simple TTS.
        
        Note: This is a placeholder for TTS functionality.
        In a full implementation, you would integrate with:
        - Piper TTS (as mentioned in the plan)
        - Windows SAPI
        - Cloud TTS services
        
        Args:
            text: Text to convert to speech
            output_file: Optional output file path
            
        Returns:
            Path to generated audio file if saved, None otherwise
        """
        try:
            logger.info(f"TTS request: '{text[:50]}...'")
            
            # For now, we'll create a simple placeholder
            # In production, integrate with Piper TTS or another TTS engine
            
            if len(text) > 200:
                text = text[:200] + "..."
                
            logger.info("TTS processing completed (placeholder implementation)")
            
            # Return a message for now
            return f"TTS would generate audio for: '{text}'"
            
        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            return None

    def process_audio_file(self, file_path: Union[str, Path]) -> str:
        """Process an uploaded audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return f"Error: Audio file not found: {file_path}"
            
            logger.info(f"Processing audio file: {file_path}")
            
            # Check file format and convert if necessary
            if file_path.suffix.lower() not in ['.wav', '.mp3', '.m4a', '.flac']:
                return f"Error: Unsupported audio format: {file_path.suffix}"
            
            # Convert to WAV if needed for Whisper
            if file_path.suffix.lower() != '.wav':
                logger.info("Converting audio format for processing...")
                audio = AudioSegment.from_file(str(file_path))
                
                # Create temporary WAV file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                audio.export(temp_path, format="wav")
                result = self.speech_to_text_whisper(temp_path)
                os.unlink(temp_path)  # Clean up
                
                return result
            else:
                return self.speech_to_text_whisper(file_path)
                
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
            return f"Error processing audio file: {str(e)}"

    def get_voice_stats(self) -> dict:
        """Get voice processor statistics.
        
        Returns:
            Dictionary with processor stats
        """
        return {
            "whisper_model": self.whisper_model,
            "microphone_available": self.microphone is not None,
            "supported_formats": [".wav", ".mp3", ".m4a", ".flac"]
        }


# Global instance
_voice_processor = None

def get_voice_processor() -> VoiceProcessor:
    """Get the global voice processor instance.
    
    Returns:
        VoiceProcessor instance
    """
    global _voice_processor
    if _voice_processor is None:
        _voice_processor = VoiceProcessor()
    return _voice_processor

def transcribe_audio(audio_source: Union[str, Path, BinaryIO]) -> str:
    """Transcribe audio to text.
    
    Args:
        audio_source: Audio file path or file-like object
        
    Returns:
        Transcribed text
    """
    processor = get_voice_processor()
    
    if isinstance(audio_source, (str, Path)):
        return processor.process_audio_file(audio_source)
    else:
        return processor.speech_to_text_whisper(audio_source)

def record_and_transcribe(timeout: float = 5.0) -> str:
    """Record from microphone and transcribe.
    
    Args:
        timeout: Recording timeout
        
    Returns:
        Transcribed text
    """
    return get_voice_processor().speech_to_text_microphone(timeout)

def synthesize_speech(text: str, output_file: Optional[str] = None) -> Optional[str]:
    """Convert text to speech.
    
    Args:
        text: Text to synthesize
        output_file: Optional output file
        
    Returns:
        Output file path or None
    """
    return get_voice_processor().text_to_speech_simple(text, output_file) 