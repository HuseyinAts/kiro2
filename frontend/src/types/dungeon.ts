export interface DungeonProgressData {
  attempt_count: number;
  best_score: number;
  last_score: number;
  completed: boolean;
}

export interface DungeonRoom {
  topic_id: string;
  code: string;
  name_tr: string;
  parent_subject: string;
  prereqs_met: boolean;
  dag_depth: number;
  progress: DungeonProgressData;
  question_count: number;
}

export interface DungeonEdge {
  from_topic: string;
  to_topic: string;
  prereq_type: 'hard' | 'soft';
}

export interface DungeonMapResponse {
  subject: string;
  theta: number;
  theta_se: number;
  rooms: DungeonRoom[];
  edges: DungeonEdge[];
}

/** Room visual level derived from progress */
export type RoomLevel = 0 | 1 | 2 | 3;

export function getRoomLevel(progress: DungeonProgressData): RoomLevel {
  if (progress.completed) return 3;
  if (progress.best_score >= 50) return 2;
  if (progress.attempt_count > 0) return 1;
  return 0;
}

/** Seeded pseudo-random for deterministic Rough.js offsets */
export function seededRandom(seed: string): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = ((hash << 5) - hash + seed.charCodeAt(i)) | 0;
  }
  return ((Math.sin(hash * 9301 + 49297) % 233280) + 233280) % 233280 / 233280;
}

/** Fog opacity based on theta + dag_depth + completion */
export function fogOpacity(
  room: DungeonRoom,
  theta: number,
): number {
  if (!room.prereqs_met) return 0.9;
  if (room.progress.completed) return 0;

  const thetaFactor = Math.max(0, Math.min(1, (theta + 3) / 6));
  const depthFactor = Math.max(0, 1 - room.dag_depth * 0.15);

  return Math.max(0, 0.7 - thetaFactor * 0.4 - depthFactor * 0.2);
}
