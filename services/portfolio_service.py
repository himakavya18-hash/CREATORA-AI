import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

class PortfolioService:
    ALLOWED_IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    ALLOWED_VIDEO_EXTS = {'mp4', 'webm', 'mov'}

    @classmethod
    def is_allowed_file(cls, filename, allowed_extensions=None):
        if not filename or '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        if allowed_extensions:
            return ext in allowed_extensions
        return ext in (cls.ALLOWED_IMAGE_EXTS | cls.ALLOWED_VIDEO_EXTS)

    @classmethod
    def save_uploaded_media(cls, file_storage, subfolder='portfolios'):
        """
        Saves uploaded file securely with unique UUID prefix to prevent collisions & path traversal.
        Returns the web-accessible relative static URL path.
        """
        if not file_storage or not file_storage.filename:
            return None

        filename = secure_filename(file_storage.filename)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if not ext:
            return None

        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(target_dir, exist_ok=True)

        destination_path = os.path.join(target_dir, unique_filename)
        file_storage.save(destination_path)

        # Return relative static URL
        return f"/static/uploads/{subfolder}/{unique_filename}"
