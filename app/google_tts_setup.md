# Google Cloud Text-to-Speech Setup Instructions

Follow these steps to set up Google Cloud Text-to-Speech API for your Research Paper Podcast Generator application.

## 1. Create a Google Cloud Project (if you haven't already)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click on the project dropdown at the top of the page.
3. Click **New Project**.
4. Name your project (e.g., "Research Paper Podcast") and click **Create**.
5. Select your new project from the project dropdown.

## 2. Enable the Text-to-Speech API

1. In the Google Cloud Console, navigate to **APIs & Services** > **Library**.
2. Search for "Text-to-Speech API" in the search bar.
3. Click on **Cloud Text-to-Speech API**.
4. Click **Enable** to enable the API for your project.

## 3. Create Service Account Credentials

1. In the Google Cloud Console, navigate to **APIs & Services** > **Credentials**.
2. Click **Create Credentials** and select **Service account**.
3. Fill in the service account details:
   - Service account name: "research-podcast-tts"
   - Service account ID: Will be auto-filled
   - Service account description: "Service account for Text-to-Speech API"
4. Click **Create and Continue**.
5. Grant the service account access:
   - Click **Select a role** dropdown
   - Search for "Text-to-Speech" (be careful not to select Speech-to-Text)
   - Select **Text-to-Speech Admin** (not Speech-to-Text) 
   - If you can't find this role, look under AI Platform or Machine Learning categories
   - Alternatively, you can use **Project Editor** but this gives broader permissions
   - Click **Continue**
6. Click **Done**.

## 4. Generate and Download the Service Account Key

1. Find your newly created service account in the credentials list.
2. Click on the service account email to open its details.
3. Go to the **Keys** tab.
4. Click **Add Key** > **Create new key**.
5. Choose **JSON** format and click **Create**.
6. The JSON key file will be downloaded automatically.
7. Save this file securely in your project directory (e.g., `credentials/google-tts-credentials.json`).

## 5. Configure Your Application

1. Update your `.env` file in your project root directory:

```env
# Flask Settings
FLASK_ENV=development
SECRET_KEY=your_secure_random_key

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id_from_google
GOOGLE_CLIENT_SECRET=your_client_secret_from_google
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback

# Google Cloud Text-to-Speech
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/google-tts-credentials.json

# Database
DATABASE_URL=sqlite:///app.db

# Audio Output
AUDIO_OUTPUT_DIR=./audio_output
```

2. For production, use environment variables or a secure secret management system.

## 6. Install System Dependencies

### For Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg sox
```

### For macOS:
```bash
brew install ffmpeg sox
```

### For NixOS (already configured in shell.nix):
The dependencies are already included in your development environment.

## 7. Verify Installation

1. Start your development environment:
```bash
nix-shell
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Test the Text-to-Speech API:
```python
# test_tts.py
from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()
voices = client.list_voices()

print("Available voices:")
for voice in voices.voices:
    print(f"- {voice.name} ({voice.ssml_gender})")
```

4. Run the test:
```bash
python test_tts.py
```

## 8. Voice Configuration

The application uses Google's premium Neural2 voices by default. Available voice types:

### Male Voices:
- `en-US-Neural2-D` - Authoritative, confident male voice
- `en-US-Neural2-J` - Warm, friendly male voice
- `en-US-Studio-O` - Clear, professional male voice
- `en-GB-Neural2-B` - British male voice
- `en-AU-Neural2-B` - Australian male voice

### Female Voices:
- `en-US-Neural2-F` - Warm, professional female voice
- `en-US-Neural2-G` - Bright, engaging female voice
- `en-US-Neural2-E` - Clear, articulate female voice
- `en-US-Neural2-C` - Smooth, calming female voice
- `en-GB-Neural2-A` - British female voice
- `en-AU-Neural2-A` - Australian female voice

## 9. API Endpoints

After setup, these endpoints will be available:

- `POST /audio/generate` - Generate audio from a script
- `POST /audio/stream` - Stream audio without downloading
- `GET /audio/voices` - List available TTS voices
- `POST /audio/test-voice` - Test a specific voice
- `GET /audio/history` - Get user's generated audio files
- `GET /audio/download/<filename>` - Download generated audio

## 10. Troubleshooting

### Common Issues:

1. **API quota exceeded**: Check your Google Cloud Console for quota limits
2. **Authentication error**: Verify the service account JSON file path and permissions
3. **FFmpeg not found**: Ensure FFmpeg is installed and in your PATH
4. **Permission errors**: Check file permissions for audio output directory

### Debugging:

1. Check the application logs:
```bash
tail -f logs/app.log
```

2. Test API connectivity:
```bash
curl -X POST http://localhost:5000/audio/voices \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json"
```

## 11. Production Deployment Notes

1. Use proper secret management for credentials
2. Set up SSL/HTTPS for secure communication
3. Configure appropriate audio file storage (cloud storage recommended)
4. Set up monitoring for API usage and errors
5. Implement rate limiting to manage API costs
6. Use environment-specific configuration files

## 12. Costs

Google Cloud Text-to-Speech pricing:
- Standard voices: $4.00 per 1 million characters
- WaveNet voices: $16.00 per 1 million characters
- Neural2 voices: $16.00 per 1 million characters

Monitor your usage through the Google Cloud Console to avoid unexpected costs.