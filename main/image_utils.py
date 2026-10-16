"""Validação e compressão das imagens enviadas pelos usuários.

Limites de tamanho:
- tweets, respostas e mensagens: 5 MB — padrão do X/Twitter para fotos (o
  etewitter é inspirado nele). Para referência, outras redes usam:
  Facebook/Instagram/Threads/Mastodon 8 MB, LinkedIn 10 MB e WhatsApp 16 MB.
- foto de perfil: 20 MB.
- foto de capa: 50 MB.

Formatos aceitos: os que os navegadores exibem nativamente (JPG, PNG, GIF, WEBP).
"""
import io
import os

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps


# Limite de upload — 5 MB (padrão X/Twitter) para tweets, respostas e mensagens.
MAX_IMAGE_UPLOAD_SIZE = 5 * 1024 * 1024
MAX_IMAGE_UPLOAD_SIZE_MB = MAX_IMAGE_UPLOAD_SIZE // (1024 * 1024)

# Limites específicos de perfil e capa.
MAX_PROFILE_IMAGE_UPLOAD_SIZE = 20 * 1024 * 1024
MAX_PROFILE_IMAGE_UPLOAD_SIZE_MB = MAX_PROFILE_IMAGE_UPLOAD_SIZE // (1024 * 1024)
MAX_BANNER_IMAGE_UPLOAD_SIZE = 50 * 1024 * 1024
MAX_BANNER_IMAGE_UPLOAD_SIZE_MB = MAX_BANNER_IMAGE_UPLOAD_SIZE // (1024 * 1024)

# Formatos de imagem suportados pelos navegadores.
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
IMAGE_ACCEPT_ATTRIBUTE = 'image/jpeg,image/png,image/gif,image/webp'

# Parâmetros da compressão.
MAX_IMAGE_DIMENSION = 1600  # maior lado da imagem depois de redimensionar
JPEG_QUALITY = 85


def _size_error(size, max_bytes, what):
    return ValidationError(
        '%(what)s é muito grande (%(size).1f MB). O limite é %(max)s MB.'
        % {'what': what, 'size': size / (1024 * 1024), 'max': max_bytes // (1024 * 1024)}
    )


def validate_image_size(file):
    """Recusa arquivos maiores que o limite padrão (5 MB)."""
    size = getattr(file, 'size', None)
    if size and size > MAX_IMAGE_UPLOAD_SIZE:
        raise _size_error(size, MAX_IMAGE_UPLOAD_SIZE, 'A imagem')
    return file


def validate_profile_image_size(file):
    """Foto de perfil: no máximo 20 MB."""
    size = getattr(file, 'size', None)
    if size and size > MAX_PROFILE_IMAGE_UPLOAD_SIZE:
        raise _size_error(size, MAX_PROFILE_IMAGE_UPLOAD_SIZE, 'A foto de perfil')
    return file


def validate_banner_image_size(file):
    """Foto de capa: no máximo 50 MB."""
    size = getattr(file, 'size', None)
    if size and size > MAX_BANNER_IMAGE_UPLOAD_SIZE:
        raise _size_error(size, MAX_BANNER_IMAGE_UPLOAD_SIZE, 'A foto de capa')
    return file


def form_image_errors(form):
    """Erros de validação ligados ao campo de imagem de um formulário."""
    return list(form.errors.get('image', []))


def compress_image(file):
    """Redimensiona e recomprime uma imagem enviada.

    - Animações (GIF/WEBP animados) são mantidas como estão.
    - As demais são achatadas num fundo branco, redimensionadas para no máximo
      MAX_IMAGE_DIMENSION no maior lado e salvas como JPEG (JPEG_QUALITY).
    """
    if not file:
        return file

    file.seek(0)
    try:
        image = Image.open(file)
        image.load()
    except Exception:
        raise ValidationError('Arquivo de imagem inválido.')

    # Animações não podem ser recomprimidas sem perder quadros.
    if getattr(image, 'is_animated', False) and getattr(image, 'n_frames', 1) > 1:
        file.seek(0)
        return file

    image = ImageOps.exif_transpose(image)
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        rgba = image.convert('RGBA')
        background = Image.new('RGB', rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.LANCZOS)

    output = io.BytesIO()
    image.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True)
    output.seek(0)

    base = os.path.splitext(os.path.basename(getattr(file, 'name', '') or 'image'))[0]
    return ContentFile(output.read(), name='%s.jpg' % (base or 'image'))
