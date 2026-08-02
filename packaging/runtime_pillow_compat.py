"""Compatibilité Pillow pour le code historique Noethys.

Restaure uniquement les alias supprimés dans les versions modernes de Pillow.
Aucune image ni donnée métier n'est modifiée par ce hook.
"""
from PIL import Image

# Constantes de rééchantillonnage retirées de l'espace de noms principal.
if hasattr(Image, "Resampling"):
    _resampling = Image.Resampling
    for _name in ("NEAREST", "BILINEAR", "BICUBIC", "LANCZOS"):
        if not hasattr(Image, _name):
            setattr(Image, _name, getattr(_resampling, _name))
    if not hasattr(Image, "ANTIALIAS"):
        Image.ANTIALIAS = _resampling.LANCZOS

# Anciennes méthodes d'encodage/décodage d'images.
if not hasattr(Image.Image, "tostring"):
    Image.Image.tostring = Image.Image.tobytes
if not hasattr(Image, "fromstring"):
    Image.fromstring = Image.frombytes
