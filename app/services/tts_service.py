# app/services/tts_service.py

import os
import io
import logging
import tempfile
from typing import Dict, Any, Optional

from google.cloud import texttospeech
from pydub import AudioSegment
from flask import current_app

logger = logging.getLogger(__name__)

class TTSService:
    """Service for text-to-speech conversion using Google Cloud TTS."""
    
    # Voice configurations
    VOICE_PROFILES = {
        "alex": {
            "name": "en-US-Neural2-D",
            "gender": "MALE",
            "speaking_rate": 1.05,
            "pitch": 0.0
        },
        "jordan": {
            "name": "en-US-Neural2-A",  
            "gender": "MALE",
            "speaking_rate": 0.95,
            "pitch": -1.0
        }
    }
    
    def __init__(self):
        """Initialize TTS service."""
        try:
            self.client = texttospeech.TextToSpeechClient()
            self.sample_rate = 24000
            
        except Exception as e:
            logger.error(f"Error initializing TTS service: {str(e)}")
            raise
    
    def generate_audio(
        self,
        script_content: Dict[str, Any],
        voice_preference: str = "mixed"
    ) -> bytes:
        """Generate audio from script content."""
        try:
            # Parse script and generate audio segments
            audio_segments = []
            
            for section in script_content.get("sections", []):
                for segment in section.get("segments", []):
                    speaker = segment.get("speaker", "alex")
                    text = segment.get("text", "")
                    
                    if not text:
                        continue
                    
                    # Generate audio for this segment
                    audio_data = self._synthesize_speech(text, speaker)
                    audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))
                    
                    # Add segment to collection
                    audio_segments.append(audio_segment)
                    
                    # Add pause between segments
                    pause = AudioSegment.silent(duration=500)  # 500ms pause
                    audio_segments.append(pause)
            
            # Combine all segments
            if not audio_segments:
                raise ValueError("No audio segments generated")
            
            combined = audio_segments[0]
            for segment in audio_segments[1:]:
                combined += segment
            
            # Export as MP3
            output_buffer = io.BytesIO()
            combined.export(output_buffer, format="mp3", bitrate="192k")
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise
    
    def _synthesize_speech(self, text: str, speaker: str) -> bytes:
        """Synthesize speech for a specific speaker."""
        try:
            # Get voice profile
            voice_profile = self.VOICE_PROFILES.get(speaker, self.VOICE_PROFILES["alex"])
            
            # Prepare input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure voice
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice_profile["name"],
                ssml_gender=getattr(texttospeech.SsmlVoiceGender, voice_profile["gender"])
            )
            
            # Configure audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=voice_profile["speaking_rate"],
                pitch=voice_profile["pitch"],
                sample_rate_hertz=self.sample_rate
            )
            
            # Synthesize speech
            response = self.client.synthesize_speech(
                request={
                    "input": synthesis_input,
                    "voice": voice,
                    "audio_config": audio_config
                }
            )
            
            return response.audio_content
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            raise
    
    def get_audio_duration(self, audio_data: bytes) -> Optional[int]:
        """Get duration of audio in seconds."""
        try:
            audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
            return int(audio.duration_seconds)
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return None
    
    def apply_ssml_enhancements(self, text: str) -> str:
        """Apply SSML enhancements to text."""
        # Add SSML tags for better speech
        ssml = f"""<speak>
            <prosody rate="medium" pitch="default">
                {text}
            </prosody>
        </speak>"""
        
        # Apply specific enhancements
        ssml = ssml.replace("ArXiv", '<say-as interpret-as="spell-out">ArXiv</say-as>')
        ssml = ssml.replace("AI", '<say-as interpret-as="spell-out">A I</say-as>')
        ssml = ssml.replace("ML", '<say-as interpret-as="spell-out">M L</say-as>')
        
        return ssml