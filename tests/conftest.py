import sys
from unittest.mock import MagicMock

# Mock missing modules
sys.modules['zemberek'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['berturk'] = MagicMock()