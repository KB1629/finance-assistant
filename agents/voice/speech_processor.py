"""Voice processing agent with STT and TTS capabilities."""

import os
import io
import logging
import tempfile
from pathlib import Path
from typing import Optional, Union, BinaryIO

import whisper
import speech_recognition as sr
try:
    from pydub import AudioSegment
    from pydub.playback import play
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not available - some audio features may be limited")

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
        
        # Initialize speech recognition (optional)
        self.recognizer = None
        self.microphone = None
        
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Microphone calibration complete")
        except ImportError:
            logger.warning("Speech recognition not available - PyAudio not installed")
        except Exception as e:
            logger.warning(f"Could not calibrate microphone: {e}")
            # Don't fail initialization - TTS can still work

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
            # Check if microphone is available
            if self.microphone is None or self.recognizer is None:
                return "Error: Microphone not available. Please check that PyAudio is installed and your microphone is connected."
            
            logger.info("Listening for speech...")
            
            with self.microphone as source:
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
            logger.info("Processing audio...")
            
            # Try Whisper first (higher quality)
            try:
                # Convert audio to wav format for Whisper
                audio_data = io.BytesIO(audio.get_wav_data())
                result = self.speech_to_text_whisper(audio_data)
                
                # Check if Whisper returned an error
                if result.startswith("Error:"):
                    raise Exception(result)
                    
                return result
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
        """Convert text to speech using Windows SAPI or fallback TTS.
        
        Args:
            text: Text to convert to speech
            output_file: Optional output file path
            
        Returns:
            Success message or None
        """
        try:
            logger.info(f"TTS request: '{text[:50]}...'")
            
            # Limit text length for TTS
            if len(text) > 500:
                text = text[:500] + "..."
            
            # Try Windows SAPI first (available on Windows desktop)
            try:
                import win32com.client
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(text)
                logger.info("TTS: Successfully played audio using Windows SAPI")
                return "Speech played successfully"
            except ImportError:
                logger.warning("Windows SAPI not available (pywin32 not installed)")
            except Exception as e:
                logger.warning(f"Windows SAPI failed (may not work in web environment): {e}")
            
            # Try edge-tts (Microsoft Edge TTS - works better in web contexts)
            try:
                import edge_tts
                import asyncio
                import tempfile
                import subprocess
                
                async def _speak():
                    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                        tmp_path = tmp_file.name
                    
                    await communicate.save(tmp_path)
                    
                    # Try to play with system default player
                    if os.name == 'nt':  # Windows
                        os.startfile(tmp_path)
                    elif os.name == 'posix':  # Linux/Mac
                        subprocess.call(['xdg-open', tmp_path])
                    
                    return tmp_path
                
                # Run async function
                if hasattr(asyncio, 'run'):
                    asyncio.run(_speak())
                    logger.info("TTS: Successfully generated audio using Edge TTS")
                    return "Speech played successfully"
                    
            except ImportError:
                logger.warning("edge-tts not available")
            except Exception as e:
                logger.warning(f"Edge TTS failed: {e}")
            
            # Try gTTS as backup (requires internet)
            try:
                from gtts import gTTS
                import pygame
                
                # Create temporary file for audio
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                    tmp_path = tmp_file.name
                
                # Generate speech
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(tmp_path)
                
                # Try pygame for playback
                pygame.mixer.init()
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                pygame.mixer.quit()
                os.unlink(tmp_path)  # Clean up
                
                logger.info("TTS: Successfully played audio using gTTS")
                return "Speech played successfully"
                
            except ImportError:
                logger.warning("gTTS/pygame not available")
            except Exception as e:
                logger.warning(f"gTTS failed: {e}")
            
            # Try pyttsx3 (cross-platform TTS)
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
                logger.info("TTS: Successfully played audio using pyttsx3")
                return "Speech played successfully"
            except ImportError:
                logger.warning("pyttsx3 not available")
            except Exception as e:
                logger.warning(f"pyttsx3 failed: {e}")
            
            # Final fallback - explain limitations
            logger.info("TTS: All speech engines failed - web environment limitations")
            return "TTS engines not available in web environment - text-to-speech works better in desktop applications"
            
        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            return f"TTS Error: {str(e)}"

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
                if not PYDUB_AVAILABLE:
                    logger.warning("Audio conversion not available - FFmpeg/pydub not installed")
                    return "Error: Audio conversion requires FFmpeg. Please install FFmpeg or upload WAV files."
                
                try:
                    logger.info("Converting audio format for processing...")
                    audio = AudioSegment.from_file(str(file_path))
                    
                    # Create temporary WAV file
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    audio.export(temp_path, format="wav")
                    result = self.speech_to_text_whisper(temp_path)
                    os.unlink(temp_path)  # Clean up
                except Exception as e:
                    logger.error(f"Audio conversion failed: {e}")
                    return f"Error: Audio conversion failed. Please ensure FFmpeg is installed or upload WAV files. Error: {e}"
                
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