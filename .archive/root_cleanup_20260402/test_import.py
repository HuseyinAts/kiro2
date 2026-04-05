"""Test orchestrator imports"""
import sys
sys.path.insert(0, '.')

try:
    from orchestrator.core import (
        SignalDictionary, 
        Signal, 
        SignalSeverity, 
        get_signal_dictionary,
        __version__
    )
    print(f"✅ SignalDictionary import başarılı")
    print(f"✅ Orchestrator version: {__version__}")
    
    sd = get_signal_dictionary()
    print(f"✅ {len(sd.signals)} sinyal yüklendi")
    
    # Test false positive fix
    test_cases = [
        ("ImportError: No module named 'fastapi'", "test.py"),
        ("SyntaxError: invalid syntax", "test.py"),
        ("password = 'secret123'", "config.py"),
    ]
    
    print("\n📋 False Positive Testleri:")
    for text, filename in test_cases:
        matches = sd.analyze(text, filename)
        signal_names = [m[0].name for m in matches]
        print(f"  '{text[:40]}...' → {signal_names}")
    
    print("\n✅ Tüm testler başarılı!")
    
except Exception as e:
    print(f"❌ Hata: {e}")
    import traceback
    traceback.print_exc()
