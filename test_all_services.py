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
    
    try:
        from app import create_app
        from app.services.gemini_service import GeminiService
        
        app = create_app('development')
        with app.app_context():
            service = GeminiService()
            print_result("Gemini client initialization", True)
            
            # Test basic generation
            mock_papers = [{'id': 'test', 'title': 'Test Paper', 'abstract': 'Test abstract', 'authors': ['Test Author']}]
            response = service.generate_script(papers=mock_papers, target_length=5)
            
            has_script = bool(response and 'title' in response)
            print_result("Script generation", has_script)
            
            return True
    except Exception as e:
        print_result("Gemini Service", False, str(e))
        return False


def test_end_to_end_workflow():
    """Test a mini end-to-end workflow using actual services"""
    print_section("END-TO-END WORKFLOW TEST")
    
    try:
        from app import create_app
        from app.services.arxiv_service import ArxivService
        from app.services.gemini_service import GeminiService
        from app.services.tts_service import TTSService
        from app.services.storage_service import StorageService
        
        app = create_app('development')
        with app.app_context():
            # Step 1: Get papers
            arxiv_service = ArxivService()
            papers, total = arxiv_service.search_papers(topics=['machine learning'], max_results=1)
            print_result("Paper retrieval", len(papers) > 0, f"Found {len(papers)} papers")
            
            # Step 2: Generate script
            gemini_service = GeminiService()
            script = gemini_service.generate_script(papers=papers[:1], target_length=5)
            print_result("Script generation", 'title' in script, f"Generated: {script.get('title', '')[:50]}...")
            
            # Step 3: Generate audio
            tts_service = TTSService()
            audio_data = tts_service.generate_audio(script)
            print_result("Audio generation", len(audio_data) > 0, f"Generated {len(audio_data)} bytes audio")
            
            # Step 4: Upload to storage
            storage_service = StorageService()
            file_url = storage_service.upload_audio(audio_data, filename="test_e2e.mp3")
            print_result("Audio storage", file_url is not None, f"Uploaded to storage")
            
            # Cleanup
            if file_url:
                storage_service.delete_audio(file_url)
                print_result("Workflow cleanup", True, "Test file removed")
            
            print("\n🎉 END-TO-END WORKFLOW SUCCESSFUL!")
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
