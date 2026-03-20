/**
 * kiro2DB — Dexie.js IndexedDB schema for offline support
 * FAZ-8: PWA + Offline Destek
 *
 * Tables:
 *   pending_answers   — answers queued for sync when offline
 *   cached_questions  — questions pre-loaded for offline practice
 *   offline_sessions  — exam/quiz sessions started offline
 *   fsrs_queue        — FSRS review cards queued for sync
 */
import Dexie, { Table } from 'dexie';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface PendingAnswer {
  id?: number;
  session_id: string;
  question_id: string;
  selected_answer: string;
  is_correct: boolean;
  time_spent_ms: number;
  answered_at: string;       // ISO datetime
  synced: boolean;
  retry_count: number;
}

export interface CachedQuestion {
  id: string;                // question_bank UUID
  subject_area: string;
  exam_type: string;
  difficulty_level: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  option_e?: string;
  correct_answer: string;
  question_image_url?: string;
  cached_at: number;         // timestamp
  expires_at: number;        // timestamp — auto-cleanup
}

export interface OfflineSession {
  id: string;                // UUID
  exam_type: string;
  subject_area: string;
  started_at: string;        // ISO datetime
  completed_at?: string;
  question_ids: string[];    // ordered list
  synced: boolean;
}

export interface FsrsQueueItem {
  id?: number;
  question_id: string;
  rating: 1 | 2 | 3 | 4;   // Again/Hard/Good/Easy
  reviewed_at: string;
  synced: boolean;
}

export interface UserPreferences {
  key: string;
  value: unknown;
  updated_at: number;
}

// ---------------------------------------------------------------------------
// DB class
// ---------------------------------------------------------------------------

class Kiro2Database extends Dexie {
  pendingAnswers!: Table<PendingAnswer>;
  cachedQuestions!: Table<CachedQuestion>;
  offlineSessions!: Table<OfflineSession>;
  fsrsQueue!: Table<FsrsQueueItem>;
  preferences!: Table<UserPreferences>;

  constructor() {
    super('kiro2_offline');

    this.version(1).stores({
      pendingAnswers:   '++id, session_id, synced, answered_at',
      cachedQuestions:  'id, subject_area, exam_type, difficulty_level, expires_at',
      offlineSessions:  'id, synced, started_at',
      fsrsQueue:        '++id, question_id, synced, reviewed_at',
      preferences:      'key',
    });
  }
}

export const db = new Kiro2Database();

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Queue an answer for sync when back online */
export async function queueAnswer(answer: Omit<PendingAnswer, 'id' | 'synced' | 'retry_count'>) {
  return db.pendingAnswers.add({ ...answer, synced: false, retry_count: 0 });
}

/** Get all unsynced answers, oldest first */
export async function getUnsyncedAnswers(): Promise<PendingAnswer[]> {
  return db.pendingAnswers
    .where('synced')
    .equals(0)
    .sortBy('answered_at');
}

/** Mark answers as synced */
export async function markAnswersSynced(ids: number[]) {
  return db.pendingAnswers.bulkUpdate(ids.map((id) => ({ key: id, changes: { synced: true } })));
}

/** Cache questions for offline practice */
export async function cacheQuestions(questions: Omit<CachedQuestion, 'cached_at' | 'expires_at'>[]) {
  const now = Date.now();
  const ttl = 7 * 24 * 60 * 60 * 1000; // 7 days
  return db.cachedQuestions.bulkPut(
    questions.map((q) => ({ ...q, cached_at: now, expires_at: now + ttl }))
  );
}

/** Get cached questions by subject/exam type */
export async function getCachedQuestions(
  subject_area?: string,
  exam_type?: string,
  limit = 20
): Promise<CachedQuestion[]> {
  const now = Date.now();
  let collection = db.cachedQuestions.where('expires_at').above(now);

  if (subject_area) {
    collection = db.cachedQuestions
      .where('[subject_area+expires_at]')
      .between([subject_area, now], [subject_area, Infinity]);
  }

  const results = await collection.limit(limit * 2).toArray();
  return results
    .filter((q) => !exam_type || q.exam_type === exam_type)
    .slice(0, limit);
}

/** Clean expired cached questions */
export async function cleanExpiredCache() {
  const now = Date.now();
  return db.cachedQuestions.where('expires_at').below(now).delete();
}

/** Save or update a user preference */
export async function setPreference(key: string, value: unknown) {
  return db.preferences.put({ key, value, updated_at: Date.now() });
}

/** Get a user preference */
export async function getPreference<T = unknown>(key: string, defaultValue?: T): Promise<T | undefined> {
  const record = await db.preferences.get(key);
  return (record?.value as T) ?? defaultValue;
}

/** Add FSRS review to queue */
export async function queueFsrsReview(question_id: string, rating: 1 | 2 | 3 | 4) {
  return db.fsrsQueue.add({
    question_id,
    rating,
    reviewed_at: new Date().toISOString(),
    synced: false,
  });
}

/** Sync queued FSRS reviews to backend */
export async function syncFsrsQueue(apiBase = '/api'): Promise<number> {
  const pending = await db.fsrsQueue.where('synced').equals(0).toArray();
  if (!pending.length) return 0;

  let synced = 0;
  for (const item of pending) {
    try {
      const res = await fetch(`${apiBase}/fsrs/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ question_id: item.question_id, rating: item.rating }),
      });
      if (res.ok && item.id != null) {
        await db.fsrsQueue.update(item.id, { synced: true });
        synced++;
      }
    } catch {
      // Will retry next sync
    }
  }
  return synced;
}

/** Sync all pending answers to backend */
export async function syncPendingAnswers(apiBase = '/api'): Promise<number> {
  const pending = await getUnsyncedAnswers();
  if (!pending.length) return 0;

  let synced = 0;
  for (const answer of pending) {
    try {
      const res = await fetch(`${apiBase}/sinav/submit-offline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(answer),
      });
      if (res.ok && answer.id != null) {
        await db.pendingAnswers.update(answer.id, { synced: true });
        synced++;
      } else if (answer.id != null) {
        await db.pendingAnswers.update(answer.id, {
          retry_count: (answer.retry_count ?? 0) + 1,
        });
      }
    } catch {
      // Network error - will retry on next sync
    }
  }
  return synced;
}

// ---------------------------------------------------------------------------
// Online sync hook — call when coming back online
// ---------------------------------------------------------------------------

export function registerOnlineSync() {
  if (typeof window === 'undefined') return;

  window.addEventListener('online', async () => {
    const [answers, fsrs] = await Promise.all([
      syncPendingAnswers(),
      syncFsrsQueue(),
    ]);
    if (answers + fsrs > 0) {
      console.info(`[KIRO2 Offline] Synced: ${answers} answers, ${fsrs} FSRS reviews`);
    }
    await cleanExpiredCache();
  });
}
