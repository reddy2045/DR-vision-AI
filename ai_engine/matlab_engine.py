import os
from pathlib import Path
from threading import Lock

from django.conf import settings


_engine = None
_engine_lock = Lock()


def get_engine():
    """Start MATLAB once and reuse the Engine for subsequent screenings."""
    global _engine
    if _engine is not None:
        return _engine

    with _engine_lock:
        if _engine is None:
            try:
                import matlab.engine
            except ImportError as exc:
                raise RuntimeError(
                    'MATLAB Engine for Python is not installed. Install it from '
                    'MATLAB R2026a extern/engines/python.'
                ) from exc
            _engine = matlab.engine.start_matlab()
            helper_path = Path(__file__).with_name('matlab')
            _engine.addpath(str(helper_path), nargout=0)
    return _engine


def configured_model_path():
    model_path = os.environ.get('MATLAB_MODEL_PATH', settings.MATLAB_MODEL_PATH)
    path = Path(model_path).expanduser()
    if not path.is_file():
        raise RuntimeError(f'MATLAB model was not found at {path}')
    return path
