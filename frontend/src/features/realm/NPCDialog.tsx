/**
 * NPCDialog — Bilge Alp NPC streaming dialog
 * FAZ-5: Alem Haritasi + NPC Sistemi
 *
 * Streams NPC responses from /api/v1/bilge-alp/chat (SSE)
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';

interface NPCDialogProps {
  realmSlug: string;
  realmName: string;
  npcName: string;
  npcTitle?: string;
  bktScore: number;
  questStep?: number;
  onClose: () => void;
  onQuestAction?: (action: 'start' | 'complete') => void;
}

interface Message {
  role: 'user' | 'npc';
  content: string;
  streaming?: boolean;
}

const NPC_AVATARS: Record<string, string> = {
  fizik:     '🔭',
  kimya:     '⚗️',
  biyoloji:  '🌿',
  matematik: '📐',
  geometri:  '📐',
  cografya:  '🗺️',
  tarih:     '⚔️',
  turkce:    '📜',
  edebiyat:  '📚',
  felsefe:   '🦉',
  din:       '☪️',
  oba:       '🛡️',
};

const GREETING_MESSAGES: Record<string, string> = {
  fizik:     'Merhaba, genç kaşif! Fiziğin sırlarını birlikte keşfedelim.',
  kimya:     'Hoş geldin! Maddenin gizli dönüşümlerini öğrenmeye hazır mısın?',
  biyoloji:  'Canın sağ olsun! Hayatın gizemlerini birlikte çözeceğiz.',
  matematik: 'Selam! Sayıların evrenine hoş geldin. Birlikte keşfedelim.',
  geometri:  'Merhaba! Şekillerin ve uzayın sırrına erişmek için doğru yerdesin.',
  cografya:  'Günaydın gezgin! Dünyanın haritasını birlikte okuyacağız.',
  tarih:     'Ah, yeni bir kahraman! Geçmişin sırlarını seninle paylaşacağım.',
  turkce:    'Hoş geldin! Dilin büyülü dünyasına birlikte dalacağız.',
  edebiyat:  'Merhaba! Kelimelerin şiirsel dünyasına hoş geldin.',
  felsefe:   'İyi düşünceler! Sorgulamanın kapısını birlikte aralayalım.',
  din:       'Selamün aleyküm! Ahlak ve değerlerin yolunu birlikte yürüyelim.',
  oba:       'Savaşçı! Obamıza hoş geldin. Birlikte büyüyeceğiz.',
};

export const NPCDialog: React.FC<NPCDialogProps> = ({
  realmSlug,
  realmName,
  npcName,
  npcTitle,
  bktScore,
  questStep = 0,
  onClose,
  onQuestAction,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'npc',
      content: GREETING_MESSAGES[realmSlug] ?? `${realmName} alemine hoş geldin!`,
    },
  ]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const avatar = NPC_AVATARS[realmSlug] ?? '🧙';
  const masteryPct = Math.round(bktScore * 100);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isStreaming) return;

      const userMsg: Message = { role: 'user', content: text };
      setMessages((prev) => [...prev, userMsg]);
      setInput('');
      setIsStreaming(true);

      // Append placeholder NPC message
      setMessages((prev) => [
        ...prev,
        { role: 'npc', content: '', streaming: true },
      ]);

      const ctrl = new AbortController();
      abortRef.current = ctrl;

      try {
        const res = await fetch('/api/v1/bilge-alp/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            realm_slug: realmSlug,
            bkt_score: bktScore,
            quest_step: questStep,
            message: text,
            history: messages.slice(-6).map((m) => ({
              role: m.role === 'user' ? 'user' : 'assistant',
              content: m.content,
            })),
          }),
          signal: ctrl.signal,
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        if (!res.body) throw new Error('No response body');

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let npcText = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          // Parse SSE: "data: <token>\n\n"
          for (const line of chunk.split('\n')) {
            if (line.startsWith('data: ')) {
              const token = line.slice(6);
              if (token === '[DONE]') break;
              npcText += token;
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.streaming) {
                  updated[updated.length - 1] = { ...last, content: npcText };
                }
                return updated;
              });
            }
          }
        }

        // Finalize (remove streaming flag)
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.streaming) {
            updated[updated.length - 1] = { ...last, streaming: false };
          }
          return updated;
        });
      } catch (err) {
        if ((err as Error).name === 'AbortError') return;
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.streaming) {
            updated[updated.length - 1] = {
              role: 'npc',
              content: 'Üzgünüm, şu an sana yardım edemiyorum. Birazdan tekrar dene!',
              streaming: false,
            };
          }
          return updated;
        });
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [isStreaming, realmSlug, bktScore, questStep, messages]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div
      className="fixed inset-0 z-[9998] flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full sm:max-w-lg sm:mx-4 bg-gray-900 rounded-t-3xl sm:rounded-3xl
                   border border-white/10 shadow-modern-xl flex flex-col overflow-hidden"
        style={{ maxHeight: '85vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-white/10 bg-white/5">
          <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600
                          flex items-center justify-center text-2xl shadow-lg">
            {avatar}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-white font-bold font-display text-sm leading-tight">{npcName}</h3>
            {npcTitle && (
              <p className="text-purple-300 text-xs truncate">{npcTitle} · {realmName}</p>
            )}
          </div>
          {/* Mastery chip */}
          <div className="flex-shrink-0 bg-white/10 rounded-full px-2.5 py-1 text-xs text-green-400 font-bold">
            %{masteryPct}
          </div>
          <button
            onClick={onClose}
            className="flex-shrink-0 text-white/40 hover:text-white/80 transition-colors text-xl leading-none ml-1"
            aria-label="Kapat"
          >
            ×
          </button>
        </div>

        {/* Quest action bar */}
        {onQuestAction && questStep === 0 && (
          <div className="flex items-center gap-2 px-4 py-2.5 bg-purple-900/40 border-b border-white/5">
            <span className="text-xs text-purple-300 flex-1">Göreve hazır mısın?</span>
            <button
              onClick={() => onQuestAction('start')}
              className="text-xs px-3 py-1 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold transition-colors"
            >
              Görevi Başlat
            </button>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-0">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {msg.role === 'npc' && (
                <div className="flex-shrink-0 w-7 h-7 rounded-full bg-purple-700/60
                                flex items-center justify-center text-sm">
                  {avatar}
                </div>
              )}
              <div
                className={[
                  'max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-purple-600 text-white rounded-tr-sm'
                    : 'bg-white/10 text-gray-100 rounded-tl-sm',
                ].join(' ')}
              >
                {msg.content || (msg.streaming && (
                  <span className="inline-flex gap-1">
                    <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </span>
                ))}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick prompts */}
        <div className="px-4 py-2 flex gap-2 overflow-x-auto scrollbar-hide">
          {['Konuyu anlat', 'Soru sor', 'İpucu ver', 'Nasıl çalışırım?'].map((q) => (
            <button
              key={q}
              onClick={() => sendMessage(q)}
              disabled={isStreaming}
              className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20
                         text-gray-300 hover:text-white transition-colors disabled:opacity-40"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="flex items-center gap-2 px-4 py-3 border-t border-white/10">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`${npcName}'e bir şey sor...`}
            disabled={isStreaming}
            className="flex-1 bg-white/10 text-white placeholder-white/30 rounded-xl px-4 py-2.5
                       text-sm border border-white/10 focus:border-purple-500/60 focus:outline-none
                       focus:ring-1 focus:ring-purple-500/40 transition-all disabled:opacity-50"
          />
          {isStreaming ? (
            <button
              type="button"
              onClick={() => abortRef.current?.abort()}
              className="w-10 h-10 rounded-xl bg-red-600/80 hover:bg-red-500 text-white
                         flex items-center justify-center text-lg transition-colors"
              aria-label="Durdur"
            >
              ⏹
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="w-10 h-10 rounded-xl bg-purple-600 hover:bg-purple-500 text-white
                         flex items-center justify-center text-lg transition-colors
                         disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="Gönder"
            >
              ➤
            </button>
          )}
        </form>
      </div>
    </div>
  );
};

export default NPCDialog;
