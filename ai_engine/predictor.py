import logging
import os
from pathlib import Path
from uuid import uuid4

from django.conf import settings

from .matlab_engine import configured_model_path, screen_fundus


CLASS_NAMES = ('No_DR', 'Mild', 'Moderate', 'Severe', 'Proliferate_DR')
logger = logging.getLogger(__name__)


def referral_for_level(dr_level):
    return {
        0: 'routine',
        1: 'routine',
        2: 'priority',
        3: 'urgent',
        4: 'urgent',
    }[dr_level]


def predict_fundus(image_path):
    """Run the existing MATLAB dlnetwork and return normalized screening data."""
    image_path = str(Path(image_path).resolve())
    gradcam_dir = Path(settings.MEDIA_ROOT) / 'gradcam'
    gradcam_dir.mkdir(parents=True, exist_ok=True)
    gradcam_path = gradcam_dir / f'{Path(image_path).stem}_{uuid4().hex}_gradcam.png'

    result = screen_fundus(configured_model_path(), image_path, gradcam_path)
    predicted_class, dr_level, confidence, referable, low_confidence, saved_gradcam = result
    dr_level = int(dr_level)
    confidence = float(confidence)
    predicted_class = str(predicted_class)
    if predicted_class not in CLASS_NAMES:
        raise RuntimeError(f'MATLAB returned an unknown DR class: {predicted_class}')

    logger.info(
        'MATLAB prediction image=%s predicted_class=%s dr_level=%s confidence=%.2f',
        image_path,
        predicted_class,
        dr_level,
        confidence,
    )

    return {
        'predicted_class': predicted_class,
        'dr_level': dr_level,
        'confidence': round(confidence, 2),
        'referable': bool(referable),
        'referral_urgency': referral_for_level(dr_level),
        'low_confidence': bool(low_confidence),
        'gradcam_path': str(saved_gradcam),
    }
