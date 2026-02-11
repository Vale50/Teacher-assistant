"""
S3 Upload Service for Student Profile and Posts
Handles file uploads to AWS S3 for student profiles, posts, and media
"""
import os
import boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import mimetypes

class S3UploadService:
    """Service for uploading files to AWS S3"""

    def __init__(self):
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.cloudfront_domain = os.getenv('CLOUDFRONT_DOMAIN', '')

        # Check if AWS credentials are configured
        self.is_configured = bool(
            self.aws_access_key_id and
            self.aws_secret_access_key and
            self.bucket_name
        )

        # Initialize S3 client only if configured
        self.s3_client = None
        if self.is_configured:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.aws_region
                )
            except Exception as e:
                print(f"Warning: Failed to initialize S3 client: {str(e)}")
                self.is_configured = False

        # Allowed file extensions
        self.ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        self.ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm', 'mkv'}
        self.ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
        self.ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

        # Max file sizes (in MB)
        self.MAX_IMAGE_SIZE_MB = 10
        self.MAX_VIDEO_SIZE_MB = 100
        self.MAX_AVATAR_SIZE_MB = 5
        self.MAX_DOCUMENT_SIZE_MB = 25

    def allowed_file(self, filename, file_type):
        """Check if file extension is allowed"""
        if '.' not in filename:
            return False

        ext = filename.rsplit('.', 1)[1].lower()

        if file_type == 'image':
            return ext in self.ALLOWED_IMAGE_EXTENSIONS
        elif file_type == 'video':
            return ext in self.ALLOWED_VIDEO_EXTENSIONS
        elif file_type == 'avatar':
            return ext in self.ALLOWED_AVATAR_EXTENSIONS
        elif file_type == 'profile_picture':
            return ext in self.ALLOWED_IMAGE_EXTENSIONS
        elif file_type == 'document':
            return ext in self.ALLOWED_DOCUMENT_EXTENSIONS

        return False

    def get_file_size_mb(self, file_obj):
        """Get file size in MB"""
        file_obj.seek(0, os.SEEK_END)
        size_bytes = file_obj.tell()
        file_obj.seek(0)  # Reset file pointer
        return round(size_bytes / (1024 * 1024), 2)

    def validate_file_size(self, file_size_mb, file_type):
        """Validate file size based on type"""
        if file_type == 'image' and file_size_mb > self.MAX_IMAGE_SIZE_MB:
            return False, f"Image size must be less than {self.MAX_IMAGE_SIZE_MB}MB"
        elif file_type == 'video' and file_size_mb > self.MAX_VIDEO_SIZE_MB:
            return False, f"Video size must be less than {self.MAX_VIDEO_SIZE_MB}MB"
        elif file_type in ['avatar', 'profile_picture'] and file_size_mb > self.MAX_AVATAR_SIZE_MB:
            return False, f"Avatar size must be less than {self.MAX_AVATAR_SIZE_MB}MB"
        elif file_type == 'document' and file_size_mb > self.MAX_DOCUMENT_SIZE_MB:
            return False, f"Document size must be less than {self.MAX_DOCUMENT_SIZE_MB}MB"

        return True, None

    def generate_unique_filename(self, original_filename, student_id, file_type):
        """Generate unique filename with timestamp and UUID"""
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]

        return f"student_{student_id}/{file_type}/{timestamp}_{unique_id}.{ext}"

    def upload_file(self, file_obj, filename, student_id, file_type):
        """
        Upload file to S3

        Args:
            file_obj: File object to upload
            filename: Original filename
            student_id: Student ID for organizing files
            file_type: Type of file (image, video, avatar, profile_picture)

        Returns:
            dict: Upload result with s3_key, s3_url, file_size_mb
        """
        try:
            # Check if S3 is configured
            if not self.is_configured:
                return {
                    'success': False,
                    'error': 'File upload is not configured. Please contact administrator to configure AWS S3 credentials.'
                }

            # Validate file extension
            if not self.allowed_file(filename, file_type):
                return {
                    'success': False,
                    'error': f'Invalid file type. Allowed types for {file_type}: {self._get_allowed_extensions(file_type)}'
                }

            # Get file size
            file_size_mb = self.get_file_size_mb(file_obj)

            # Validate file size
            is_valid, error_msg = self.validate_file_size(file_size_mb, file_type)
            if not is_valid:
                return {
                    'success': False,
                    'error': error_msg
                }

            # Generate unique filename
            s3_key = self.generate_unique_filename(filename, student_id, file_type)

            # Determine content type
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

            # Upload to S3
            # Note: ACL removed - modern S3 buckets use bucket policies instead of ACLs
            # Ensure your bucket has a policy allowing public read access:
            # {
            #   "Effect": "Allow",
            #   "Principal": "*",
            #   "Action": "s3:GetObject",
            #   "Resource": "arn:aws:s3:::your-bucket-name/*"
            # }
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type
                }
            )

            # Generate URL
            if self.cloudfront_domain:
                s3_url = f"https://{self.cloudfront_domain}/{s3_key}"
            else:
                s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"

            return {
                'success': True,
                's3_key': s3_key,
                's3_url': s3_url,
                'file_size_mb': file_size_mb,
                'file_name': filename,
                'content_type': content_type
            }

        except ClientError as e:
            return {
                'success': False,
                'error': f'S3 upload error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Upload error: {str(e)}'
            }

    def delete_file(self, s3_key):
        """
        Delete file from S3

        Args:
            s3_key: S3 object key to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            print(f"Error deleting file from S3: {str(e)}")
            return False

    def _get_allowed_extensions(self, file_type):
        """Get allowed extensions for a file type"""
        if file_type == 'image':
            return ', '.join(self.ALLOWED_IMAGE_EXTENSIONS)
        elif file_type == 'video':
            return ', '.join(self.ALLOWED_VIDEO_EXTENSIONS)
        elif file_type in ['avatar', 'profile_picture']:
            return ', '.join(self.ALLOWED_AVATAR_EXTENSIONS)
        elif file_type == 'document':
            return ', '.join(self.ALLOWED_DOCUMENT_EXTENSIONS)
        return ''


# Create singleton instance
s3_service = S3UploadService()