def _lazy_import_numpy():
    """Numpy'i lazy import et"""
    try:
        import numpy as np

        return np
    except ImportError:
        # Numpy yoksa basit alternatif
        class SimpleNumpy:
            @staticmethod
            def mean(arr):
                return sum(arr) / len(arr) if arr else 0

            @staticmethod
            def max(arr):
                return max(arr) if arr else 0

            @staticmethod
            def min(arr):
                return min(arr) if arr else 0

        return SimpleNumpy()


# Global lazy numpy
_np = None


def get_numpy():
    global _np
    if _np is None:
        _np = _lazy_import_numpy()
    return _np
