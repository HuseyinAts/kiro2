import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure project root is in sys.path (needed for xdist workers)
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

# Mock missing modules
sys.modules['zemberek'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['berturk'] = MagicMock()