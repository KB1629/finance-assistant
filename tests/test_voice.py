"""Tests for the Voice Agent (Whisper STT + TTS)."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import io


class TestVoiceProcessor:
    """Test cases for the Voice Processor."""
    
    @pytest.fixture
    def mock_whisper_model(self):
        """Mock Whisper model for testing."""
        with patch("agents.voice.speech_processor.whisper.load_model") as mock_load:
            mock_model = Mock()
            mock_model.transcribe.return_value = {"text": "Test transcription result"}
            mock_load.return_value = mock_model
            yield mock_model

    @pytest.fixture
    def mock_speech_recognition(self):
        """Mock speech recognition components."""
        with patch("agents.voice.speech_processor.sr.Recognizer") as mock_recognizer:
            with patch("agents.voice.speech_processor.sr.Microphone") as mock_microphone:
                mock_rec_instance = Mock()
                mock_mic_instance = Mock()
                
                # Fix context manager protocol for microphone
                mock_mic_instance.__enter__ = Mock(return_value=mock_mic_instance)
                mock_mic_instance.__exit__ = Mock(return_value=None)
                
                mock_recognizer.return_value = mock_rec_instance
                mock_microphone.return_value = mock_mic_instance
                yield mock_rec_instance, mock_mic_instance

    def test_voice_processor_initialization(self, mock_whisper_model, mock_speech_recognition):
        """Test VoiceProcessor initialization."""
        from agents.voice.speech_processor import VoiceProcessor
        
        processor = VoiceProcessor(whisper_model="base")
        
        assert processor.whisper_model == "base"
        assert processor.whisper is not None
        assert processor.recognizer is not None
        assert processor.microphone is not None

    def test_speech_to_text_whisper_file_path(self, mock_whisper_model, mock_speech_recognition):
        """Test Whisper STT with file path."""
        from agents.voice.speech_processor import VoiceProcessor
        
        processor = VoiceProcessor()
        
        # Test with file path
        result = processor.speech_to_text_whisper("test_audio.wav")
        
        assert result == "Test transcription result"
        mock_whisper_model.transcribe.assert_called_once_with("test_audio.wav")

    def test_speech_to_text_whisper_file_object(self, mock_whisper_model, mock_speech_recognition):
        """Test Whisper STT with file-like object."""
        from agents.voice.speech_processor import VoiceProcessor
        
        processor = VoiceProcessor()
        
        # Create mock file-like object
        audio_data = io.BytesIO(b"fake audio data")
        
        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            with patch("os.unlink") as mock_unlink:
                mock_temp_file = Mock()
                mock_temp_file.name = "/tmp/test.wav"
                mock_temp.return_value.__enter__ = Mock(return_value=mock_temp_file)
                mock_temp.return_value.__exit__ = Mock(return_value=None)
                
                result = processor.speech_to_text_whisper(audio_data)
                
                assert result == "Test transcription result"

    def test_speech_to_text_microphone(self, mock_whisper_model, mock_speech_recognition):
        """Test microphone speech-to-text."""
        from agents.voice.speech_processor import VoiceProcessor
        import speech_recognition as sr
        
        processor = VoiceProcessor()
        mock_recognizer, mock_microphone = mock_speech_recognition
        
        # Mock audio data
        mock_audio = Mock()
        mock_audio.get_wav_data.return_value = b"fake wav data"
        mock_recognizer.listen.return_value = mock_audio
        
        # Test successful Whisper transcription
        result = processor.speech_to_text_microphone(timeout=5.0)
        
        assert result == "Test transcription result"

    def test_speech_to_text_microphone_fallback(self, mock_whisper_model, mock_speech_recognition):
        """Test microphone STT with Google fallback."""
        from agents.voice.speech_processor import VoiceProcessor
        import speech_recognition as sr
        
        processor = VoiceProcessor()
        mock_recognizer, mock_microphone = mock_speech_recognition
        
        # Mock audio data
        mock_audio = Mock()
        mock_audio.get_wav_data.return_value = b"fake wav data"
        mock_recognizer.listen.return_value = mock_audio
        
        # Make Whisper fail, Google succeed
        mock_whisper_model.transcribe.side_effect = Exception("Whisper failed")
        mock_recognizer.recognize_google.return_value = "Google transcription"
        
        result = processor.speech_to_text_microphone(timeout=5.0)
        
        assert result == "Google transcription"

    def test_speech_to_text_microphone_timeout(self, mock_whisper_model, mock_speech_recognition):
        """Test microphone timeout handling."""
        from agents.voice.speech_processor import VoiceProcessor
        import speech_recognition as sr
        
        processor = VoiceProcessor()
        mock_recognizer, mock_microphone = mock_speech_recognition
        
        # Simulate timeout
        mock_recognizer.listen.side_effect = sr.WaitTimeoutError("Timeout")
        
        result = processor.speech_to_text_microphone(timeout=5.0)
        
        assert "No speech detected" in result

    def test_text_to_speech_simple(self, mock_whisper_model, mock_speech_recognition):
        """Test simple TTS functionality."""
        from agents.voice.speech_processor import VoiceProcessor
        
        processor = VoiceProcessor()
        
        # Test normal text
        result = processor.text_to_speech_simple("Hello world")
        assert "TTS would generate audio for" in result
        assert "Hello world" in result
        
        # Test long text truncation
        long_text = "A" * 300
        result = processor.text_to_speech_simple(long_text)
        assert "..." in result

    def test_process_audio_file_wav(self, mock_whisper_model, mock_speech_recognition):
        """Test processing WAV audio file."""
        from agents.voice.speech_processor import VoiceProcessor
        
        processor = VoiceProcessor()
        
        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b"fake wav data")
            temp_path = temp_file.name
        
        try:
            result = processor.process_audio_file(temp_path)
            assert result == "Test transcription result"
        finally:
            os.unlink(temp_path)

    def test_process_audio_file_mp3(self, mock_whisper_model, mock_speech_recognition):
        """Test processing MP3 audio file with conversion."""
        from agents.voice.speech_processor import VoiceProcessor
        
        processor = VoiceProcessor()
        
        # Create temporary MP3 file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b"fake mp3 data")
            temp_path = temp_file.name
        
        try:
            with patch("agents.voice.speech_processor.AudioSegment.from_file") as mock_audio:
                mock_audio_instance = Mock()
                mock_audio.return_value = mock_audio_instance
                
                result = processor.process_audio_file(temp_path)
                
                # Should attempt to convert from MP3
                mock_audio.assert_called_once()
                mock_audio_instance.export.assert_called_once()
                
        finally:
            os.unlink(temp_path)

    def test_process_audio_file_unsupported(self, mock_whisper_model, mock_speech_recognition):
        """Test processing unsupported audio format."""
        from agents.voice.speech_processor import VoiceProcessor
        
        processor = VoiceProcessor()
        
        # Create temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as temp_file:
            temp_file.write(b"fake data")
            temp_path = temp_file.name
        
        try:
            result = processor.process_audio_file(temp_path)
            assert "Unsupported audio format" in result
            assert ".xyz" in result
        finally:
            os.unlink(temp_path)

    def test_process_audio_file_not_found(self, mock_whisper_model, mock_speech_recognition):
        """Test processing non-existent audio file."""
        from agents.voice.speech_processor import VoiceProcessor
        
        processor = VoiceProcessor()
        
        result = processor.process_audio_file("non_existent_file.wav")
        assert "Audio file not found" in result

    def test_get_voice_stats(self, mock_whisper_model, mock_speech_recognition):
        """Test voice processor statistics."""
        from agents.voice.speech_processor import VoiceProcessor
        
        processor = VoiceProcessor(whisper_model="small")
        stats = processor.get_voice_stats()
        
        assert stats["whisper_model"] == "small"
        assert isinstance(stats["microphone_available"], bool)
        assert ".wav" in stats["supported_formats"]
        assert ".mp3" in stats["supported_formats"]

    def test_error_handling_whisper_load_failure(self, mock_speech_recognition):
        """Test error handling when Whisper model fails to load."""
        from agents.voice.speech_processor import VoiceProcessor
        
        with patch("agents.voice.speech_processor.whisper.load_model", side_effect=Exception("Model load failed")):
            with pytest.raises(Exception, match="Model load failed"):
                VoiceProcessor()

    def test_error_handling_microphone_calibration(self, mock_whisper_model):
        """Test microphone calibration error handling."""
        from agents.voice.speech_processor import VoiceProcessor
        import speech_recognition as sr
        
        with patch("agents.voice.speech_processor.sr.Recognizer") as mock_recognizer:
            with patch("agents.voice.speech_processor.sr.Microphone") as mock_microphone:
                mock_rec_instance = Mock()
                mock_mic_instance = Mock()
                mock_recognizer.return_value = mock_rec_instance
                mock_microphone.return_value = mock_mic_instance
                
                # Make microphone context manager raise exception
                mock_mic_instance.__enter__ = Mock(side_effect=Exception("Mic error"))
                
                # Should not raise exception, just log warning
                processor = VoiceProcessor()
                assert processor is not None


class TestVoiceProcessorGlobalFunctions:
    """Test global functions for voice processing."""
    
    @pytest.fixture
    def mock_voice_processor(self):
        """Mock the global voice processor instance."""
        with patch("agents.voice.speech_processor.VoiceProcessor") as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            with patch("agents.voice.speech_processor._voice_processor", mock_instance):
                yield mock_instance

    def test_get_voice_processor_singleton(self, mock_voice_processor):
        """Test singleton pattern for voice processor."""
        from agents.voice.speech_processor import get_voice_processor
        
        processor1 = get_voice_processor()
        processor2 = get_voice_processor()
        
        # Should return same instance
        assert processor1 is processor2

    def test_transcribe_audio_file_path(self, mock_voice_processor):
        """Test transcribe_audio with file path."""
        from agents.voice.speech_processor import transcribe_audio
        
        mock_voice_processor.process_audio_file.return_value = "File transcription"
        
        result = transcribe_audio("test.wav")
        
        assert result == "File transcription"
        mock_voice_processor.process_audio_file.assert_called_once_with("test.wav")

    def test_transcribe_audio_file_object(self, mock_voice_processor):
        """Test transcribe_audio with file object."""
        from agents.voice.speech_processor import transcribe_audio
        
        mock_voice_processor.speech_to_text_whisper.return_value = "Object transcription"
        
        audio_obj = io.BytesIO(b"fake data")
        result = transcribe_audio(audio_obj)
        
        assert result == "Object transcription"
        mock_voice_processor.speech_to_text_whisper.assert_called_once_with(audio_obj)

    def test_record_and_transcribe(self, mock_voice_processor):
        """Test record_and_transcribe function."""
        from agents.voice.speech_processor import record_and_transcribe
        
        mock_voice_processor.speech_to_text_microphone.return_value = "Microphone transcription"
        
        result = record_and_transcribe(timeout=10.0)
        
        assert result == "Microphone transcription"
        mock_voice_processor.speech_to_text_microphone.assert_called_once_with(10.0)

    def test_synthesize_speech(self, mock_voice_processor):
        """Test synthesize_speech function."""
        from agents.voice.speech_processor import synthesize_speech
        
        mock_voice_processor.text_to_speech_simple.return_value = "output.wav"
        
        result = synthesize_speech("Hello world", "output.wav")
        
        assert result == "output.wav"
        mock_voice_processor.text_to_speech_simple.assert_called_once_with("Hello world", "output.wav")


if __name__ == "__main__":
    pytest.main([__file__]) 