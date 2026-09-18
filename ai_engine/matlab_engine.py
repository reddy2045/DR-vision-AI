import os
from pathlib import Path
from threading import Lock

from django.conf import settings


_engine = None
_engine_lock = Lock()


class MATLABConfigurationError(RuntimeError):
    """Raised when the configured MATLAB integration files are unavailable."""

    public_message = 'MATLAB AI engine configuration is invalid. Please verify MATLAB_ROOT, MATLAB_MODEL_PATH, and MATLAB_SCRIPT_PATH.'


class MATLABEngineUnavailable(RuntimeError):
    """Raised when the real MATLAB Engine cannot be imported or started."""

    public_message = 'MATLAB AI engine is unavailable. Please verify MATLAB R2026a and MATLAB Engine for Python installation.'



def configured_paths():
    matlab_root = Path(os.environ.get('MATLAB_ROOT', settings.MATLAB_ROOT)).expanduser()
    model_path = Path(os.environ.get('MATLAB_MODEL_PATH', settings.MATLAB_MODEL_PATH)).expanduser()
    script_path = Path(os.environ.get('MATLAB_SCRIPT_PATH', settings.MATLAB_SCRIPT_PATH)).expanduser()

    if not (matlab_root / 'bin' / 'matlab.exe').is_file():
        raise MATLABConfigurationError(f'MATLAB executable was not found at {matlab_root / "bin" / "matlab.exe"}')
    if not model_path.is_file():
        raise MATLABConfigurationError(f'MATLAB model was not found at {model_path}')
    if not (script_path / 'screen_fundus.m').is_file():
        raise MATLABConfigurationError(f'MATLAB helper was not found at {script_path / "screen_fundus.m"}')

    return matlab_root, model_path, script_path


def _engine_is_alive(engine):
    try:
        engine.eval('1', nargout=1)
        return True
    except Exception:
        return False


def _close_engine():
    global _engine
    if _engine is not None:
        try:
            _engine.quit()
        except Exception:
            pass
        _engine = None


def get_engine():
    """Start MATLAB once and reuse the Engine for subsequent screenings."""
    global _engine

    with _engine_lock:
        if _engine is not None and _engine_is_alive(_engine):
            return _engine

        _close_engine()
        _, _, script_path = configured_paths()
        try:
            import matlab.engine
            _engine = matlab.engine.start_matlab()
            _engine.addpath(str(script_path), nargout=0)
        except ImportError as exc:
            _engine = None
            raise MATLABEngineUnavailable from exc
        except Exception as exc:
            _close_engine()
            raise MATLABEngineUnavailable from exc
    return _engine


def configured_model_path():
    _, model_path, _ = configured_paths()
    return model_path


def screen_fundus(model_path, image_path, gradcam_path):
    """Call MATLAB and reconnect once if an existing Engine has stopped."""
    engine = get_engine()
    try:
        return engine.screen_fundus(
            str(model_path),
            str(image_path),
            str(gradcam_path),
            nargout=6,
        )
    except Exception:
        if _engine_is_alive(engine):
            raise
        with _engine_lock:
            _close_engine()
        engine = get_engine()
        return engine.screen_fundus(
            str(model_path),
            str(image_path),
            str(gradcam_path),
            nargout=6,
        )
