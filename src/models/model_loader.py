from pathlib import Path
from threading import Lock

import joblib

from src.utils.exceptions import ModelLoadError


class ModelLoader:
    def __init__(self):
        self._cache = {}
        self._lock = Lock()

    def load(self, path: Path):
        path = Path(path)
        if not path.is_file():
            raise ModelLoadError(f"Required model artifact does not exist: {path}")
        key = str(path.resolve())
        with self._lock:
            if key not in self._cache:
                try:
                    self._cache[key] = joblib.load(path)
                except Exception as exc:
                    raise ModelLoadError(f"Could not load model artifact: {path.name}") from exc
            return self._cache[key]

    def clear(self):
        with self._lock:
            self._cache.clear()
