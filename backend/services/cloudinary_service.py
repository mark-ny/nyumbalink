# services/cloudinary_service.py
import cloudinary
import cloudinary.uploader
from flask import current_app


def _configure():
    cloudinary.config(
        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=current_app.config['CLOUDINARY_API_KEY'],
        api_secret=current_app.config['CLOUDINARY_API_SECRET'],
    )


def upload_image(file, folder='nyumbalink') -> dict:
    _configure()
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        transformation=[
            {'width': 1200, 'height': 900, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'auto'}
        ]
    )
    return result


def delete_image(public_id: str) -> dict:
    _configure()
    return cloudinary.uploader.destroy(public_id)
