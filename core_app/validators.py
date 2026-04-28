from django.core.exceptions import ValidationError
import os

def validate_file_size(value):
    """Limite la taille des fichiers à 2 Mo"""
    filesize = value.size
    if filesize > 2 * 1024 * 1024:
        raise ValidationError("La taille maximale autorisée est de 2 Mo")

def validate_image_extension(value):
    """Vérifie que l'extension est bien une image"""
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if not ext.lower() in valid_extensions:
        raise ValidationError("Seuls les formats JPG, PNG et WEBP sont autorisés.")
