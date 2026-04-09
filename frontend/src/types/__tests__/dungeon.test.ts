import { describe, it, expect } from 'vitest';
import {
  getRoomLevel,
  seededRandom,
  fogOpacity,
  type DungeonRoom,
  type DungeonProgressData,
} from '../dungeon';

describe('getRoomLevel', () => {
  it('returns 0 when no attempts', () => {
    const p: DungeonProgressData = { attempt_count: 0, best_score: 0, last_score: 0, completed: false };
    expect(getRoomLevel(p)).toBe(0);
  });

  it('returns 1 when attempted but low score', () => {
    const p: DungeonProgressData = { attempt_count: 2, best_score: 30, last_score: 30, completed: false };
    expect(getRoomLevel(p)).toBe(1);
  });

  it('returns 2 when best_score >= 50', () => {
    const p: DungeonProgressData = { attempt_count: 3, best_score: 60, last_score: 40, completed: false };
    expect(getRoomLevel(p)).toBe(2);
  });

  it('returns 3 when completed', () => {
    const p: DungeonProgressData = { attempt_count: 5, best_score: 85, last_score: 85, completed: true };
    expect(getRoomLevel(p)).toBe(3);
  });
});

describe('seededRandom', () => {
  it('returns deterministic value for same seed', () => {
    const a = seededRandom('topic-a-topic-b');
    const b = seededRandom('topic-a-topic-b');
    expect(a).toBe(b);
  });

  it('returns different values for different seeds', () => {
    const a = seededRandom('topic-a-topic-b');
    const c = seededRandom('topic-x-topic-y');
    expect(a).not.toBe(c);
  });

  it('returns value between 0 and 1', () => {
    const v = seededRandom('any-seed');
    expect(v).toBeGreaterThanOrEqual(0);
    expect(v).toBeLessThanOrEqual(1);
  });
});

describe('fogOpacity', () => {
  const makeRoom = (overrides: Partial<DungeonRoom> = {}): DungeonRoom => ({
    topic_id: 'test',
    code: 'TST.01',
    name_tr: 'Test',
    parent_subject: 'TEST',
    prereqs_met: true,
    dag_depth: 0,
    progress: { attempt_count: 0, best_score: 0, last_score: 0, completed: false },
    question_count: 10,
    ...overrides,
  });

  it('returns 0.9 when prereqs not met', () => {
    const room = makeRoom({ prereqs_met: false });
    expect(fogOpacity(room, 0)).toBe(0.9);
  });

  it('returns 0 when completed', () => {
    const room = makeRoom({
      progress: { attempt_count: 5, best_score: 90, last_score: 90, completed: true },
    });
    expect(fogOpacity(room, 0)).toBe(0);
  });

  it('returns lower fog for higher theta', () => {
    const room = makeRoom();
    const lowTheta = fogOpacity(room, -2);
    const highTheta = fogOpacity(room, 2);
    expect(highTheta).toBeLessThan(lowTheta);
  });

  it('returns higher fog for deeper dag_depth', () => {
    const shallow = makeRoom({ dag_depth: 0 });
    const deep = makeRoom({ dag_depth: 5 });
    const theta = 0;
    expect(fogOpacity(deep, theta)).toBeGreaterThan(fogOpacity(shallow, theta));
  });
});
