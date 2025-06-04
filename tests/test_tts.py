# test_tts.py (from your setup guide)
from google.cloud import texttospeech

# Ensure GOOGLE_APPLICATION_CREDENTIALS is set in your environment
client = texttospeech.TextToSpeechClient()
response = client.list_voices()

print("Available voices:")
for voice in response.voices:
    if "en-US" in voice.language_codes: # Filter for relevance
        print(f"- Name: {voice.name}, Gender: {texttospeech.SsmlVoiceGender(voice.ssml_gender).name}")