"""Compatibilité Pillow pour le code historique Noethys.

Restaure uniquement les alias supprimés dans les versions modernes de Pillow.
Aucune image ni donnée métier n'est modifiée par ce hook.
"""
from PIL import Image

if hasattr(Image, "Resampling"):
    _resampling = Image.Resampling
    for _name in ("NEAREST", "BILINEAR", "BICUBIC", "LANCZOS"):
        if not hasattr(Image, _name):
            setattr(Image, _name, getattr(_resampling, _name))
    if not hasattr(Image, "ANTIALIAS"):
        Image.ANTIALIAS = _resampling.LANCZOS

if not hasattr(Image.Image, "tostring"):
    Image.Image.tostring = Image.Image.tobytes
if not hasattr(Image, "fromstring"):
    Image.fromstring = Image.frombytes
