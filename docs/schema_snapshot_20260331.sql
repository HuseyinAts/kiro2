--
-- PostgreSQL database dump
--

\restrict tPaEriuD4U5rB6c2wCBcSBB2vgvgbjh4GzP55VvOhUNyEO6g8F3l6bp7yRtf96o

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA public;


--
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: ebacontentcategory; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.ebacontentcategory AS ENUM (
    'MATEMATIK',
    'TURKCE',
    'FEN_BILIMLERI',
    'SOSYAL_BILGILER',
    'INGILIZCE',
    'FIZIK',
    'KIMYA',
    'BIYOLOJI',
    'TARIH',
    'COGRAFYA',
    'FELSEFE',
    'EDEBIYAT'
);


ALTER TYPE public.ebacontentcategory OWNER TO postgres;

--
-- Name: ebagradelevel; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.ebagradelevel AS ENUM (
    'SINIF_5',
    'SINIF_6',
    'SINIF_7',
    'SINIF_8',
    'SINIF_9',
    'SINIF_10',
    'SINIF_11',
    'SINIF_12'
);


ALTER TYPE public.ebagradelevel OWNER TO postgres;

--
-- Name: ebavideoquality; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.ebavideoquality AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH'
);


ALTER TYPE public.ebavideoquality OWNER TO postgres;

--
-- Name: examtype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.examtype AS ENUM (
    'TYT',
    'AYT',
    'YDT',
    'DENEME'
);


ALTER TYPE public.examtype OWNER TO postgres;

--
-- Name: learningstyle; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.learningstyle AS ENUM (
    'VISUAL',
    'AUDITORY',
    'KINESTHETIC',
    'READING_WRITING'
);


ALTER TYPE public.learningstyle OWNER TO postgres;

--
-- Name: questiondifficulty; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.questiondifficulty AS ENUM (
    'EASY',
    'MEDIUM',
    'HARD'
);


ALTER TYPE public.questiondifficulty OWNER TO postgres;

--
-- Name: questiondifficultylevel; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.questiondifficultylevel AS ENUM (
    'VERY_EASY',
    'EASY',
    'MEDIUM',
    'HARD',
    'VERY_HARD'
);


ALTER TYPE public.questiondifficultylevel OWNER TO postgres;

--
-- Name: subjectarea; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.subjectarea AS ENUM (
    'MATEMATIK',
    'TURKCE',
    'FEN',
    'SOSYAL',
    'FIZIK',
    'KIMYA',
    'BIYOLOJI',
    'INGILIZCE'
);


ALTER TYPE public.subjectarea OWNER TO postgres;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.userrole AS ENUM (
    'STUDENT',
    'TEACHER',
    'PARENT',
    'ADMIN'
);


ALTER TYPE public.userrole OWNER TO postgres;

--
-- Name: fn_sync_answer_to_learning_events(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.fn_sync_answer_to_learning_events() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_id TEXT;
BEGIN
    SELECT student_id INTO v_user_id
    FROM exam_sessions
    WHERE id = NEW.exam_session_id
    LIMIT 1;

    IF v_user_id IS NULL THEN
        RETURN NEW;
    END IF;

    IF EXISTS (
        SELECT 1 FROM kiro2_learning_events
        WHERE question_id::text = NEW.question_id
          AND user_id::text = v_user_id
          AND event_type = 'exam_answer'
          AND occurred_at::date = NEW.answered_at::date
    ) THEN
        RETURN NEW;
    END IF;

    INSERT INTO kiro2_learning_events (
        id, user_id, question_id, session_id,
        event_type, is_correct, theta_after, response_ms, occurred_at
    ) VALUES (
        gen_random_uuid(),
        v_user_id::uuid,
        NEW.question_id::uuid,
        NULL,
        'exam_answer',
        NEW.is_correct,
        NULL,
        (NEW.response_time_seconds * 1000)::int,
        NEW.answered_at
    );

    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'fn_sync_answer_to_learning_events hata: %', SQLERRM;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.fn_sync_answer_to_learning_events() OWNER TO postgres;

--
-- Name: fn_update_qb_stats_from_le(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.fn_update_qb_stats_from_le() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.event_type NOT IN ('exam_answer', 'cat_answer') THEN
        RETURN NEW;
    END IF;
    UPDATE question_bank SET
        times_asked    = times_asked + 1,
        times_correct  = times_correct + CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        times_wrong    = times_wrong   + CASE WHEN NEW.is_correct THEN 0 ELSE 1 END,
        last_used_date = NOW()
    WHERE id::text = NEW.question_id::text;
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'fn_update_qb_stats_from_le hata: %', SQLERRM;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.fn_update_qb_stats_from_le() OWNER TO postgres;

--
-- Name: fn_update_qb_stats_from_sa(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.fn_update_qb_stats_from_sa() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE question_bank SET
        times_asked   = times_asked + 1,
        times_correct = times_correct + CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        times_wrong   = times_wrong   + CASE WHEN NEW.is_correct THEN 0 ELSE 1 END,
        last_used_date = NOW()
    WHERE id::text = NEW.question_id::text;
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'fn_update_qb_stats_from_sa hata: %', SQLERRM;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.fn_update_qb_stats_from_sa() OWNER TO postgres;

--
-- Name: fn_update_student_ability(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.fn_update_student_ability() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE v_subject_id INT;
BEGIN
    IF NEW.event_type NOT IN ('exam_answer','cat_answer') THEN RETURN NEW; END IF;
    IF NEW.theta_after IS NULL THEN RETURN NEW; END IF;
    SELECT s.id INTO v_subject_id FROM question_bank qb
    JOIN subjects s ON s.name = qb.subject_area
    WHERE qb.id::text = NEW.question_id::text LIMIT 1;
    IF v_subject_id IS NULL THEN RETURN NEW; END IF;
    INSERT INTO student_abilities (student_id, subject_id, theta, theta_se, updated_at)
    VALUES (NEW.user_id::text, v_subject_id, ROUND(NEW.theta_after::numeric,3), 0.4, NOW())
    ON CONFLICT (student_id, subject_id) DO UPDATE SET
        theta      = ROUND(EXCLUDED.theta::numeric,3),
        theta_se   = GREATEST(student_abilities.theta_se - 0.02, 0.3),
        updated_at = NOW();
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN RETURN NEW;
END; $$;


ALTER FUNCTION public.fn_update_student_ability() OWNER TO postgres;

--
-- Name: update_fsrs_updated_at(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_fsrs_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;


ALTER FUNCTION public.update_fsrs_updated_at() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: api_keys; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.api_keys (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    key_hash character varying(255) NOT NULL,
    key_prefix character varying(20) NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    scopes json,
    allowed_ips json,
    rate_limit integer NOT NULL,
    is_active boolean NOT NULL,
    expires_at timestamp with time zone,
    revoked boolean NOT NULL,
    revoked_at timestamp with time zone,
    revoke_reason character varying(200),
    last_used_at timestamp with time zone,
    usage_count integer NOT NULL,
    last_used_ip character varying(45),
    created_from_ip character varying(45),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.api_keys OWNER TO postgres;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_logs (
    id character varying NOT NULL,
    user_id character varying,
    action character varying(100) NOT NULL,
    resource_type character varying(100) NOT NULL,
    resource_id character varying,
    old_values json,
    new_values json,
    ip_address character varying(45),
    user_agent character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.audit_logs OWNER TO postgres;

--
-- Name: badges; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.badges (
    id character varying(100) NOT NULL,
    slug character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    icon character varying(10),
    category character varying(20),
    condition jsonb
);


ALTER TABLE public.badges OWNER TO postgres;

--
-- Name: badges_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.badges_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.badges_id_seq OWNER TO postgres;

--
-- Name: badges_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.badges_id_seq OWNED BY public.badges.id;


--
-- Name: bkt_states; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bkt_states (
    student_id character varying NOT NULL,
    topic_id character varying NOT NULL,
    p_learn numeric(5,4) DEFAULT 0.05 NOT NULL,
    p_transit numeric(5,4) DEFAULT 0.10 NOT NULL,
    p_guess numeric(5,4) DEFAULT 0.20 NOT NULL,
    p_slip numeric(5,4) DEFAULT 0.10 NOT NULL,
    attempt_count integer DEFAULT 0 NOT NULL,
    mastery_status character varying(20) DEFAULT 'learning'::character varying NOT NULL,
    last_attempt timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.bkt_states OWNER TO postgres;

--
-- Name: blocked_users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.blocked_users (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    blocker_id character varying NOT NULL,
    blocked_id character varying NOT NULL,
    reason text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.blocked_users OWNER TO postgres;

--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_messages (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    session_id character varying NOT NULL,
    role character varying(20) NOT NULL,
    content text NOT NULL,
    image_id character varying,
    model character varying(100),
    tokens_used integer,
    cost double precision,
    response_time_ms integer,
    confidence_score double precision,
    relevance_score double precision,
    user_rating integer,
    is_helpful boolean,
    feedback_comment text,
    meta_data jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.chat_messages OWNER TO postgres;

--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_sessions (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    user_id character varying NOT NULL,
    title character varying(255),
    subject_type character varying(20) DEFAULT 'general'::character varying,
    status character varying(20) DEFAULT 'active'::character varying,
    context jsonb DEFAULT '{}'::jsonb,
    meta_data jsonb DEFAULT '{}'::jsonb,
    model_name character varying(100) DEFAULT 'qwen3:8b'::character varying,
    temperature double precision DEFAULT 0.7,
    max_tokens integer DEFAULT 2000,
    message_count integer DEFAULT 0,
    total_tokens integer DEFAULT 0,
    total_cost double precision DEFAULT 0.0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_message_at timestamp with time zone
);


ALTER TABLE public.chat_sessions OWNER TO postgres;

--
-- Name: class_reports; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.class_reports (
    id character varying NOT NULL,
    teacher_user_id character varying NOT NULL,
    class_name character varying(100) NOT NULL,
    subject character varying(100) NOT NULL,
    report_period character varying(50) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    total_students integer NOT NULL,
    average_grade double precision NOT NULL,
    passing_students integer NOT NULL,
    failing_students integer NOT NULL,
    grade_distribution json,
    top_students json NOT NULL,
    struggling_students json NOT NULL,
    teacher_notes text,
    recommendations json NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.class_reports OWNER TO postgres;

--
-- Name: COLUMN class_reports.class_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.class_reports.class_name IS '12-A, 11-B, etc.';


--
-- Name: COLUMN class_reports.report_period; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.class_reports.report_period IS '2025-W47, 2025-Q1, etc.';


--
-- Name: COLUMN class_reports.grade_distribution; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.class_reports.grade_distribution IS '{"90-100": 5, "80-90": 10, ...}';


--
-- Name: classrooms; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.classrooms (
    id character varying NOT NULL,
    teacher_id character varying NOT NULL,
    class_name character varying(100) NOT NULL,
    grade_level integer NOT NULL,
    subject_area public.subjectarea NOT NULL,
    school_year character varying(20) NOT NULL,
    student_ids json,
    is_active boolean NOT NULL,
    max_students integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_class_grade_level CHECK (((grade_level >= 9) AND (grade_level <= 12)))
);


ALTER TABLE public.classrooms OWNER TO postgres;

--
-- Name: coaching_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.coaching_events (
    id character varying DEFAULT gen_random_uuid() NOT NULL,
    student_id character varying NOT NULL,
    event_type character varying(50) NOT NULL,
    suggestion_text text,
    metadata json,
    is_read boolean DEFAULT false,
    interaction character varying(20),
    created_at timestamp without time zone DEFAULT now(),
    shown_at timestamp without time zone,
    clicked_at timestamp without time zone,
    dismissed_at timestamp without time zone,
    trigger_data json,
    message text,
    action_url character varying,
    priority integer DEFAULT 0
);


ALTER TABLE public.coaching_events OWNER TO postgres;

--
-- Name: content_reports; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.content_reports (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    reporter_id character varying NOT NULL,
    reported_user_id character varying,
    reported_content_id character varying,
    content_type character varying(30) NOT NULL,
    content_snapshot text,
    reason character varying(20) NOT NULL,
    description text,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    reviewed_by character varying,
    reviewed_at timestamp with time zone,
    resolution_note text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.content_reports OWNER TO postgres;

--
-- Name: curriculum_alignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.curriculum_alignments (
    id character varying(100) NOT NULL,
    meb_standard_id character varying(100) NOT NULL,
    osym_standard_id character varying(100) NOT NULL,
    alignment_score double precision NOT NULL,
    alignment_type character varying(50) NOT NULL,
    gaps_identified json,
    recommendations json,
    verified_by character varying(100),
    verification_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_alignment_score CHECK (((alignment_score >= (0.0)::double precision) AND (alignment_score <= (1.0)::double precision)))
);


ALTER TABLE public.curriculum_alignments OWNER TO postgres;

--
-- Name: curriculum_update_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.curriculum_update_requests (
    id character varying(100) NOT NULL,
    update_type character varying(50) NOT NULL,
    subject character varying(50) NOT NULL,
    affected_standards json,
    changes_description text NOT NULL,
    source_document character varying(500),
    requested_by character varying(100) NOT NULL,
    requested_at timestamp with time zone DEFAULT now() NOT NULL,
    status character varying(50) NOT NULL,
    reviewed_by character varying(100),
    reviewed_at timestamp with time zone,
    implementation_date timestamp with time zone,
    notes text
);


ALTER TABLE public.curriculum_update_requests OWNER TO postgres;

--
-- Name: daily_plans; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_plans (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id character varying(255) NOT NULL,
    plan_date date NOT NULL,
    exam_date date NOT NULL,
    days_remaining integer NOT NULL,
    total_minutes integer DEFAULT 0 NOT NULL,
    plan_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    weak_subject character varying(50),
    strong_subject character varying(50),
    motivational_note text,
    generated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.daily_plans OWNER TO postgres;

--
-- Name: TABLE daily_plans; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.daily_plans IS 'ZPD+DAG+IRT+FSRS ile üretilen günlük çalışma planları';


--
-- Name: dina_parameters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dina_parameters (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    slip double precision DEFAULT '0.1'::double precision,
    guess double precision DEFAULT '0.2'::double precision,
    calibrated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.dina_parameters OWNER TO postgres;

--
-- Name: duel_matches; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.duel_matches (
    id character varying DEFAULT gen_random_uuid() NOT NULL,
    session_id character varying NOT NULL,
    question_id character varying NOT NULL,
    question_order integer NOT NULL,
    player1_answer character varying(1),
    player2_answer character varying(1),
    player1_correct boolean,
    player2_correct boolean,
    player1_time_ms integer,
    player2_time_ms integer,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.duel_matches OWNER TO postgres;

--
-- Name: duel_ratings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.duel_ratings (
    id character varying DEFAULT gen_random_uuid() NOT NULL,
    student_id character varying NOT NULL,
    elo_rating double precision DEFAULT 1200.0,
    wins integer DEFAULT 0,
    losses integer DEFAULT 0,
    draws integer DEFAULT 0,
    peak_rating double precision DEFAULT 1200.0,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.duel_ratings OWNER TO postgres;

--
-- Name: duel_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.duel_sessions (
    id character varying NOT NULL,
    player1_id character varying NOT NULL,
    player2_id character varying,
    subject character varying NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying,
    player1_score integer DEFAULT 0,
    player2_score integer DEFAULT 0,
    winner_id character varying,
    started_at timestamp without time zone DEFAULT now(),
    finished_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now(),
    question_count integer DEFAULT 5,
    time_per_question_sec integer DEFAULT 30,
    player1_elo_change double precision DEFAULT 0,
    player2_elo_change double precision DEFAULT 0
);


ALTER TABLE public.duel_sessions OWNER TO postgres;

--
-- Name: duels; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.duels (
    id integer NOT NULL,
    player1_id character varying NOT NULL,
    player2_id character varying NOT NULL,
    topic_id character varying NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    winner_id character varying(36),
    player1_score integer DEFAULT 0 NOT NULL,
    player2_score integer DEFAULT 0 NOT NULL,
    elo_delta integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone
);


ALTER TABLE public.duels OWNER TO postgres;

--
-- Name: duels_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.duels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.duels_id_seq OWNER TO postgres;

--
-- Name: duels_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.duels_id_seq OWNED BY public.duels.id;


--
-- Name: eba_content_analytics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.eba_content_analytics (
    id character varying NOT NULL,
    analysis_date date NOT NULL,
    category public.ebacontentcategory NOT NULL,
    grade_level public.ebagradelevel NOT NULL,
    total_views integer NOT NULL,
    unique_viewers integer NOT NULL,
    total_watch_time_minutes integer NOT NULL,
    average_completion_rate double precision NOT NULL,
    average_user_rating double precision NOT NULL,
    total_ratings integer NOT NULL,
    average_learning_effectiveness double precision NOT NULL,
    trending_score double precision NOT NULL,
    engagement_score double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.eba_content_analytics OWNER TO postgres;

--
-- Name: eba_content_collections; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.eba_content_collections (
    id character varying NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    category public.ebacontentcategory NOT NULL,
    grade_level public.ebagradelevel NOT NULL,
    video_ids json,
    total_videos integer NOT NULL,
    total_duration_minutes integer NOT NULL,
    average_quality_score double precision NOT NULL,
    is_active boolean NOT NULL,
    is_featured boolean NOT NULL,
    created_by character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.eba_content_collections OWNER TO postgres;

--
-- Name: eba_video_recommendations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.eba_video_recommendations (
    id character varying NOT NULL,
    video_id character varying NOT NULL,
    student_id character varying NOT NULL,
    recommendation_score double precision NOT NULL,
    recommendation_reason character varying(200) NOT NULL,
    recommendation_category character varying(100) NOT NULL,
    learning_style_match double precision NOT NULL,
    difficulty_appropriateness double precision NOT NULL,
    curriculum_relevance double precision NOT NULL,
    shown_to_student boolean NOT NULL,
    clicked_by_student boolean NOT NULL,
    watched_by_student boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    shown_at timestamp with time zone,
    clicked_at timestamp with time zone,
    CONSTRAINT check_eba_rec_score CHECK (((recommendation_score >= (0.0)::double precision) AND (recommendation_score <= (10.0)::double precision)))
);


ALTER TABLE public.eba_video_recommendations OWNER TO postgres;

--
-- Name: eba_video_usage; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.eba_video_usage (
    id character varying NOT NULL,
    video_id character varying NOT NULL,
    student_id character varying NOT NULL,
    started_at timestamp with time zone NOT NULL,
    ended_at timestamp with time zone,
    watch_duration_seconds integer NOT NULL,
    completion_percentage double precision NOT NULL,
    paused_count integer NOT NULL,
    rewound_count integer NOT NULL,
    fast_forwarded_count integer NOT NULL,
    user_rating double precision,
    user_feedback text,
    pre_knowledge_score double precision,
    post_knowledge_score double precision,
    learning_effectiveness double precision,
    CONSTRAINT check_eba_completion CHECK (((completion_percentage >= (0.0)::double precision) AND (completion_percentage <= (100.0)::double precision))),
    CONSTRAINT check_eba_rating CHECK (((user_rating IS NULL) OR ((user_rating >= (1.0)::double precision) AND (user_rating <= (5.0)::double precision))))
);


ALTER TABLE public.eba_video_usage OWNER TO postgres;

--
-- Name: eba_videos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.eba_videos (
    id character varying NOT NULL,
    title character varying(300) NOT NULL,
    description text NOT NULL,
    duration_minutes integer NOT NULL,
    category public.ebacontentcategory NOT NULL,
    grade_level public.ebagradelevel NOT NULL,
    subject_topics json,
    difficulty_level public.questiondifficulty NOT NULL,
    video_url character varying(500) NOT NULL,
    thumbnail_url character varying(500),
    transcript text,
    quality_score double precision NOT NULL,
    quality_category public.ebavideoquality NOT NULL,
    curriculum_alignment json,
    accessibility_features json,
    has_subtitles boolean NOT NULL,
    has_transcript boolean NOT NULL,
    view_count integer NOT NULL,
    like_count integer NOT NULL,
    share_count integer NOT NULL,
    bookmark_count integer NOT NULL,
    duration_score double precision NOT NULL,
    title_clarity_score double precision NOT NULL,
    description_quality_score double precision NOT NULL,
    curriculum_alignment_score double precision NOT NULL,
    accessibility_score double precision NOT NULL,
    moderation_status character varying(50) NOT NULL,
    moderated_by character varying,
    moderation_date timestamp with time zone,
    moderation_notes text,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_eba_duration CHECK (((duration_minutes >= 1) AND (duration_minutes <= 180))),
    CONSTRAINT check_eba_quality_score CHECK (((quality_score >= (0.0)::double precision) AND (quality_score <= (10.0)::double precision)))
);


ALTER TABLE public.eba_videos OWNER TO postgres;

--
-- Name: educational_contents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.educational_contents (
    id character varying NOT NULL,
    title character varying(300) NOT NULL,
    description text,
    content_type character varying(50) NOT NULL,
    source_platform character varying(100) NOT NULL,
    source_url character varying(500) NOT NULL,
    source_id character varying(200),
    subject_area public.subjectarea NOT NULL,
    topic character varying(200) NOT NULL,
    subtopic character varying(200),
    grade_level integer NOT NULL,
    difficulty_level public.questiondifficulty NOT NULL,
    educational_score double precision NOT NULL,
    duration_minutes integer,
    has_subtitles boolean NOT NULL,
    has_transcript boolean NOT NULL,
    language character varying(10) NOT NULL,
    view_count integer NOT NULL,
    like_count integer NOT NULL,
    rating double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE public.educational_contents OWNER TO postgres;

--
-- Name: error_clusters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.error_clusters (
    id character varying NOT NULL,
    subject character varying(50) NOT NULL,
    topic_ids jsonb DEFAULT '[]'::jsonb,
    error_pattern character varying(100) NOT NULL,
    student_count integer DEFAULT 0,
    recommended_remediation jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.error_clusters OWNER TO postgres;

--
-- Name: exam_questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.exam_questions (
    id character varying NOT NULL,
    exam_session_id character varying NOT NULL,
    question_id character varying NOT NULL,
    question_order integer NOT NULL
);


ALTER TABLE public.exam_questions OWNER TO postgres;

--
-- Name: exam_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.exam_sessions (
    id character varying NOT NULL,
    student_id character varying NOT NULL,
    exam_type public.examtype NOT NULL,
    exam_name character varying(200) NOT NULL,
    total_questions integer NOT NULL,
    duration_minutes integer NOT NULL,
    status character varying(50) NOT NULL,
    current_question_index integer NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    time_spent_seconds integer NOT NULL,
    total_correct integer NOT NULL,
    total_wrong integer NOT NULL,
    total_empty integer NOT NULL,
    raw_score double precision NOT NULL,
    scaled_score double precision,
    percentile double precision,
    estimated_ability double precision NOT NULL,
    ability_confidence double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.exam_sessions OWNER TO postgres;

--
-- Name: fallback_videos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fallback_videos (
    id integer NOT NULL,
    subject character varying(100) NOT NULL,
    topic character varying(100),
    video_id character varying(100) NOT NULL,
    title character varying(500) NOT NULL,
    description text,
    url character varying(500) NOT NULL,
    thumbnail_url character varying(500),
    duration character varying(20),
    duration_minutes integer,
    channel_name character varying(200),
    channel_id character varying(100),
    turkish_score double precision NOT NULL,
    relevance_score double precision NOT NULL,
    quality_score double precision NOT NULL,
    final_score double precision NOT NULL,
    is_accessible boolean NOT NULL,
    is_embeddable boolean NOT NULL,
    is_turkish boolean NOT NULL,
    is_example boolean NOT NULL,
    tags json NOT NULL,
    metadata_json json NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.fallback_videos OWNER TO postgres;

--
-- Name: fallback_videos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fallback_videos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fallback_videos_id_seq OWNER TO postgres;

--
-- Name: fallback_videos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fallback_videos_id_seq OWNED BY public.fallback_videos.id;


--
-- Name: forum_questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forum_questions (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    student_id character varying NOT NULL,
    question_bank_id character varying,
    subject_area character varying(50) NOT NULL,
    topic character varying(100),
    question_type character varying(30) DEFAULT 'how_to_solve'::character varying NOT NULL,
    title character varying(200) NOT NULL,
    body text,
    status character varying(20) DEFAULT 'open'::character varying NOT NULL,
    solution_count integer DEFAULT 0,
    accepted_solution_id character varying,
    xp_awarded boolean DEFAULT false,
    flagged boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.forum_questions OWNER TO postgres;

--
-- Name: forum_solutions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forum_solutions (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    question_id character varying NOT NULL,
    solver_id character varying NOT NULL,
    body text NOT NULL,
    image_url character varying(500),
    helpful_count integer DEFAULT 0,
    not_helpful_count integer DEFAULT 0,
    is_accepted boolean DEFAULT false,
    xp_awarded integer DEFAULT 0,
    flagged boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.forum_solutions OWNER TO postgres;

--
-- Name: forum_votes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forum_votes (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    voter_id character varying NOT NULL,
    solution_id character varying NOT NULL,
    vote_type character varying(15) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.forum_votes OWNER TO postgres;

--
-- Name: fsrs_cards; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fsrs_cards (
    id character varying NOT NULL,
    student_id character varying NOT NULL,
    front_text text NOT NULL,
    back_text text NOT NULL,
    subject_area public.subjectarea NOT NULL,
    topic character varying(200) NOT NULL,
    stability double precision NOT NULL,
    difficulty double precision NOT NULL,
    elapsed_days integer NOT NULL,
    scheduled_days integer NOT NULL,
    reps integer NOT NULL,
    lapses integer NOT NULL,
    state character varying(20) NOT NULL,
    due_date timestamp with time zone NOT NULL,
    last_review timestamp with time zone,
    cultural_factors json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.fsrs_cards OWNER TO postgres;

--
-- Name: fsrs_reviews; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fsrs_reviews (
    id character varying NOT NULL,
    card_id character varying NOT NULL,
    student_id character varying NOT NULL,
    grade integer NOT NULL,
    review_date timestamp with time zone NOT NULL,
    response_time_seconds double precision NOT NULL,
    old_stability double precision NOT NULL,
    new_stability double precision NOT NULL,
    old_difficulty double precision NOT NULL,
    new_difficulty double precision NOT NULL,
    cultural_adjustment double precision NOT NULL,
    CONSTRAINT check_fsrs_grade CHECK (((grade >= 1) AND (grade <= 4)))
);


ALTER TABLE public.fsrs_reviews OWNER TO postgres;

--
-- Name: fsrs_schedules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fsrs_schedules (
    id character varying NOT NULL,
    student_id character varying NOT NULL,
    schedule_date date NOT NULL,
    total_cards_due integer NOT NULL,
    new_cards integer NOT NULL,
    review_cards integer NOT NULL,
    cards_studied integer NOT NULL,
    study_time_minutes integer NOT NULL,
    retention_rate double precision NOT NULL,
    cultural_period character varying(50),
    adjustment_factor double precision NOT NULL
);


ALTER TABLE public.fsrs_schedules OWNER TO postgres;

--
-- Name: fsrs_student_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fsrs_student_profiles (
    id character varying NOT NULL,
    student_id character varying NOT NULL,
    fsrs_parameters json NOT NULL,
    cultural_parameters json NOT NULL,
    total_reviews integer NOT NULL,
    average_retention double precision NOT NULL,
    study_streak_days integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.fsrs_student_profiles OWNER TO postgres;

--
-- Name: fsrs_study_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fsrs_study_sessions (
    id character varying NOT NULL,
    student_id character varying NOT NULL,
    session_date timestamp with time zone NOT NULL,
    duration_minutes integer NOT NULL,
    cards_reviewed integer NOT NULL,
    correct_reviews integer NOT NULL,
    average_response_time double precision NOT NULL,
    cultural_context json
);


ALTER TABLE public.fsrs_study_sessions OWNER TO postgres;

--
-- Name: fsrs_subject_stats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fsrs_subject_stats (
    id character varying NOT NULL,
    student_id character varying NOT NULL,
    subject_area public.subjectarea NOT NULL,
    total_cards integer NOT NULL,
    mature_cards integer NOT NULL,
    average_stability double precision NOT NULL,
    average_difficulty double precision NOT NULL,
    retention_rate double precision NOT NULL,
    last_updated timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.fsrs_subject_stats OWNER TO postgres;

--
-- Name: irt_calibration_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.irt_calibration_history (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    calibration_date timestamp with time zone NOT NULL,
    calibration_method character varying(50) NOT NULL,
    sample_size integer NOT NULL,
    old_discrimination double precision,
    old_difficulty double precision,
    old_guessing double precision,
    old_upper_asymptote double precision,
    new_discrimination double precision NOT NULL,
    new_difficulty double precision NOT NULL,
    new_guessing double precision NOT NULL,
    new_upper_asymptote double precision NOT NULL,
    standard_error double precision NOT NULL,
    convergence_iterations integer NOT NULL,
    log_likelihood double precision NOT NULL,
    discrimination_ci_lower double precision NOT NULL,
    discrimination_ci_upper double precision NOT NULL,
    difficulty_ci_lower double precision NOT NULL,
    difficulty_ci_upper double precision NOT NULL,
    CONSTRAINT check_calibration_sample_size CHECK ((sample_size >= 30)),
    CONSTRAINT check_new_difficulty CHECK (((new_difficulty >= ('-3.0'::numeric)::double precision) AND (new_difficulty <= (3.0)::double precision))),
    CONSTRAINT check_new_discrimination CHECK (((new_discrimination >= (0.1)::double precision) AND (new_discrimination <= (3.0)::double precision))),
    CONSTRAINT check_new_guessing CHECK (((new_guessing >= (0.0)::double precision) AND (new_guessing <= (1.0)::double precision))),
    CONSTRAINT check_new_upper_asymptote CHECK (((new_upper_asymptote >= (0.0)::double precision) AND (new_upper_asymptote <= (1.0)::double precision)))
);


ALTER TABLE public.irt_calibration_history OWNER TO postgres;

--
-- Name: kiro2_cat_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.kiro2_cat_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    subject_id text NOT NULL,
    theta_final numeric(6,4) DEFAULT 0.0 NOT NULL,
    se_final numeric(6,4) DEFAULT 1.0 NOT NULL,
    n_questions smallint DEFAULT 0 NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    state text DEFAULT 'active'::text NOT NULL,
    termination_reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT kiro2_cat_sessions_state_check CHECK ((state = ANY (ARRAY['active'::text, 'completed'::text, 'abandoned'::text])))
);


ALTER TABLE public.kiro2_cat_sessions OWNER TO postgres;

--
-- Name: kiro2_learning_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.kiro2_learning_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    question_id text NOT NULL,
    session_id uuid,
    event_type text DEFAULT 'cat_answer'::text NOT NULL,
    is_correct boolean,
    theta_after numeric(6,4),
    response_ms integer,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.kiro2_learning_events OWNER TO postgres;

--
-- Name: kiro2_learning_events_synthetic; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.kiro2_learning_events_synthetic (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    question_id text NOT NULL,
    session_id uuid,
    event_type text DEFAULT 'synthetic_response'::text NOT NULL,
    is_correct boolean,
    theta_after numeric,
    response_ms integer,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.kiro2_learning_events_synthetic OWNER TO postgres;

--
-- Name: knowledge_points; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.knowledge_points (
    id character varying NOT NULL,
    topic_id character varying,
    code character varying(50) NOT NULL,
    name_tr character varying(200) NOT NULL,
    subject character varying(50) NOT NULL,
    prerequisite_ids json,
    difficulty_range json,
    description text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.knowledge_points OWNER TO postgres;

--
-- Name: league_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.league_history (
    id character varying DEFAULT gen_random_uuid() NOT NULL,
    student_id character varying NOT NULL,
    week_start timestamp with time zone NOT NULL,
    from_tier character varying(20) NOT NULL,
    to_tier character varying(20) NOT NULL,
    final_rank integer,
    final_xp integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.league_history OWNER TO postgres;

--
-- Name: league_memberships; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.league_memberships (
    id character varying DEFAULT gen_random_uuid() NOT NULL,
    student_id character varying NOT NULL,
    league_tier character varying(20) DEFAULT 'BRONZE'::character varying NOT NULL,
    weekly_xp integer DEFAULT 0 NOT NULL,
    week_start timestamp with time zone NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    rank integer
);


ALTER TABLE public.league_memberships OWNER TO postgres;

--
-- Name: learning_analytics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.learning_analytics (
    id character varying NOT NULL,
    student_id character varying NOT NULL,
    date date NOT NULL,
    subject_area public.subjectarea NOT NULL,
    questions_attempted integer NOT NULL,
    questions_correct integer NOT NULL,
    average_response_time double precision NOT NULL,
    study_time_minutes integer NOT NULL,
    skill_level double precision NOT NULL,
    improvement_rate double precision NOT NULL,
    difficulty_preference double precision NOT NULL,
    zpd_utilization double precision NOT NULL,
    fsrs_retention_rate double precision NOT NULL,
    morphology_awareness double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.learning_analytics OWNER TO postgres;

--
-- Name: learning_outcomes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.learning_outcomes (
    id character varying(100) NOT NULL,
    code character varying(50) NOT NULL,
    description text NOT NULL,
    subject character varying(50) NOT NULL,
    grade_level character varying(10) NOT NULL,
    cognitive_level character varying(50) NOT NULL,
    bloom_taxonomy character varying(20) NOT NULL,
    meb_standard_id character varying(100) NOT NULL,
    assessment_methods json,
    sample_activities json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.learning_outcomes OWNER TO postgres;

--
-- Name: learning_path_student_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.learning_path_student_profiles (
    student_id character varying(100) NOT NULL,
    user_id character varying(100),
    name character varying(200) NOT NULL,
    grade character varying(20) NOT NULL,
    exam_target character varying(50) NOT NULL,
    learning_style character varying(50) NOT NULL,
    knowledge_level character varying(50) NOT NULL,
    interests json NOT NULL,
    goals json NOT NULL,
    available_time integer NOT NULL,
    target_university character varying(200),
    target_department character varying(200),
    target_ranking character varying(50),
    weekly_study_commitment integer,
    exam_date date,
    vark_visual_score double precision,
    vark_auditory_score double precision,
    vark_reading_score double precision,
    vark_kinesthetic_score double precision,
    felder_active_reflective double precision,
    felder_sensing_intuitive double precision,
    felder_visual_verbal double precision,
    felder_sequential_global double precision,
    overall_progress double precision,
    average_quiz_score double precision,
    total_study_time_minutes integer,
    last_activity_at timestamp without time zone,
    metadata_json json NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    daily_streak integer DEFAULT 0,
    best_streak integer DEFAULT 0,
    last_study_date date
);


ALTER TABLE public.learning_path_student_profiles OWNER TO postgres;

--
-- Name: learning_paths; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.learning_paths (
    path_id character varying(100) NOT NULL,
    student_id character varying(100) NOT NULL,
    subject character varying(100) NOT NULL,
    difficulty_level character varying(50) NOT NULL,
    duration_weeks integer NOT NULL,
    target_date timestamp without time zone,
    modules json NOT NULL,
    phases json NOT NULL,
    resources json NOT NULL,
    ai_generated boolean NOT NULL,
    reasoning text,
    agent_metadata json NOT NULL,
    total_modules integer NOT NULL,
    completed_modules integer NOT NULL,
    total_topics integer NOT NULL,
    completed_topics integer NOT NULL,
    overall_progress double precision NOT NULL,
    total_time integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    CONSTRAINT check_progress_range CHECK (((overall_progress >= (0)::double precision) AND (overall_progress <= (100)::double precision)))
);


ALTER TABLE public.learning_paths OWNER TO postgres;

--
-- Name: learning_progress_daily; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.learning_progress_daily (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id character varying(255) NOT NULL,
    log_date date DEFAULT CURRENT_DATE NOT NULL,
    subject character varying(50) NOT NULL,
    minutes_spent integer DEFAULT 0 NOT NULL,
    questions_done integer DEFAULT 0 NOT NULL,
    correct_count integer DEFAULT 0 NOT NULL,
    activity_type character varying(30) DEFAULT 'cat'::character varying NOT NULL,
    theta_before double precision,
    theta_after double precision,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT learning_progress_daily_activity_type_check CHECK (((activity_type)::text = ANY ((ARRAY['cat'::character varying, 'fsrs_review'::character varying, 'practice'::character varying, 'placement'::character varying])::text[])))
);


ALTER TABLE public.learning_progress_daily OWNER TO postgres;

--
-- Name: TABLE learning_progress_daily; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.learning_progress_daily IS 'Her gün her ders için tamamlama kaydı';


--
-- Name: manipulative_activities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.manipulative_activities (
    id integer NOT NULL,
    user_id character varying NOT NULL,
    manipulative_type character varying(50) NOT NULL,
    activity_type character varying(50),
    duration_seconds integer,
    completed boolean,
    attempts integer,
    details json,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.manipulative_activities OWNER TO postgres;

--
-- Name: manipulative_activities_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.manipulative_activities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.manipulative_activities_id_seq OWNER TO postgres;

--
-- Name: manipulative_activities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.manipulative_activities_id_seq OWNED BY public.manipulative_activities.id;


--
-- Name: manipulative_progress; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.manipulative_progress (
    id integer NOT NULL,
    user_id character varying NOT NULL,
    manipulative_type character varying(50) NOT NULL,
    activity_type character varying(50),
    operation_count integer,
    completion_count integer,
    total_duration_seconds integer,
    avg_duration_seconds double precision,
    mastery_level double precision,
    activity_data json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_activity_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.manipulative_progress OWNER TO postgres;

--
-- Name: manipulative_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.manipulative_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.manipulative_progress_id_seq OWNER TO postgres;

--
-- Name: manipulative_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.manipulative_progress_id_seq OWNED BY public.manipulative_progress.id;


--
-- Name: meb_curriculum_standards; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.meb_curriculum_standards (
    id character varying(100) NOT NULL,
    subject character varying(50) NOT NULL,
    grade_level character varying(10) NOT NULL,
    unit_name character varying(200) NOT NULL,
    topic_name character varying(200) NOT NULL,
    learning_outcomes json,
    key_concepts json,
    skills json,
    prerequisites json,
    assessment_criteria json,
    duration_hours integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE public.meb_curriculum_standards OWNER TO postgres;

--
-- Name: mentor_feedback; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mentor_feedback (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    session_id character varying NOT NULL,
    giver_id character varying NOT NULL,
    receiver_id character varying NOT NULL,
    rating integer NOT NULL,
    tags text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.mentor_feedback OWNER TO postgres;

--
-- Name: mentor_pairs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mentor_pairs (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    mentor_id character varying NOT NULL,
    mentee_id character varying NOT NULL,
    subject_area character varying(50) NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    session_count integer DEFAULT 0,
    total_xp_mentor integer DEFAULT 0,
    total_xp_mentee integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    ended_at timestamp with time zone
);


ALTER TABLE public.mentor_pairs OWNER TO postgres;

--
-- Name: mentor_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mentor_sessions (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    pair_id character varying NOT NULL,
    question_bank_id character varying,
    topic character varying(100),
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    duration_minutes integer,
    mentor_xp integer DEFAULT 0,
    mentee_xp integer DEFAULT 0,
    started_at timestamp with time zone DEFAULT now(),
    ended_at timestamp with time zone
);


ALTER TABLE public.mentor_sessions OWNER TO postgres;

--
-- Name: message_audit_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.message_audit_log (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    sender_id character varying NOT NULL,
    content_type character varying(30) NOT NULL,
    content_hash character varying(64) NOT NULL,
    content_length integer NOT NULL,
    flagged boolean DEFAULT false,
    flag_reason character varying(20) DEFAULT 'clean'::character varying,
    flag_details jsonb,
    pipeline_ms integer,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.message_audit_log OWNER TO postgres;

--
-- Name: moderation_actions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.moderation_actions (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    moderator_id character varying,
    target_user_id character varying NOT NULL,
    content_id character varying,
    content_type character varying(30),
    action_type character varying(30) NOT NULL,
    reason text NOT NULL,
    report_id character varying,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.moderation_actions OWNER TO postgres;

--
-- Name: questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.questions (
    id character varying NOT NULL,
    question_text text NOT NULL,
    question_image_url character varying(500),
    option_a text NOT NULL,
    option_b text NOT NULL,
    option_c text NOT NULL,
    option_d text NOT NULL,
    option_e text,
    correct_answer character varying(1) NOT NULL,
    explanation text,
    exam_type character varying(6) NOT NULL,
    subject_area character varying(9) NOT NULL,
    topic character varying(200) NOT NULL,
    subtopic character varying(200),
    difficulty character varying(6) NOT NULL,
    irt_difficulty double precision DEFAULT 0.0 NOT NULL,
    irt_discrimination double precision DEFAULT 1.0 NOT NULL,
    irt_guessing double precision DEFAULT 0.2 NOT NULL,
    morphology_complexity double precision DEFAULT 0.5 NOT NULL,
    readability_score double precision DEFAULT 0.5 NOT NULL,
    times_asked integer DEFAULT 0 NOT NULL,
    times_correct integer DEFAULT 0 NOT NULL,
    average_response_time double precision DEFAULT 0.0 NOT NULL,
    created_by character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    aktif boolean DEFAULT true NOT NULL,
    visual_content json,
    irt_upper_asymptote double precision DEFAULT 1.0,
    irt_calibrated boolean DEFAULT false,
    irt_sample_size integer DEFAULT 0,
    source_book character varying(300),
    source_page integer,
    is_reviewed boolean DEFAULT true,
    CONSTRAINT check_correct_answer CHECK (((correct_answer)::text = ANY ((ARRAY['A'::character varying, 'B'::character varying, 'C'::character varying, 'D'::character varying, 'E'::character varying])::text[]))),
    CONSTRAINT check_irt_difficulty CHECK (((irt_difficulty >= ('-3.0'::numeric)::double precision) AND (irt_difficulty <= (3.0)::double precision))),
    CONSTRAINT check_irt_discrimination CHECK (((irt_discrimination >= (0.1)::double precision) AND (irt_discrimination <= (3.0)::double precision))),
    CONSTRAINT check_irt_guessing CHECK (((irt_guessing >= (0.0)::double precision) AND (irt_guessing <= (1.0)::double precision))),
    CONSTRAINT check_positive_stats CHECK (((times_asked >= 0) AND (times_correct >= 0) AND (times_correct <= times_asked)))
);


ALTER TABLE public.questions OWNER TO postgres;

--
-- Name: mv_daily_question_stats; Type: MATERIALIZED VIEW; Schema: public; Owner: postgres
--

CREATE MATERIALIZED VIEW public.mv_daily_question_stats AS
 SELECT date_trunc('day'::text, created_at) AS day,
    exam_type,
    subject_area,
    count(*) AS question_count,
    avg(irt_difficulty) AS avg_difficulty
   FROM public.questions
  GROUP BY (date_trunc('day'::text, created_at)), exam_type, subject_area
  WITH NO DATA;


ALTER MATERIALIZED VIEW public.mv_daily_question_stats OWNER TO postgres;

--
-- Name: nano_skills; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.nano_skills (
    id character varying NOT NULL,
    knowledge_point_id character varying NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    subject character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.nano_skills OWNER TO postgres;

--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    title character varying(200) NOT NULL,
    message text NOT NULL,
    notification_type character varying(20) NOT NULL,
    action_url character varying(500),
    is_read boolean NOT NULL,
    read_at timestamp with time zone,
    created_at timestamp without time zone NOT NULL,
    priority integer NOT NULL,
    expires_at timestamp with time zone
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: COLUMN notifications.priority; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.notifications.priority IS 'Higher = more important';


--
-- Name: COLUMN notifications.expires_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.notifications.expires_at IS 'Auto-delete after this date';


--
-- Name: oba_challenge_progress; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.oba_challenge_progress (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    challenge_id character varying NOT NULL,
    student_id character varying NOT NULL,
    contribution integer DEFAULT 0,
    contribution_ratio double precision DEFAULT 0.0,
    xp_earned integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.oba_challenge_progress OWNER TO postgres;

--
-- Name: oba_challenges; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.oba_challenges (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    oba_id character varying NOT NULL,
    title character varying(200) NOT NULL,
    description character varying(500),
    challenge_type character varying(30) DEFAULT 'solve_questions'::character varying NOT NULL,
    target_value integer NOT NULL,
    current_value integer DEFAULT 0,
    bonus_xp_per_member integer DEFAULT 50,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    completed boolean DEFAULT false,
    start_date date NOT NULL,
    end_date date NOT NULL,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.oba_challenges OWNER TO postgres;

--
-- Name: oba_uyeler; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.oba_uyeler (
    id integer NOT NULL,
    oba_id integer NOT NULL,
    user_id character varying NOT NULL,
    role character varying(10) DEFAULT 'toycu'::character varying NOT NULL,
    joined_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.oba_uyeler OWNER TO postgres;

--
-- Name: oba_uyeler_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.oba_uyeler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.oba_uyeler_id_seq OWNER TO postgres;

--
-- Name: oba_uyeler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.oba_uyeler_id_seq OWNED BY public.oba_uyeler.id;


--
-- Name: obalar; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.obalar (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    xp_pool integer DEFAULT 0 NOT NULL,
    max_members integer DEFAULT 20 NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.obalar OWNER TO postgres;

--
-- Name: obalar_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.obalar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.obalar_id_seq OWNER TO postgres;

--
-- Name: obalar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.obalar_id_seq OWNED BY public.obalar.id;


--
-- Name: osym_standards; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.osym_standards (
    id character varying(100) NOT NULL,
    exam_type character varying(20) NOT NULL,
    subject character varying(50) NOT NULL,
    topic_code character varying(50) NOT NULL,
    topic_name character varying(200) NOT NULL,
    priority_level integer NOT NULL,
    question_count_range json,
    difficulty_distribution json,
    cognitive_levels json,
    exam_frequency double precision NOT NULL,
    last_exam_appearance character varying(50),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE public.osym_standards OWNER TO postgres;

--
-- Name: parent_approvals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parent_approvals (
    id character varying NOT NULL,
    student_user_id character varying NOT NULL,
    parent_user_id character varying NOT NULL,
    request_type character varying(100) NOT NULL,
    request_description text NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    responded_at timestamp with time zone,
    parent_note text
);


ALTER TABLE public.parent_approvals OWNER TO postgres;

--
-- Name: COLUMN parent_approvals.request_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.parent_approvals.request_type IS 'ekstra_ders_izni, sinav_kayit, ozel_egitim';


--
-- Name: COLUMN parent_approvals.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.parent_approvals.status IS 'beklemede, onaylandi, reddedildi';


--
-- Name: parent_child; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parent_child (
    id integer NOT NULL,
    parent_id character varying NOT NULL,
    child_id character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    approved boolean DEFAULT false NOT NULL,
    relation_type character varying(50) DEFAULT 'parent'::character varying,
    approved_at timestamp with time zone
);


ALTER TABLE public.parent_child OWNER TO postgres;

--
-- Name: parent_child_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.parent_child_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.parent_child_id_seq OWNER TO postgres;

--
-- Name: parent_child_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.parent_child_id_seq OWNED BY public.parent_child.id;


--
-- Name: parent_notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parent_notifications (
    id integer NOT NULL,
    parent_id character varying NOT NULL,
    child_id character varying,
    title character varying(200) NOT NULL,
    message text,
    notification_type character varying(50) DEFAULT 'general'::character varying NOT NULL,
    is_read boolean DEFAULT false NOT NULL,
    read_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.parent_notifications OWNER TO postgres;

--
-- Name: parent_notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.parent_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.parent_notifications_id_seq OWNER TO postgres;

--
-- Name: parent_notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.parent_notifications_id_seq OWNED BY public.parent_notifications.id;


--
-- Name: parent_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parent_profiles (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    children_ids json,
    email_notifications boolean NOT NULL,
    sms_notifications boolean NOT NULL,
    weekly_reports boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.parent_profiles OWNER TO postgres;

--
-- Name: parent_reports; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parent_reports (
    id character varying NOT NULL,
    parent_user_id character varying NOT NULL,
    student_user_id character varying NOT NULL,
    student_name character varying(200) NOT NULL,
    report_period character varying(50) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    total_study_minutes integer NOT NULL,
    completed_exams_count integer NOT NULL,
    average_success_rate double precision NOT NULL,
    strong_subjects json NOT NULL,
    weak_subjects json NOT NULL,
    weekly_progress_description text,
    parent_recommendations json NOT NULL,
    support_areas json NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    is_read boolean NOT NULL
);


ALTER TABLE public.parent_reports OWNER TO postgres;

--
-- Name: COLUMN parent_reports.report_period; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.parent_reports.report_period IS 'e.g., 2025-W47';


--
-- Name: COLUMN parent_reports.average_success_rate; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.parent_reports.average_success_rate IS '0-100';


--
-- Name: parent_social_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parent_social_settings (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    parent_id character varying NOT NULL,
    student_id character varying NOT NULL,
    social_enabled boolean DEFAULT true,
    chat_enabled boolean DEFAULT true,
    study_rooms_enabled boolean DEFAULT true,
    duels_enabled boolean DEFAULT true,
    forum_enabled boolean DEFAULT true,
    notifications_enabled boolean DEFAULT true,
    visibility_level character varying(20) DEFAULT 'full'::character varying,
    max_daily_messages integer DEFAULT 200,
    allowed_hours_start integer DEFAULT 6,
    allowed_hours_end integer DEFAULT 23,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.parent_social_settings OWNER TO postgres;

--
-- Name: peer_recommendations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.peer_recommendations (
    id character varying NOT NULL,
    cluster_id character varying NOT NULL,
    source_topic character varying(200) NOT NULL,
    target_topic character varying(200) NOT NULL,
    improvement_rate double precision DEFAULT '0'::double precision,
    sample_size integer DEFAULT 0,
    description text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.peer_recommendations OWNER TO postgres;

--
-- Name: platform_stats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.platform_stats (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    stat_date date DEFAULT CURRENT_DATE NOT NULL,
    total_users integer DEFAULT 0,
    active_users integer DEFAULT 0,
    total_questions integer DEFAULT 0,
    total_exams integer DEFAULT 0,
    avg_exam_score double precision DEFAULT 0.0,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.platform_stats OWNER TO postgres;

--
-- Name: point_transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.point_transactions (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    points integer NOT NULL,
    reason character varying(255) NOT NULL,
    meta_data json,
    "timestamp" timestamp without time zone NOT NULL
);


ALTER TABLE public.point_transactions OWNER TO postgres;

--
-- Name: pomodoro_participants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pomodoro_participants (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    room_id character varying NOT NULL,
    student_id character varying NOT NULL,
    status character varying(20) DEFAULT 'joined'::character varying NOT NULL,
    rounds_completed integer DEFAULT 0,
    total_work_minutes integer DEFAULT 0,
    xp_earned integer DEFAULT 0,
    joined_at timestamp with time zone DEFAULT now(),
    left_at timestamp with time zone
);


ALTER TABLE public.pomodoro_participants OWNER TO postgres;

--
-- Name: pomodoro_rooms; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pomodoro_rooms (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    subject_area character varying(50) NOT NULL,
    topic character varying(100),
    status character varying(20) DEFAULT 'waiting'::character varying NOT NULL,
    max_participants integer DEFAULT 4,
    current_participants integer DEFAULT 0,
    work_minutes integer DEFAULT 25,
    break_minutes integer DEFAULT 5,
    total_rounds integer DEFAULT 4,
    current_round integer DEFAULT 0,
    started_at timestamp with time zone,
    ended_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.pomodoro_rooms OWNER TO postgres;

--
-- Name: q_matrix; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.q_matrix (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    nano_skill_id character varying NOT NULL,
    is_required boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.q_matrix OWNER TO postgres;

--
-- Name: quality_gate_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.quality_gate_results (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    run_id uuid NOT NULL,
    gate_name character varying(100) NOT NULL,
    status character varying(20) NOT NULL,
    score double precision NOT NULL,
    threshold double precision NOT NULL,
    blocking boolean DEFAULT true,
    message text NOT NULL,
    issues_count integer DEFAULT 0,
    auto_fixed boolean DEFAULT false,
    issues jsonb,
    metrics jsonb,
    details jsonb,
    execution_time_ms double precision NOT NULL,
    retries integer DEFAULT 0,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.quality_gate_results OWNER TO postgres;

--
-- Name: COLUMN quality_gate_results.run_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.run_id IS 'Parent pipeline run ID';


--
-- Name: COLUMN quality_gate_results.gate_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.gate_name IS 'Gate identifier';


--
-- Name: COLUMN quality_gate_results.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.status IS 'Gate status: pass, warning, fail, skipped, timeout, error';


--
-- Name: COLUMN quality_gate_results.score; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.score IS 'Gate score 0-10';


--
-- Name: COLUMN quality_gate_results.threshold; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.threshold IS 'Pass threshold';


--
-- Name: COLUMN quality_gate_results.blocking; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.blocking IS 'Whether this is a blocking gate';


--
-- Name: COLUMN quality_gate_results.message; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.message IS 'Result summary message';


--
-- Name: COLUMN quality_gate_results.issues_count; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.issues_count IS 'Number of issues found';


--
-- Name: COLUMN quality_gate_results.auto_fixed; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.auto_fixed IS 'Whether issues were auto-fixed';


--
-- Name: COLUMN quality_gate_results.issues; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.issues IS 'List of issues with file, line, severity';


--
-- Name: COLUMN quality_gate_results.metrics; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.metrics IS 'Gate-specific metrics';


--
-- Name: COLUMN quality_gate_results.details; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.details IS 'Additional details';


--
-- Name: COLUMN quality_gate_results.execution_time_ms; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.execution_time_ms IS 'Gate execution time in milliseconds';


--
-- Name: COLUMN quality_gate_results.retries; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.retries IS 'Number of retry attempts';


--
-- Name: COLUMN quality_gate_results.started_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.started_at IS 'Gate start time';


--
-- Name: COLUMN quality_gate_results.completed_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.completed_at IS 'Gate completion time';


--
-- Name: COLUMN quality_gate_results.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gate_results.created_at IS 'Record creation time';


--
-- Name: quality_gates_override_audit; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.quality_gates_override_audit (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    gate_name character varying(100) NOT NULL,
    run_id uuid,
    requestor character varying(255) NOT NULL,
    reason text NOT NULL,
    ticket_id character varying(100),
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    approver character varying(255),
    approver_comments text,
    approved_at timestamp with time zone,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.quality_gates_override_audit OWNER TO postgres;

--
-- Name: COLUMN quality_gates_override_audit.gate_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.gate_name IS 'Gate being overridden';


--
-- Name: COLUMN quality_gates_override_audit.run_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.run_id IS 'Related pipeline run ID';


--
-- Name: COLUMN quality_gates_override_audit.requestor; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.requestor IS 'Who requested the override';


--
-- Name: COLUMN quality_gates_override_audit.reason; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.reason IS 'Justification for override';


--
-- Name: COLUMN quality_gates_override_audit.ticket_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.ticket_id IS 'Related ticket/issue ID';


--
-- Name: COLUMN quality_gates_override_audit.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.status IS 'Override status: pending, approved, denied, expired';


--
-- Name: COLUMN quality_gates_override_audit.approver; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.approver IS 'Who approved/denied';


--
-- Name: COLUMN quality_gates_override_audit.approver_comments; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.approver_comments IS 'Approver comments';


--
-- Name: COLUMN quality_gates_override_audit.approved_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.approved_at IS 'Approval timestamp';


--
-- Name: COLUMN quality_gates_override_audit.expires_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.expires_at IS 'Override expiration time';


--
-- Name: COLUMN quality_gates_override_audit.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.created_at IS 'Record creation time';


--
-- Name: COLUMN quality_gates_override_audit.updated_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_override_audit.updated_at IS 'Last update time';


--
-- Name: quality_gates_runs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.quality_gates_runs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    pipeline_name character varying(100) NOT NULL,
    status character varying(20) NOT NULL,
    total_score double precision NOT NULL,
    passed_gates integer DEFAULT 0,
    failed_gates integer DEFAULT 0,
    skipped_gates integer DEFAULT 0,
    total_execution_time_ms double precision NOT NULL,
    parallel_execution_used boolean DEFAULT false,
    fail_fast_mode boolean DEFAULT false,
    commit_hash character varying(40),
    branch character varying(200),
    repository character varying(500),
    triggered_by character varying(255),
    trigger_type character varying(50),
    overridden boolean DEFAULT false,
    override_reason text,
    override_approver character varying(255),
    config_snapshot jsonb,
    started_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.quality_gates_runs OWNER TO postgres;

--
-- Name: COLUMN quality_gates_runs.pipeline_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.pipeline_name IS 'Pipeline identifier';


--
-- Name: COLUMN quality_gates_runs.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.status IS 'Overall status: pass, warning, fail, error';


--
-- Name: COLUMN quality_gates_runs.total_score; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.total_score IS 'Weighted average score 0-10';


--
-- Name: COLUMN quality_gates_runs.passed_gates; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.passed_gates IS 'Number of passed gates';


--
-- Name: COLUMN quality_gates_runs.failed_gates; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.failed_gates IS 'Number of failed gates';


--
-- Name: COLUMN quality_gates_runs.skipped_gates; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.skipped_gates IS 'Number of skipped gates';


--
-- Name: COLUMN quality_gates_runs.total_execution_time_ms; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.total_execution_time_ms IS 'Total execution time in milliseconds';


--
-- Name: COLUMN quality_gates_runs.parallel_execution_used; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.parallel_execution_used IS 'Whether parallel execution was used';


--
-- Name: COLUMN quality_gates_runs.fail_fast_mode; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.fail_fast_mode IS 'Whether fail-fast mode was enabled';


--
-- Name: COLUMN quality_gates_runs.commit_hash; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.commit_hash IS 'Git commit hash';


--
-- Name: COLUMN quality_gates_runs.branch; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.branch IS 'Git branch name';


--
-- Name: COLUMN quality_gates_runs.repository; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.repository IS 'Repository identifier';


--
-- Name: COLUMN quality_gates_runs.triggered_by; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.triggered_by IS 'User/system that triggered the run';


--
-- Name: COLUMN quality_gates_runs.trigger_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.trigger_type IS 'Trigger type: manual, push, pr, schedule';


--
-- Name: COLUMN quality_gates_runs.overridden; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.overridden IS 'Whether result was overridden';


--
-- Name: COLUMN quality_gates_runs.override_reason; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.override_reason IS 'Override justification';


--
-- Name: COLUMN quality_gates_runs.override_approver; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.override_approver IS 'Who approved the override';


--
-- Name: COLUMN quality_gates_runs.config_snapshot; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.config_snapshot IS 'Pipeline configuration at time of run';


--
-- Name: COLUMN quality_gates_runs.started_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.started_at IS 'Pipeline start time';


--
-- Name: COLUMN quality_gates_runs.completed_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.completed_at IS 'Pipeline completion time';


--
-- Name: COLUMN quality_gates_runs.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quality_gates_runs.created_at IS 'Record creation time';


--
-- Name: question_bank; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.question_bank (
    id character varying NOT NULL,
    question_text text NOT NULL,
    question_html text,
    question_latex text,
    question_image_url character varying(500),
    question_audio_url character varying(500),
    option_a text NOT NULL,
    option_b text NOT NULL,
    option_c text NOT NULL,
    option_d text NOT NULL,
    option_e text,
    correct_answer character varying(1) NOT NULL,
    explanation text,
    explanation_video_url character varying(500),
    alternative_solutions json,
    primary_topic_id character varying NOT NULL,
    secondary_topics json,
    bloom_level integer NOT NULL,
    bloom_category character varying(50) NOT NULL,
    difficulty_level public.questiondifficultylevel NOT NULL,
    irt_based_difficulty character varying(20) NOT NULL,
    student_success_rate double precision NOT NULL,
    last_difficulty_update timestamp with time zone,
    difficulty_update_count integer NOT NULL,
    irt_discrimination double precision NOT NULL,
    irt_difficulty double precision NOT NULL,
    irt_guessing double precision NOT NULL,
    irt_upper_asymptote double precision NOT NULL,
    is_calibrated boolean NOT NULL,
    calibration_sample_size integer NOT NULL,
    last_calibration_date timestamp with time zone,
    calibration_quality_score double precision NOT NULL,
    morphology_complexity double precision NOT NULL,
    word_count integer NOT NULL,
    unique_word_count integer NOT NULL,
    average_word_length double precision NOT NULL,
    readability_score double precision NOT NULL,
    times_asked integer NOT NULL,
    times_correct integer NOT NULL,
    times_wrong integer NOT NULL,
    times_skipped integer NOT NULL,
    average_response_time double precision NOT NULL,
    median_response_time double precision NOT NULL,
    exposure_rate double precision NOT NULL,
    last_used_date timestamp with time zone,
    exam_type character varying(20) NOT NULL,
    subject_area character varying(50) NOT NULL,
    grade_level integer NOT NULL,
    osym_format_compliant boolean NOT NULL,
    osym_year integer,
    quality_score double precision NOT NULL,
    quality_review_status character varying(20) NOT NULL,
    source_book character varying(300),
    source_page integer,
    pipeline_metadata json,
    created_by character varying,
    reviewed_by character varying,
    is_active boolean NOT NULL,
    is_public boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    embedding public.vector(768),
    image_ocr_text text,
    image_width integer,
    image_height integer,
    irt_a numeric(6,4),
    irt_b numeric(6,4),
    irt_c numeric(5,4),
    irt_calibrated boolean DEFAULT false,
    irt_method text,
    irt_calibrated_at timestamp with time zone,
    irt_n_responses integer DEFAULT 0,
    is_calib_pool boolean DEFAULT false NOT NULL,
    CONSTRAINT check_bloom_level CHECK (((bloom_level >= 1) AND (bloom_level <= 6))),
    CONSTRAINT check_correct_answer_bank CHECK (((correct_answer)::text = ANY ((ARRAY['A'::character varying, 'B'::character varying, 'C'::character varying, 'D'::character varying, 'E'::character varying])::text[]))),
    CONSTRAINT check_exposure_rate CHECK (((exposure_rate >= (0.0)::double precision) AND (exposure_rate <= (1.0)::double precision))),
    CONSTRAINT check_grade_level_bank CHECK (((grade_level >= 9) AND (grade_level <= 12))),
    CONSTRAINT check_irt_difficulty_bank CHECK (((irt_difficulty >= ('-3.0'::numeric)::double precision) AND (irt_difficulty <= (3.0)::double precision))),
    CONSTRAINT check_irt_discrimination_bank CHECK (((irt_discrimination >= (0.1)::double precision) AND (irt_discrimination <= (3.0)::double precision))),
    CONSTRAINT check_irt_guessing_bank CHECK (((irt_guessing >= (0.0)::double precision) AND (irt_guessing <= (1.0)::double precision))),
    CONSTRAINT check_irt_upper_asymptote_bank CHECK (((irt_upper_asymptote >= (0.0)::double precision) AND (irt_upper_asymptote <= (1.0)::double precision))),
    CONSTRAINT check_quality_score CHECK (((quality_score >= (0.0)::double precision) AND (quality_score <= (100.0)::double precision))),
    CONSTRAINT check_success_rate CHECK (((student_success_rate >= (0.0)::double precision) AND (student_success_rate <= (1.0)::double precision)))
);


ALTER TABLE public.question_bank OWNER TO postgres;

--
-- Name: question_knowledge_mappings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.question_knowledge_mappings (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    knowledge_point_id character varying NOT NULL,
    is_primary boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.question_knowledge_mappings OWNER TO postgres;

--
-- Name: question_performance_analytics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.question_performance_analytics (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    analysis_date timestamp with time zone NOT NULL,
    period_type character varying(20) NOT NULL,
    attempts integer NOT NULL,
    correct_count integer NOT NULL,
    wrong_count integer NOT NULL,
    skipped_count integer NOT NULL,
    success_rate double precision NOT NULL,
    average_response_time double precision NOT NULL,
    high_ability_success_rate double precision CONSTRAINT question_performance_analyti_high_ability_success_rate_not_null NOT NULL,
    medium_ability_success_rate double precision CONSTRAINT question_performance_analyt_medium_ability_success_rat_not_null NOT NULL,
    low_ability_success_rate double precision CONSTRAINT question_performance_analytic_low_ability_success_rate_not_null NOT NULL
);


ALTER TABLE public.question_performance_analytics OWNER TO postgres;

--
-- Name: question_tag_associations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.question_tag_associations (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    tag_id character varying NOT NULL,
    weight double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.question_tag_associations OWNER TO postgres;

--
-- Name: question_tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.question_tags (
    id character varying NOT NULL,
    tag_name character varying(100) NOT NULL,
    tag_category character varying(50) NOT NULL,
    description text,
    usage_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.question_tags OWNER TO postgres;

--
-- Name: quiz_questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.quiz_questions (
    id integer NOT NULL,
    quiz_id character varying(100) NOT NULL,
    question_id character varying NOT NULL,
    order_number integer NOT NULL,
    points double precision NOT NULL
);


ALTER TABLE public.quiz_questions OWNER TO postgres;

--
-- Name: quiz_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.quiz_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.quiz_questions_id_seq OWNER TO postgres;

--
-- Name: quiz_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.quiz_questions_id_seq OWNED BY public.quiz_questions.id;


--
-- Name: quiz_submissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.quiz_submissions (
    id integer NOT NULL,
    student_id character varying(100) NOT NULL,
    quiz_id character varying(100) NOT NULL,
    question_count integer NOT NULL,
    passing_score double precision NOT NULL,
    score double precision NOT NULL,
    correct_count integer NOT NULL,
    passed boolean NOT NULL,
    answers json NOT NULL,
    total_time_seconds integer NOT NULL,
    submitted_at timestamp without time zone NOT NULL,
    CONSTRAINT check_quiz_score_range CHECK (((score >= (0)::double precision) AND (score <= (100)::double precision)))
);


ALTER TABLE public.quiz_submissions OWNER TO postgres;

--
-- Name: quiz_submissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.quiz_submissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.quiz_submissions_id_seq OWNER TO postgres;

--
-- Name: quiz_submissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.quiz_submissions_id_seq OWNED BY public.quiz_submissions.id;


--
-- Name: quizzes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.quizzes (
    id character varying(100) NOT NULL,
    title character varying(500) NOT NULL,
    description text,
    subject character varying(100) NOT NULL,
    topic character varying(200),
    time_limit_minutes integer,
    passing_score double precision NOT NULL,
    shuffle_questions boolean NOT NULL,
    show_answers_after boolean NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.quizzes OWNER TO postgres;

--
-- Name: realm_progress; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.realm_progress (
    id integer NOT NULL,
    student_id character varying NOT NULL,
    realm_id integer NOT NULL,
    bkt_score numeric(5,4) DEFAULT 0.0 NOT NULL,
    quest_stop integer DEFAULT 0 NOT NULL,
    xp_earned integer DEFAULT 0 NOT NULL,
    completed_at timestamp with time zone,
    unlocked_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.realm_progress OWNER TO postgres;

--
-- Name: realm_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.realm_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.realm_progress_id_seq OWNER TO postgres;

--
-- Name: realm_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.realm_progress_id_seq OWNED BY public.realm_progress.id;


--
-- Name: realms; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.realms (
    id integer NOT NULL,
    slug character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    era character varying(150),
    npc_name character varying(100),
    npc_title character varying(100),
    tech_stack jsonb,
    color_primary character varying(7),
    color_secondary character varying(7),
    order_index integer,
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE public.realms OWNER TO postgres;

--
-- Name: realms_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.realms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.realms_id_seq OWNER TO postgres;

--
-- Name: realms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.realms_id_seq OWNED BY public.realms.id;


--
-- Name: refresh_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.refresh_tokens (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    token_hash character varying(255) NOT NULL,
    jti character varying(255) NOT NULL,
    device_id character varying(255),
    device_name character varying(200),
    device_type character varying(50),
    ip_address character varying(45),
    user_agent character varying(500),
    expires_at timestamp with time zone NOT NULL,
    revoked boolean NOT NULL,
    revoked_at timestamp with time zone,
    revoke_reason character varying(200),
    last_used_at timestamp with time zone,
    usage_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.refresh_tokens OWNER TO postgres;

--
-- Name: sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sessions (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    token character varying(64) NOT NULL,
    device_info json,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    last_activity_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE public.sessions OWNER TO postgres;

--
-- Name: COLUMN sessions.device_info; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.sessions.device_info IS 'Device/browser info';


--
-- Name: solution_duel_submissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solution_duel_submissions (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    duel_id character varying NOT NULL,
    student_id character varying NOT NULL,
    body text NOT NULL,
    image_url character varying(500),
    vote_count integer DEFAULT 0,
    flagged boolean DEFAULT false,
    submitted_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.solution_duel_submissions OWNER TO postgres;

--
-- Name: solution_duel_votes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solution_duel_votes (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    duel_id character varying NOT NULL,
    voter_id character varying NOT NULL,
    voted_for_id character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.solution_duel_votes OWNER TO postgres;

--
-- Name: solution_duels; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solution_duels (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    question_bank_id character varying NOT NULL,
    subject_area character varying(50) NOT NULL,
    challenger_id character varying NOT NULL,
    opponent_id character varying,
    status character varying(20) DEFAULT 'waiting'::character varying NOT NULL,
    solve_time_seconds integer DEFAULT 300,
    voting_ends_at timestamp with time zone,
    winner_id character varying,
    winner_xp integer DEFAULT 30,
    loser_xp integer DEFAULT 10,
    started_at timestamp with time zone,
    ended_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.solution_duels OWNER TO postgres;

--
-- Name: streak_daily_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.streak_daily_log (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    pair_id character varying NOT NULL,
    student_id character varying NOT NULL,
    log_date date NOT NULL,
    completed boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.streak_daily_log OWNER TO postgres;

--
-- Name: streak_pairs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.streak_pairs (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    student_a_id character varying NOT NULL,
    student_b_id character varying NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    current_streak integer DEFAULT 0,
    max_streak integer DEFAULT 0,
    total_xp_earned integer DEFAULT 0,
    started_at timestamp with time zone DEFAULT now(),
    broken_at timestamp with time zone
);


ALTER TABLE public.streak_pairs OWNER TO postgres;

--
-- Name: streak_tracking; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.streak_tracking (
    id character varying DEFAULT gen_random_uuid() NOT NULL,
    student_id character varying NOT NULL,
    current_streak integer DEFAULT 0,
    best_streak integer DEFAULT 0,
    last_activity_date date,
    total_active_days integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    user_id character varying,
    last_correct_answer timestamp without time zone,
    milestones_reached json,
    streak_start_date date
);


ALTER TABLE public.streak_tracking OWNER TO postgres;

--
-- Name: streaks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.streaks (
    user_id character varying NOT NULL,
    current_streak integer DEFAULT 0 NOT NULL,
    largest_streak integer DEFAULT 0 NOT NULL,
    freeze_count integer DEFAULT 2 NOT NULL,
    last_activity date,
    total_days_active integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.streaks OWNER TO postgres;

--
-- Name: student_abilities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student_abilities (
    student_id character varying NOT NULL,
    subject_id integer NOT NULL,
    theta numeric(6,4) DEFAULT 0.0 NOT NULL,
    theta_se numeric(6,4) DEFAULT 1.0 NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.student_abilities OWNER TO postgres;

--
-- Name: student_answers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student_answers (
    id character varying NOT NULL,
    exam_session_id character varying NOT NULL,
    question_id character varying NOT NULL,
    selected_answer character varying(1),
    is_correct boolean,
    response_time_seconds double precision NOT NULL,
    answer_changes integer NOT NULL,
    time_to_first_answer double precision NOT NULL,
    confidence_level double precision,
    answered_at timestamp with time zone DEFAULT now() NOT NULL,
    error_type character varying(20),
    CONSTRAINT check_error_type CHECK (((error_type IS NULL) OR ((error_type)::text = ANY ((ARRAY['concept'::character varying, 'procedural'::character varying, 'careless'::character varying, 'knowledge_gap'::character varying])::text[])))),
    CONSTRAINT check_response_time CHECK (((response_time_seconds >= (0)::double precision) AND (response_time_seconds <= (7200)::double precision))),
    CONSTRAINT check_selected_answer CHECK (((selected_answer IS NULL) OR ((selected_answer)::text = ANY ((ARRAY['A'::character varying, 'B'::character varying, 'C'::character varying, 'D'::character varying, 'E'::character varying])::text[]))))
);


ALTER TABLE public.student_answers OWNER TO postgres;

--
-- Name: student_engagement_signals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student_engagement_signals (
    id character varying DEFAULT gen_random_uuid() NOT NULL,
    student_id character varying NOT NULL,
    signal_type character varying(50) NOT NULL,
    signal_value double precision,
    metadata json,
    created_at timestamp without time zone DEFAULT now(),
    recorded_at timestamp without time zone,
    value double precision
);


ALTER TABLE public.student_engagement_signals OWNER TO postgres;

--
-- Name: student_goals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student_goals (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    goal_type character varying(20) NOT NULL,
    target_value double precision NOT NULL,
    current_value double precision,
    start_date timestamp without time zone NOT NULL,
    end_date timestamp without time zone NOT NULL,
    status character varying(20),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    completed_at timestamp with time zone
);


ALTER TABLE public.student_goals OWNER TO postgres;

--
-- Name: TABLE student_goals; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.student_goals IS 'Öğrencinin sınav tipi, tarihi ve günlük çalışma hedefi';


--
-- Name: student_grades; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student_grades (
    id character varying NOT NULL,
    teacher_user_id character varying NOT NULL,
    student_user_id character varying NOT NULL,
    subject character varying(100) NOT NULL,
    grade_type character varying(50) NOT NULL,
    grade_value double precision NOT NULL,
    max_grade double precision NOT NULL,
    weight double precision NOT NULL,
    notes text,
    graded_at timestamp with time zone DEFAULT now() NOT NULL,
    academic_year character varying(20) NOT NULL,
    semester integer NOT NULL
);


ALTER TABLE public.student_grades OWNER TO postgres;

--
-- Name: COLUMN student_grades.subject; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.student_grades.subject IS 'Matematik, Türkçe, etc.';


--
-- Name: COLUMN student_grades.grade_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.student_grades.grade_type IS 'yazili, sözlü, proje, performans';


--
-- Name: COLUMN student_grades.grade_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.student_grades.grade_value IS '0-100 or other scale';


--
-- Name: COLUMN student_grades.weight; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.student_grades.weight IS 'Weight in final grade calculation';


--
-- Name: COLUMN student_grades.academic_year; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.student_grades.academic_year IS '2024-2025';


--
-- Name: COLUMN student_grades.semester; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.student_grades.semester IS '1 or 2';


--
-- Name: student_knowledge_states; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student_knowledge_states (
    id character varying NOT NULL,
    student_id character varying NOT NULL,
    knowledge_point_id character varying NOT NULL,
    mastery_level double precision DEFAULT '0'::double precision,
    confidence double precision DEFAULT '0'::double precision,
    response_count integer DEFAULT 0,
    last_assessed timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.student_knowledge_states OWNER TO postgres;

--
-- Name: student_learning_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student_learning_profiles (
    id character varying NOT NULL,
    student_id character varying NOT NULL,
    vark_visual double precision NOT NULL,
    vark_auditory double precision NOT NULL,
    vark_reading double precision NOT NULL,
    vark_kinesthetic double precision NOT NULL,
    felder_active_reflective double precision NOT NULL,
    felder_sensing_intuitive double precision NOT NULL,
    felder_visual_verbal double precision NOT NULL,
    felder_sequential_global double precision NOT NULL,
    hybrid_code character varying(20) NOT NULL,
    dominant_vark_style character varying(20) NOT NULL,
    dominant_felder_dimension character varying(30) NOT NULL,
    confidence_score double precision NOT NULL,
    profile_description text,
    behavioral_data_snapshot json,
    questionnaire_responses json,
    detected_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.student_learning_profiles OWNER TO postgres;

--
-- Name: student_nano_skill_mastery; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student_nano_skill_mastery (
    id character varying NOT NULL,
    student_id character varying NOT NULL,
    nano_skill_id character varying NOT NULL,
    mastery double precision DEFAULT '0.5'::double precision,
    confidence double precision DEFAULT '0'::double precision,
    response_count integer DEFAULT 0,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.student_nano_skill_mastery OWNER TO postgres;

--
-- Name: student_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student_profiles (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    grade_level integer NOT NULL,
    school_name character varying(200),
    target_university character varying(200),
    target_department character varying(200),
    hedef_sinav character varying(20),
    veli_onay boolean NOT NULL,
    learning_style public.learningstyle,
    study_hours_per_day integer,
    preferred_study_time character varying(50),
    current_level double precision NOT NULL,
    total_study_hours integer NOT NULL,
    total_questions_solved integer NOT NULL,
    correct_answers integer NOT NULL,
    vark_profile json,
    zpd_range json,
    irt_ability double precision NOT NULL,
    fsrs_parameters json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_current_level CHECK (((current_level >= (0.0)::double precision) AND (current_level <= (10.0)::double precision))),
    CONSTRAINT check_grade_level CHECK (((grade_level >= 9) AND (grade_level <= 12)))
);


ALTER TABLE public.student_profiles OWNER TO postgres;

--
-- Name: study_plans; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.study_plans (
    id integer NOT NULL,
    student_id character varying NOT NULL,
    yks_date date NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    total_weeks integer DEFAULT 0,
    target_net double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.study_plans OWNER TO postgres;

--
-- Name: study_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.study_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.study_plans_id_seq OWNER TO postgres;

--
-- Name: study_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.study_plans_id_seq OWNED BY public.study_plans.id;


--
-- Name: subjects; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.subjects (
    id integer NOT NULL,
    name text NOT NULL,
    display_name text,
    exam_type text DEFAULT 'TYT'::text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.subjects OWNER TO postgres;

--
-- Name: subjects_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.subjects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.subjects_id_seq OWNER TO postgres;

--
-- Name: subjects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.subjects_id_seq OWNED BY public.subjects.id;


--
-- Name: system_configurations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.system_configurations (
    id character varying NOT NULL,
    config_key character varying(100) NOT NULL,
    config_value text NOT NULL,
    config_type character varying(50) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.system_configurations OWNER TO postgres;

--
-- Name: teacher_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.teacher_profiles (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    school_name character varying(200) NOT NULL,
    subject_areas json,
    experience_years integer NOT NULL,
    education_level character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.teacher_profiles OWNER TO postgres;

--
-- Name: topic_completions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.topic_completions (
    id integer NOT NULL,
    student_id character varying(100) NOT NULL,
    node_id character varying(100) NOT NULL,
    completed boolean NOT NULL,
    completion_date timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.topic_completions OWNER TO postgres;

--
-- Name: topic_completions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.topic_completions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.topic_completions_id_seq OWNER TO postgres;

--
-- Name: topic_completions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.topic_completions_id_seq OWNED BY public.topic_completions.id;


--
-- Name: topic_hierarchy; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.topic_hierarchy (
    id character varying NOT NULL,
    level integer NOT NULL,
    parent_id character varying,
    code character varying(50) NOT NULL,
    name_tr character varying(200) NOT NULL,
    name_en character varying(200),
    description text,
    meb_code character varying(100),
    meb_kazanim json,
    osym_relevance double precision NOT NULL,
    osym_frequency integer NOT NULL,
    total_questions integer NOT NULL,
    average_difficulty double precision NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    difficulty_level double precision DEFAULT 0.0,
    subject_area character varying(50),
    CONSTRAINT check_osym_relevance CHECK (((osym_relevance >= (0.0)::double precision) AND (osym_relevance <= (1.0)::double precision))),
    CONSTRAINT check_topic_level CHECK (((level >= 1) AND (level <= 5)))
);


ALTER TABLE public.topic_hierarchy OWNER TO postgres;

--
-- Name: topic_prerequisites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.topic_prerequisites (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    topic_id text NOT NULL,
    prereq_id text NOT NULL,
    prereq_type text DEFAULT 'hard'::text NOT NULL,
    strength numeric(3,2) DEFAULT 1.0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT topic_prerequisites_prereq_type_check CHECK ((prereq_type = ANY (ARRAY['hard'::text, 'soft'::text]))),
    CONSTRAINT topic_prerequisites_strength_check CHECK (((strength >= 0.0) AND (strength <= 1.0)))
);


ALTER TABLE public.topic_prerequisites OWNER TO postgres;

--
-- Name: topic_progress; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.topic_progress (
    id integer NOT NULL,
    student_id character varying(100) NOT NULL,
    node_id character varying(100) NOT NULL,
    progress integer NOT NULL,
    time_spent integer NOT NULL,
    completed boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    CONSTRAINT check_progress_percentage CHECK (((progress >= 0) AND (progress <= 100)))
);


ALTER TABLE public.topic_progress OWNER TO postgres;

--
-- Name: topic_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.topic_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.topic_progress_id_seq OWNER TO postgres;

--
-- Name: topic_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.topic_progress_id_seq OWNED BY public.topic_progress.id;


--
-- Name: user_achievements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_achievements (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    achievement_id character varying(100) NOT NULL,
    achievement_type character varying(50) NOT NULL,
    achievement_name character varying(200) NOT NULL,
    achievement_description text,
    progress_current integer NOT NULL,
    progress_target integer NOT NULL,
    progress_percentage integer NOT NULL,
    is_completed boolean NOT NULL,
    completed_at timestamp without time zone,
    reward_xp integer,
    reward_points integer,
    reward_badge_id character varying(100),
    extra_data json,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.user_achievements OWNER TO postgres;

--
-- Name: user_badges; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_badges (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    badge_id character varying(100) NOT NULL,
    earned_at timestamp without time zone NOT NULL,
    auto_awarded boolean
);


ALTER TABLE public.user_badges OWNER TO postgres;

--
-- Name: user_item_fsrs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_item_fsrs (
    user_id uuid NOT NULL,
    question_id text NOT NULL,
    stability numeric(10,4) DEFAULT 1.0 NOT NULL,
    difficulty numeric(4,2) DEFAULT 5.0 NOT NULL,
    due_date timestamp with time zone DEFAULT now() NOT NULL,
    last_review timestamp with time zone,
    scheduled_days integer DEFAULT 0 NOT NULL,
    elapsed_days numeric(8,2) DEFAULT 0.0 NOT NULL,
    state smallint DEFAULT 0 NOT NULL,
    reps smallint DEFAULT 0 NOT NULL,
    lapses smallint DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT user_item_fsrs_state_check CHECK ((state = ANY (ARRAY[0, 1, 2, 3])))
);


ALTER TABLE public.user_item_fsrs OWNER TO postgres;

--
-- Name: user_theta; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_theta (
    user_id character varying(255) NOT NULL,
    subject_area character varying(50) NOT NULL,
    theta_estimate double precision DEFAULT 0.0 NOT NULL,
    theta_se double precision DEFAULT 0.5 NOT NULL,
    response_count integer DEFAULT 0 NOT NULL,
    last_updated timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_theta OWNER TO postgres;

--
-- Name: TABLE user_theta; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.user_theta IS 'IRT θ tahmini — ders bazlı yetenek seviyesi';


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id character varying NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    secret_2fa character varying(32),
    is_2fa_enabled boolean DEFAULT false NOT NULL,
    backup_codes_hashed json,
    is_premium boolean DEFAULT false NOT NULL,
    premium_expires_at timestamp with time zone,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    role public.userrole NOT NULL,
    phone character varying(20),
    birth_date date,
    total_xp integer DEFAULT 0 NOT NULL,
    level integer DEFAULT 1 NOT NULL,
    last_level_up_at timestamp with time zone,
    is_active boolean DEFAULT true NOT NULL,
    is_verified boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_login timestamp with time zone,
    elo_rating integer DEFAULT 1000 NOT NULL,
    is_parent boolean DEFAULT false NOT NULL,
    CONSTRAINT check_birth_date CHECK (((birth_date <= CURRENT_DATE) AND (birth_date >= '1950-01-01'::date)))
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: COLUMN users.secret_2fa; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.users.secret_2fa IS 'TOTP secret key for 2FA';


--
-- Name: COLUMN users.is_2fa_enabled; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.users.is_2fa_enabled IS '2FA enabled status';


--
-- Name: COLUMN users.backup_codes_hashed; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.users.backup_codes_hashed IS 'Hashed backup codes for 2FA recovery';


--
-- Name: COLUMN users.is_premium; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.users.is_premium IS 'Premium subscription status';


--
-- Name: COLUMN users.premium_expires_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.users.premium_expires_at IS 'Premium subscription expiry';


--
-- Name: v_response_log; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_response_log AS
 SELECT (kiro2_learning_events.user_id)::text AS student_id,
    kiro2_learning_events.question_id,
    kiro2_learning_events.is_correct,
    ((kiro2_learning_events.response_ms)::double precision / (1000.0)::double precision) AS response_time_sec,
    kiro2_learning_events.occurred_at AS answered_at,
    'cat'::text AS source
   FROM public.kiro2_learning_events
  WHERE ((kiro2_learning_events.event_type = 'cat_answer'::text) AND (kiro2_learning_events.is_correct IS NOT NULL))
UNION ALL
 SELECT (kiro2_learning_events.user_id)::text AS student_id,
    kiro2_learning_events.question_id,
    kiro2_learning_events.is_correct,
    ((kiro2_learning_events.response_ms)::double precision / (1000.0)::double precision) AS response_time_sec,
    kiro2_learning_events.occurred_at AS answered_at,
    'exam'::text AS source
   FROM public.kiro2_learning_events
  WHERE ((kiro2_learning_events.event_type = 'exam_answer'::text) AND (kiro2_learning_events.is_correct IS NOT NULL))
UNION ALL
 SELECT (kiro2_learning_events.user_id)::text AS student_id,
    kiro2_learning_events.question_id,
    kiro2_learning_events.is_correct,
    ((kiro2_learning_events.response_ms)::double precision / (1000.0)::double precision) AS response_time_sec,
    kiro2_learning_events.occurred_at AS answered_at,
    'synthetic'::text AS source
   FROM public.kiro2_learning_events
  WHERE ((kiro2_learning_events.event_type = 'synthetic_response'::text) AND (kiro2_learning_events.is_correct IS NOT NULL));


ALTER VIEW public.v_response_log OWNER TO postgres;

--
-- Name: v_calibration_candidates; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_calibration_candidates AS
 SELECT question_id,
    count(*) AS n_responses,
    round(avg((is_correct)::integer), 4) AS p_value,
    sum(
        CASE
            WHEN (source = 'cat'::text) THEN 1
            ELSE 0
        END) AS cat_responses,
    sum(
        CASE
            WHEN (source = 'exam'::text) THEN 1
            ELSE 0
        END) AS exam_responses,
    sum(
        CASE
            WHEN (source = 'synthetic'::text) THEN 1
            ELSE 0
        END) AS synthetic_responses
   FROM public.v_response_log
  GROUP BY question_id
 HAVING (count(*) >= 50)
  ORDER BY (count(*)) DESC;


ALTER VIEW public.v_calibration_candidates OWNER TO postgres;

--
-- Name: vw_user_topic_mastery; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.vw_user_topic_mastery AS
 SELECT cs.user_id,
    q.primary_topic_id AS topic_id,
    th.name_tr AS topic_name,
    q.subject_area AS subject_name,
    max(cs.theta_final) AS best_theta,
    count(*) AS session_count,
    max(cs.completed_at) AS last_studied
   FROM ((public.kiro2_cat_sessions cs
     JOIN public.question_bank q ON (((q.subject_area)::text = cs.subject_id)))
     JOIN public.topic_hierarchy th ON (((th.id)::text = (q.primary_topic_id)::text)))
  WHERE (cs.state = 'completed'::text)
  GROUP BY cs.user_id, q.primary_topic_id, th.name_tr, q.subject_area;


ALTER VIEW public.vw_user_topic_mastery OWNER TO postgres;

--
-- Name: weekly_goals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.weekly_goals (
    id integer NOT NULL,
    plan_id integer NOT NULL,
    week_number integer NOT NULL,
    topics json,
    target_questions integer DEFAULT 0,
    target_reviews integer DEFAULT 0,
    completed_questions integer DEFAULT 0,
    completed_reviews integer DEFAULT 0,
    accuracy_rate double precision,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.weekly_goals OWNER TO postgres;

--
-- Name: weekly_goals_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.weekly_goals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.weekly_goals_id_seq OWNER TO postgres;

--
-- Name: weekly_goals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.weekly_goals_id_seq OWNED BY public.weekly_goals.id;


--
-- Name: weekly_progress; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.weekly_progress (
    id integer NOT NULL,
    user_id character varying NOT NULL,
    year integer NOT NULL,
    week_number integer NOT NULL,
    total_activities integer,
    total_time_seconds integer,
    streak_days integer,
    daily_data json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.weekly_progress OWNER TO postgres;

--
-- Name: weekly_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.weekly_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.weekly_progress_id_seq OWNER TO postgres;

--
-- Name: weekly_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.weekly_progress_id_seq OWNED BY public.weekly_progress.id;


--
-- Name: xp_transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.xp_transactions (
    id integer NOT NULL,
    student_id character varying NOT NULL,
    amount integer NOT NULL,
    source character varying(20) NOT NULL,
    topic_id character varying,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.xp_transactions OWNER TO postgres;

--
-- Name: xp_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.xp_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.xp_transactions_id_seq OWNER TO postgres;

--
-- Name: xp_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.xp_transactions_id_seq OWNED BY public.xp_transactions.id;


--
-- Name: yks_exam_goals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.yks_exam_goals (
    user_id character varying(255) NOT NULL,
    exam_type character varying(20) DEFAULT 'TYT'::character varying NOT NULL,
    exam_date date DEFAULT '2026-06-07'::date NOT NULL,
    daily_minutes integer DEFAULT 120 NOT NULL,
    target_university character varying(200),
    target_department character varying(200),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT yks_exam_goals_daily_minutes_check CHECK (((daily_minutes >= 30) AND (daily_minutes <= 480))),
    CONSTRAINT yks_exam_goals_exam_type_check CHECK (((exam_type)::text = ANY ((ARRAY['TYT'::character varying, 'AYT_SAY'::character varying, 'AYT_EA'::character varying, 'AYT_SOZ'::character varying])::text[])))
);


ALTER TABLE public.yks_exam_goals OWNER TO postgres;

--
-- Name: zpd_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.zpd_history (
    id character varying NOT NULL,
    student_id character varying NOT NULL,
    topic_id character varying NOT NULL,
    zone character varying(20) NOT NULL,
    p_learn double precision DEFAULT '0'::double precision,
    theta double precision DEFAULT '0'::double precision,
    scaffold_level integer DEFAULT 0,
    recorded_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.zpd_history OWNER TO postgres;

--
-- Name: badges id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.badges ALTER COLUMN id SET DEFAULT nextval('public.badges_id_seq'::regclass);


--
-- Name: duels id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.duels ALTER COLUMN id SET DEFAULT nextval('public.duels_id_seq'::regclass);


--
-- Name: fallback_videos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fallback_videos ALTER COLUMN id SET DEFAULT nextval('public.fallback_videos_id_seq'::regclass);


--
-- Name: manipulative_activities id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.manipulative_activities ALTER COLUMN id SET DEFAULT nextval('public.manipulative_activities_id_seq'::regclass);


--
-- Name: manipulative_progress id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.manipulative_progress ALTER COLUMN id SET DEFAULT nextval('public.manipulative_progress_id_seq'::regclass);


--
-- Name: oba_uyeler id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.oba_uyeler ALTER COLUMN id SET DEFAULT nextval('public.oba_uyeler_id_seq'::regclass);


--
-- Name: obalar id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.obalar ALTER COLUMN id SET DEFAULT nextval('public.obalar_id_seq'::regclass);


--
-- Name: parent_child id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_child ALTER COLUMN id SET DEFAULT nextval('public.parent_child_id_seq'::regclass);


--
-- Name: parent_notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_notifications ALTER COLUMN id SET DEFAULT nextval('public.parent_notifications_id_seq'::regclass);


--
-- Name: quiz_questions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_questions ALTER COLUMN id SET DEFAULT nextval('public.quiz_questions_id_seq'::regclass);


--
-- Name: quiz_submissions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_submissions ALTER COLUMN id SET DEFAULT nextval('public.quiz_submissions_id_seq'::regclass);


--
-- Name: realm_progress id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_progress ALTER COLUMN id SET DEFAULT nextval('public.realm_progress_id_seq'::regclass);


--
-- Name: realms id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realms ALTER COLUMN id SET DEFAULT nextval('public.realms_id_seq'::regclass);


--
-- Name: study_plans id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.study_plans ALTER COLUMN id SET DEFAULT nextval('public.study_plans_id_seq'::regclass);


--
-- Name: subjects id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subjects ALTER COLUMN id SET DEFAULT nextval('public.subjects_id_seq'::regclass);


--
-- Name: topic_completions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_completions ALTER COLUMN id SET DEFAULT nextval('public.topic_completions_id_seq'::regclass);


--
-- Name: topic_progress id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_progress ALTER COLUMN id SET DEFAULT nextval('public.topic_progress_id_seq'::regclass);


--
-- Name: weekly_goals id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.weekly_goals ALTER COLUMN id SET DEFAULT nextval('public.weekly_goals_id_seq'::regclass);


--
-- Name: weekly_progress id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.weekly_progress ALTER COLUMN id SET DEFAULT nextval('public.weekly_progress_id_seq'::regclass);


--
-- Name: xp_transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.xp_transactions ALTER COLUMN id SET DEFAULT nextval('public.xp_transactions_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: api_keys api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: badges badges_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.badges
    ADD CONSTRAINT badges_pkey PRIMARY KEY (id);


--
-- Name: badges badges_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.badges
    ADD CONSTRAINT badges_slug_key UNIQUE (slug);


--
-- Name: bkt_states bkt_states_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bkt_states
    ADD CONSTRAINT bkt_states_pkey PRIMARY KEY (student_id, topic_id);


--
-- Name: blocked_users blocked_users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blocked_users
    ADD CONSTRAINT blocked_users_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: class_reports class_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.class_reports
    ADD CONSTRAINT class_reports_pkey PRIMARY KEY (id);


--
-- Name: classrooms classrooms_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classrooms
    ADD CONSTRAINT classrooms_pkey PRIMARY KEY (id);


--
-- Name: coaching_events coaching_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coaching_events
    ADD CONSTRAINT coaching_events_pkey PRIMARY KEY (id);


--
-- Name: content_reports content_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_reports
    ADD CONSTRAINT content_reports_pkey PRIMARY KEY (id);


--
-- Name: curriculum_alignments curriculum_alignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curriculum_alignments
    ADD CONSTRAINT curriculum_alignments_pkey PRIMARY KEY (id);


--
-- Name: curriculum_update_requests curriculum_update_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curriculum_update_requests
    ADD CONSTRAINT curriculum_update_requests_pkey PRIMARY KEY (id);


--
-- Name: daily_plans daily_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_plans
    ADD CONSTRAINT daily_plans_pkey PRIMARY KEY (id);


--
-- Name: daily_plans daily_plans_user_id_plan_date_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_plans
    ADD CONSTRAINT daily_plans_user_id_plan_date_key UNIQUE (user_id, plan_date);


--
-- Name: dina_parameters dina_parameters_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dina_parameters
    ADD CONSTRAINT dina_parameters_pkey PRIMARY KEY (id);


--
-- Name: dina_parameters dina_parameters_question_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dina_parameters
    ADD CONSTRAINT dina_parameters_question_id_key UNIQUE (question_id);


--
-- Name: duel_matches duel_matches_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.duel_matches
    ADD CONSTRAINT duel_matches_pkey PRIMARY KEY (id);


--
-- Name: duel_ratings duel_ratings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.duel_ratings
    ADD CONSTRAINT duel_ratings_pkey PRIMARY KEY (id);


--
-- Name: duel_ratings duel_ratings_student_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.duel_ratings
    ADD CONSTRAINT duel_ratings_student_id_key UNIQUE (student_id);


--
-- Name: duel_sessions duel_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.duel_sessions
    ADD CONSTRAINT duel_sessions_pkey PRIMARY KEY (id);


--
-- Name: duels duels_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.duels
    ADD CONSTRAINT duels_pkey PRIMARY KEY (id);


--
-- Name: eba_content_analytics eba_content_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_content_analytics
    ADD CONSTRAINT eba_content_analytics_pkey PRIMARY KEY (id);


--
-- Name: eba_content_collections eba_content_collections_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_content_collections
    ADD CONSTRAINT eba_content_collections_pkey PRIMARY KEY (id);


--
-- Name: eba_video_recommendations eba_video_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_video_recommendations
    ADD CONSTRAINT eba_video_recommendations_pkey PRIMARY KEY (id);


--
-- Name: eba_video_usage eba_video_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_video_usage
    ADD CONSTRAINT eba_video_usage_pkey PRIMARY KEY (id);


--
-- Name: eba_videos eba_videos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_videos
    ADD CONSTRAINT eba_videos_pkey PRIMARY KEY (id);


--
-- Name: educational_contents educational_contents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.educational_contents
    ADD CONSTRAINT educational_contents_pkey PRIMARY KEY (id);


--
-- Name: error_clusters error_clusters_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.error_clusters
    ADD CONSTRAINT error_clusters_pkey PRIMARY KEY (id);


--
-- Name: exam_questions exam_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exam_questions
    ADD CONSTRAINT exam_questions_pkey PRIMARY KEY (id);


--
-- Name: exam_sessions exam_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exam_sessions
    ADD CONSTRAINT exam_sessions_pkey PRIMARY KEY (id);


--
-- Name: fallback_videos fallback_videos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fallback_videos
    ADD CONSTRAINT fallback_videos_pkey PRIMARY KEY (id);


--
-- Name: fallback_videos fallback_videos_video_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fallback_videos
    ADD CONSTRAINT fallback_videos_video_id_key UNIQUE (video_id);


--
-- Name: forum_questions forum_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_questions
    ADD CONSTRAINT forum_questions_pkey PRIMARY KEY (id);


--
-- Name: forum_solutions forum_solutions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_solutions
    ADD CONSTRAINT forum_solutions_pkey PRIMARY KEY (id);


--
-- Name: forum_votes forum_votes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_votes
    ADD CONSTRAINT forum_votes_pkey PRIMARY KEY (id);


--
-- Name: fsrs_cards fsrs_cards_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_cards
    ADD CONSTRAINT fsrs_cards_pkey PRIMARY KEY (id);


--
-- Name: fsrs_reviews fsrs_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_reviews
    ADD CONSTRAINT fsrs_reviews_pkey PRIMARY KEY (id);


--
-- Name: fsrs_schedules fsrs_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_schedules
    ADD CONSTRAINT fsrs_schedules_pkey PRIMARY KEY (id);


--
-- Name: fsrs_student_profiles fsrs_student_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_student_profiles
    ADD CONSTRAINT fsrs_student_profiles_pkey PRIMARY KEY (id);


--
-- Name: fsrs_student_profiles fsrs_student_profiles_student_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_student_profiles
    ADD CONSTRAINT fsrs_student_profiles_student_id_key UNIQUE (student_id);


--
-- Name: fsrs_study_sessions fsrs_study_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_study_sessions
    ADD CONSTRAINT fsrs_study_sessions_pkey PRIMARY KEY (id);


--
-- Name: fsrs_subject_stats fsrs_subject_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_subject_stats
    ADD CONSTRAINT fsrs_subject_stats_pkey PRIMARY KEY (id);


--
-- Name: irt_calibration_history irt_calibration_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.irt_calibration_history
    ADD CONSTRAINT irt_calibration_history_pkey PRIMARY KEY (id);


--
-- Name: kiro2_cat_sessions kiro2_cat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.kiro2_cat_sessions
    ADD CONSTRAINT kiro2_cat_sessions_pkey PRIMARY KEY (id);


--
-- Name: kiro2_learning_events kiro2_learning_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.kiro2_learning_events
    ADD CONSTRAINT kiro2_learning_events_pkey PRIMARY KEY (id);


--
-- Name: kiro2_learning_events_synthetic kiro2_learning_events_synthetic_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.kiro2_learning_events_synthetic
    ADD CONSTRAINT kiro2_learning_events_synthetic_pkey PRIMARY KEY (id);


--
-- Name: knowledge_points knowledge_points_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_points
    ADD CONSTRAINT knowledge_points_code_key UNIQUE (code);


--
-- Name: knowledge_points knowledge_points_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_points
    ADD CONSTRAINT knowledge_points_pkey PRIMARY KEY (id);


--
-- Name: league_history league_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.league_history
    ADD CONSTRAINT league_history_pkey PRIMARY KEY (id);


--
-- Name: league_memberships league_memberships_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.league_memberships
    ADD CONSTRAINT league_memberships_pkey PRIMARY KEY (id);


--
-- Name: league_memberships league_memberships_student_id_week_start_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.league_memberships
    ADD CONSTRAINT league_memberships_student_id_week_start_key UNIQUE (student_id, week_start);


--
-- Name: learning_analytics learning_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.learning_analytics
    ADD CONSTRAINT learning_analytics_pkey PRIMARY KEY (id);


--
-- Name: learning_outcomes learning_outcomes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.learning_outcomes
    ADD CONSTRAINT learning_outcomes_pkey PRIMARY KEY (id);


--
-- Name: learning_path_student_profiles learning_path_student_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.learning_path_student_profiles
    ADD CONSTRAINT learning_path_student_profiles_pkey PRIMARY KEY (student_id);


--
-- Name: learning_paths learning_paths_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.learning_paths
    ADD CONSTRAINT learning_paths_pkey PRIMARY KEY (path_id);


--
-- Name: learning_progress_daily learning_progress_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.learning_progress_daily
    ADD CONSTRAINT learning_progress_daily_pkey PRIMARY KEY (id);


--
-- Name: learning_progress_daily learning_progress_daily_user_id_log_date_subject_activity_t_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.learning_progress_daily
    ADD CONSTRAINT learning_progress_daily_user_id_log_date_subject_activity_t_key UNIQUE (user_id, log_date, subject, activity_type);


--
-- Name: manipulative_activities manipulative_activities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.manipulative_activities
    ADD CONSTRAINT manipulative_activities_pkey PRIMARY KEY (id);


--
-- Name: manipulative_progress manipulative_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.manipulative_progress
    ADD CONSTRAINT manipulative_progress_pkey PRIMARY KEY (id);


--
-- Name: meb_curriculum_standards meb_curriculum_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.meb_curriculum_standards
    ADD CONSTRAINT meb_curriculum_standards_pkey PRIMARY KEY (id);


--
-- Name: mentor_feedback mentor_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mentor_feedback
    ADD CONSTRAINT mentor_feedback_pkey PRIMARY KEY (id);


--
-- Name: mentor_pairs mentor_pairs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mentor_pairs
    ADD CONSTRAINT mentor_pairs_pkey PRIMARY KEY (id);


--
-- Name: mentor_sessions mentor_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mentor_sessions
    ADD CONSTRAINT mentor_sessions_pkey PRIMARY KEY (id);


--
-- Name: message_audit_log message_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.message_audit_log
    ADD CONSTRAINT message_audit_log_pkey PRIMARY KEY (id);


--
-- Name: moderation_actions moderation_actions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.moderation_actions
    ADD CONSTRAINT moderation_actions_pkey PRIMARY KEY (id);


--
-- Name: nano_skills nano_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nano_skills
    ADD CONSTRAINT nano_skills_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: oba_challenge_progress oba_challenge_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.oba_challenge_progress
    ADD CONSTRAINT oba_challenge_progress_pkey PRIMARY KEY (id);


--
-- Name: oba_challenges oba_challenges_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.oba_challenges
    ADD CONSTRAINT oba_challenges_pkey PRIMARY KEY (id);


--
-- Name: oba_uyeler oba_uyeler_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.oba_uyeler
    ADD CONSTRAINT oba_uyeler_pkey PRIMARY KEY (id);


--
-- Name: oba_uyeler oba_uyeler_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.oba_uyeler
    ADD CONSTRAINT oba_uyeler_user_id_key UNIQUE (user_id);


--
-- Name: obalar obalar_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.obalar
    ADD CONSTRAINT obalar_pkey PRIMARY KEY (id);


--
-- Name: osym_standards osym_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.osym_standards
    ADD CONSTRAINT osym_standards_pkey PRIMARY KEY (id);


--
-- Name: parent_approvals parent_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_approvals
    ADD CONSTRAINT parent_approvals_pkey PRIMARY KEY (id);


--
-- Name: parent_child parent_child_parent_id_child_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_child
    ADD CONSTRAINT parent_child_parent_id_child_id_key UNIQUE (parent_id, child_id);


--
-- Name: parent_child parent_child_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_child
    ADD CONSTRAINT parent_child_pkey PRIMARY KEY (id);


--
-- Name: parent_notifications parent_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_notifications
    ADD CONSTRAINT parent_notifications_pkey PRIMARY KEY (id);


--
-- Name: parent_profiles parent_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_profiles
    ADD CONSTRAINT parent_profiles_pkey PRIMARY KEY (id);


--
-- Name: parent_profiles parent_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_profiles
    ADD CONSTRAINT parent_profiles_user_id_key UNIQUE (user_id);


--
-- Name: parent_reports parent_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_reports
    ADD CONSTRAINT parent_reports_pkey PRIMARY KEY (id);


--
-- Name: parent_social_settings parent_social_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_social_settings
    ADD CONSTRAINT parent_social_settings_pkey PRIMARY KEY (id);


--
-- Name: peer_recommendations peer_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.peer_recommendations
    ADD CONSTRAINT peer_recommendations_pkey PRIMARY KEY (id);


--
-- Name: platform_stats platform_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.platform_stats
    ADD CONSTRAINT platform_stats_pkey PRIMARY KEY (id);


--
-- Name: platform_stats platform_stats_stat_date_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.platform_stats
    ADD CONSTRAINT platform_stats_stat_date_key UNIQUE (stat_date);


--
-- Name: point_transactions point_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.point_transactions
    ADD CONSTRAINT point_transactions_pkey PRIMARY KEY (id);


--
-- Name: pomodoro_participants pomodoro_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pomodoro_participants
    ADD CONSTRAINT pomodoro_participants_pkey PRIMARY KEY (id);


--
-- Name: pomodoro_rooms pomodoro_rooms_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pomodoro_rooms
    ADD CONSTRAINT pomodoro_rooms_pkey PRIMARY KEY (id);


--
-- Name: q_matrix q_matrix_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.q_matrix
    ADD CONSTRAINT q_matrix_pkey PRIMARY KEY (id);


--
-- Name: quality_gate_results quality_gate_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quality_gate_results
    ADD CONSTRAINT quality_gate_results_pkey PRIMARY KEY (id);


--
-- Name: quality_gates_override_audit quality_gates_override_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quality_gates_override_audit
    ADD CONSTRAINT quality_gates_override_audit_pkey PRIMARY KEY (id);


--
-- Name: quality_gates_runs quality_gates_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quality_gates_runs
    ADD CONSTRAINT quality_gates_runs_pkey PRIMARY KEY (id);


--
-- Name: question_bank question_bank_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_bank
    ADD CONSTRAINT question_bank_pkey PRIMARY KEY (id);


--
-- Name: question_knowledge_mappings question_knowledge_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_knowledge_mappings
    ADD CONSTRAINT question_knowledge_mappings_pkey PRIMARY KEY (id);


--
-- Name: question_performance_analytics question_performance_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_performance_analytics
    ADD CONSTRAINT question_performance_analytics_pkey PRIMARY KEY (id);


--
-- Name: question_tag_associations question_tag_associations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_tag_associations
    ADD CONSTRAINT question_tag_associations_pkey PRIMARY KEY (id);


--
-- Name: question_tags question_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_tags
    ADD CONSTRAINT question_tags_pkey PRIMARY KEY (id);


--
-- Name: question_tags question_tags_tag_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_tags
    ADD CONSTRAINT question_tags_tag_name_key UNIQUE (tag_name);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: quiz_questions quiz_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_pkey PRIMARY KEY (id);


--
-- Name: quiz_submissions quiz_submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_submissions
    ADD CONSTRAINT quiz_submissions_pkey PRIMARY KEY (id);


--
-- Name: quizzes quizzes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quizzes
    ADD CONSTRAINT quizzes_pkey PRIMARY KEY (id);


--
-- Name: realm_progress realm_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_progress
    ADD CONSTRAINT realm_progress_pkey PRIMARY KEY (id);


--
-- Name: realm_progress realm_progress_student_id_realm_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_progress
    ADD CONSTRAINT realm_progress_student_id_realm_id_key UNIQUE (student_id, realm_id);


--
-- Name: realms realms_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realms
    ADD CONSTRAINT realms_pkey PRIMARY KEY (id);


--
-- Name: realms realms_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realms
    ADD CONSTRAINT realms_slug_key UNIQUE (slug);


--
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: solution_duel_submissions solution_duel_submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solution_duel_submissions
    ADD CONSTRAINT solution_duel_submissions_pkey PRIMARY KEY (id);


--
-- Name: solution_duel_votes solution_duel_votes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solution_duel_votes
    ADD CONSTRAINT solution_duel_votes_pkey PRIMARY KEY (id);


--
-- Name: solution_duels solution_duels_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solution_duels
    ADD CONSTRAINT solution_duels_pkey PRIMARY KEY (id);


--
-- Name: streak_daily_log streak_daily_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.streak_daily_log
    ADD CONSTRAINT streak_daily_log_pkey PRIMARY KEY (id);


--
-- Name: streak_pairs streak_pairs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.streak_pairs
    ADD CONSTRAINT streak_pairs_pkey PRIMARY KEY (id);


--
-- Name: streak_tracking streak_tracking_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.streak_tracking
    ADD CONSTRAINT streak_tracking_pkey PRIMARY KEY (id);


--
-- Name: streak_tracking streak_tracking_student_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.streak_tracking
    ADD CONSTRAINT streak_tracking_student_id_key UNIQUE (student_id);


--
-- Name: streaks streaks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.streaks
    ADD CONSTRAINT streaks_pkey PRIMARY KEY (user_id);


--
-- Name: student_abilities student_abilities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_abilities
    ADD CONSTRAINT student_abilities_pkey PRIMARY KEY (student_id, subject_id);


--
-- Name: student_answers student_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_answers
    ADD CONSTRAINT student_answers_pkey PRIMARY KEY (id);


--
-- Name: student_engagement_signals student_engagement_signals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_engagement_signals
    ADD CONSTRAINT student_engagement_signals_pkey PRIMARY KEY (id);


--
-- Name: student_goals student_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_goals
    ADD CONSTRAINT student_goals_pkey PRIMARY KEY (id);


--
-- Name: student_grades student_grades_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_grades
    ADD CONSTRAINT student_grades_pkey PRIMARY KEY (id);


--
-- Name: student_knowledge_states student_knowledge_states_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_knowledge_states
    ADD CONSTRAINT student_knowledge_states_pkey PRIMARY KEY (id);


--
-- Name: student_learning_profiles student_learning_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_learning_profiles
    ADD CONSTRAINT student_learning_profiles_pkey PRIMARY KEY (id);


--
-- Name: student_nano_skill_mastery student_nano_skill_mastery_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_nano_skill_mastery
    ADD CONSTRAINT student_nano_skill_mastery_pkey PRIMARY KEY (id);


--
-- Name: student_profiles student_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_pkey PRIMARY KEY (id);


--
-- Name: student_profiles student_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_user_id_key UNIQUE (user_id);


--
-- Name: study_plans study_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.study_plans
    ADD CONSTRAINT study_plans_pkey PRIMARY KEY (id);


--
-- Name: subjects subjects_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subjects
    ADD CONSTRAINT subjects_name_key UNIQUE (name);


--
-- Name: subjects subjects_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subjects
    ADD CONSTRAINT subjects_pkey PRIMARY KEY (id);


--
-- Name: system_configurations system_configurations_config_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_configurations
    ADD CONSTRAINT system_configurations_config_key_key UNIQUE (config_key);


--
-- Name: system_configurations system_configurations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_configurations
    ADD CONSTRAINT system_configurations_pkey PRIMARY KEY (id);


--
-- Name: teacher_profiles teacher_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teacher_profiles
    ADD CONSTRAINT teacher_profiles_pkey PRIMARY KEY (id);


--
-- Name: teacher_profiles teacher_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teacher_profiles
    ADD CONSTRAINT teacher_profiles_user_id_key UNIQUE (user_id);


--
-- Name: topic_completions topic_completions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_completions
    ADD CONSTRAINT topic_completions_pkey PRIMARY KEY (id);


--
-- Name: topic_hierarchy topic_hierarchy_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_hierarchy
    ADD CONSTRAINT topic_hierarchy_code_key UNIQUE (code);


--
-- Name: topic_hierarchy topic_hierarchy_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_hierarchy
    ADD CONSTRAINT topic_hierarchy_pkey PRIMARY KEY (id);


--
-- Name: topic_prerequisites topic_prerequisites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_prerequisites
    ADD CONSTRAINT topic_prerequisites_pkey PRIMARY KEY (id);


--
-- Name: topic_prerequisites topic_prerequisites_topic_id_prereq_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_prerequisites
    ADD CONSTRAINT topic_prerequisites_topic_id_prereq_id_key UNIQUE (topic_id, prereq_id);


--
-- Name: topic_progress topic_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_progress
    ADD CONSTRAINT topic_progress_pkey PRIMARY KEY (id);


--
-- Name: blocked_users uq_block_pair; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blocked_users
    ADD CONSTRAINT uq_block_pair UNIQUE (blocker_id, blocked_id);


--
-- Name: solution_duel_votes uq_duel_vote; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solution_duel_votes
    ADD CONSTRAINT uq_duel_vote UNIQUE (duel_id, voter_id);


--
-- Name: eba_content_analytics uq_eba_analytics; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_content_analytics
    ADD CONSTRAINT uq_eba_analytics UNIQUE (analysis_date, category, grade_level);


--
-- Name: eba_video_usage uq_eba_video_usage; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_video_usage
    ADD CONSTRAINT uq_eba_video_usage UNIQUE (video_id, student_id, started_at);


--
-- Name: exam_questions uq_exam_question_order; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exam_questions
    ADD CONSTRAINT uq_exam_question_order UNIQUE (exam_session_id, question_order);


--
-- Name: forum_votes uq_forum_vote; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_votes
    ADD CONSTRAINT uq_forum_vote UNIQUE (voter_id, solution_id);


--
-- Name: fsrs_schedules uq_fsrs_schedule; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_schedules
    ADD CONSTRAINT uq_fsrs_schedule UNIQUE (student_id, schedule_date);


--
-- Name: fsrs_subject_stats uq_fsrs_subject_stats; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_subject_stats
    ADD CONSTRAINT uq_fsrs_subject_stats UNIQUE (student_id, subject_area);


--
-- Name: league_memberships uq_league_membership_student_week; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.league_memberships
    ADD CONSTRAINT uq_league_membership_student_week UNIQUE (student_id, week_start);


--
-- Name: learning_analytics uq_learning_analytics; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.learning_analytics
    ADD CONSTRAINT uq_learning_analytics UNIQUE (student_id, date, subject_area);


--
-- Name: parent_social_settings uq_parent_student_settings; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_social_settings
    ADD CONSTRAINT uq_parent_student_settings UNIQUE (parent_id, student_id);


--
-- Name: q_matrix uq_qmatrix_pair; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.q_matrix
    ADD CONSTRAINT uq_qmatrix_pair UNIQUE (question_id, nano_skill_id);


--
-- Name: question_performance_analytics uq_question_analytics; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_performance_analytics
    ADD CONSTRAINT uq_question_analytics UNIQUE (question_id, analysis_date, period_type);


--
-- Name: question_knowledge_mappings uq_question_knowledge_mapping; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_knowledge_mappings
    ADD CONSTRAINT uq_question_knowledge_mapping UNIQUE (question_id, knowledge_point_id);


--
-- Name: question_tag_associations uq_question_tag; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_tag_associations
    ADD CONSTRAINT uq_question_tag UNIQUE (question_id, tag_id);


--
-- Name: student_nano_skill_mastery uq_snsm_pair; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_nano_skill_mastery
    ADD CONSTRAINT uq_snsm_pair UNIQUE (student_id, nano_skill_id);


--
-- Name: student_answers uq_student_answer; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_answers
    ADD CONSTRAINT uq_student_answer UNIQUE (exam_session_id, question_id);


--
-- Name: student_knowledge_states uq_student_knowledge_state; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_knowledge_states
    ADD CONSTRAINT uq_student_knowledge_state UNIQUE (student_id, knowledge_point_id);


--
-- Name: weekly_progress uq_weekly_progress; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.weekly_progress
    ADD CONSTRAINT uq_weekly_progress UNIQUE (user_id, year, week_number);


--
-- Name: user_achievements user_achievements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_pkey PRIMARY KEY (id);


--
-- Name: user_badges user_badges_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_badges
    ADD CONSTRAINT user_badges_pkey PRIMARY KEY (id);


--
-- Name: user_item_fsrs user_item_fsrs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_item_fsrs
    ADD CONSTRAINT user_item_fsrs_pkey PRIMARY KEY (user_id, question_id);


--
-- Name: user_theta user_theta_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_theta
    ADD CONSTRAINT user_theta_pkey PRIMARY KEY (user_id, subject_area);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: weekly_goals weekly_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.weekly_goals
    ADD CONSTRAINT weekly_goals_pkey PRIMARY KEY (id);


--
-- Name: weekly_progress weekly_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.weekly_progress
    ADD CONSTRAINT weekly_progress_pkey PRIMARY KEY (id);


--
-- Name: xp_transactions xp_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.xp_transactions
    ADD CONSTRAINT xp_transactions_pkey PRIMARY KEY (id);


--
-- Name: yks_exam_goals yks_exam_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.yks_exam_goals
    ADD CONSTRAINT yks_exam_goals_pkey PRIMARY KEY (user_id);


--
-- Name: zpd_history zpd_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zpd_history
    ADD CONSTRAINT zpd_history_pkey PRIMARY KEY (id);


--
-- Name: idx_alignment_meb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_alignment_meb ON public.curriculum_alignments USING btree (meb_standard_id);


--
-- Name: idx_alignment_osym; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_alignment_osym ON public.curriculum_alignments USING btree (osym_standard_id);


--
-- Name: idx_alignment_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_alignment_score ON public.curriculum_alignments USING btree (alignment_score);


--
-- Name: idx_api_key_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_api_key_active ON public.api_keys USING btree (is_active);


--
-- Name: idx_api_key_expires; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_api_key_expires ON public.api_keys USING btree (expires_at);


--
-- Name: idx_api_key_hash; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_api_key_hash ON public.api_keys USING btree (key_hash);


--
-- Name: idx_api_key_prefix; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_api_key_prefix ON public.api_keys USING btree (key_prefix);


--
-- Name: idx_api_key_revoked; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_api_key_revoked ON public.api_keys USING btree (revoked);


--
-- Name: idx_api_key_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_api_key_user ON public.api_keys USING btree (user_id);


--
-- Name: idx_approval_parent_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_approval_parent_status ON public.parent_approvals USING btree (parent_user_id, status);


--
-- Name: idx_approval_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_approval_student ON public.parent_approvals USING btree (student_user_id);


--
-- Name: idx_audit_action; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_action ON public.audit_logs USING btree (action);


--
-- Name: idx_audit_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_created ON public.audit_logs USING btree (created_at);


--
-- Name: idx_audit_logs_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_logs_created ON public.audit_logs USING btree (created_at DESC);


--
-- Name: idx_audit_logs_created_brin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_logs_created_brin ON public.audit_logs USING brin (created_at);


--
-- Name: idx_audit_resource; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_resource ON public.audit_logs USING btree (resource_type, resource_id);


--
-- Name: idx_audit_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_user ON public.audit_logs USING btree (user_id);


--
-- Name: idx_bkt_states_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bkt_states_student ON public.bkt_states USING btree (student_id);


--
-- Name: idx_blocked_users_blocked; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_blocked_users_blocked ON public.blocked_users USING btree (blocked_id);


--
-- Name: idx_blocked_users_blocker; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_blocked_users_blocker ON public.blocked_users USING btree (blocker_id);


--
-- Name: idx_calibration_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_calibration_date ON public.irt_calibration_history USING btree (calibration_date);


--
-- Name: idx_calibration_question; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_calibration_question ON public.irt_calibration_history USING btree (question_id);


--
-- Name: idx_cat_sessions_state; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cat_sessions_state ON public.kiro2_cat_sessions USING btree (state);


--
-- Name: idx_cat_sessions_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cat_sessions_user ON public.kiro2_cat_sessions USING btree (user_id);


--
-- Name: idx_chat_messages_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chat_messages_created ON public.chat_messages USING btree (created_at);


--
-- Name: idx_chat_messages_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chat_messages_role ON public.chat_messages USING btree (role);


--
-- Name: idx_chat_messages_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chat_messages_session ON public.chat_messages USING btree (session_id);


--
-- Name: idx_chat_sessions_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chat_sessions_created ON public.chat_sessions USING btree (created_at);


--
-- Name: idx_chat_sessions_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chat_sessions_status ON public.chat_sessions USING btree (status);


--
-- Name: idx_chat_sessions_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chat_sessions_user ON public.chat_sessions USING btree (user_id);


--
-- Name: idx_class_report_period; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_class_report_period ON public.class_reports USING btree (report_period);


--
-- Name: idx_class_report_teacher; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_class_report_teacher ON public.class_reports USING btree (teacher_user_id, created_at);


--
-- Name: idx_classroom_grade; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_classroom_grade ON public.classrooms USING btree (grade_level);


--
-- Name: idx_classroom_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_classroom_subject ON public.classrooms USING btree (subject_area);


--
-- Name: idx_classroom_teacher; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_classroom_teacher ON public.classrooms USING btree (teacher_id);


--
-- Name: idx_coaching_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coaching_created ON public.coaching_events USING btree (created_at);


--
-- Name: idx_coaching_event_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coaching_event_type ON public.coaching_events USING btree (event_type);


--
-- Name: idx_coaching_shown; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coaching_shown ON public.coaching_events USING btree (student_id, shown_at);


--
-- Name: idx_coaching_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coaching_student ON public.coaching_events USING btree (student_id);


--
-- Name: idx_completion_student_node; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_completion_student_node ON public.topic_completions USING btree (student_id, node_id);


--
-- Name: idx_config_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_config_key ON public.system_configurations USING btree (config_key);


--
-- Name: idx_content_difficulty; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_difficulty ON public.educational_contents USING btree (difficulty_level);


--
-- Name: idx_content_grade; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_grade ON public.educational_contents USING btree (grade_level);


--
-- Name: idx_content_platform; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_platform ON public.educational_contents USING btree (source_platform);


--
-- Name: idx_content_reports_content; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_reports_content ON public.content_reports USING btree (reported_content_id);


--
-- Name: idx_content_reports_reporter; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_reports_reporter ON public.content_reports USING btree (reporter_id);


--
-- Name: idx_content_reports_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_reports_status ON public.content_reports USING btree (status);


--
-- Name: idx_content_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_score ON public.educational_contents USING btree (educational_score);


--
-- Name: idx_content_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_subject ON public.educational_contents USING btree (subject_area);


--
-- Name: idx_content_topic; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_topic ON public.educational_contents USING btree (topic);


--
-- Name: idx_daily_plans_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_daily_plans_date ON public.daily_plans USING btree (plan_date);


--
-- Name: idx_daily_plans_user_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_daily_plans_user_date ON public.daily_plans USING btree (user_id, plan_date DESC);


--
-- Name: idx_dina_question; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_dina_question ON public.dina_parameters USING btree (question_id);


--
-- Name: idx_duel_challenger; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_challenger ON public.solution_duels USING btree (challenger_id);


--
-- Name: idx_duel_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_created ON public.duel_sessions USING btree (created_at);


--
-- Name: idx_duel_match_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_match_order ON public.duel_matches USING btree (session_id, question_order);


--
-- Name: idx_duel_match_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_match_session ON public.duel_matches USING btree (session_id);


--
-- Name: idx_duel_opponent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_opponent ON public.solution_duels USING btree (opponent_id);


--
-- Name: idx_duel_player1; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_player1 ON public.duel_sessions USING btree (player1_id);


--
-- Name: idx_duel_player2; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_player2 ON public.duel_sessions USING btree (player2_id);


--
-- Name: idx_duel_qbank; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_qbank ON public.solution_duels USING btree (question_bank_id);


--
-- Name: idx_duel_rating_elo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_rating_elo ON public.duel_ratings USING btree (elo_rating);


--
-- Name: idx_duel_rating_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_duel_rating_student ON public.duel_ratings USING btree (student_id);


--
-- Name: idx_duel_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_status ON public.duel_sessions USING btree (status);


--
-- Name: idx_duel_sub_duel; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_sub_duel ON public.solution_duel_submissions USING btree (duel_id);


--
-- Name: idx_duel_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_subject ON public.solution_duels USING btree (subject_area);


--
-- Name: idx_duel_vote_duel; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duel_vote_duel ON public.solution_duel_votes USING btree (duel_id);


--
-- Name: idx_duels_player1; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duels_player1 ON public.duels USING btree (player1_id);


--
-- Name: idx_duels_player2; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_duels_player2 ON public.duels USING btree (player2_id);


--
-- Name: idx_eba_analytics_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_analytics_category ON public.eba_content_analytics USING btree (category);


--
-- Name: idx_eba_analytics_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_analytics_date ON public.eba_content_analytics USING btree (analysis_date);


--
-- Name: idx_eba_analytics_grade; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_analytics_grade ON public.eba_content_analytics USING btree (grade_level);


--
-- Name: idx_eba_collection_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_collection_category ON public.eba_content_collections USING btree (category);


--
-- Name: idx_eba_collection_featured; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_collection_featured ON public.eba_content_collections USING btree (is_featured);


--
-- Name: idx_eba_collection_grade; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_collection_grade ON public.eba_content_collections USING btree (grade_level);


--
-- Name: idx_eba_rec_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_rec_created ON public.eba_video_recommendations USING btree (created_at);


--
-- Name: idx_eba_rec_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_rec_score ON public.eba_video_recommendations USING btree (recommendation_score);


--
-- Name: idx_eba_rec_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_rec_student ON public.eba_video_recommendations USING btree (student_id);


--
-- Name: idx_eba_rec_video; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_rec_video ON public.eba_video_recommendations USING btree (video_id);


--
-- Name: idx_eba_usage_started; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_usage_started ON public.eba_video_usage USING btree (started_at);


--
-- Name: idx_eba_usage_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_usage_student ON public.eba_video_usage USING btree (student_id);


--
-- Name: idx_eba_usage_video; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_usage_video ON public.eba_video_usage USING btree (video_id);


--
-- Name: idx_eba_video_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_video_category ON public.eba_videos USING btree (category);


--
-- Name: idx_eba_video_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_video_created ON public.eba_videos USING btree (created_at);


--
-- Name: idx_eba_video_difficulty; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_video_difficulty ON public.eba_videos USING btree (difficulty_level);


--
-- Name: idx_eba_video_grade; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_video_grade ON public.eba_videos USING btree (grade_level);


--
-- Name: idx_eba_video_moderation; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_video_moderation ON public.eba_videos USING btree (moderation_status);


--
-- Name: idx_eba_video_quality; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_eba_video_quality ON public.eba_videos USING btree (quality_score);


--
-- Name: idx_educational_contents_search; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_educational_contents_search ON public.educational_contents USING gin (title public.gin_trgm_ops);


--
-- Name: idx_engagement_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_engagement_student ON public.student_engagement_signals USING btree (student_id);


--
-- Name: idx_engagement_type_recorded; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_engagement_type_recorded ON public.student_engagement_signals USING btree (student_id, signal_type, recorded_at);


--
-- Name: idx_error_cluster_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_error_cluster_subject ON public.error_clusters USING btree (subject);


--
-- Name: idx_error_cluster_updated; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_error_cluster_updated ON public.error_clusters USING btree (updated_at);


--
-- Name: idx_exam_question_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exam_question_order ON public.exam_questions USING btree (question_order);


--
-- Name: idx_exam_question_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exam_question_session ON public.exam_questions USING btree (exam_session_id);


--
-- Name: idx_exam_session_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exam_session_created ON public.exam_sessions USING btree (created_at);


--
-- Name: idx_exam_session_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exam_session_status ON public.exam_sessions USING btree (status);


--
-- Name: idx_exam_session_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exam_session_student ON public.exam_sessions USING btree (student_id);


--
-- Name: idx_exam_session_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exam_session_type ON public.exam_sessions USING btree (exam_type);


--
-- Name: idx_exam_sessions_timestamps; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exam_sessions_timestamps ON public.exam_sessions USING btree (created_at DESC, updated_at DESC);


--
-- Name: idx_fallback_final_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fallback_final_score ON public.fallback_videos USING btree (final_score);


--
-- Name: idx_fallback_is_example; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fallback_is_example ON public.fallback_videos USING btree (is_example);


--
-- Name: idx_fallback_subject_topic; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fallback_subject_topic ON public.fallback_videos USING btree (subject, topic);


--
-- Name: idx_forum_q_qbank; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_forum_q_qbank ON public.forum_questions USING btree (question_bank_id);


--
-- Name: idx_forum_q_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_forum_q_status ON public.forum_questions USING btree (status);


--
-- Name: idx_forum_q_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_forum_q_student ON public.forum_questions USING btree (student_id);


--
-- Name: idx_forum_q_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_forum_q_subject ON public.forum_questions USING btree (subject_area);


--
-- Name: idx_forum_sol_question; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_forum_sol_question ON public.forum_solutions USING btree (question_id);


--
-- Name: idx_forum_sol_solver; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_forum_sol_solver ON public.forum_solutions USING btree (solver_id);


--
-- Name: idx_forum_vote_solution; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_forum_vote_solution ON public.forum_votes USING btree (solution_id);


--
-- Name: idx_forum_vote_voter; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_forum_vote_voter ON public.forum_votes USING btree (voter_id);


--
-- Name: idx_fsrs_card_due; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_card_due ON public.fsrs_cards USING btree (due_date);


--
-- Name: idx_fsrs_card_state; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_card_state ON public.fsrs_cards USING btree (state);


--
-- Name: idx_fsrs_card_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_card_student ON public.fsrs_cards USING btree (student_id);


--
-- Name: idx_fsrs_card_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_card_subject ON public.fsrs_cards USING btree (subject_area);


--
-- Name: idx_fsrs_cards_student_due; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_cards_student_due ON public.fsrs_cards USING btree (student_id, due_date);


--
-- Name: idx_fsrs_due; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_due ON public.user_item_fsrs USING btree (user_id, due_date) WHERE (state = ANY (ARRAY[1, 2, 3]));


--
-- Name: idx_fsrs_profile_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_profile_student ON public.fsrs_student_profiles USING btree (student_id);


--
-- Name: idx_fsrs_review_card; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_review_card ON public.fsrs_reviews USING btree (card_id);


--
-- Name: idx_fsrs_review_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_review_date ON public.fsrs_reviews USING btree (review_date);


--
-- Name: idx_fsrs_review_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_review_student ON public.fsrs_reviews USING btree (student_id);


--
-- Name: idx_fsrs_schedule_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_schedule_date ON public.fsrs_schedules USING btree (schedule_date);


--
-- Name: idx_fsrs_schedule_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_schedule_student ON public.fsrs_schedules USING btree (student_id);


--
-- Name: idx_fsrs_session_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_session_date ON public.fsrs_study_sessions USING btree (session_date);


--
-- Name: idx_fsrs_session_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_session_student ON public.fsrs_study_sessions USING btree (student_id);


--
-- Name: idx_fsrs_stats_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_stats_student ON public.fsrs_subject_stats USING btree (student_id);


--
-- Name: idx_fsrs_stats_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_stats_subject ON public.fsrs_subject_stats USING btree (subject_area);


--
-- Name: idx_fsrs_user_state; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fsrs_user_state ON public.user_item_fsrs USING btree (user_id, state);


--
-- Name: idx_goal_end_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_goal_end_date ON public.student_goals USING btree (end_date);


--
-- Name: idx_goal_user_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_goal_user_status ON public.student_goals USING btree (user_id, status);


--
-- Name: idx_grade_academic_year; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_grade_academic_year ON public.student_grades USING btree (academic_year, semester);


--
-- Name: idx_grade_student_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_grade_student_subject ON public.student_grades USING btree (student_user_id, subject);


--
-- Name: idx_grade_teacher; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_grade_teacher ON public.student_grades USING btree (teacher_user_id);


--
-- Name: idx_kiro2_cat_done; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_kiro2_cat_done ON public.kiro2_cat_sessions USING btree (user_id, completed_at DESC) WHERE (state = 'completed'::text);


--
-- Name: idx_kiro2_cat_sessions_user_state; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_kiro2_cat_sessions_user_state ON public.kiro2_cat_sessions USING btree (user_id, state, completed_at DESC);


--
-- Name: idx_kiro2_cat_sessions_user_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_kiro2_cat_sessions_user_subject ON public.kiro2_cat_sessions USING btree (user_id, subject_id);


--
-- Name: idx_kiro2_cat_subj; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_kiro2_cat_subj ON public.kiro2_cat_sessions USING btree (user_id, subject_id);


--
-- Name: idx_kiro2_cat_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_kiro2_cat_user ON public.kiro2_cat_sessions USING btree (user_id);


--
-- Name: idx_kiro2_le_question; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_kiro2_le_question ON public.kiro2_learning_events USING btree (question_id, event_type);


--
-- Name: idx_kiro2_le_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_kiro2_le_user ON public.kiro2_learning_events USING btree (user_id, occurred_at DESC);


--
-- Name: idx_kp_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_kp_code ON public.knowledge_points USING btree (code);


--
-- Name: idx_kp_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_kp_subject ON public.knowledge_points USING btree (subject);


--
-- Name: idx_kp_topic; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_kp_topic ON public.knowledge_points USING btree (topic_id);


--
-- Name: idx_league_hist_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_league_hist_student ON public.league_history USING btree (student_id);


--
-- Name: idx_league_history_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_league_history_student ON public.league_history USING btree (student_id);


--
-- Name: idx_league_history_week; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_league_history_week ON public.league_history USING btree (week_start);


--
-- Name: idx_league_membership_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_league_membership_student ON public.league_memberships USING btree (student_id);


--
-- Name: idx_league_membership_tier_week; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_league_membership_tier_week ON public.league_memberships USING btree (league_tier, week_start);


--
-- Name: idx_league_membership_xp_rank; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_league_membership_xp_rank ON public.league_memberships USING btree (league_tier, week_start, weekly_xp);


--
-- Name: idx_league_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_league_student ON public.league_memberships USING btree (student_id);


--
-- Name: idx_league_tier_week; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_league_tier_week ON public.league_memberships USING btree (league_tier, week_start);


--
-- Name: idx_learning_analytics_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_learning_analytics_date ON public.learning_analytics USING btree (date);


--
-- Name: idx_learning_analytics_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_learning_analytics_student ON public.learning_analytics USING btree (student_id);


--
-- Name: idx_learning_analytics_student_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_learning_analytics_student_date ON public.learning_analytics USING btree (student_id, date DESC);


--
-- Name: idx_learning_analytics_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_learning_analytics_subject ON public.learning_analytics USING btree (subject_area);


--
-- Name: idx_learning_events_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_learning_events_session ON public.kiro2_learning_events USING btree (session_id);


--
-- Name: idx_learning_events_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_learning_events_user ON public.kiro2_learning_events USING btree (user_id, occurred_at DESC);


--
-- Name: idx_learning_paths_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_learning_paths_student ON public.learning_paths USING btree (student_id);


--
-- Name: idx_learning_paths_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_learning_paths_subject ON public.learning_paths USING btree (student_id, subject);


--
-- Name: idx_manip_activity_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_manip_activity_created ON public.manipulative_activities USING btree (created_at);


--
-- Name: idx_manip_activity_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_manip_activity_user ON public.manipulative_activities USING btree (user_id);


--
-- Name: idx_manip_activity_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_manip_activity_user_created ON public.manipulative_activities USING btree (user_id, created_at);


--
-- Name: idx_manip_progress_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_manip_progress_type ON public.manipulative_progress USING btree (manipulative_type);


--
-- Name: idx_manip_progress_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_manip_progress_user ON public.manipulative_progress USING btree (user_id);


--
-- Name: idx_manip_progress_user_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_manip_progress_user_type ON public.manipulative_progress USING btree (user_id, manipulative_type);


--
-- Name: idx_meb_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_meb_active ON public.meb_curriculum_standards USING btree (is_active);


--
-- Name: idx_meb_grade_level; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_meb_grade_level ON public.meb_curriculum_standards USING btree (grade_level);


--
-- Name: idx_meb_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_meb_subject ON public.meb_curriculum_standards USING btree (subject);


--
-- Name: idx_meb_subject_grade; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_meb_subject_grade ON public.meb_curriculum_standards USING btree (subject, grade_level);


--
-- Name: idx_mentor_fb_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mentor_fb_session ON public.mentor_feedback USING btree (session_id);


--
-- Name: idx_mentor_pair_mentee; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mentor_pair_mentee ON public.mentor_pairs USING btree (mentee_id);


--
-- Name: idx_mentor_pair_mentor; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mentor_pair_mentor ON public.mentor_pairs USING btree (mentor_id);


--
-- Name: idx_mentor_pair_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mentor_pair_status ON public.mentor_pairs USING btree (status);


--
-- Name: idx_mentor_pair_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mentor_pair_subject ON public.mentor_pairs USING btree (subject_area);


--
-- Name: idx_mentor_sess_pair; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mentor_sess_pair ON public.mentor_sessions USING btree (pair_id);


--
-- Name: idx_mod_actions_expires; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mod_actions_expires ON public.moderation_actions USING btree (expires_at);


--
-- Name: idx_mod_actions_target; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mod_actions_target ON public.moderation_actions USING btree (target_user_id);


--
-- Name: idx_mod_actions_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mod_actions_type ON public.moderation_actions USING btree (action_type);


--
-- Name: idx_msg_audit_flagged; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_msg_audit_flagged ON public.message_audit_log USING btree (flagged);


--
-- Name: idx_msg_audit_sender; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_msg_audit_sender ON public.message_audit_log USING btree (sender_id);


--
-- Name: idx_mv_daily_stats_day; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mv_daily_stats_day ON public.mv_daily_question_stats USING btree (day DESC);


--
-- Name: idx_nano_skill_kp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_nano_skill_kp ON public.nano_skills USING btree (knowledge_point_id);


--
-- Name: idx_notification_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notification_created_at ON public.notifications USING btree (created_at);


--
-- Name: idx_notification_priority; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notification_priority ON public.notifications USING btree (user_id, priority, is_read);


--
-- Name: idx_notification_user_read; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notification_user_read ON public.notifications USING btree (user_id, is_read);


--
-- Name: idx_notifications_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_created ON public.notifications USING btree (created_at);


--
-- Name: idx_notifications_user_read; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_user_read ON public.notifications USING btree (user_id, is_read);


--
-- Name: idx_notifications_user_unread; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_user_unread ON public.notifications USING btree (user_id, is_read) WHERE (is_read = false);


--
-- Name: idx_oba_ch_oba; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_oba_ch_oba ON public.oba_challenges USING btree (oba_id);


--
-- Name: idx_oba_ch_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_oba_ch_status ON public.oba_challenges USING btree (status);


--
-- Name: idx_oba_prog_ch; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_oba_prog_ch ON public.oba_challenge_progress USING btree (challenge_id);


--
-- Name: idx_oba_prog_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_oba_prog_student ON public.oba_challenge_progress USING btree (student_id);


--
-- Name: idx_osym_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_osym_active ON public.osym_standards USING btree (is_active);


--
-- Name: idx_osym_exam_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_osym_exam_type ON public.osym_standards USING btree (exam_type);


--
-- Name: idx_osym_priority; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_osym_priority ON public.osym_standards USING btree (priority_level);


--
-- Name: idx_osym_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_osym_subject ON public.osym_standards USING btree (subject);


--
-- Name: idx_outcome_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_outcome_code ON public.learning_outcomes USING btree (code);


--
-- Name: idx_outcome_meb_standard; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_outcome_meb_standard ON public.learning_outcomes USING btree (meb_standard_id);


--
-- Name: idx_outcome_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_outcome_subject ON public.learning_outcomes USING btree (subject);


--
-- Name: idx_parent_approvals_parent_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_parent_approvals_parent_student ON public.parent_approvals USING btree (parent_user_id, student_user_id);


--
-- Name: idx_parent_notif_parent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_parent_notif_parent ON public.parent_notifications USING btree (parent_id);


--
-- Name: idx_parent_report_parent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_parent_report_parent ON public.parent_reports USING btree (parent_user_id, created_at);


--
-- Name: idx_parent_report_period; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_parent_report_period ON public.parent_reports USING btree (report_period);


--
-- Name: idx_parent_report_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_parent_report_student ON public.parent_reports USING btree (student_user_id);


--
-- Name: idx_parent_social_parent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_parent_social_parent ON public.parent_social_settings USING btree (parent_id);


--
-- Name: idx_parent_social_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_parent_social_student ON public.parent_social_settings USING btree (student_id);


--
-- Name: idx_path_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_path_created_at ON public.learning_paths USING btree (created_at);


--
-- Name: idx_path_student_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_path_student_subject ON public.learning_paths USING btree (student_id, subject);


--
-- Name: idx_peer_rec_cluster; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_peer_rec_cluster ON public.peer_recommendations USING btree (cluster_id);


--
-- Name: idx_peer_rec_source; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_peer_rec_source ON public.peer_recommendations USING btree (source_topic);


--
-- Name: idx_platform_stats_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_platform_stats_date ON public.platform_stats USING btree (stat_date DESC);


--
-- Name: idx_pomo_part_room; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pomo_part_room ON public.pomodoro_participants USING btree (room_id);


--
-- Name: idx_pomo_part_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pomo_part_student ON public.pomodoro_participants USING btree (student_id);


--
-- Name: idx_pomo_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pomo_status ON public.pomodoro_rooms USING btree (status);


--
-- Name: idx_pomo_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pomo_subject ON public.pomodoro_rooms USING btree (subject_area);


--
-- Name: idx_progress_student_node; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_progress_student_node ON public.topic_progress USING btree (student_id, node_id);


--
-- Name: idx_progress_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_progress_subject ON public.learning_progress_daily USING btree (subject, log_date DESC);


--
-- Name: idx_progress_user_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_progress_user_date ON public.learning_progress_daily USING btree (user_id, log_date DESC);


--
-- Name: idx_qb_calib_pool; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qb_calib_pool ON public.question_bank USING btree (is_calib_pool) WHERE (is_calib_pool = true);


--
-- Name: idx_qbank_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_active ON public.question_bank USING btree (is_active);


--
-- Name: idx_qbank_calib_pool; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_calib_pool ON public.question_bank USING btree (subject_area, is_calib_pool) WHERE ((is_calib_pool = true) AND (is_active = true));


--
-- Name: idx_qbank_calibrated; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_calibrated ON public.question_bank USING btree (is_calibrated);


--
-- Name: idx_qbank_calibrated_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_calibrated_active ON public.question_bank USING btree (is_calibrated, is_active, quality_score);


--
-- Name: idx_qbank_difficulty; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_difficulty ON public.question_bank USING btree (difficulty_level);


--
-- Name: idx_qbank_embedding_hnsw; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_embedding_hnsw ON public.question_bank USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: idx_qbank_exam_subject_difficulty; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_exam_subject_difficulty ON public.question_bank USING btree (exam_type, subject_area, irt_difficulty);


--
-- Name: idx_qbank_exam_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_exam_type ON public.question_bank USING btree (exam_type);


--
-- Name: idx_qbank_grade; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_grade ON public.question_bank USING btree (grade_level);


--
-- Name: idx_qbank_irt_difficulty; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_irt_difficulty ON public.question_bank USING btree (irt_difficulty);


--
-- Name: idx_qbank_quality; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_quality ON public.question_bank USING btree (quality_score);


--
-- Name: idx_qbank_source_book; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_source_book ON public.question_bank USING btree (source_book);


--
-- Name: idx_qbank_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_subject ON public.question_bank USING btree (subject_area);


--
-- Name: idx_qbank_text_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_text_gin ON public.question_bank USING gin (to_tsvector('simple'::regconfig, question_text));


--
-- Name: idx_qbank_topic; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_topic ON public.question_bank USING btree (primary_topic_id);


--
-- Name: idx_qbank_topic_difficulty; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qbank_topic_difficulty ON public.question_bank USING btree (primary_topic_id, difficulty_level);


--
-- Name: idx_qg_override_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_override_created ON public.quality_gates_override_audit USING btree (created_at);


--
-- Name: idx_qg_override_gate; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_override_gate ON public.quality_gates_override_audit USING btree (gate_name);


--
-- Name: idx_qg_override_pending; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_override_pending ON public.quality_gates_override_audit USING btree (status, expires_at) WHERE ((status)::text = 'pending'::text);


--
-- Name: idx_qg_override_requestor; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_override_requestor ON public.quality_gates_override_audit USING btree (requestor);


--
-- Name: idx_qg_override_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_override_status ON public.quality_gates_override_audit USING btree (status);


--
-- Name: idx_qg_result_gate; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_result_gate ON public.quality_gate_results USING btree (gate_name);


--
-- Name: idx_qg_result_run; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_result_run ON public.quality_gate_results USING btree (run_id);


--
-- Name: idx_qg_result_run_gate; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_result_run_gate ON public.quality_gate_results USING btree (run_id, gate_name);


--
-- Name: idx_qg_result_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_result_status ON public.quality_gate_results USING btree (status);


--
-- Name: idx_qg_run_branch; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_run_branch ON public.quality_gates_runs USING btree (branch);


--
-- Name: idx_qg_run_commit; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_run_commit ON public.quality_gates_runs USING btree (commit_hash);


--
-- Name: idx_qg_run_started; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_run_started ON public.quality_gates_runs USING btree (started_at);


--
-- Name: idx_qg_run_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_run_status ON public.quality_gates_runs USING btree (status);


--
-- Name: idx_qg_run_status_started; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_run_status_started ON public.quality_gates_runs USING btree (status, started_at);


--
-- Name: idx_qg_run_triggered_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qg_run_triggered_by ON public.quality_gates_runs USING btree (triggered_by);


--
-- Name: idx_qkm_knowledge_point; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qkm_knowledge_point ON public.question_knowledge_mappings USING btree (knowledge_point_id);


--
-- Name: idx_qkm_question; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qkm_question ON public.question_knowledge_mappings USING btree (question_id);


--
-- Name: idx_qmatrix_question; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qmatrix_question ON public.q_matrix USING btree (question_id);


--
-- Name: idx_qmatrix_skill; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qmatrix_skill ON public.q_matrix USING btree (nano_skill_id);


--
-- Name: idx_qperf_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qperf_date ON public.question_performance_analytics USING btree (analysis_date);


--
-- Name: idx_qperf_period; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qperf_period ON public.question_performance_analytics USING btree (period_type);


--
-- Name: idx_qperf_question; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qperf_question ON public.question_performance_analytics USING btree (question_id);


--
-- Name: idx_qtag_question; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qtag_question ON public.question_tag_associations USING btree (question_id);


--
-- Name: idx_qtag_tag; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_qtag_tag ON public.question_tag_associations USING btree (tag_id);


--
-- Name: idx_question_difficulty; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_question_difficulty ON public.questions USING btree (difficulty);


--
-- Name: idx_question_exam_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_question_exam_type ON public.questions USING btree (exam_type);


--
-- Name: idx_question_irt_difficulty; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_question_irt_difficulty ON public.questions USING btree (irt_difficulty);


--
-- Name: idx_question_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_question_subject ON public.questions USING btree (subject_area);


--
-- Name: idx_question_topic; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_question_topic ON public.questions USING btree (topic);


--
-- Name: idx_questions_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_active ON public.questions USING btree (exam_type, subject_area, difficulty) WHERE (aktif = true);


--
-- Name: idx_questions_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_created_at ON public.questions USING btree (created_at);


--
-- Name: idx_questions_subj_diff_aktif; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_subj_diff_aktif ON public.questions USING btree (subject_area, difficulty, aktif);


--
-- Name: idx_questions_text_gin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_text_gin ON public.questions USING gin (to_tsvector('simple'::regconfig, COALESCE(question_text, ''::text)));


--
-- Name: idx_questions_text_search; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_text_search ON public.questions USING gin (question_text public.gin_trgm_ops);


--
-- Name: idx_questions_topic_search; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_topic_search ON public.questions USING gin (topic public.gin_trgm_ops);


--
-- Name: idx_quiz_question_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_quiz_question_order ON public.quiz_questions USING btree (quiz_id, order_number);


--
-- Name: idx_quiz_student_quiz; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_quiz_student_quiz ON public.quiz_submissions USING btree (student_id, quiz_id);


--
-- Name: idx_quiz_subject_topic; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_quiz_subject_topic ON public.quizzes USING btree (subject, topic);


--
-- Name: idx_quiz_submitted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_quiz_submitted_at ON public.quiz_submissions USING btree (submitted_at);


--
-- Name: idx_realm_progress_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_realm_progress_student ON public.realm_progress USING btree (student_id);


--
-- Name: idx_refresh_token_expires; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_refresh_token_expires ON public.refresh_tokens USING btree (expires_at);


--
-- Name: idx_refresh_token_hash; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_refresh_token_hash ON public.refresh_tokens USING btree (token_hash);


--
-- Name: idx_refresh_token_jti; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_refresh_token_jti ON public.refresh_tokens USING btree (jti);


--
-- Name: idx_refresh_token_revoked; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_refresh_token_revoked ON public.refresh_tokens USING btree (revoked);


--
-- Name: idx_refresh_token_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_refresh_token_user ON public.refresh_tokens USING btree (user_id);


--
-- Name: idx_refresh_token_user_device; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_refresh_token_user_device ON public.refresh_tokens USING btree (user_id, device_id);


--
-- Name: idx_session_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_session_active ON public.sessions USING btree (is_active, expires_at);


--
-- Name: idx_session_expires_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_session_expires_at ON public.sessions USING btree (expires_at);


--
-- Name: idx_session_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_session_user_id ON public.sessions USING btree (user_id);


--
-- Name: idx_sks_knowledge_point; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sks_knowledge_point ON public.student_knowledge_states USING btree (knowledge_point_id);


--
-- Name: idx_sks_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sks_student ON public.student_knowledge_states USING btree (student_id);


--
-- Name: idx_snsm_skill; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_snsm_skill ON public.student_nano_skill_mastery USING btree (nano_skill_id);


--
-- Name: idx_snsm_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_snsm_student ON public.student_nano_skill_mastery USING btree (student_id);


--
-- Name: idx_streak_a; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_streak_a ON public.streak_pairs USING btree (student_a_id);


--
-- Name: idx_streak_b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_streak_b ON public.streak_pairs USING btree (student_b_id);


--
-- Name: idx_streak_log_pair; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_streak_log_pair ON public.streak_daily_log USING btree (pair_id);


--
-- Name: idx_streak_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_streak_status ON public.streak_pairs USING btree (status);


--
-- Name: idx_student_answer_error_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_answer_error_type ON public.student_answers USING btree (error_type);


--
-- Name: idx_student_answer_question; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_answer_question ON public.student_answers USING btree (question_id);


--
-- Name: idx_student_answer_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_answer_session ON public.student_answers USING btree (exam_session_id);


--
-- Name: idx_student_answers_response_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_answers_response_time ON public.student_answers USING btree (response_time_seconds) WHERE (response_time_seconds IS NOT NULL);


--
-- Name: idx_student_answers_session_correct; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_answers_session_correct ON public.student_answers USING btree (exam_session_id, is_correct);


--
-- Name: idx_student_exam_target; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_exam_target ON public.learning_path_student_profiles USING btree (exam_target);


--
-- Name: idx_student_grade; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_grade ON public.learning_path_student_profiles USING btree (grade);


--
-- Name: idx_student_grade_level; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_grade_level ON public.student_profiles USING btree (grade_level);


--
-- Name: idx_student_grade_style; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_grade_style ON public.student_profiles USING btree (grade_level, learning_style);


--
-- Name: idx_student_last_activity; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_last_activity ON public.learning_path_student_profiles USING btree (last_activity_at);


--
-- Name: idx_student_learning_style; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_learning_style ON public.student_profiles USING btree (learning_style);


--
-- Name: idx_student_profiles_grade; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_profiles_grade ON public.student_profiles USING btree (grade_level);


--
-- Name: idx_student_user_grade; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_user_grade ON public.student_profiles USING btree (user_id, grade_level);


--
-- Name: idx_student_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_user_id ON public.learning_path_student_profiles USING btree (user_id);


--
-- Name: idx_study_plans_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_study_plans_active ON public.study_plans USING btree (student_id, is_active);


--
-- Name: idx_study_plans_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_study_plans_student ON public.study_plans USING btree (student_id);


--
-- Name: idx_synthetic_events_question; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_synthetic_events_question ON public.kiro2_learning_events_synthetic USING btree (question_id);


--
-- Name: idx_synthetic_events_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_synthetic_events_user ON public.kiro2_learning_events_synthetic USING btree (user_id, occurred_at DESC);


--
-- Name: idx_tag_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tag_category ON public.question_tags USING btree (tag_category);


--
-- Name: idx_tag_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tag_name ON public.question_tags USING btree (tag_name);


--
-- Name: idx_teacher_school; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_teacher_school ON public.teacher_profiles USING btree (school_name);


--
-- Name: idx_th_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_th_subject ON public.topic_hierarchy USING btree (subject_area) WHERE (is_active = true);


--
-- Name: idx_topic_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_topic_code ON public.topic_hierarchy USING btree (code);


--
-- Name: idx_topic_level; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_topic_level ON public.topic_hierarchy USING btree (level);


--
-- Name: idx_topic_meb_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_topic_meb_code ON public.topic_hierarchy USING btree (meb_code);


--
-- Name: idx_topic_parent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_topic_parent ON public.topic_hierarchy USING btree (parent_id);


--
-- Name: idx_topic_prereqs_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_topic_prereqs_active ON public.topic_prerequisites USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_topic_prereqs_topic; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_topic_prereqs_topic ON public.topic_prerequisites USING btree (topic_id);


--
-- Name: idx_tp_prereq; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tp_prereq ON public.topic_prerequisites USING btree (prereq_id) WHERE is_active;


--
-- Name: idx_tp_topic; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tp_topic ON public.topic_prerequisites USING btree (topic_id) WHERE is_active;


--
-- Name: idx_uif_due; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_uif_due ON public.user_item_fsrs USING btree (user_id, due_date) WHERE (state = ANY (ARRAY[1, 2, 3]));


--
-- Name: idx_update_req_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_update_req_status ON public.curriculum_update_requests USING btree (status);


--
-- Name: idx_update_req_subject; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_update_req_subject ON public.curriculum_update_requests USING btree (subject);


--
-- Name: idx_update_req_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_update_req_type ON public.curriculum_update_requests USING btree (update_type);


--
-- Name: idx_user_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_created_at ON public.users USING btree (created_at);


--
-- Name: idx_user_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_email ON public.users USING btree (email);


--
-- Name: idx_user_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_role ON public.users USING btree (role);


--
-- Name: idx_user_theta_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_theta_user ON public.user_theta USING btree (user_id);


--
-- Name: idx_user_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_username ON public.users USING btree (username);


--
-- Name: idx_users_premium; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_premium ON public.users USING btree (email, username) WHERE (is_premium = true);


--
-- Name: idx_weekly_goals_plan; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_weekly_goals_plan ON public.weekly_goals USING btree (plan_id);


--
-- Name: idx_weekly_goals_week; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_weekly_goals_week ON public.weekly_goals USING btree (plan_id, week_number);


--
-- Name: idx_weekly_progress_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_weekly_progress_user ON public.weekly_progress USING btree (user_id);


--
-- Name: idx_weekly_progress_year_week; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_weekly_progress_year_week ON public.weekly_progress USING btree (year, week_number);


--
-- Name: idx_xp_transactions_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_xp_transactions_created ON public.xp_transactions USING btree (created_at DESC);


--
-- Name: idx_xp_transactions_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_xp_transactions_student ON public.xp_transactions USING btree (student_id);


--
-- Name: ix_api_keys_expires_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_api_keys_expires_at ON public.api_keys USING btree (expires_at);


--
-- Name: ix_api_keys_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_api_keys_is_active ON public.api_keys USING btree (is_active);


--
-- Name: ix_api_keys_key_hash; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_api_keys_key_hash ON public.api_keys USING btree (key_hash);


--
-- Name: ix_api_keys_key_prefix; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_api_keys_key_prefix ON public.api_keys USING btree (key_prefix);


--
-- Name: ix_api_keys_revoked; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_api_keys_revoked ON public.api_keys USING btree (revoked);


--
-- Name: ix_api_keys_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_api_keys_user_id ON public.api_keys USING btree (user_id);


--
-- Name: ix_manipulative_activities_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_manipulative_activities_created_at ON public.manipulative_activities USING btree (created_at);


--
-- Name: ix_manipulative_activities_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_manipulative_activities_id ON public.manipulative_activities USING btree (id);


--
-- Name: ix_manipulative_activities_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_manipulative_activities_user_id ON public.manipulative_activities USING btree (user_id);


--
-- Name: ix_manipulative_progress_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_manipulative_progress_id ON public.manipulative_progress USING btree (id);


--
-- Name: ix_manipulative_progress_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_manipulative_progress_user_id ON public.manipulative_progress USING btree (user_id);


--
-- Name: ix_notifications_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_notifications_created_at ON public.notifications USING btree (created_at);


--
-- Name: ix_notifications_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_notifications_id ON public.notifications USING btree (id);


--
-- Name: ix_notifications_is_read; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_notifications_is_read ON public.notifications USING btree (is_read);


--
-- Name: ix_notifications_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: ix_point_transactions_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_point_transactions_timestamp ON public.point_transactions USING btree ("timestamp");


--
-- Name: ix_point_transactions_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_point_transactions_user_id ON public.point_transactions USING btree (user_id);


--
-- Name: ix_refresh_tokens_expires_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_refresh_tokens_expires_at ON public.refresh_tokens USING btree (expires_at);


--
-- Name: ix_refresh_tokens_jti; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_refresh_tokens_jti ON public.refresh_tokens USING btree (jti);


--
-- Name: ix_refresh_tokens_revoked; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_refresh_tokens_revoked ON public.refresh_tokens USING btree (revoked);


--
-- Name: ix_refresh_tokens_token_hash; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_refresh_tokens_token_hash ON public.refresh_tokens USING btree (token_hash);


--
-- Name: ix_refresh_tokens_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_refresh_tokens_user_id ON public.refresh_tokens USING btree (user_id);


--
-- Name: ix_sessions_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_sessions_token ON public.sessions USING btree (token);


--
-- Name: ix_student_goals_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_student_goals_id ON public.student_goals USING btree (id);


--
-- Name: ix_student_goals_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_student_goals_user_id ON public.student_goals USING btree (user_id);


--
-- Name: ix_student_learning_profiles_hybrid_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_student_learning_profiles_hybrid_code ON public.student_learning_profiles USING btree (hybrid_code);


--
-- Name: ix_student_learning_profiles_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_student_learning_profiles_id ON public.student_learning_profiles USING btree (id);


--
-- Name: ix_student_learning_profiles_student_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_student_learning_profiles_student_id ON public.student_learning_profiles USING btree (student_id);


--
-- Name: ix_user_achievements_achievement_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_achievements_achievement_id ON public.user_achievements USING btree (achievement_id);


--
-- Name: ix_user_achievements_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_achievements_user_id ON public.user_achievements USING btree (user_id);


--
-- Name: ix_user_badges_badge_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_badges_badge_id ON public.user_badges USING btree (badge_id);


--
-- Name: ix_user_badges_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_badges_user_id ON public.user_badges USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_weekly_progress_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_weekly_progress_id ON public.weekly_progress USING btree (id);


--
-- Name: ix_weekly_progress_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_weekly_progress_user_id ON public.weekly_progress USING btree (user_id);


--
-- Name: ix_zpd_history_student_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_zpd_history_student_id ON public.zpd_history USING btree (student_id);


--
-- Name: ix_zpd_history_topic_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_zpd_history_topic_id ON public.zpd_history USING btree (topic_id);


--
-- Name: user_item_fsrs trg_fsrs_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_fsrs_updated_at BEFORE UPDATE ON public.user_item_fsrs FOR EACH ROW EXECUTE FUNCTION public.update_fsrs_updated_at();


--
-- Name: student_answers trg_sync_answer_to_le; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_sync_answer_to_le AFTER INSERT OR UPDATE OF is_correct ON public.student_answers FOR EACH ROW WHEN ((new.is_correct IS NOT NULL)) EXECUTE FUNCTION public.fn_sync_answer_to_learning_events();


--
-- Name: kiro2_learning_events trg_update_qb_stats; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_update_qb_stats AFTER INSERT ON public.kiro2_learning_events FOR EACH ROW EXECUTE FUNCTION public.fn_update_qb_stats_from_le();


--
-- Name: student_answers trg_update_qb_stats_sa; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_update_qb_stats_sa AFTER INSERT ON public.student_answers FOR EACH ROW EXECUTE FUNCTION public.fn_update_qb_stats_from_sa();


--
-- Name: kiro2_learning_events trg_update_student_ability; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_update_student_ability AFTER INSERT ON public.kiro2_learning_events FOR EACH ROW EXECUTE FUNCTION public.fn_update_student_ability();


--
-- Name: api_keys api_keys_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: bkt_states bkt_states_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bkt_states
    ADD CONSTRAINT bkt_states_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id);


--
-- Name: chat_messages chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: class_reports class_reports_teacher_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.class_reports
    ADD CONSTRAINT class_reports_teacher_user_id_fkey FOREIGN KEY (teacher_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: classrooms classrooms_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classrooms
    ADD CONSTRAINT classrooms_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teacher_profiles(id) ON DELETE CASCADE;


--
-- Name: curriculum_alignments curriculum_alignments_meb_standard_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curriculum_alignments
    ADD CONSTRAINT curriculum_alignments_meb_standard_id_fkey FOREIGN KEY (meb_standard_id) REFERENCES public.meb_curriculum_standards(id) ON DELETE CASCADE;


--
-- Name: curriculum_alignments curriculum_alignments_osym_standard_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curriculum_alignments
    ADD CONSTRAINT curriculum_alignments_osym_standard_id_fkey FOREIGN KEY (osym_standard_id) REFERENCES public.osym_standards(id) ON DELETE CASCADE;


--
-- Name: duel_matches duel_matches_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.duel_matches
    ADD CONSTRAINT duel_matches_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.duel_sessions(id);


--
-- Name: duels duels_player1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.duels
    ADD CONSTRAINT duels_player1_id_fkey FOREIGN KEY (player1_id) REFERENCES public.users(id);


--
-- Name: duels duels_player2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.duels
    ADD CONSTRAINT duels_player2_id_fkey FOREIGN KEY (player2_id) REFERENCES public.users(id);


--
-- Name: eba_content_collections eba_content_collections_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_content_collections
    ADD CONSTRAINT eba_content_collections_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: eba_video_recommendations eba_video_recommendations_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_video_recommendations
    ADD CONSTRAINT eba_video_recommendations_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: eba_video_recommendations eba_video_recommendations_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_video_recommendations
    ADD CONSTRAINT eba_video_recommendations_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.eba_videos(id) ON DELETE CASCADE;


--
-- Name: eba_video_usage eba_video_usage_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_video_usage
    ADD CONSTRAINT eba_video_usage_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: eba_video_usage eba_video_usage_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_video_usage
    ADD CONSTRAINT eba_video_usage_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.eba_videos(id) ON DELETE CASCADE;


--
-- Name: eba_videos eba_videos_moderated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eba_videos
    ADD CONSTRAINT eba_videos_moderated_by_fkey FOREIGN KEY (moderated_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: exam_questions exam_questions_exam_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exam_questions
    ADD CONSTRAINT exam_questions_exam_session_id_fkey FOREIGN KEY (exam_session_id) REFERENCES public.exam_sessions(id) ON DELETE CASCADE;


--
-- Name: exam_sessions exam_sessions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exam_sessions
    ADD CONSTRAINT exam_sessions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: fsrs_cards fsrs_cards_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_cards
    ADD CONSTRAINT fsrs_cards_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: fsrs_reviews fsrs_reviews_card_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_reviews
    ADD CONSTRAINT fsrs_reviews_card_id_fkey FOREIGN KEY (card_id) REFERENCES public.fsrs_cards(id) ON DELETE CASCADE;


--
-- Name: fsrs_reviews fsrs_reviews_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_reviews
    ADD CONSTRAINT fsrs_reviews_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: fsrs_schedules fsrs_schedules_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_schedules
    ADD CONSTRAINT fsrs_schedules_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: fsrs_student_profiles fsrs_student_profiles_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_student_profiles
    ADD CONSTRAINT fsrs_student_profiles_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: fsrs_study_sessions fsrs_study_sessions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_study_sessions
    ADD CONSTRAINT fsrs_study_sessions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: fsrs_subject_stats fsrs_subject_stats_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsrs_subject_stats
    ADD CONSTRAINT fsrs_subject_stats_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: irt_calibration_history irt_calibration_history_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.irt_calibration_history
    ADD CONSTRAINT irt_calibration_history_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: learning_analytics learning_analytics_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.learning_analytics
    ADD CONSTRAINT learning_analytics_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: learning_outcomes learning_outcomes_meb_standard_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.learning_outcomes
    ADD CONSTRAINT learning_outcomes_meb_standard_id_fkey FOREIGN KEY (meb_standard_id) REFERENCES public.meb_curriculum_standards(id) ON DELETE CASCADE;


--
-- Name: learning_path_student_profiles learning_path_student_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.learning_path_student_profiles
    ADD CONSTRAINT learning_path_student_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: learning_paths learning_paths_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.learning_paths
    ADD CONSTRAINT learning_paths_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.learning_path_student_profiles(student_id);


--
-- Name: manipulative_activities manipulative_activities_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.manipulative_activities
    ADD CONSTRAINT manipulative_activities_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: manipulative_progress manipulative_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.manipulative_progress
    ADD CONSTRAINT manipulative_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: oba_uyeler oba_uyeler_oba_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.oba_uyeler
    ADD CONSTRAINT oba_uyeler_oba_id_fkey FOREIGN KEY (oba_id) REFERENCES public.obalar(id);


--
-- Name: oba_uyeler oba_uyeler_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.oba_uyeler
    ADD CONSTRAINT oba_uyeler_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: parent_approvals parent_approvals_parent_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_approvals
    ADD CONSTRAINT parent_approvals_parent_user_id_fkey FOREIGN KEY (parent_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_approvals parent_approvals_student_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_approvals
    ADD CONSTRAINT parent_approvals_student_user_id_fkey FOREIGN KEY (student_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_child parent_child_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_child
    ADD CONSTRAINT parent_child_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.users(id);


--
-- Name: parent_child parent_child_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_child
    ADD CONSTRAINT parent_child_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.users(id);


--
-- Name: parent_notifications parent_notifications_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_notifications
    ADD CONSTRAINT parent_notifications_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.users(id);


--
-- Name: parent_notifications parent_notifications_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_notifications
    ADD CONSTRAINT parent_notifications_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_profiles parent_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_profiles
    ADD CONSTRAINT parent_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_reports parent_reports_parent_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_reports
    ADD CONSTRAINT parent_reports_parent_user_id_fkey FOREIGN KEY (parent_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_reports parent_reports_student_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parent_reports
    ADD CONSTRAINT parent_reports_student_user_id_fkey FOREIGN KEY (student_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: point_transactions point_transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.point_transactions
    ADD CONSTRAINT point_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: q_matrix q_matrix_nano_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.q_matrix
    ADD CONSTRAINT q_matrix_nano_skill_id_fkey FOREIGN KEY (nano_skill_id) REFERENCES public.nano_skills(id) ON DELETE CASCADE;


--
-- Name: quality_gate_results quality_gate_results_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quality_gate_results
    ADD CONSTRAINT quality_gate_results_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.quality_gates_runs(id) ON DELETE CASCADE;


--
-- Name: quality_gates_override_audit quality_gates_override_audit_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quality_gates_override_audit
    ADD CONSTRAINT quality_gates_override_audit_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.quality_gates_runs(id) ON DELETE SET NULL;


--
-- Name: question_bank question_bank_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_bank
    ADD CONSTRAINT question_bank_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: question_bank question_bank_primary_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_bank
    ADD CONSTRAINT question_bank_primary_topic_id_fkey FOREIGN KEY (primary_topic_id) REFERENCES public.topic_hierarchy(id);


--
-- Name: question_bank question_bank_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_bank
    ADD CONSTRAINT question_bank_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: question_performance_analytics question_performance_analytics_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_performance_analytics
    ADD CONSTRAINT question_performance_analytics_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: question_tag_associations question_tag_associations_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_tag_associations
    ADD CONSTRAINT question_tag_associations_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: question_tag_associations question_tag_associations_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_tag_associations
    ADD CONSTRAINT question_tag_associations_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.question_tags(id) ON DELETE CASCADE;


--
-- Name: questions questions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: quiz_questions quiz_questions_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: quiz_questions quiz_questions_quiz_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_quiz_id_fkey FOREIGN KEY (quiz_id) REFERENCES public.quizzes(id) ON DELETE CASCADE;


--
-- Name: quiz_submissions quiz_submissions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_submissions
    ADD CONSTRAINT quiz_submissions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.learning_path_student_profiles(student_id);


--
-- Name: realm_progress realm_progress_realm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_progress
    ADD CONSTRAINT realm_progress_realm_id_fkey FOREIGN KEY (realm_id) REFERENCES public.realms(id);


--
-- Name: realm_progress realm_progress_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_progress
    ADD CONSTRAINT realm_progress_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id);


--
-- Name: refresh_tokens refresh_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: streaks streaks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.streaks
    ADD CONSTRAINT streaks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: student_abilities student_abilities_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_abilities
    ADD CONSTRAINT student_abilities_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id);


--
-- Name: student_answers student_answers_exam_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_answers
    ADD CONSTRAINT student_answers_exam_session_id_fkey FOREIGN KEY (exam_session_id) REFERENCES public.exam_sessions(id) ON DELETE CASCADE;


--
-- Name: student_goals student_goals_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_goals
    ADD CONSTRAINT student_goals_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_grades student_grades_student_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_grades
    ADD CONSTRAINT student_grades_student_user_id_fkey FOREIGN KEY (student_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_grades student_grades_teacher_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_grades
    ADD CONSTRAINT student_grades_teacher_user_id_fkey FOREIGN KEY (teacher_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_learning_profiles student_learning_profiles_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_learning_profiles
    ADD CONSTRAINT student_learning_profiles_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_nano_skill_mastery student_nano_skill_mastery_nano_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_nano_skill_mastery
    ADD CONSTRAINT student_nano_skill_mastery_nano_skill_id_fkey FOREIGN KEY (nano_skill_id) REFERENCES public.nano_skills(id) ON DELETE CASCADE;


--
-- Name: student_nano_skill_mastery student_nano_skill_mastery_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_nano_skill_mastery
    ADD CONSTRAINT student_nano_skill_mastery_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id);


--
-- Name: student_profiles student_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: study_plans study_plans_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.study_plans
    ADD CONSTRAINT study_plans_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id);


--
-- Name: teacher_profiles teacher_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teacher_profiles
    ADD CONSTRAINT teacher_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: topic_completions topic_completions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_completions
    ADD CONSTRAINT topic_completions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.learning_path_student_profiles(student_id);


--
-- Name: topic_hierarchy topic_hierarchy_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_hierarchy
    ADD CONSTRAINT topic_hierarchy_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.topic_hierarchy(id) ON DELETE CASCADE;


--
-- Name: topic_prerequisites topic_prerequisites_prereq_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_prerequisites
    ADD CONSTRAINT topic_prerequisites_prereq_id_fkey FOREIGN KEY (prereq_id) REFERENCES public.topic_hierarchy(id);


--
-- Name: topic_prerequisites topic_prerequisites_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_prerequisites
    ADD CONSTRAINT topic_prerequisites_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topic_hierarchy(id);


--
-- Name: topic_progress topic_progress_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.topic_progress
    ADD CONSTRAINT topic_progress_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.learning_path_student_profiles(student_id);


--
-- Name: user_achievements user_achievements_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_badges user_badges_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_badges
    ADD CONSTRAINT user_badges_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: weekly_goals weekly_goals_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.weekly_goals
    ADD CONSTRAINT weekly_goals_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.study_plans(id) ON DELETE CASCADE;


--
-- Name: weekly_progress weekly_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.weekly_progress
    ADD CONSTRAINT weekly_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: xp_transactions xp_transactions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.xp_transactions
    ADD CONSTRAINT xp_transactions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id);


--
-- Name: zpd_history zpd_history_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zpd_history
    ADD CONSTRAINT zpd_history_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict tPaEriuD4U5rB6c2wCBcSBB2vgvgbjh4GzP55VvOhUNyEO6g8F3l6bp7yRtf96o

