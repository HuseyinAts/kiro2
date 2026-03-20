/**
 * RealmPage — YKS Alemler Haritası ana sayfa
 * FAZ-5: Alem Haritasi + NPC Sistemi
 *
 * Routes: /realms
 */
import React, { useState, useEffect, useCallback } from 'react';
import { RealmMap, RealmData } from '../features/realm/RealmMap';
import { NPCDialog } from '../features/realm/NPCDialog';
import { XPBar } from '../components/Gamification/XPBar';
import { StreakBadge } from '../components/Gamification/StreakBadge';

const API_BASE = '/api';

interface UserGamification {
  total_xp: number;
  current_level: number;
  streak: number;
  streak_active_today: boolean;
}

const LEVEL_XP = (level: number) => level * 500;

export const RealmPage: React.FC = () => {
  const [realms, setRealms] = useState<RealmData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRealm, setSelectedRealm] = useState<RealmData | null>(null);
  const [showNPC, setShowNPC] = useState(false);
  const [gamification, setGamification] = useState<UserGamification | null>(null);

  // Load realms
  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/realms/`, { credentials: 'include' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setRealms(data.realms ?? []);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // Load gamification profile
  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/gamification/profile`, { credentials: 'include' });
        if (!res.ok) return;
        const data = await res.json();
        setGamification({
          total_xp: data.total_xp ?? 0,
          current_level: data.current_level ?? 1,
          streak: data.streak ?? 0,
          streak_active_today: data.streak_active_today ?? false,
        });
      } catch {
        // optional — gamification not critical
      }
    };
    load();
  }, []);

  const handleRealmSelect = useCallback((realm: RealmData) => {
    setSelectedRealm(realm);
    setShowNPC(false); // reset, user can open dialog separately
  }, []);

  const handleQuestAction = useCallback(
    async (action: 'start' | 'complete') => {
      if (!selectedRealm) return;
      try {
        await fetch(`${API_BASE}/realms/${selectedRealm.slug}/quest/${action}`, {
          method: 'POST',
          credentials: 'include',
        });
        // Refresh progress for this realm
        const res = await fetch(`${API_BASE}/realms/${selectedRealm.slug}/progress`, {
          credentials: 'include',
        });
        if (res.ok) {
          const prog = await res.json();
          setRealms((prev) =>
            prev.map((r) =>
              r.slug === selectedRealm.slug
                ? {
                    ...r,
                    progress: {
                      bkt_score: prog.bkt_score,
                      quest_stop: prog.quest_stop,
                      xp_earned: prog.xp_earned,
                      completed: prog.completed,
                    },
                  }
                : r
            )
          );
          setSelectedRealm((prev) =>
            prev?.slug === selectedRealm.slug
              ? {
                  ...prev,
                  progress: {
                    bkt_score: prog.bkt_score,
                    quest_stop: prog.quest_stop,
                    xp_earned: prog.xp_earned,
                    completed: prog.completed,
                  },
                }
              : prev
          );
        }
      } catch {
        /* ignore */
      }
    },
    [selectedRealm]
  );

  const level = gamification?.current_level ?? 1;
  const totalXP = gamification?.total_xp ?? 0;
  const maxXP = LEVEL_XP(level);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Top bar */}
      <header className="sticky top-0 z-40 bg-gray-950/80 backdrop-blur-md border-b border-white/5 px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center gap-4">
          <div className="flex-1">
            <h1 className="text-lg font-bold font-display text-white/90">YKS Evren Haritası</h1>
            <p className="text-xs text-white/40">Konu alemlerini keşfet, ustalaş</p>
          </div>

          <div className="flex items-center gap-3">
            {gamification && (
              <>
                <StreakBadge
                  streak={gamification.streak}
                  isActiveToday={gamification.streak_active_today}
                  size="sm"
                />
                <div className="w-40">
                  <XPBar
                    currentXP={totalXP % maxXP}
                    maxXP={maxXP}
                    level={level}
                    showLabel={false}
                  />
                </div>
                <span className="text-xs text-purple-400 font-bold">
                  Sv.{level}
                </span>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <div className="lg:col-span-2">
          {loading ? (
            <div className="aspect-[4/3] rounded-2xl bg-gray-800/50 animate-pulse flex items-center justify-center">
              <p className="text-white/40 text-sm">Harita yükleniyor...</p>
            </div>
          ) : error ? (
            <div className="aspect-[4/3] rounded-2xl bg-red-900/20 flex items-center justify-center p-8">
              <div className="text-center">
                <p className="text-red-400 text-sm font-semibold">Harita yüklenemedi</p>
                <p className="text-white/40 text-xs mt-1">{error}</p>
              </div>
            </div>
          ) : (
            <RealmMap
              realms={realms}
              onRealmSelect={handleRealmSelect}
              selectedSlug={selectedRealm?.slug}
              className="rounded-2xl overflow-hidden border border-white/5"
            />
          )}

          {/* Legend */}
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-white/50">
            {[
              { color: '#10B981', label: 'Ustalaşıldı (>%80)' },
              { color: '#F59E0B', label: 'İlerleme (%60-80)' },
              { color: '#3B82F6', label: 'Öğrenme (%40-60)' },
              { color: '#E5E7EB', label: 'Başlangıç (<40)' },
            ].map(({ color, label }) => (
              <span key={label} className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full" style={{ background: color }} />
                {label}
              </span>
            ))}
          </div>
        </div>

        {/* Side panel — selected realm detail */}
        <div className="lg:col-span-1">
          {selectedRealm ? (
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5 space-y-4">
              {/* Realm header */}
              <div className="flex items-start gap-3">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0"
                  style={{ background: selectedRealm.color_primary + '33' }}
                >
                  {selectedRealm.name.charAt(0)}
                </div>
                <div>
                  <h2 className="text-white font-bold font-display">{selectedRealm.name}</h2>
                  <p className="text-white/50 text-xs">{selectedRealm.era}</p>
                </div>
              </div>

              {/* Progress */}
              {selectedRealm.progress ? (
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-white/50">
                    <span>BKT Ustalık</span>
                    <span className="text-white font-bold">
                      %{Math.round(selectedRealm.progress.bkt_score * 100)}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${selectedRealm.progress.bkt_score * 100}%`,
                        background: selectedRealm.color_primary,
                      }}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2 mt-3">
                    <div className="bg-white/5 rounded-xl p-2.5 text-center">
                      <p className="text-lg font-bold text-white">
                        {selectedRealm.progress.xp_earned}
                      </p>
                      <p className="text-xs text-white/40">XP Kazanıldı</p>
                    </div>
                    <div className="bg-white/5 rounded-xl p-2.5 text-center">
                      <p className="text-lg font-bold text-white">
                        {selectedRealm.progress.quest_stop}
                      </p>
                      <p className="text-xs text-white/40">Görev Adımı</p>
                    </div>
                  </div>

                  {selectedRealm.progress.completed && (
                    <div className="flex items-center gap-2 bg-green-900/30 rounded-xl p-2.5">
                      <span className="text-green-400">✓</span>
                      <span className="text-xs text-green-300">Bu alem tamamlandı!</span>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-white/40">İlerleme bilgisi yükleniyor...</p>
              )}

              {/* Actions */}
              <div className="space-y-2 pt-2">
                <button
                  onClick={() => setShowNPC(true)}
                  className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl
                             bg-purple-600 hover:bg-purple-500 text-white text-sm font-semibold
                             transition-colors"
                >
                  <span>💬</span>
                  <span>{selectedRealm.npc_name} ile Konuş</span>
                </button>

                {selectedRealm.progress?.quest_stop === 0 && (
                  <button
                    onClick={() => handleQuestAction('start')}
                    className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl
                               bg-white/10 hover:bg-white/20 text-white text-sm font-semibold
                               transition-colors"
                  >
                    <span>⚔️</span>
                    <span>Görevi Başlat</span>
                  </button>
                )}

                {(selectedRealm.progress?.quest_stop ?? 0) > 0 &&
                  !selectedRealm.progress?.completed && (
                    <button
                      onClick={() => handleQuestAction('complete')}
                      className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl
                                 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold
                                 transition-colors"
                    >
                      <span>🏆</span>
                      <span>Görevi Tamamla (+200 XP)</span>
                    </button>
                  )}
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-white/5 bg-white/3 p-6 flex flex-col items-center justify-center gap-3 text-center min-h-48">
              <span className="text-4xl opacity-40">🌍</span>
              <p className="text-sm text-white/40">
                Bir alem seçin ve detayları görün.
              </p>
              <p className="text-xs text-white/25">
                Haritadan bir konu alemine tıklayın.
              </p>
            </div>
          )}

          {/* Stats summary */}
          {realms.length > 0 && (
            <div className="mt-4 rounded-2xl border border-white/5 bg-white/3 p-4 space-y-2">
              <h3 className="text-xs font-bold text-white/50 uppercase tracking-wider">Özet</h3>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <p className="text-lg font-bold text-white">
                    {realms.filter((r) => r.progress?.completed).length}
                  </p>
                  <p className="text-xs text-white/40">Tamamlanan</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-white">
                    {realms.filter((r) => (r.progress?.quest_stop ?? 0) > 0 && !r.progress?.completed).length}
                  </p>
                  <p className="text-xs text-white/40">Devam Eden</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-white">
                    {realms.filter((r) => !r.progress?.quest_stop).length}
                  </p>
                  <p className="text-xs text-white/40">Keşfedilmemiş</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* NPC Dialog */}
      {showNPC && selectedRealm && (
        <NPCDialog
          realmSlug={selectedRealm.slug}
          realmName={selectedRealm.name}
          npcName={selectedRealm.npc_name}
          npcTitle={(selectedRealm as RealmData & { npc_title?: string }).npc_title}
          bktScore={selectedRealm.progress?.bkt_score ?? 0}
          questStep={selectedRealm.progress?.quest_stop ?? 0}
          onClose={() => setShowNPC(false)}
          onQuestAction={handleQuestAction}
        />
      )}
    </div>
  );
};

export default RealmPage;
