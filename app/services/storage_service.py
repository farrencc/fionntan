# app/services/storage_service.py

import os
import io
import logging
import tempfile
from datetime import datetime
from typing import Optional

from google.cloud import storage
from flask import current_app

logger = logging.getLogger(__name__)

class StorageService:
    """Service for managing file storage with Google Cloud Storage."""
    
    def __init__(self):
        """Initialize storage service."""
        try:
            self.bucket_name = current_app.config.get('GCS_BUCKET_NAME', 'podcast-audio-storage')
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            
            # Ensure bucket exists
            if not self.bucket.exists():
                self.bucket = self.client.create_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Error initializing storage service: {str(e)}")
            raise
    
    def upload_audio(self, audio_data: bytes, filename: str) -> str:
        """Upload audio file to storage."""
        try:
            # Create a unique file path
            file_path = f"audio/{datetime.utcnow().strftime('%Y/%m/%d')}/{filename}"
        
            # Upload to GCS
            blob = self.bucket.blob(file_path)
            blob.upload_from_string(audio_data, content_type='audio/mpeg')
        
            # Remove this line that's causing the error:
            # blob.make_public()
        
            # Return the storage URL (not public URL)
            return f"gs://{self.bucket_name}/{file_path}"
        
        except Exception as e:
            logger.error(f"Error uploading audio: {str(e)}")
            raise 

    def download_audio(self, file_url: str) -> str:
        """Download audio file and return local path."""
        try:
            # Extract blob name from URL
            blob_name = self._extract_blob_name(file_url)
            
            if not blob_name:
                raise ValueError("Invalid file URL")
            
            # Download to temporary file
            blob = self.bucket.blob(blob_name)
            
            # Create temporary file
            fd, temp_path = tempfile.mkstemp(suffix='.mp3')
            os.close(fd)
            
            # Download file
            blob.download_to_filename(temp_path)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            raise
    
    def delete_audio(self, file_url: str) -> bool:
        """Delete audio file from storage."""
        try:
            blob_name = self._extract_blob_name(file_url)
            
            if not blob_name:
                return False
            
            blob = self.bucket.blob(blob_name)
            blob.delete()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting audio: {str(e)}")
            return False
    
    def get_audio_info(self, file_url: str) -> Optional[dict]:
        """Get audio file information."""
        try:
            blob_name = self._extract_blob_name(file_url)
            
            if not blob_name:
                return None
            
            blob = self.bucket.blob(blob_name)
            
            if not blob.exists():
                return None
            
            blob.reload()
            
            return {
                'size': blob.size,
                'content_type': blob.content_type,
                'created_at': blob.time_created,
                'updated_at': blob.updated,
                'public_url': blob.public_url
            }
            
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            return None
    
    def _extract_blob_name(self, file_url: str) -> Optional[str]:
        """Extract blob name from public URL."""
        try:
            # Parse public URL to get blob name
            if file_url.startswith('https://storage.googleapis.com/'):
                parts = file_url.split(f'/{self.bucket_name}/')
                if len(parts) > 1:
                    return parts[1]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting blob name: {str(e)}")
            return None
