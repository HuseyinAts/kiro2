-- Social Features Tables Migration (F1-F6)
-- Created: 2026-03-24

-- F1: Soru Meydani (Q&A Forum)
CREATE TABLE IF NOT EXISTS forum_questions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    student_id VARCHAR NOT NULL,
    question_bank_id VARCHAR,
    subject_area VARCHAR(50) NOT NULL,
    topic VARCHAR(100),
    question_type VARCHAR(30) NOT NULL DEFAULT 'how_to_solve',
    title VARCHAR(200) NOT NULL,
    body TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    solution_count INTEGER DEFAULT 0,
    accepted_solution_id VARCHAR,
    xp_awarded BOOLEAN DEFAULT FALSE,
    flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_forum_q_student ON forum_questions(student_id);
CREATE INDEX IF NOT EXISTS idx_forum_q_qbank ON forum_questions(question_bank_id);
CREATE INDEX IF NOT EXISTS idx_forum_q_subject ON forum_questions(subject_area);
CREATE INDEX IF NOT EXISTS idx_forum_q_status ON forum_questions(status);

CREATE TABLE IF NOT EXISTS forum_solutions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    question_id VARCHAR NOT NULL,
    solver_id VARCHAR NOT NULL,
    body TEXT NOT NULL,
    image_url VARCHAR(500),
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    is_accepted BOOLEAN DEFAULT FALSE,
    xp_awarded INTEGER DEFAULT 0,
    flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_forum_sol_question ON forum_solutions(question_id);
CREATE INDEX IF NOT EXISTS idx_forum_sol_solver ON forum_solutions(solver_id);

CREATE TABLE IF NOT EXISTS forum_votes (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    voter_id VARCHAR NOT NULL,
    solution_id VARCHAR NOT NULL,
    vote_type VARCHAR(15) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_forum_vote UNIQUE (voter_id, solution_id)
);
CREATE INDEX IF NOT EXISTS idx_forum_vote_voter ON forum_votes(voter_id);
CREATE INDEX IF NOT EXISTS idx_forum_vote_solution ON forum_votes(solution_id);

-- F4: Pomodoro Rooms
CREATE TABLE IF NOT EXISTS pomodoro_rooms (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    subject_area VARCHAR(50) NOT NULL,
    topic VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'waiting',
    max_participants INTEGER DEFAULT 4,
    current_participants INTEGER DEFAULT 0,
    work_minutes INTEGER DEFAULT 25,
    break_minutes INTEGER DEFAULT 5,
    total_rounds INTEGER DEFAULT 4,
    current_round INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pomo_subject ON pomodoro_rooms(subject_area);
CREATE INDEX IF NOT EXISTS idx_pomo_status ON pomodoro_rooms(status);

CREATE TABLE IF NOT EXISTS pomodoro_participants (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    room_id VARCHAR NOT NULL,
    student_id VARCHAR NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'joined',
    rounds_completed INTEGER DEFAULT 0,
    total_work_minutes INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    joined_at TIMESTAMPTZ DEFAULT now(),
    left_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_pomo_part_room ON pomodoro_participants(room_id);
CREATE INDEX IF NOT EXISTS idx_pomo_part_student ON pomodoro_participants(student_id);

-- F5: Birlikte Streak
CREATE TABLE IF NOT EXISTS streak_pairs (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    student_a_id VARCHAR NOT NULL,
    student_b_id VARCHAR NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    current_streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,
    total_xp_earned INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT now(),
    broken_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_streak_a ON streak_pairs(student_a_id);
CREATE INDEX IF NOT EXISTS idx_streak_b ON streak_pairs(student_b_id);
CREATE INDEX IF NOT EXISTS idx_streak_status ON streak_pairs(status);

CREATE TABLE IF NOT EXISTS streak_daily_log (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    pair_id VARCHAR NOT NULL,
    student_id VARCHAR NOT NULL,
    log_date DATE NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_streak_log_pair ON streak_daily_log(pair_id);

-- F6: Usta-Cirak (Mentor-Mentee)
CREATE TABLE IF NOT EXISTS mentor_pairs (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    mentor_id VARCHAR NOT NULL,
    mentee_id VARCHAR NOT NULL,
    subject_area VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    session_count INTEGER DEFAULT 0,
    total_xp_mentor INTEGER DEFAULT 0,
    total_xp_mentee INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_mentor_pair_mentor ON mentor_pairs(mentor_id);
CREATE INDEX IF NOT EXISTS idx_mentor_pair_mentee ON mentor_pairs(mentee_id);
CREATE INDEX IF NOT EXISTS idx_mentor_pair_subject ON mentor_pairs(subject_area);
CREATE INDEX IF NOT EXISTS idx_mentor_pair_status ON mentor_pairs(status);

CREATE TABLE IF NOT EXISTS mentor_sessions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    pair_id VARCHAR NOT NULL,
    question_bank_id VARCHAR,
    topic VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    duration_minutes INTEGER,
    mentor_xp INTEGER DEFAULT 0,
    mentee_xp INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_mentor_sess_pair ON mentor_sessions(pair_id);

CREATE TABLE IF NOT EXISTS mentor_feedback (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    session_id VARCHAR NOT NULL,
    giver_id VARCHAR NOT NULL,
    receiver_id VARCHAR NOT NULL,
    rating INTEGER NOT NULL,
    tags TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_mentor_fb_session ON mentor_feedback(session_id);

-- F2: Cozum Duellosu (Solution Duel)
CREATE TABLE IF NOT EXISTS solution_duels (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    question_bank_id VARCHAR NOT NULL,
    subject_area VARCHAR(50) NOT NULL,
    challenger_id VARCHAR NOT NULL,
    opponent_id VARCHAR,
    status VARCHAR(20) NOT NULL DEFAULT 'waiting',
    solve_time_seconds INTEGER DEFAULT 300,
    voting_ends_at TIMESTAMPTZ,
    winner_id VARCHAR,
    winner_xp INTEGER DEFAULT 30,
    loser_xp INTEGER DEFAULT 10,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_duel_qbank ON solution_duels(question_bank_id);
CREATE INDEX IF NOT EXISTS idx_duel_subject ON solution_duels(subject_area);
CREATE INDEX IF NOT EXISTS idx_duel_challenger ON solution_duels(challenger_id);
CREATE INDEX IF NOT EXISTS idx_duel_opponent ON solution_duels(opponent_id);
CREATE INDEX IF NOT EXISTS idx_duel_status ON solution_duels(status);

CREATE TABLE IF NOT EXISTS solution_duel_submissions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    duel_id VARCHAR NOT NULL,
    student_id VARCHAR NOT NULL,
    body TEXT NOT NULL,
    image_url VARCHAR(500),
    vote_count INTEGER DEFAULT 0,
    flagged BOOLEAN DEFAULT FALSE,
    submitted_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_duel_sub_duel ON solution_duel_submissions(duel_id);

CREATE TABLE IF NOT EXISTS solution_duel_votes (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    duel_id VARCHAR NOT NULL,
    voter_id VARCHAR NOT NULL,
    voted_for_id VARCHAR NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_duel_vote UNIQUE (duel_id, voter_id)
);
CREATE INDEX IF NOT EXISTS idx_duel_vote_duel ON solution_duel_votes(duel_id);

-- F3: Oba Seferleri (Team Challenges)
CREATE TABLE IF NOT EXISTS oba_challenges (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    oba_id VARCHAR NOT NULL,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(500),
    challenge_type VARCHAR(30) NOT NULL DEFAULT 'solve_questions',
    target_value INTEGER NOT NULL,
    current_value INTEGER DEFAULT 0,
    bonus_xp_per_member INTEGER DEFAULT 50,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    completed BOOLEAN DEFAULT FALSE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_oba_ch_oba ON oba_challenges(oba_id);
CREATE INDEX IF NOT EXISTS idx_oba_ch_status ON oba_challenges(status);

CREATE TABLE IF NOT EXISTS oba_challenge_progress (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    challenge_id VARCHAR NOT NULL,
    student_id VARCHAR NOT NULL,
    contribution INTEGER DEFAULT 0,
    contribution_ratio FLOAT DEFAULT 0.0,
    xp_earned INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_oba_prog_ch ON oba_challenge_progress(challenge_id);
CREATE INDEX IF NOT EXISTS idx_oba_prog_student ON oba_challenge_progress(student_id);
