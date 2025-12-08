import uuid
from datetime import timedelta
from typing import Dict, Any
from google.cloud import storage
from app.core.config import settings

class StorageService:
    @staticmethod
    def generate_upload_url(filename: str, content_type: str) -> Dict[str, str]:
        """
        Generates a Signed URL to allow frontend to upload files directly to Google Cloud Storage.
        """
        if not settings.GCS_BUCKET_NAME:
             raise ValueError("Google Cloud Storage bucket name is not configured.")

        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)

            unique_filename = f"uploads/{uuid.uuid4()}-{filename}"
            
            blob = bucket.blob(unique_filename)

            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=15),
                method="PUT",
                content_type=content_type,
            )
            return {"upload_url": url, "gcs_path": unique_filename}
        except Exception as e:
            raise RuntimeError(f"Could not generate upload URL: {e}")

storage_service = StorageService()
