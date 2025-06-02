# test_all_services.py
"""
Combined test script for all external services:
- Text-to-Speech (TTS)
- Cloud Storage
- Gemini API

Run this after setting up all three services to verify everything works.
"""

import os
from dotenv import load_dotenv

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")

def test_tts():
    """Test Text-to-Speech service"""
    print_section("TEXT-TO-SPEECH SERVICE")
    
    try:
        from google.cloud import texttospeech
        
        client = texttospeech.TextToSpeechClient()
        print_result("TTS Client initialization", True)
        
        # Generate test audio
        synthesis_input = texttospeech.SynthesisInput(text="Testing TTS service")
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-D",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        audio_size = len(response.audio_content)
        print_result("Audio generation", audio_size > 0, f"{audio_size} bytes generated")
        
        return True
        
    except Exception as e:
        print_result("TTS Service", False, str(e))
        return False

def test_storage():
    """Test Cloud Storage service"""
    print_section("CLOUD STORAGE SERVICE")
    
    bucket_name = os.getenv('GCS_BUCKET_NAME')
    if not bucket_name:
        print_result("Storage configuration", False, "GCS_BUCKET_NAME not set in .env")
        return False
    
    try:
        from google.cloud import storage
        
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        print_result("Storage client initialization", True)
        
        # Test bucket access
        bucket_exists = bucket.exists()
        print_result("Bucket access", bucket_exists, f"Bucket: {bucket_name}")
        
        if not bucket_exists:
            return False
        
        # Test file upload
        test_content = b"Test file for Fionntan services validation"
        blob = bucket.blob("test/validation_test.txt")
        blob.upload_from_string(test_content, content_type='text/plain')
        print_result("File upload", True, "Test file uploaded")
        
        # Test file download
        downloaded = blob.download_as_bytes()
        download_success = downloaded == test_content
        print_result("File download", download_success, "Content verified")
        
        # Cleanup
        blob.delete()
        print_result("File cleanup", True, "Test file deleted")
        
        return True
        
    except Exception as e:
        print_result("Storage Service", False, str(e))
        return False

def test_gemini():
    """Test Gemini API service"""
    print_section("GEMINI API SERVICE")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print_result("Gemini configuration", False, "GEMINI_API_KEY not set in .env")
        return False
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        print_result("Gemini client initialization", True)
        
        # Test basic generation
        response = model.generate_content("Say hello in one sentence.")
        
        has_text = bool(response.text and len(response.text.strip()) > 0)
        print_result("Text generation", has_text, f"Generated {len(response.text)} characters")
        
        # Test podcast-style generation
        podcast_prompt = """Create a brief dialogue:
        HOST1: Welcome to our show!
        HOST2: [respond with excitement]"""
        
        podcast_response = model.generate_content(podcast_prompt)
        has_dialogue = "HOST1:" in podcast_response.text and "HOST2:" in podcast_response.text
        print_result("Podcast dialogue format", has_dialogue, "Structured dialogue generated")
        
        return True
        
    except ImportError:
        print_result("Gemini library", False, "google-generativeai not installed")
        return False
    except Exception as e:
        print_result("Gemini Service", False, str(e))
        return False

def test_end_to_end_workflow():
    """Test a mini end-to-end workflow"""
    print_section("END-TO-END WORKFLOW TEST")
    
    try:
        # Step 1: Generate script with Gemini
        import google.generativeai as genai
        from google.cloud import texttospeech, storage
        
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        script_prompt = "Write one sentence from a podcast host introducing an AI research paper."
        script_response = model.generate_content(script_prompt)
        script_text = script_response.text.strip()
        
        print_result("Script generation", len(script_text) > 0, f"Generated: {script_text[:50]}...")
        
        # Step 2: Convert to audio with TTS
        tts_client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=script_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-D",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        audio_response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        audio_data = audio_response.audio_content
        print_result("Audio generation", len(audio_data) > 0, f"Generated {len(audio_data)} bytes audio")
        
        # Step 3: Upload to storage
        storage_client = storage.Client()
        bucket_name = os.getenv('GCS_BUCKET_NAME')
        bucket = storage_client.bucket(bucket_name)
        
        blob = bucket.blob("test/end_to_end_test.mp3")
        blob.upload_from_string(audio_data, content_type='audio/mpeg')
        
        # Make public for testing
        blob.make_public()
        public_url = blob.public_url
        
        print_result("Audio storage", True, f"Uploaded to: {public_url[:50]}...")
        
        # Cleanup
        blob.delete()
        print_result("Workflow cleanup", True, "Test file removed")
        
        print("\n🎉 END-TO-END WORKFLOW SUCCESSFUL!")
        print("🎙️  Your system can generate complete podcasts!")
        
        return True
        
    except Exception as e:
        print_result("End-to-end workflow", False, str(e))
        return False

def main():
    """Run all service tests"""
    load_dotenv()
    
    print("🚀 FIONNTAN SERVICES VALIDATION")
    print("Testing all external services for podcast generation...")
    
    # Test individual services
    tts_ok = test_tts()
    storage_ok = test_storage()
    gemini_ok = test_gemini()
    
    # Test end-to-end workflow if all services work
    e2e_ok = False
    if tts_ok and storage_ok and gemini_ok:
        e2e_ok = test_end_to_end_workflow()
    
    # Summary
    print_section("VALIDATION SUMMARY")
    
    services = [
        ("Text-to-Speech", tts_ok),
        ("Cloud Storage", storage_ok),
        ("Gemini API", gemini_ok),
        ("End-to-End Workflow", e2e_ok)
    ]
    
    passed = sum(result for _, result in services)
    total = len(services)
    
    for service_name, result in services:
        status = "✅" if result else "❌"
        print(f"{status} {service_name}")
    
    print(f"\n🎯 OVERALL SCORE: {passed}/{total} services ready")
    
    if passed == total:
        print("\n🎉 EXCELLENT! All services are working perfectly!")
        print("✅ You can now implement the real service integrations!")
        print("🎙️  Ready to generate your first complete podcast!")
    elif passed >= 3:
        print("\n👍 GOOD! Core services are working.")
        print("⚠️  Fix any failing services, then proceed.")
    else:
        print("\n⚠️  NEEDS WORK! Multiple services need attention.")
        print("🔧 Fix these issues before implementing real integrations.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
