import { VolumeX, Play, Pause, Settings } from 'lucide-react';
import * as React from 'react';
import {  useState, useEffect, useRef, useCallback  } from 'react';

/**
 * Text-to-Speech Sistemi
 *
 * Özellikler:
 * - Web Speech API entegrasyonu
 * - Türkçe ses desteği
 * - Fallback TTS servisi
 * - Ses hızı ayarlama (%50-%200)
 * - Ses tonu ayarlama
 * - Karaoke mode (kelime vurgulama)
 *
 * Requirements: REQ-50.43 - REQ-50.56
 */

interface TTSSettings {
  enabled: boolean;
  voice: string;
  rate: number; // 0.5 - 2.0
  pitch: number; // 0.5 - 2.0
  volume: number; // 0.0 - 1.0
  highlightColor: string;
  karaokeModeEnabled: boolean;
}

interface TextToSpeechProps {
  text: string;
  autoPlay?: boolean;
  showControls?: boolean;
  className?: string;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: Error) => void;
}

const DEFAULT_SETTINGS: TTSSettings = {
  enabled: true,
  voice: 'tr-TR',
  rate: 1.0,
  pitch: 1.0,
  volume: 1.0,
  highlightColor: '#FFD700',
  karaokeModeEnabled: true,
};

const SPEED_PRESETS = [
  { label: 'Çok Yavaş', value: 0.5 },
  { label: 'Yavaş', value: 0.75 },
  { label: 'Normal', value: 1.0 },
  { label: 'Hızlı', value: 1.25 },
  { label: 'Çok Hızlı', value: 1.5 },
  { label: 'Maksimum', value: 2.0 },
];

export const TextToSpeech: React.FC<TextToSpeechProps> = ({
  text,
  autoPlay = false,
  showControls = true,
  className = '',
  onStart,
  onEnd,
  onError,
}) => {
  const [settings, setSettings] = useState<TTSSettings>(() => {
    const saved = localStorage.getItem('tts-settings');
    return saved ? { ...DEFAULT_SETTINGS, ...JSON.parse(saved) } : DEFAULT_SETTINGS;
  });

  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentWordIndex, setCurrentWordIndex] = useState(-1);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [isSpeechSupported, setIsSpeechSupported] = useState(true);

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const wordsRef = useRef<string[]>([]);

  // REQ-50.43: Web Speech API entegrasyonu
  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setIsSpeechSupported(false);
      console.warn('Web Speech API desteklenmiyor. Fallback servisi devreye alınacak.');
      return;
    }

    // REQ-50.44: Türkçe ses seçimi
    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      const turkishVoices = voices.filter(voice =>
        voice.lang.startsWith('tr') || voice.lang.startsWith('TR'),
      );
      setAvailableVoices(turkishVoices.length > 0 ? turkishVoices : voices);
    };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  // Ayarları localStorage'a kaydet
  useEffect(() => {
    localStorage.setItem('tts-settings', JSON.stringify(settings));
  }, [settings]);

  // Metni kelimelere ayır
  useEffect(() => {
    wordsRef.current = text.split(/\s+/).filter(word => word.length > 0);
  }, [text]);

  // REQ-50.53, REQ-50.54: Karaoke mode - kelime kelime vurgulama
  const handleBoundary = useCallback((event: SpeechSynthesisEvent) => {
    if (!settings.karaokeModeEnabled) {return;}

    const charIndex = event.charIndex;
    const currentText = text.substring(0, charIndex);
    const wordIndex = currentText.split(/\s+/).length - 1;
    setCurrentWordIndex(wordIndex);
  }, [text, settings.karaokeModeEnabled]);

  // TTS başlat
  const speak = useCallback(() => {
    if (!isSpeechSupported) {
      // REQ-50.45: Fallback TTS servisi
      handleFallbackTTS();
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    // REQ-50.44: Türkçe ses seçimi
    const selectedVoice = availableVoices.find(v => v.name.includes(settings.voice))
      || availableVoices[0];
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }

    // REQ-50.47, REQ-50.49: Ses hızı ayarlama
    utterance.rate = settings.rate;

    // REQ-50.50: Ses tonu ayarlama
    utterance.pitch = settings.pitch;

    utterance.volume = settings.volume;

    // REQ-50.46: Ses kalitesi ve akıcılığı optimize et
    utterance.lang = 'tr-TR';

    utterance.onstart = () => {
      setIsPlaying(true);
      setIsPaused(false);
      setCurrentWordIndex(0);
      onStart?.();
    };

    utterance.onend = () => {
      setIsPlaying(false);
      setIsPaused(false);
      setCurrentWordIndex(-1);
      onEnd?.();
    };

    utterance.onerror = (event) => {
      console.error('TTS Error:', event);
      setIsPlaying(false);
      setIsPaused(false);
      onError?.(new Error(event.error));

      // REQ-50.45: Hata durumunda fallback
      handleFallbackTTS();
    };

    // REQ-50.54: Senkronize vurgulama
    utterance.onboundary = handleBoundary;

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, [text, settings, availableVoices, isSpeechSupported, onStart, onEnd, onError, handleBoundary]);

  // REQ-50.45: Fallback TTS servisi
  const handleFallbackTTS = async () => {
    try {
      // Backend TTS API'sine istek gönder
      const response = await fetch('/api/v1/tts/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          language: 'tr-TR',
          rate: settings.rate,
          pitch: settings.pitch,
        }),
      });

      if (!response.ok) {throw new Error('Fallback TTS başarısız');}

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      audio.onplay = () => {
        setIsPlaying(true);
        onStart?.();
      };

      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
        onEnd?.();
      };

      audio.play();
    } catch (error) {
      console.error('Fallback TTS hatası:', error);
      onError?.(error as Error);
    }
  };

  const pause = () => {
    window.speechSynthesis.pause();
    setIsPaused(true);
  };

  const resume = () => {
    window.speechSynthesis.resume();
    setIsPaused(false);
  };

  const stop = () => {
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setIsPaused(false);
    setCurrentWordIndex(-1);
  };

  // REQ-50.47: Ses hızı ayarlama
  const updateRate = (rate: number) => {
    setSettings(prev => ({ ...prev, rate }));
    if (isPlaying) {
      stop();
      setTimeout(speak, 100);
    }
  };

  // REQ-50.50: Ses tonu ayarlama
  const updatePitch = (pitch: number) => {
    setSettings(prev => ({ ...prev, pitch }));
    if (isPlaying) {
      stop();
      setTimeout(speak, 100);
    }
  };

  // REQ-50.51: Ses seçimi
  const updateVoice = (voiceName: string) => {
    setSettings(prev => ({ ...prev, voice: voiceName }));
    if (isPlaying) {
      stop();
      setTimeout(speak, 100);
    }
  };

  // REQ-50.55: Vurgulama rengi ayarlama
  const updateHighlightColor = (color: string) => {
    setSettings(prev => ({ ...prev, highlightColor: color }));
  };

  // Auto-play
  useEffect(() => {
    if (autoPlay && text && settings.enabled) {
      speak();
    }
  }, [autoPlay, text, settings.enabled]);

  // REQ-50.53, REQ-50.56: Karaoke mode - kelime vurgulama
  const renderTextWithHighlight = () => {
    if (!settings.karaokeModeEnabled) {
      return <p className="text-lg leading-relaxed">{text}</p>;
    }

    return (
      <p className="text-lg leading-relaxed">
        {wordsRef.current.map((word, index) => (
          <span
            key={index}
            className="transition-all duration-150"
            style={{
              backgroundColor: index === currentWordIndex ? settings.highlightColor : 'transparent',
              padding: '2px 4px',
              borderRadius: '3px',
              fontWeight: index === currentWordIndex ? 'bold' : 'normal',
            }}
          >
            {word}{' '}
          </span>
        ))}
      </p>
    );
  };

  if (!settings.enabled) {return null;}

  return (
    <div className={`tts-container ${className}`}>
      {/* Metin Görüntüleme */}
      <div className="mb-4 p-4 bg-gray-50 rounded-lg">
        {renderTextWithHighlight()}
      </div>

      {/* Kontroller */}
      {showControls && (
        <div className="flex flex-col gap-4">
          {/* Oynatma Kontrolleri */}
          <div className="flex items-center gap-2">
            {!isPlaying ? (
              <button
                onClick={speak}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                aria-label="Metni seslendir"
              >
                <Play size={20} />
                <span>Seslendir</span>
              </button>
            ) : (
              <>
                {!isPaused ? (
                  <button
                    onClick={pause}
                    className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
                    aria-label="Duraklat"
                  >
                    <Pause size={20} />
                    <span>Duraklat</span>
                  </button>
                ) : (
                  <button
                    onClick={resume}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    aria-label="Devam et"
                  >
                    <Play size={20} />
                    <span>Devam</span>
                  </button>
                )}
                <button
                  onClick={stop}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  aria-label="Durdur"
                >
                  <VolumeX size={20} />
                  <span>Durdur</span>
                </button>
              </>
            )}

            <button
              onClick={() => setShowSettings(!showSettings)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors ml-auto"
              aria-label="Ayarlar"
            >
              <Settings size={20} />
              <span>Ayarlar</span>
            </button>
          </div>

          {/* Ayarlar Paneli */}
          {showSettings && (
            <div className="p-4 bg-white border border-gray-200 rounded-lg space-y-4">
              {/* REQ-50.47, REQ-50.48: Ses Hızı */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Ses Hızı: {(settings.rate * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={settings.rate}
                  onChange={(e) => updateRate(parseFloat(e.target.value))}
                  className="w-full"
                  aria-label="Ses hızı ayarlama"
                />
                <div className="flex gap-2 mt-2 flex-wrap">
                  {SPEED_PRESETS.map(preset => (
                    <button
                      key={preset.value}
                      onClick={() => updateRate(preset.value)}
                      className={`px-3 py-1 text-sm rounded ${
                        settings.rate === preset.value
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 hover:bg-gray-300'
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* REQ-50.50: Ses Tonu */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Ses Tonu: {settings.pitch.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={settings.pitch}
                  onChange={(e) => updatePitch(parseFloat(e.target.value))}
                  className="w-full"
                  aria-label="Ses tonu ayarlama"
                />
              </div>

              {/* REQ-50.51, REQ-50.52: Ses Seçimi */}
              {availableVoices.length > 0 && (
                <div>
                  <label htmlFor="tts-voice-select" className="block text-sm font-medium mb-2">
                    Ses Seçimi
                  </label>
                  <select
                    id="tts-voice-select"
                    value={settings.voice}
                    onChange={(e) => updateVoice(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded"
                    aria-label="Ses seçimi"
                  >
                    {availableVoices.map(voice => (
                      <option key={voice.name} value={voice.name}>
                        {voice.name} ({voice.lang})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* REQ-50.53: Karaoke Mode */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="karaoke-mode"
                  checked={settings.karaokeModeEnabled}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    karaokeModeEnabled: e.target.checked,
                  }))}
                  className="w-4 h-4"
                />
                <label htmlFor="karaoke-mode" className="text-sm font-medium">
                  Karaoke Modu (Kelime Vurgulama)
                </label>
              </div>

              {/* REQ-50.55: Vurgulama Rengi */}
              {settings.karaokeModeEnabled && (
                <div>
                  <div className="block text-sm font-medium mb-2" role="group" aria-label="Vurgulama Rengi">
                    Vurgulama Rengi
                  </div>
                  <div className="flex gap-2">
                    {['#FFD700', '#90EE90', '#87CEEB', '#FFB6C1', '#DDA0DD'].map(color => (
                      <button
                        key={color}
                        onClick={() => updateHighlightColor(color)}
                        className={`w-10 h-10 rounded border-2 ${
                          settings.highlightColor === color
                            ? 'border-black'
                            : 'border-gray-300'
                        }`}
                        style={{ backgroundColor: color }}
                        aria-label={`Renk seç: ${color}`}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Ses Seviyesi */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Ses Seviyesi: {(settings.volume * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.volume}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    volume: parseFloat(e.target.value),
                  }))}
                  className="w-full"
                  aria-label="Ses seviyesi ayarlama"
                />
              </div>
            </div>
          )}

          {/* Durum Mesajları */}
          {!isSpeechSupported && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
              ⚠️ Tarayıcınız Web Speech API&apos;yi desteklemiyor. Alternatif TTS servisi kullanılıyor.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TextToSpeech;
