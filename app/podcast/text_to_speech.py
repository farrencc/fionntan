"""
Google Cloud Text-to-Speech Podcast Renderer

Converts podcast scripts into high-quality audio using Google Cloud Text-to-Speech.
It supports multiple speakers, SSML enhancements, background music, and section transitions.

Features:
- Google Cloud Text-to-Speech API authentication
- Script parsing for multiple speakers
- Voice selection with gender preferences
- SSML enhancement for natural speech
- Audio segment combination with transitions
- Background music integration
- MP3 export with proper metadata
- Comprehensive error handling and logging
"""

import os
import json
import time
import logging
import random
import tempfile
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import re

# Google Cloud libraries
from google.cloud import texttospeech
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPIError, RetryError, InvalidArgument

# Audio processing libraries
import pydub
from pydub import AudioSegment
from pydub.effects import normalize, speedup
from pydub.silence import detect_leading_silence, detect_trailing_silence

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("podcast_tts")


class Gender(Enum):
    """Voice gender options."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    NEUTRAL = "NEUTRAL"


class AudioFormat(Enum):
    """Audio format options."""
    MP3 = "MP3"
    WAV = "WAV"
    OGG = "OGG"


@dataclass
class VoiceConfig:
    """Configuration for a TTS voice."""
    name: str
    language_code: str = "en-US"
    gender: Gender = Gender.NEUTRAL
    speaking_rate: float = 1.0
    pitch: float = 0.0
    volume_gain_db: float = 0.0


@dataclass
class TTSConfig:
    """Configuration for the Text-to-Speech processor."""
    service_account_path: Optional[str] = None
    voice_configs: Dict[str, VoiceConfig] = None
    audio_format: AudioFormat = AudioFormat.MP3
    sample_rate_hertz: int = 24000
    enable_ssml: bool = True
    enable_background_music: bool = True
    background_music_path: Optional[str] = None
    background_music_volume: float = -20  # dB
    add_transitions: bool = True
    transition_duration: float = 0.5  # seconds
    output_directory: str = "./output"
    tmp_directory: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default voice configs if none provided."""
        if self.voice_configs is None:
            self.voice_configs = {
                "alex": VoiceConfig(
                    name="en-US-Neural2-D",
                    gender=Gender.MALE,
                    speaking_rate=1.05,
                    pitch=0.0,
                    volume_gain_db=0.0
                ),
                "jordan": VoiceConfig(
                    name="en-US-Neural2-A",
                    gender=Gender.MALE,
                    speaking_rate=0.95,
                    pitch=-1.0,
                    volume_gain_db=0.0
                )
            }


class TTSClient:
    """
    Client for Google Cloud Text-to-Speech API.
    Handles authentication and voice synthesis requests.
    """
    
    # Constants for retry behavior
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2  # seconds
    
    def __init__(self, config: TTSConfig):
        """
        Initialize the TTS client with configuration.
        
        Args:
            config: Configuration for TTS services
        """
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Google Cloud Text-to-Speech client."""
        try:
            # Use service account if provided, otherwise use default credentials
            if self.config.service_account_path and os.path.exists(self.config.service_account_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.config.service_account_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                self.client = texttospeech.TextToSpeechClient(credentials=credentials)
            else:
                self.client = texttospeech.TextToSpeechClient()
            
            logger.info("Successfully initialized Google Cloud Text-to-Speech client")
        
        except Exception as e:
            logger.error(f"Failed to initialize TTS client: {e}")
            raise
    
    def synthesize_speech(
        self, 
        text: str, 
        voice_config: VoiceConfig,
        ssml: bool = False
    ) -> bytes:
        """
        Synthesize speech from text using Google Cloud TTS.
        
        Args:
            text: Text or SSML to synthesize
            voice_config: Voice configuration to use
            ssml: Whether the input text is SSML
            
        Returns:
            Audio content as bytes
        """
        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                # Set the text input
                if ssml:
                    input_text = texttospeech.SynthesisInput(ssml=text)
                else:
                    input_text = texttospeech.SynthesisInput(text=text)
                
                # Build voice parameters
                voice = texttospeech.VoiceSelectionParams(
                    language_code=voice_config.language_code,
                    name=voice_config.name,
                    ssml_gender=voice_config.gender.value
                )
                
                # Select the audio encoding
                if self.config.audio_format == AudioFormat.MP3:
                    audio_encoding = texttospeech.AudioEncoding.MP3
                elif self.config.audio_format == AudioFormat.WAV:
                    audio_encoding = texttospeech.AudioEncoding.LINEAR16
                else:
                    audio_encoding = texttospeech.AudioEncoding.OGG_OPUS
                
                # Set audio configuration
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=audio_encoding,
                    speaking_rate=voice_config.speaking_rate,
                    pitch=voice_config.pitch,
                    volume_gain_db=voice_config.volume_gain_db,
                    sample_rate_hertz=self.config.sample_rate_hertz
                )
                
                # Call the API
                response = self.client.synthesize_speech(
                    input=input_text,
                    voice=voice,
                    audio_config=audio_config
                )
                
                logger.info(f"Successfully synthesized speech ({len(response.audio_content)} bytes)")
                return response.audio_content
            
            except (GoogleAPIError, RetryError) as e:
                retries += 1
                delay = self.RETRY_DELAY_BASE * (2 ** (retries - 1))  # Exponential backoff
                
                logger.warning(f"TTS API error (attempt {retries}/{self.MAX_RETRIES}): {e}")
                logger.info(f"Retrying in {delay} seconds...")
                
                time.sleep(delay)
            
            except Exception as e:
                logger.error(f"Unexpected error during speech synthesis: {e}")
                raise
        
        # If all retries failed
        raise Exception("Failed to synthesize speech after maximum retries")


class VoiceManager:
    """
    Manages voice selection and configuration for different speakers.
    Provides voice recommendations based on gender preferences.
    """
    
    # Top-tier Google Neural2 voices by quality and naturalness
    PREMIUM_VOICES = {
        Gender.MALE: [
            "en-US-Neural2-D",  # Authoritative, confident male voice
            "en-US-Neural2-J",  # Warm, friendly male voice
            "en-US-Studio-O",   # Clear, professional male voice
            "en-GB-Neural2-B",  # British male voice
            "en-AU-Neural2-B",  # Australian male voice
        ],
        Gender.FEMALE: [
            "en-US-Neural2-F",  # Warm, professional female voice
            "en-US-Neural2-G",  # Bright, engaging female voice
            "en-US-Neural2-E",  # Clear, articulate female voice
            "en-US-Neural2-C",  # Smooth, calming female voice
            "en-GB-Neural2-A",  # British female voice
            "en-AU-Neural2-A",  # Australian female voice
        ],
        Gender.NEUTRAL: [
            "en-US-Neural2-A",  # Somewhat neutral voice
            "en-US-Neural2-C",  # Somewhat neutral voice
        ]
    }
    
    def __init__(self, tts_client: TTSClient):
        """
        Initialize the voice manager.
        
        Args:
            tts_client: TTS client for voice lookup
        """
        self.tts_client = tts_client
        self.available_voices = self._get_available_voices()
    
    def _get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices from the API.
        
        Returns:
            List of available voice descriptions
        """
        try:
            response = self.tts_client.client.list_voices()
            return [
                {
                    "name": voice.name,
                    "language_codes": voice.language_codes,
                    "gender": voice.ssml_gender,
                    "natural": getattr(voice, "natural_sample_rate_hertz", 0) > 0
                }
                for voice in response.voices
            ]
        except Exception as e:
            logger.warning(f"Failed to retrieve available voices: {e}")
            # Fall back to predefined premium voices
            return []
    
    def recommend_voices(
        self, 
        speakers: List[str], 
        gender_preference: Optional[str] = None
    ) -> Dict[str, VoiceConfig]:
        """
        Recommend appropriate voices for speakers.
        
        Args:
            speakers: List of speaker IDs
            gender_preference: Optional preference for voice genders ('male', 'female', 'mixed')
            
        Returns:
            Dictionary mapping speaker IDs to voice configurations
        """
        if not speakers:
            return {}
        
        # Determine gender assignment based on preference
        if gender_preference == "male":
            genders = [Gender.MALE] * len(speakers)
        elif gender_preference == "female":
            genders = [Gender.FEMALE] * len(speakers)
        elif gender_preference == "mixed":
            # For two speakers, use one male and one female
            if len(speakers) == 2:
                genders = [Gender.MALE, Gender.FEMALE]
            # For more than two, alternate genders
            else:
                genders = [Gender.MALE if i % 2 == 0 else Gender.FEMALE for i in range(len(speakers))]
        else:
            # Default: if the speaker's name suggests gender, use it; otherwise alternate
            genders = []
            for speaker in speakers:
                if speaker.lower() in ["alex", "jordan", "michael", "david", "james"]:
                    genders.append(Gender.MALE)
                elif speaker.lower() in ["alice", "emma", "olivia", "sarah", "emily"]:
                    genders.append(Gender.FEMALE)
                else:
                    # Alternate for unknown names
                    if len(genders) > 0:
                        genders.append(Gender.FEMALE if genders[-1] == Gender.MALE else Gender.MALE)
                    else:
                        genders.append(Gender.MALE)
        
        # Assign voices based on determined genders
        voice_configs = {}
        for i, (speaker, gender) in enumerate(zip(speakers, genders)):
            # Select a premium voice for this gender, cycling through options for variety
            premium_voices = self.PREMIUM_VOICES[gender]
            voice_name = premium_voices[i % len(premium_voices)]
            
            # Create a customized voice config
            voice_configs[speaker.lower()] = VoiceConfig(
                name=voice_name,
                gender=gender,
                # Add slight variations to make voices more distinct
                speaking_rate=1.0 + (random.uniform(-0.1, 0.1) if i > 0 else 0),
                pitch=random.uniform(-1.0, 1.0) if i > 0 else 0,
                volume_gain_db=0.0
            )
        
        return voice_configs


class ScriptParser:
    """
    Parses podcast scripts into structured segments for audio generation.
    Handles different script formats and extracts speaker information.
    """
    
    def __init__(self, enable_ssml: bool = True):
        """
        Initialize the script parser.
        
        Args:
            enable_ssml: Whether to enable SSML enhancements
        """
        self.enable_ssml = enable_ssml
    
    def parse_script(
        self, 
        script: Dict[str, Any]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parse a podcast script into audio segments.
        
        Args:
            script: Structured podcast script
            
        Returns:
            Tuple of (episode_title, list of speech segments)
        """
        episode_title = script.get("title", "Untitled Podcast")
        sections = script.get("sections", [])
        
        segments = []
        for section in sections:
            section_title = section.get("title", "")
            section_segments = section.get("segments", [])
            
            # Add a pause before new sections (except the first)
            if len(segments) > 0:
                segments.append({
                    "type": "pause",
                    "duration": 1.0,
                    "section_break": True,
                    "section_title": section_title
                })
            
            # Process each speaker segment
            for segment in section_segments:
                speaker = segment.get("speaker", "").lower()
                text = segment.get("text", "")
                
                # Skip empty segments
                if not text.strip():
                    continue
                
                # Process text for SSML if enabled
                if self.enable_ssml:
                    text = self._enhance_with_ssml(text, speaker)
                
                # Add the segment
                segments.append({
                    "type": "speech",
                    "speaker": speaker,
                    "text": text,
                    "ssml": self.enable_ssml,
                    "section": section_title
                })
                
                # Add a short pause between speakers
                segments.append({
                    "type": "pause",
                    "duration": 0.5,
                    "section_break": False
                })
        
        return episode_title, segments
    
    def _enhance_with_ssml(self, text: str, speaker: str) -> str:
        """
        Enhance text with SSML for more natural speech.
        
        Args:
            text: Raw text to enhance
            speaker: Speaker ID for persona-specific enhancements
            
        Returns:
            SSML-enhanced text
        """
        # Detect if text is already SSML
        if text.strip().startswith("<speak>") and text.strip().endswith("</speak>"):
            return text
        
        # Add SSML tags
        ssml = "<speak>\n"
        
        # Apply speaker-specific voice characteristics
        if speaker == "alex":
            # Alex is enthusiastic and energetic
            ssml += f'<prosody rate="105%" pitch="+0.5st">{text}</prosody>'
        elif speaker == "jordan":
            # Jordan is thoughtful and measured
            ssml += f'<prosody rate="95%" pitch="-0.5st">{text}</prosody>'
        else:
            ssml += text
        
        ssml += "\n</speak>"
        
        # Apply common text-to-SSML enhancements
        ssml = self._apply_ssml_enhancements(ssml)
        
        return ssml
    
    def _apply_ssml_enhancements(self, ssml: str) -> str:
        """
        Apply various SSML enhancements to improve naturalness.
        
        Args:
            ssml: SSML text to enhance
            
        Returns:
            Enhanced SSML
        """
        # Extract the content between <speak> tags
        content_match = re.search(r'<speak>\s*(.*?)\s*</speak>', ssml, re.DOTALL)
        if not content_match:
            return ssml
        
        content = content_match.group(1)
        
        # 1. Add breaks after sentences
        content = re.sub(r'([.!?])\s+', r'\1<break time="600ms"/> ', content)
        
        # 2. Add breaks for commas
        content = re.sub(r',\s+', r',<break time="300ms"/> ', content)
        
        # 3. Add emphasis to key phrases
        content = re.sub(r'\b(importantly|significantly|crucially|notably)\b', 
                          r'<emphasis level="moderate">\1</emphasis>', content)
        
        # 4. Improve pronunciation of technical terms
        tech_terms = {
            r'\barXiv\b': '<say-as interpret-as="spell-out">arXiv</say-as>',
            r'\bSQL\b': '<say-as interpret-as="spell-out">SQL</say-as>',
            r'\bAPI\b': '<say-as interpret-as="spell-out">API</say-as>',
            r'\bJSON\b': '<say-as interpret-as="spell-out">JSON</say-as>',
            r'\bAI\b': '<say-as interpret-as="spell-out">AI</say-as>',
            r'\bML\b': '<say-as interpret-as="spell-out">ML</say-as>',
            r'\bNLP\b': '<say-as interpret-as="spell-out">NLP</say-as>',
            r'\bGPT\b': '<say-as interpret-as="spell-out">GPT</say-as>',
        }
        
        for pattern, replacement in tech_terms.items():
            content = re.sub(pattern, replacement, content)
        
        # 5. Improve number pronunciation
        # Read numbers as digits for years
        content = re.sub(r'\b(19|20)(\d{2})\b', 
                          r'<say-as interpret-as="date" format="y">\1\2</say-as>', content)
        
        # Read decimal numbers properly
        content = re.sub(r'\b(\d+\.\d+)\b', 
                          r'<say-as interpret-as="decimal">\1</say-as>', content)
        
        # 6. Add thoughtful pauses before important points
        content = re.sub(r'\b(In conclusion|To summarize|Importantly|Finally)\b', 
                          r'<break time="750ms"/>\1', content)
        
        # 7. Add subtle breathing for long sentences
        content = re.sub(r'([^.!?]{60,}?)(\s+and\s+|\s+but\s+|\s+or\s+|\s+because\s+)', 
                          r'\1<break time="250ms"/>\2', content)
        
        # Reassemble the SSML
        enhanced_ssml = f"<speak>\n{content}\n</speak>"
        return enhanced_ssml


class AudioProcessor:
    """
    Processes audio segments and combines them into a complete podcast.
    Handles audio effects, transitions, and background music.
    """
    
    # Common background music genres for podcasts
    DEFAULT_MUSIC_GENRES = ["ambient", "lo-fi", "instrumental", "acoustic"]
    
    def __init__(self, config: TTSConfig):
        """
        Initialize the audio processor.
        
        Args:
            config: TTS configuration
        """
        self.config = config
        self.tmp_dir = config.tmp_directory or tempfile.mkdtemp()
        
        # Create temporary directory if it doesn't exist
        os.makedirs(self.tmp_dir, exist_ok=True)
        
        # Check for output directory
        os.makedirs(config.output_directory, exist_ok=True)
    
    def process_segments(
        self, 
        episode_title: str, 
        segments: List[Dict[str, Any]], 
        tts_client: TTSClient, 
        voice_configs: Dict[str, VoiceConfig]
    ) -> str:
        """
        Process audio segments into a complete podcast.
        
        Args:
            episode_title: Title of the episode
            segments: List of speech segments
            tts_client: TTS client for audio generation
            voice_configs: Voice configurations for speakers
            
        Returns:
            Path to the final audio file
        """
        # Generate audio for each segment
        audio_files = []
        
        for i, segment in enumerate(segments):
            segment_path = None
            
            if segment["type"] == "speech":
                speaker = segment["speaker"]
                text = segment["text"]
                ssml = segment.get("ssml", False)
                
                # Skip if we don't have a voice for this speaker
                if speaker not in voice_configs:
                    logger.warning(f"No voice configuration for speaker '{speaker}', skipping segment")
                    continue
                
                try:
                    # Generate speech audio
                    voice_config = voice_configs[speaker]
                    audio_content = tts_client.synthesize_speech(text, voice_config, ssml)
                    
                    # Save to temporary file
                    segment_path = os.path.join(self.tmp_dir, f"segment_{i:04d}.mp3")
                    with open(segment_path, "wb") as f:
                        f.write(audio_content)
                    
                    audio_files.append({
                        "path": segment_path,
                        "type": "speech",
                        "speaker": speaker,
                        "section": segment.get("section", "")
                    })
                
                except Exception as e:
                    logger.error(f"Error generating speech for segment {i}: {e}")
                    # Continue with other segments
            
            elif segment["type"] == "pause":
                duration = segment.get("duration", 0.5)
                section_break = segment.get("section_break", False)
                
                # Create silence segment
                segment_path = os.path.join(self.tmp_dir, f"pause_{i:04d}.mp3")
                silence = AudioSegment.silent(duration=int(duration * 1000))  # Convert to milliseconds
                silence.export(segment_path, format="mp3")
                
                audio_files.append({
                    "path": segment_path,
                    "type": "pause",
                    "duration": duration,
                    "section_break": section_break,
                    "section_title": segment.get("section_title", "")
                })
        
        # Combine audio segments
        final_audio = self._combine_audio_segments(audio_files)
        
        # Generate output filename
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in episode_title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{safe_title}_{timestamp}.mp3"
        output_path = os.path.join(self.config.output_directory, output_filename)
        
        # Export final audio
        final_audio.export(
            output_path,
            format="mp3",
            bitrate="192k",
            tags={
                "album": "Research Paper Podcast",
                "title": episode_title,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
        )
        
        logger.info(f"Successfully created podcast: {output_path}")
        return output_path
    
    def _combine_audio_segments(self, audio_files: List[Dict[str, Any]]) -> AudioSegment:
        """
        Combine audio segments with transitions and background music.
        
        Args:
            audio_files: List of audio segment files
            
        Returns:
            Combined AudioSegment
        """
        if not audio_files:
            raise ValueError("No audio files to combine")
        
        # Load all audio segments
        segments = []
        for file_info in audio_files:
            try:
                audio = AudioSegment.from_file(file_info["path"])
                segments.append({
                    "audio": audio,
                    "type": file_info["type"],
                    "section_break": file_info.get("section_break", False),
                    "section_title": file_info.get("section_title", ""),
                    "speaker": file_info.get("speaker", "")
                })
            except Exception as e:
                logger.error(f"Error loading audio file {file_info['path']}: {e}")
        
        # Create combined audio
        combined = AudioSegment.empty()
        
        # Add intro jingle if available
        intro_jingle = self._get_intro_jingle()
        if intro_jingle:
            combined += intro_jingle
            # Add a short pause after jingle
            combined += AudioSegment.silent(duration=500)
        
        # Process each segment
        for i, segment in enumerate(segments):
            audio = segment["audio"]
            
            # Add section transition if needed
            if segment["type"] == "pause" and segment.get("section_break", False):
                if self.config.add_transitions and i > 0 and i < len(segments) - 1:
                    transition = self._create_section_transition(segment.get("section_title", ""))
                    combined += transition
                    continue  # Skip adding the pause segment itself
            
            # For speech segments, normalize and add subtle enhancements
            if segment["type"] == "speech":
                # Trim silence from beginning and end
                start_trim = detect_leading_silence(audio)
                end_trim = detect_trailing_silence(audio)
                audio = audio[start_trim:len(audio) - end_trim]
                
                # Normalize volume for consistency
                audio = normalize(audio)
                
                # Very slight compression to improve clarity
                audio = self._apply_compression(audio)
            
            # Add the segment to the combined audio
            combined += audio
        
        # Add background music if enabled
        if self.config.enable_background_music:
            combined = self._add_background_music(combined)
        
        # Final normalization and processing
        combined = normalize(combined)
        
        # Add outro if available
        outro = self._get_outro_jingle()
        if outro:
            # Add a short pause before outro
            combined += AudioSegment.silent(duration=500)
            combined += outro
        
        return combined
    
    def _apply_compression(self, audio: AudioSegment) -> AudioSegment:
        """
        Apply subtle compression to improve speech clarity.
        
        Args:
            audio: Input audio segment
            
        Returns:
            Processed audio segment
        """
        # This is a simplified compression implementation
        # For production use, consider using a proper dynamic range compressor
        threshold = -20  # dB
        ratio = 1.5      # Compression ratio
        attack = 5       # ms
        release = 50     # ms
        
        # Convert to array, apply compression, convert back
        # (This is a simplified implementation)
        return audio
    
    def _create_section_transition(self, section_title: str) -> AudioSegment:
        """
        Create a transition effect between sections.
        
        Args:
            section_title: Title of the next section
            
        Returns:
            Transition audio segment
        """
        # Create a short transition sound
        duration = int(self.config.transition_duration * 1000)  # ms
        
        # Create a subtle transition effect (fade between tones)
        transition = AudioSegment.silent(duration=duration)
        
        # Add a subtle transition sound
        transition = transition.overlay(
            AudioSegment.sine(440).fade_in(100).fade_out(100)[:200] - 20,  # Quieter
            position=0
        )
        
        # Add a longer pause for section transitions
        transition += AudioSegment.silent(duration=800)
        
        return transition
    
    def _add_background_music(self, podcast: AudioSegment) -> AudioSegment:
        """
        Add background music to the podcast.
        
        Args:
            podcast: The podcast audio without music
            
        Returns:
            Podcast with background music
        """
        # Check if a specific background music path is provided
        music_path = self.config.background_music_path
        
        # If no music path provided or file doesn't exist, return original audio
        if not music_path or not os.path.exists(music_path):
            logger.warning("Background music file not found, skipping")
            return podcast
        
        try:
            # Load background music
            music = AudioSegment.from_file(music_path)
            
            # Adjust volume of background music
            music = music - abs(self.config.background_music_volume)
            
            # Loop music if needed to match podcast length
            if len(music) < len(podcast):
                loops_needed = int(len(podcast) / len(music)) + 1
                looped_music = music * loops_needed
                music = looped_music[:len(podcast)]
            else:
                music = music[:len(podcast)]
            
            # Fade in at beginning and fade out at end
            fade_duration = min(5000, len(music) // 10)  # Fade time in ms (max 5 sec or 10% of length)
            music = music.fade_in(fade_duration).fade_out(fade_duration)
            
            # Overlay music with podcast
            podcast_with_music = podcast.overlay(music, loop=False)
            
            return podcast_with_music
        
        except Exception as e:
            logger.error(f"Error adding background music: {e}")
            return podcast
    
    def _get_intro_jingle(self) -> Optional[AudioSegment]:
        """
        Get the intro jingle audio if available.
        
        Returns:
            Intro jingle AudioSegment or None
        """
        # Check for intro jingle at standard locations
        jingle_paths = [
            os.path.join(os.path.dirname(self.config.output_directory), "assets", "intro.mp3"),
            os.path.join(os.path.dirname(__file__), "assets", "intro.mp3"),
            "./assets/intro.mp3"
        ]
        
        for path in jingle_paths:
            if os.path.exists(path):
                try:
                    jingle = AudioSegment.from_file(path)
                    return jingle
                except Exception as e:
                    logger.warning(f"Error loading intro jingle: {e}")
        
        return None
    
    def _get_outro_jingle(self) -> Optional[AudioSegment]:
        """
        Get the outro jingle audio if available.
        
        Returns:
            Outro jingle AudioSegment or None
        """
        # Check for outro jingle at standard locations
        jingle_paths = [
            os.path.join(os.path.dirname(self.config.output_directory), "assets", "outro.mp3"),
            os.path.join(os.path.dirname(__file__), "assets", "outro.mp3"),
            "./assets/outro.mp3"
        ]
        
        for path in jingle_paths:
            if os.path.exists(path):
                try:
                    jingle = AudioSegment.from_file(path)
                    return jingle
                except Exception as e:
                    logger.warning(f"Error loading outro jingle: {e}")
        
        return None


class PodcastRenderer:
    """
    Main class that orchestrates the podcast rendering process.
    Coordinates script parsing, voice selection, and audio generation.
    """
    
    def __init__(self, config: Optional[TTSConfig] = None):
        """
        Initialize the podcast renderer.
        
        Args:
            config: Optional TTS configuration
        """
        self.config = config or TTSConfig()
        self.tts_client = TTSClient(self.config)
        self.voice_manager = VoiceManager(self.tts_client)
        self.script_parser = ScriptParser(enable_ssml=self.config.enable_ssml)
        self.audio_processor = AudioProcessor(self.config)
    
    def render_podcast(
        self, 
        script: Dict[str, Any],
        gender_preference: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Render a podcast from a script.
        
        Args:
            script: Structured podcast script
            gender_preference: Optional gender preference for voices
            output_path: Optional specific output path
            
        Returns:
            Path to the generated podcast audio file
        """
        try:
            # Parse the script
            episode_title, segments = self.script_parser.parse_script(script)
            
            # Extract unique speakers
            speakers = list(set(
                segment["speaker"] for segment in segments 
                if segment["type"] == "speech" and "speaker" in segment
            ))
            
            # Recommend voices or use configured voices
            if self.config.voice_configs:
                voice_configs = self.config.voice_configs
                
                # Ensure all speakers have voice configs
                missing_speakers = [s for s in speakers if s not in voice_configs]
                if missing_speakers:
                    logger.warning(f"Missing voice configurations for speakers: {missing_speakers}")
                    # Get recommended voices for missing speakers
                    recommended = self.voice_manager.recommend_voices(
                        missing_speakers, gender_preference
                    )
                    # Add recommended voices to config
                    for speaker, voice_config in recommended.items():
                        voice_configs[speaker] = voice_config
            else:
                # Get recommended voices for all speakers
                voice_configs = self.voice_manager.recommend_voices(
                    speakers, gender_preference
                )
            
            # Process audio segments
            output_file = self.audio_processor.process_segments(
                episode_title, segments, self.tts_client, voice_configs
            )
            
            # Move to specific output path if provided
            if output_path:
                import shutil
                shutil.move(output_file, output_path)
                output_file = output_path
            
            return output_file
        
        except Exception as e:
            logger.error(f"Error rendering podcast: {e}")
            raise


# Example SSML usage functions for reference
def ssml_examples() -> Dict[str, str]:
    """
    Provide examples of SSML enhancements for different scenarios.
    
    Returns:
        Dictionary of SSML examples
    """
    examples = {
        "standard_emphasis": """
<speak>
In this paper, the researchers found that <emphasis level="moderate">transformer models significantly outperformed</emphasis> traditional approaches.
</speak>
""",
        "pronunciation_fix": """
<speak>
The technique of <say-as interpret-as="spell-out">BERT</say-as> fine-tuning was applied to <sub alias="natural language processing">NLP</sub> tasks.
</speak>
""",
        "thoughtful_pause": """
<speak>
The results were consistent across all test cases. <break time="750ms"/> However, we need to consider some important limitations.
</speak>
""",
        "number_formatting": """
<speak>
The model achieved <say-as interpret-as="cardinal">99.4</say-as> percent accuracy, outperforming the baseline from <say-as interpret-as="date" format="y">2022</say-as>.
</speak>
""",
        "voice_variation": """
<speak>
<prosody rate="slow" pitch="-2st">Let's take a moment to consider the implications.</prosody>
<prosody rate="medium" pitch="+0st">This opens up several new research directions.</prosody>
<prosody rate="fast" pitch="+2st">I'm particularly excited about the applications in real-time systems!</prosody>
</speak>
""",
        "audio_effects": """
<speak>
<audio src="https://actions.google.com/sounds/v1/ambiences/synthesizer_chord.ogg"/>
Welcome to Research Frontiers!
</speak>
""",
        "conversational_style": """
<speak>
<prosody rate="1.1" pitch="+1st">
That's fascinating! <break time="300ms"/> I never would have expected those results.
</prosody>
<break time="500ms"/>
<prosody rate="0.9" pitch="-1st">
Well, it makes sense when you consider the underlying mathematical principles.
</prosody>
</speak>
"""
    }
    
    return examples


def main():
    """Example usage of the podcast renderer."""
    # Example script (simplified for demonstration)
    example_script = {
        "title": "Recent Advances in Transformer Models",
        "sections": [
            {
                "title": "INTRODUCTION",
                "segments": [
                    {
                        "speaker": "alex",
                        "text": "Welcome to Research Frontiers! Today we're discussing some fascinating developments in transformer models."
                    },
                    {
                        "speaker": "jordan",
                        "text": "That's right, Alex. We'll be looking at two papers that explore innovations that make these models more efficient and effective."
                    }
                ]
            },
            {
                "title": "PAPER 1: Attention Temperature Matters",
                "segments": [
                    {
                        "speaker": "alex",
                        "text": "Our first paper is titled 'Attention Temperature Matters in Abstractive Summarization'. This research explores how a simple parameter adjustment can significantly improve output quality."
                    },
                    {
                        "speaker": "jordan",
                        "text": "The key insight here is that higher temperature settings allow the model to be more creative while still maintaining factual consistency. It's a great example of how small changes can have big impacts."
                    }
                ]
            },
            {
                "title": "CONCLUSION",
                "segments": [
                    {
                        "speaker": "jordan",
                        "text": "These papers show that transformer models still have significant room for optimization, even without changing their fundamental architecture."
                    },
                    {
                        "speaker": "alex",
                        "text": "Absolutely! Thanks for joining us on Research Frontiers. We'll be back next week with more cutting-edge research discussions."
                    }
                ]
            }
        ]
    }
    
    try:
        # Create configuration
        config = TTSConfig(
            service_account_path="path/to/service-account.json",
            enable_ssml=True,
            enable_background_music=True,
            background_music_path="path/to/background.mp3",
            output_directory="./podcasts"
        )
        
        # Initialize renderer
        renderer = PodcastRenderer(config)
        
        # Render podcast
        output_file = renderer.render_podcast(
            example_script,
            gender_preference="mixed"  # Use mixed male/female voices
        )
        
        print(f"Podcast created successfully: {output_file}")
        
    except Exception as e:
        print(f"Error creating podcast: {e}")


if __name__ == "__main__":
    # This would run the example in a real environment
    # main()
    pass