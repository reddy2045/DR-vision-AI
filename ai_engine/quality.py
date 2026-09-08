from pathlib import Path

import numpy as np
from PIL import Image, ImageStat


SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def check_image_quality(image_path):
    """Return prototype capture-quality metrics before MATLAB inference."""
    path = Path(image_path)
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return {'passed': False, 'message': 'Use a JPG, JPEG, or PNG fundus image.'}
    if path.stat().st_size > MAX_IMAGE_BYTES:
        return {'passed': False, 'message': 'Image is too large. Maximum size is 10 MB.'}

    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            rgb = np.asarray(image.convert('RGB'), dtype=np.float32)
    except (OSError, ValueError):
        return {'passed': False, 'message': 'The uploaded image could not be read.'}

    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return {'passed': False, 'message': 'The uploaded image must be a valid color image.'}

    grayscale = np.dot(rgb[..., :3], [0.299, 0.587, 0.114])
    brightness = float(grayscale.mean())
    if grayscale.shape[0] < 3 or grayscale.shape[1] < 3:
        sharpness = 0.0
    else:
        laplacian = (
            -4 * grayscale
            + np.roll(grayscale, 1, axis=0)
            + np.roll(grayscale, -1, axis=0)
            + np.roll(grayscale, 1, axis=1)
            + np.roll(grayscale, -1, axis=1)
        )
        sharpness = float(laplacian[1:-1, 1:-1].var())

    normalized = grayscale / 255.0
    field_mask = normalized > 0.08
    field_of_view = float(field_mask.mean() * 100)
    metrics = {
        'sharpness': round(sharpness, 2),
        'brightness': round(brightness, 2),
        'field_of_view_percent': round(field_of_view, 2),
        'width': int(rgb.shape[1]),
        'height': int(rgb.shape[0]),
    }

    if sharpness < 5:
        return {'passed': False, 'message': 'Image appears blurred. Please recapture it in focus.', 'metrics': metrics}
    if brightness < 40 or brightness > 220:
        return {'passed': False, 'message': 'Image illumination is unsuitable. Please recapture it with proper brightness.', 'metrics': metrics}
    if field_of_view < 20:
        return {'passed': False, 'message': 'Insufficient retinal field of view. Please recapture the fundus image.', 'metrics': metrics}

    return {'passed': True, 'message': 'Image quality is acceptable for prototype screening.', 'metrics': metrics}
