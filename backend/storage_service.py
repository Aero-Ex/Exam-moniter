import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import base64
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class StorageService:
    def __init__(self):
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")

        if self.aws_access_key and self.aws_secret_key and self.bucket_name:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region
            )
        else:
            self.s3_client = None
            print("Warning: S3 credentials not configured. File uploads will be disabled.")

    def upload_screenshot(self, image_base64: str, session_id: int, event_type: str) -> Optional[str]:
        """Upload a screenshot to S3 and return the URL"""
        if not self.s3_client:
            return None

        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)

            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"screenshots/session_{session_id}/{event_type}_{timestamp}.jpg"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=image_data,
                ContentType='image/jpeg',
                ACL='private'
            )

            # Generate URL
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
            return url

        except ClientError as e:
            print(f"Error uploading screenshot to S3: {e}")
            return None

    def upload_video_chunk(self, video_data: bytes, session_id: int, chunk_number: int) -> Optional[str]:
        """Upload a video chunk to S3"""
        if not self.s3_client:
            return None

        try:
            filename = f"recordings/session_{session_id}/chunk_{chunk_number:04d}.webm"

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=video_data,
                ContentType='video/webm',
                ACL='private'
            )

            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
            return url

        except ClientError as e:
            print(f"Error uploading video chunk to S3: {e}")
            return None

    def upload_complete_video(self, video_data: bytes, session_id: int, video_type: str = "webcam") -> Optional[str]:
        """Upload complete video recording to S3"""
        if not self.s3_client:
            return None

        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"recordings/session_{session_id}/{video_type}_{timestamp}.webm"

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=video_data,
                ContentType='video/webm',
                ACL='private'
            )

            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
            return url

        except ClientError as e:
            print(f"Error uploading video to S3: {e}")
            return None

    def generate_presigned_url(self, file_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate a presigned URL for accessing a private file"""
        if not self.s3_client:
            return None

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None
