/**
 * Social Features API Service
 * F0-F6: Moderation, Soru Meydani, Pomodoro, Streak, Usta-Cirak
 */

const BASE = '/api/v1';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || `HTTP ${res.status}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// F1: Soru Meydani
// ---------------------------------------------------------------------------

export interface ForumQuestion {
  id: string;
  student_id: string;
  subject_area: string;
  topic: string | null;
  question_type: string;
  title: string;
  body?: string;
  status: string;
  solution_count: number;
  accepted_solution_id?: string;
  created_at: string | null;
}

export interface ForumSolution {
  id: string;
  solver_id: string;
  body: string;
  image_url: string | null;
  helpful_count: number;
  not_helpful_count: number;
  is_accepted: boolean;
  created_at: string | null;
}

export const soruMeydani = {
  getQuestionTypes: () =>
    request<{ success: boolean; data: { type: string; label: string }[] }>(
      `${BASE}/soru-meydani/question-types`
    ),

  listQuestions: (params?: { subject_area?: string; status?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.subject_area) q.set('subject_area', params.subject_area);
    if (params?.status) q.set('status', params.status);
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.offset) q.set('offset', String(params.offset));
    return request<{ success: boolean; data: { items: ForumQuestion[]; total: number } }>(
      `${BASE}/soru-meydani/questions?${q}`
    );
  },

  getQuestion: (id: string) =>
    request<{ success: boolean; data: { question: ForumQuestion; solutions: ForumSolution[] } }>(
      `${BASE}/soru-meydani/questions/${id}`
    ),

  askQuestion: (data: {
    subject_area: string;
    question_type: string;
    title: string;
    body?: string;
    question_bank_id?: string;
    topic?: string;
  }) =>
    request<{ success: boolean; data: { id: string } }>(`${BASE}/soru-meydani/questions`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  submitSolution: (questionId: string, data: { body: string; image_url?: string }) =>
    request<{ success: boolean; data: { id: string } }>(
      `${BASE}/soru-meydani/questions/${questionId}/solutions`,
      { method: 'POST', body: JSON.stringify(data) }
    ),

  voteSolution: (solutionId: string, vote_type: 'helpful' | 'not_helpful') =>
    request<{ success: boolean }>(`${BASE}/soru-meydani/solutions/${solutionId}/vote`, {
      method: 'POST',
      body: JSON.stringify({ vote_type }),
    }),

  acceptSolution: (questionId: string, solutionId: string) =>
    request<{ success: boolean }>(`${BASE}/soru-meydani/questions/${questionId}/accept/${solutionId}`, {
      method: 'POST',
    }),
};

// ---------------------------------------------------------------------------
// F2: Cozum Duellosu (Solution Duel)
// ---------------------------------------------------------------------------

export interface DuelInfo {
  id: string;
  question_bank_id: string;
  subject_area: string;
  challenger_id: string;
  opponent_id: string | null;
  status: string;
  solve_time_seconds: number;
  winner_id: string | null;
  started_at: string | null;
}

export interface DuelSubmission {
  id: string;
  student_id: string;
  body: string;
  image_url: string | null;
  vote_count: number;
  submitted_at: string | null;
}

export const cozumDuellosu = {
  create: (data: { question_bank_id: string; subject_area: string; solve_time_seconds?: number }) =>
    request<{ success: boolean; data: { duel_id: string; matched: boolean }; message: string }>(
      `${BASE}/cozum-duellosu/create`,
      { method: 'POST', body: JSON.stringify(data) }
    ),

  getDuel: (duelId: string) =>
    request<{ success: boolean; data: { duel: DuelInfo; submissions: DuelSubmission[] } }>(
      `${BASE}/cozum-duellosu/${duelId}`
    ),

  submit: (duelId: string, data: { body: string; image_url?: string }) =>
    request<{ success: boolean; data: { id: string }; message: string }>(
      `${BASE}/cozum-duellosu/${duelId}/submit`,
      { method: 'POST', body: JSON.stringify(data) }
    ),

  vote: (duelId: string, submissionId: string) =>
    request<{ success: boolean; message: string }>(
      `${BASE}/cozum-duellosu/${duelId}/vote`,
      { method: 'POST', body: JSON.stringify({ submission_id: submissionId }) }
    ),

  listActive: (params?: { subject_area?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.subject_area) q.set('subject_area', params.subject_area);
    if (params?.limit) q.set('limit', String(params.limit));
    return request<{ success: boolean; data: { id: string; subject_area: string; question_bank_id: string; voting_ends_at: string | null }[] }>(
      `${BASE}/cozum-duellosu/active/list?${q}`
    );
  },
};

// ---------------------------------------------------------------------------
// F3: Oba Seferleri (Team Challenges)
// ---------------------------------------------------------------------------

export interface ObaChallengeInfo {
  id: string;
  title: string;
  description: string | null;
  challenge_type: string;
  target_value: number;
  current_value: number;
  progress_pct: number;
  bonus_xp_per_member: number;
  completed: boolean;
  start_date: string;
  end_date: string;
}

export interface ObaContributor {
  student_id: string;
  contribution: number;
  ratio: number;
}

export const obaSeferleri = {
  getActive: (obaId: string) =>
    request<{ success: boolean; data: { challenge: ObaChallengeInfo; contributors: ObaContributor[] } | null; message?: string }>(
      `${BASE}/oba-seferleri/active/${obaId}`
    ),

  contribute: (challengeId: string, amount: number) =>
    request<{ success: boolean; data: { contribution: number; challenge_current: number; challenge_target: number; completed: boolean }; message: string }>(
      `${BASE}/oba-seferleri/contribute/${challengeId}`,
      { method: 'POST', body: JSON.stringify({ amount }) }
    ),

  getHistory: (obaId: string, limit?: number) => {
    const q = new URLSearchParams();
    if (limit) q.set('limit', String(limit));
    return request<{ success: boolean; data: { id: string; title: string; challenge_type: string; target_value: number; current_value: number; completed: boolean; start_date: string; end_date: string }[] }>(
      `${BASE}/oba-seferleri/history/${obaId}?${q}`
    );
  },

  getMyContributions: (limit?: number) => {
    const q = new URLSearchParams();
    if (limit) q.set('limit', String(limit));
    return request<{ success: boolean; data: { challenge_id: string; contribution: number; ratio: number; xp_earned: number }[] }>(
      `${BASE}/oba-seferleri/my-contributions?${q}`
    );
  },
};

// ---------------------------------------------------------------------------
// F4: Pomodoro Rooms
// ---------------------------------------------------------------------------

export interface PomodoroRoom {
  id: string;
  subject_area: string;
  topic: string | null;
  status: string;
  current_round: number;
  total_rounds: number;
  work_minutes: number;
  break_minutes: number;
  started_at: string | null;
}

export interface PomodoroParticipant {
  student_id: string;
  status: string;
  rounds_completed: number;
}

export const pomodoro = {
  join: (data: { subject_area: string; topic?: string }) =>
    request<{ success: boolean; data: { room_id: string; status: string; participants: number } }>(
      `${BASE}/pomodoro/join`,
      { method: 'POST', body: JSON.stringify(data) }
    ),

  getRoom: (roomId: string) =>
    request<{ success: boolean; data: { room: PomodoroRoom; participants: PomodoroParticipant[] } }>(
      `${BASE}/pomodoro/room/${roomId}`
    ),

  updateStatus: (roomId: string, status: 'working' | 'on_break' | 'left') =>
    request<{ success: boolean }>(`${BASE}/pomodoro/room/${roomId}/status`, {
      method: 'POST',
      body: JSON.stringify({ status }),
    }),

  completeRound: (roomId: string) =>
    request<{ success: boolean; data: { rounds_completed: number; xp_earned: number; total_xp: number } }>(
      `${BASE}/pomodoro/room/${roomId}/complete-round`,
      { method: 'POST' }
    ),
};

// ---------------------------------------------------------------------------
// F5: Birlikte Streak
// ---------------------------------------------------------------------------

export interface StreakStatus {
  pair_id: string;
  status: string;
  current_streak: number;
  max_streak: number;
  total_xp: number;
  my_today: boolean;
  partner_today: boolean;
}

export const streak = {
  request: () =>
    request<{ success: boolean; data: { pair_id: string; matched: boolean } }>(
      `${BASE}/birlikte-streak/request`,
      { method: 'POST' }
    ),

  getStatus: () =>
    request<{ success: boolean; data: StreakStatus | null }>(
      `${BASE}/birlikte-streak/status`
    ),

  completeToday: () =>
    request<{ success: boolean; data: { streak: number; xp_earned: number; bonus: number } }>(
      `${BASE}/birlikte-streak/complete-today`,
      { method: 'POST' }
    ),
};

// ---------------------------------------------------------------------------
// F6: Usta-Cirak
// ---------------------------------------------------------------------------

export interface MentorPairInfo {
  id: string;
  mentor_id: string;
  mentee_id: string;
  subject_area: string;
  session_count: number;
  my_role: 'mentor' | 'mentee';
}

export const ustaCirak = {
  requestMatch: (data: { subject_area: string; role: 'mentor' | 'mentee' }) =>
    request<{ success: boolean; data: { pair_id: string; matched: boolean } }>(
      `${BASE}/usta-cirak/request`,
      { method: 'POST', body: JSON.stringify(data) }
    ),

  getPairs: () =>
    request<{ success: boolean; data: MentorPairInfo[] }>(`${BASE}/usta-cirak/pairs`),

  startSession: (pairId: string, data?: { question_bank_id?: string; topic?: string }) =>
    request<{ success: boolean; data: { session_id: string } }>(
      `${BASE}/usta-cirak/pairs/${pairId}/session`,
      { method: 'POST', body: JSON.stringify(data || {}) }
    ),

  endSession: (sessionId: string) =>
    request<{ success: boolean; data: { duration_minutes: number; mentor_xp: number; mentee_xp: number } }>(
      `${BASE}/usta-cirak/sessions/${sessionId}/end`,
      { method: 'POST' }
    ),

  submitFeedback: (sessionId: string, data: { rating: number; tags?: string[] }) =>
    request<{ success: boolean }>(`${BASE}/usta-cirak/sessions/${sessionId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};
