--
-- PostgreSQL database dump
--


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
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: accommodationtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.accommodationtype AS ENUM (
    'STATE_DORMITORY',
    'UNIVERSITY_DORMITORY',
    'PRIVATE_DORMITORY',
    'APARTMENT',
    'SHARED_APARTMENT'
);


--
-- Name: appointmentstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.appointmentstatus AS ENUM (
    'PENDING',
    'CONFIRMED',
    'CANCELLED',
    'COMPLETED',
    'NO_SHOW'
);


--
-- Name: appointmenttype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.appointmenttype AS ENUM (
    'ONE_ON_ONE',
    'GROUP_SESSION',
    'QUESTION_ANSWER',
    'EXAM_PREP'
);


--
-- Name: campustype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.campustype AS ENUM (
    'MAIN_CAMPUS',
    'SATELLITE_CAMPUS',
    'MEDICAL_CAMPUS',
    'RESEARCH_CAMPUS'
);


--
-- Name: certificationtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.certificationtype AS ENUM (
    'TEACHING_LICENSE',
    'UNIVERSITY_DEGREE',
    'MASTERS_DEGREE',
    'PHD_DEGREE',
    'TRAINING_CERTIFICATE',
    'EXPERIENCE_CERTIFICATE'
);


--
-- Name: consent_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.consent_status AS ENUM (
    'given',
    'withdrawn',
    'expired'
);


--
-- Name: data_processing_purpose; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.data_processing_purpose AS ENUM (
    'service_provision',
    'account_management',
    'authentication',
    'communication',
    'notifications',
    'support',
    'analytics',
    'performance_monitoring',
    'product_improvement',
    'marketing',
    'personalization',
    'legal_compliance',
    'fraud_prevention',
    'exam_evaluation',
    'progress_tracking',
    'content_recommendation'
);


--
-- Name: dayofweek; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.dayofweek AS ENUM (
    'MONDAY',
    'TUESDAY',
    'WEDNESDAY',
    'THURSDAY',
    'FRIDAY',
    'SATURDAY',
    'SUNDAY'
);


--
-- Name: deletion_request_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.deletion_request_status AS ENUM (
    'pending',
    'approved',
    'processing',
    'completed',
    'rejected'
);


--
-- Name: ebacontentcategory; Type: TYPE; Schema: public; Owner: -
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


--
-- Name: ebagradelevel; Type: TYPE; Schema: public; Owner: -
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


--
-- Name: ebavideoquality; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.ebavideoquality AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH'
);


--
-- Name: educationalrecordtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.educationalrecordtype AS ENUM (
    'ACADEMIC_PERFORMANCE',
    'ATTENDANCE',
    'BEHAVIORAL_RECORDS',
    'HEALTH_RECORDS',
    'SPECIAL_EDUCATION',
    'DISCIPLINARY_RECORDS',
    'STANDARDIZED_TEST_SCORES'
);


--
-- Name: examtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.examtype AS ENUM (
    'TYT',
    'AYT',
    'YDT',
    'DENEME'
);


--
-- Name: experiencelevel; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.experiencelevel AS ENUM (
    'ENTRY',
    'JUNIOR',
    'MID',
    'SENIOR',
    'EXPERT'
);


--
-- Name: export_request_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.export_request_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed',
    'expired'
);


--
-- Name: exportformat; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.exportformat AS ENUM (
    'MARKDOWN',
    'PDF',
    'JSON'
);


--
-- Name: filetype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.filetype AS ENUM (
    'DOCUMENT',
    'IMAGE',
    'VIDEO',
    'AUDIO',
    'ARCHIVE',
    'OTHER'
);


--
-- Name: fileversionstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.fileversionstatus AS ENUM (
    'CURRENT',
    'ARCHIVED'
);


--
-- Name: goalstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.goalstatus AS ENUM (
    'ACTIVE',
    'COMPLETED',
    'AT_RISK',
    'CANCELLED'
);


--
-- Name: imageprocessingstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.imageprocessingstatus AS ENUM (
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'FAILED'
);


--
-- Name: industrytype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.industrytype AS ENUM (
    'TECHNOLOGY',
    'FINANCE',
    'HEALTHCARE',
    'EDUCATION',
    'MANUFACTURING',
    'RETAIL',
    'CONSULTING',
    'GOVERNMENT',
    'STARTUP',
    'OTHER'
);


--
-- Name: insightcategory; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.insightcategory AS ENUM (
    'TECHNICAL',
    'PROCESS',
    'COMMUNICATION'
);


--
-- Name: learningstyle; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.learningstyle AS ENUM (
    'VISUAL',
    'AUDITORY',
    'KINESTHETIC',
    'READING_WRITING'
);


--
-- Name: llmproviderenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.llmproviderenum AS ENUM (
    'GEMINI',
    'OPENAI',
    'CLAUDE',
    'QWEN',
    'ENSEMBLE'
);


--
-- Name: memberrole; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.memberrole AS ENUM (
    'OWNER',
    'ADMIN',
    'MODERATOR',
    'MEMBER'
);


--
-- Name: memberstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.memberstatus AS ENUM (
    'ACTIVE',
    'INVITED',
    'BANNED'
);


--
-- Name: messagetype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.messagetype AS ENUM (
    'TEXT',
    'FILE',
    'IMAGE',
    'LINK',
    'SYSTEM'
);


--
-- Name: parentalconsentstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.parentalconsentstatus AS ENUM (
    'PENDING',
    'VERIFIED',
    'DENIED',
    'EXPIRED',
    'WITHDRAWN'
);


--
-- Name: participantrole; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.participantrole AS ENUM (
    'HOST',
    'CO_HOST',
    'PARTICIPANT',
    'OBSERVER'
);


--
-- Name: platformtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.platformtype AS ENUM (
    'ZOOM',
    'GOOGLE_MEET',
    'JITSI',
    'CUSTOM'
);


--
-- Name: programtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.programtype AS ENUM (
    'NORMAL',
    'KKTC',
    'OZEL_YETENEK',
    'IKINCI_OGRETIM'
);


--
-- Name: questiondifficulty; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.questiondifficulty AS ENUM (
    'EASY',
    'MEDIUM',
    'HARD'
);


--
-- Name: questiondifficultylevel; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.questiondifficultylevel AS ENUM (
    'VERY_EASY',
    'EASY',
    'MEDIUM',
    'HARD',
    'VERY_HARD'
);


--
-- Name: reasoningsessionstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.reasoningsessionstatus AS ENUM (
    'PENDING',
    'IN_PROGRESS',
    'COMPLETED',
    'FAILED',
    'TIMEOUT'
);


--
-- Name: reasoningsteptypeenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.reasoningsteptypeenum AS ENUM (
    'UNDERSTANDING',
    'DECOMPOSITION',
    'CALCULATION',
    'INFERENCE',
    'VERIFICATION',
    'CONCLUSION'
);


--
-- Name: recordingstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.recordingstatus AS ENUM (
    'RECORDING',
    'PROCESSING',
    'READY',
    'FAILED'
);


--
-- Name: reflectiondepth; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.reflectiondepth AS ENUM (
    'SURFACE',
    'MODERATE',
    'DEEP'
);


--
-- Name: roomstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.roomstatus AS ENUM (
    'ACTIVE',
    'ARCHIVED',
    'DELETED'
);


--
-- Name: roomvisibility; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.roomvisibility AS ENUM (
    'PUBLIC',
    'PRIVATE',
    'PASSWORD'
);


--
-- Name: scholarshiptype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.scholarshiptype AS ENUM (
    'FULL_SCHOLARSHIP',
    'PARTIAL_SCHOLARSHIP',
    'MERIT_BASED',
    'NEED_BASED',
    'SPORTS',
    'ACADEMIC_EXCELLENCE',
    'SPECIAL_TALENT'
);


--
-- Name: scoretype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.scoretype AS ENUM (
    'SAY',
    'EA',
    'SOZ',
    'DIL'
);


--
-- Name: screensharetype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.screensharetype AS ENUM (
    'ENTIRE_SCREEN',
    'WINDOW',
    'APPLICATION',
    'WHITEBOARD'
);


--
-- Name: sessionstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sessionstatus AS ENUM (
    'SCHEDULED',
    'LIVE',
    'ENDED',
    'CANCELLED'
);


--
-- Name: sessiontype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sessiontype AS ENUM (
    'ONE_ON_ONE',
    'GROUP_SESSION',
    'WEBINAR',
    'STUDY_GROUP'
);


--
-- Name: subjectarea; Type: TYPE; Schema: public; Owner: -
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


--
-- Name: subjectexpertise; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.subjectexpertise AS ENUM (
    'MATHEMATICS',
    'PHYSICS',
    'CHEMISTRY',
    'BIOLOGY',
    'TURKISH',
    'HISTORY',
    'GEOGRAPHY',
    'ENGLISH',
    'PHILOSOPHY',
    'LITERATURE',
    'GEOMETRY'
);


--
-- Name: teacherstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.teacherstatus AS ENUM (
    'PENDING',
    'VERIFIED',
    'SUSPENDED',
    'REJECTED'
);


--
-- Name: timeslotstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.timeslotstatus AS ENUM (
    'AVAILABLE',
    'BOOKED',
    'BLOCKED'
);


--
-- Name: transcriptstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.transcriptstatus AS ENUM (
    'NOT_GENERATED',
    'GENERATING',
    'AUTO_GENERATED',
    'MANUALLY_EDITED',
    'VERIFIED'
);


--
-- Name: universitytype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.universitytype AS ENUM (
    'DEVLET',
    'VAKIF'
);


--
-- Name: userrole; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.userrole AS ENUM (
    'STUDENT',
    'TEACHER',
    'PARENT',
    'ADMIN',
    'SUPER_ADMIN'
);


--
-- Name: verificationstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.verificationstatus AS ENUM (
    'NOT_SUBMITTED',
    'PENDING',
    'APPROVED',
    'REJECTED'
);


--
-- Name: videoformat; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.videoformat AS ENUM (
    'MP4',
    'WEBM',
    'AVI',
    'MOV',
    'MKV'
);


--
-- Name: videoprocessingstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.videoprocessingstatus AS ENUM (
    'PENDING',
    'VALIDATING',
    'COMPRESSING',
    'TRANSCODING',
    'GENERATING_THUMBNAILS',
    'GENERATING_TRANSCRIPT',
    'READY',
    'FAILED',
    'ARCHIVED'
);


--
-- Name: whiteboardtooltype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.whiteboardtooltype AS ENUM (
    'PEN',
    'ERASER',
    'TEXT',
    'SHAPE',
    'HIGHLIGHTER',
    'EQUATION'
);


--
-- Name: refresh_safe_for_beta(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.refresh_safe_for_beta() RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_safe_for_beta;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: api_keys; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_keys (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.api_keys FORCE ROW LEVEL SECURITY;


--
-- Name: appointment_reminders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.appointment_reminders (
    id character varying NOT NULL,
    appointment_id character varying NOT NULL,
    remind_at timestamp with time zone NOT NULL,
    reminder_type character varying(50),
    is_sent boolean,
    sent_at timestamp with time zone,
    recipient_type character varying(50),
    recipient_id character varying,
    message_template character varying(100),
    message_sent text,
    delivery_status character varying(50),
    error_message text,
    created_at timestamp with time zone
);


--
-- Name: appointments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.appointments (
    id character varying NOT NULL,
    teacher_id character varying NOT NULL,
    student_id character varying NOT NULL,
    availability_slot_id character varying,
    appointment_type public.appointmenttype,
    subject public.subjectexpertise,
    scheduled_date date NOT NULL,
    start_time time without time zone NOT NULL,
    end_time time without time zone NOT NULL,
    duration_minutes integer,
    status public.appointmentstatus,
    topic character varying(255),
    description text,
    student_notes text,
    teacher_notes text,
    preparation_materials jsonb,
    confirmed_at timestamp with time zone,
    confirmed_by character varying,
    cancelled_at timestamp with time zone,
    cancelled_by character varying,
    cancellation_reason text,
    completed_at timestamp with time zone,
    session_summary text,
    homework_assigned text,
    meeting_url character varying(500),
    meeting_id character varying(100),
    meeting_password character varying(100),
    reminder_sent_at timestamp with time zone,
    reminder_count integer,
    price double precision,
    currency character varying(10),
    payment_status character varying(50),
    meta_data jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.audit_logs FORCE ROW LEVEL SECURITY;


--
-- Name: badges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.badges (
    id character varying NOT NULL,
    slug character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    description character varying,
    icon character varying(10),
    category character varying(20),
    condition json
);


--
-- Name: billing_data_processing_agreements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.billing_data_processing_agreements (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    version character varying(20) DEFAULT 'v1'::character varying NOT NULL,
    status character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    signer_name character varying(200),
    signer_email character varying(255),
    signed_at timestamp with time zone,
    document_url character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: bkt_states; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bkt_states (
    student_id character varying NOT NULL,
    topic_id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    p_learn real,
    p_transit real,
    p_guess real,
    p_slip real,
    attempt_count integer,
    mastery_status character varying(20),
    last_attempt timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE ONLY public.bkt_states FORCE ROW LEVEL SECURITY;


--
-- Name: blocked_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.blocked_users (
    id character varying NOT NULL,
    blocker_id character varying NOT NULL,
    blocked_id character varying NOT NULL,
    reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: campus_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.campus_info (
    id uuid NOT NULL,
    university_id uuid NOT NULL,
    campus_name character varying(255) NOT NULL,
    campus_type public.campustype,
    city character varying(100) NOT NULL,
    district character varying(100),
    address text,
    total_area_sqm integer,
    building_count integer,
    libraries jsonb,
    sports_facilities character varying[],
    laboratories jsonb,
    dining_facilities jsonb,
    health_center boolean,
    counseling_center boolean,
    career_center boolean,
    international_office boolean,
    wifi_available boolean,
    computer_labs integer,
    online_resources boolean,
    student_clubs jsonb,
    total_student_clubs integer,
    cultural_centers character varying[],
    events_per_year integer,
    public_transport_access boolean,
    shuttle_service boolean,
    parking_spaces integer,
    bicycle_friendly boolean,
    wheelchair_accessible boolean,
    disability_support boolean,
    description text,
    highlights character varying[],
    photos character varying[],
    phone character varying(50),
    email character varying(255),
    website character varying(255),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: career_opportunities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.career_opportunities (
    id uuid NOT NULL,
    department_id uuid NOT NULL,
    job_title character varying(200) NOT NULL,
    job_description text,
    industry_type public.industrytype,
    employment_rate double precision,
    average_hiring_time_days integer,
    demand_level character varying(20),
    required_skills character varying[],
    preferred_certifications character varying[],
    career_growth_potential character varying(20),
    promotion_timeline_years integer,
    top_employers character varying[],
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: chat_analytics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_analytics (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying,
    date timestamp with time zone NOT NULL,
    period_type character varying(20),
    total_sessions integer,
    active_sessions integer,
    completed_sessions integer,
    total_messages integer,
    user_messages integer,
    assistant_messages integer,
    total_images integer,
    images_with_math integer,
    images_handwritten integer,
    subject_distribution jsonb,
    avg_response_time_ms double precision,
    avg_confidence_score double precision,
    avg_user_rating double precision,
    helpful_responses integer,
    total_tokens integer,
    total_cost double precision,
    last_updated timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE ONLY public.chat_analytics FORCE ROW LEVEL SECURITY;


--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_messages (
    id character varying NOT NULL,
    session_id character varying NOT NULL,
    role character varying(50) NOT NULL,
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
    meta_data jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_sessions (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    title character varying(255),
    subject_type character varying(50),
    status character varying(50),
    context jsonb,
    meta_data jsonb,
    model_name character varying(100),
    temperature double precision,
    max_tokens integer,
    message_count integer,
    total_tokens integer,
    total_cost double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_message_at timestamp with time zone
);

ALTER TABLE ONLY public.chat_sessions FORCE ROW LEVEL SECURITY;


--
-- Name: city_living_costs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.city_living_costs (
    id uuid NOT NULL,
    city character varying(100) NOT NULL,
    region character varying(100),
    rent_studio_min integer,
    rent_studio_max integer,
    rent_studio_avg integer,
    rent_1br_min integer,
    rent_1br_max integer,
    rent_1br_avg integer,
    rent_2br_min integer,
    rent_2br_max integer,
    rent_2br_avg integer,
    shared_room_min integer,
    shared_room_max integer,
    shared_room_avg integer,
    utilities_min integer,
    utilities_max integer,
    utilities_avg integer,
    food_budget_min integer,
    food_budget_max integer,
    food_budget_avg integer,
    meal_restaurant_avg integer,
    meal_inexpensive_avg integer,
    groceries_weekly_avg integer,
    public_transport_monthly integer,
    public_transport_single integer,
    taxi_start_fare integer,
    taxi_per_km integer,
    student_transport_discount double precision,
    entertainment_min integer,
    entertainment_max integer,
    entertainment_avg integer,
    books_supplies_avg integer,
    personal_care_avg integer,
    phone_internet_avg integer,
    total_min_budget integer,
    total_avg_budget integer,
    total_comfortable_budget integer,
    cost_of_living_index double precision,
    student_discount_available boolean,
    notes text,
    year integer NOT NULL,
    month integer,
    currency character varying(10),
    data_source character varying(255),
    sample_size integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: class_reports; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN class_reports.class_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.class_reports.class_name IS '12-A, 11-B, etc.';


--
-- Name: COLUMN class_reports.report_period; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.class_reports.report_period IS '2025-W47, 2025-Q1, etc.';


--
-- Name: COLUMN class_reports.grade_distribution; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.class_reports.grade_distribution IS '{"90-100": 5, "80-90": 10, ...}';


--
-- Name: classrooms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.classrooms (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.classrooms FORCE ROW LEVEL SECURITY;


--
-- Name: coaching_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.coaching_events (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    event_type character varying(30) NOT NULL,
    trigger_data json,
    message text NOT NULL,
    priority integer NOT NULL,
    action_url character varying(500),
    shown_at timestamp with time zone,
    clicked_at timestamp with time zone,
    dismissed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.coaching_events FORCE ROW LEVEL SECURITY;


--
-- Name: content_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.content_reports (
    id character varying NOT NULL,
    reporter_id character varying NOT NULL,
    reported_user_id character varying,
    reported_content_id character varying,
    content_type character varying(30) NOT NULL,
    content_snapshot text,
    reason character varying(20) NOT NULL,
    description text,
    status character varying(20) NOT NULL,
    reviewed_by character varying,
    reviewed_at timestamp with time zone,
    resolution_note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: coppa_parental_consents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.coppa_parental_consents (
    id integer NOT NULL,
    consent_id character varying(36) NOT NULL,
    child_id character varying NOT NULL,
    parent_id character varying NOT NULL,
    child_date_of_birth date NOT NULL,
    consent_status public.parentalconsentstatus NOT NULL,
    verification_method character varying(100),
    verification_date timestamp without time zone,
    verification_document_path character varying(500),
    allow_data_collection boolean NOT NULL,
    allow_marketing_communication boolean NOT NULL,
    allow_third_party_sharing boolean NOT NULL,
    consent_given_date timestamp without time zone,
    consent_expiry_date timestamp without time zone,
    withdrawal_date timestamp without time zone,
    withdrawal_reason text,
    parent_ip_address character varying(50),
    parent_user_agent character varying(500),
    consent_form_version character varying(20),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    last_modified timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: coppa_parental_consents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.coppa_parental_consents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: coppa_parental_consents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.coppa_parental_consents_id_seq OWNED BY public.coppa_parental_consents.id;


--
-- Name: curriculum_alignments; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: curriculum_update_requests; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: daily_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.daily_plans (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.daily_plans FORCE ROW LEVEL SECURITY;


--
-- Name: daily_quests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.daily_quests (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    quest_date date NOT NULL,
    student_id character varying NOT NULL,
    quest_type character varying(30) NOT NULL,
    title character varying(200) NOT NULL,
    description character varying,
    target_value integer,
    current_value integer,
    xp_reward integer,
    completed boolean,
    completed_at timestamp with time zone,
    bonus_claimed boolean
);

ALTER TABLE ONLY public.daily_quests FORCE ROW LEVEL SECURITY;


--
-- Name: daily_quests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.daily_quests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: daily_quests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.daily_quests_id_seq OWNED BY public.daily_quests.id;


--
-- Name: data_processing_agreements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_processing_agreements (
    id integer NOT NULL,
    agreement_id character varying(36) NOT NULL,
    third_party_name character varying(200) NOT NULL,
    third_party_contact character varying(500),
    agreement_type character varying(50),
    ferpa_compliant boolean NOT NULL,
    coppa_compliant boolean NOT NULL,
    data_types_shared text,
    data_usage_purpose text,
    data_retention_period integer,
    agreement_start_date date NOT NULL,
    agreement_end_date date,
    agreement_status character varying(50),
    agreement_document_path character varying(500),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    last_modified timestamp without time zone DEFAULT now() NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL
);

ALTER TABLE ONLY public.data_processing_agreements FORCE ROW LEVEL SECURITY;


--
-- Name: data_processing_agreements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_processing_agreements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: data_processing_agreements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_processing_agreements_id_seq OWNED BY public.data_processing_agreements.id;


--
-- Name: data_retention_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_retention_policies (
    id integer NOT NULL,
    policy_id character varying(36) NOT NULL,
    policy_name character varying(200) NOT NULL,
    data_category character varying(100),
    retention_period_days integer NOT NULL,
    compliance_framework character varying(50),
    auto_delete_enabled boolean NOT NULL,
    deletion_grace_period_days integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    last_modified timestamp without time zone DEFAULT now() NOT NULL,
    created_by character varying
);


--
-- Name: data_retention_policies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_retention_policies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: data_retention_policies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_retention_policies_id_seq OWNED BY public.data_retention_policies.id;


--
-- Name: department_curricula; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.department_curricula (
    id uuid NOT NULL,
    department_id uuid NOT NULL,
    total_credits integer,
    duration_years integer,
    duration_semesters integer,
    core_courses jsonb,
    elective_courses jsonb,
    specialization_tracks character varying[],
    major_courses_credits integer,
    minor_courses_credits integer,
    general_education_credits integer,
    learning_outcomes text[],
    skills_gained character varying[],
    required_equipment character varying[],
    software_requirements character varying[],
    internship_required boolean,
    internship_duration_weeks integer,
    thesis_required boolean,
    capstone_project boolean,
    last_updated timestamp with time zone,
    created_at timestamp with time zone
);


--
-- Name: department_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.department_statistics (
    id uuid NOT NULL,
    department_id uuid NOT NULL,
    overall_employment_rate double precision,
    average_hiring_time_days integer,
    graduates_employed_in_field double precision,
    entry_level_avg_salary integer,
    entry_level_min_salary integer,
    entry_level_max_salary integer,
    mid_career_avg_salary integer,
    senior_avg_salary integer,
    salary_growth_rate double precision,
    top_industries jsonb,
    top_job_titles jsonb,
    top_cities jsonb,
    job_market_demand character varying(20),
    future_growth_potential character varying(20),
    year integer NOT NULL,
    last_updated timestamp with time zone,
    created_at timestamp with time zone
);


--
-- Name: departments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.departments (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    code character varying(50),
    faculty character varying(200),
    degree_type character varying(50) NOT NULL,
    education_language character varying(50),
    education_duration integer,
    description text,
    overview text,
    career_opportunities character varying[],
    job_titles character varying[],
    average_salary integer,
    employment_rate double precision,
    required_subjects character varying[],
    recommended_skills character varying[],
    accreditation jsonb,
    international_programs character varying[],
    seo_keywords character varying[],
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: diary_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.diary_entries (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    date date NOT NULL,
    success_count integer,
    failure_count integer,
    total_tasks integer,
    total_duration_minutes integer,
    highlights jsonb,
    learnings jsonb,
    challenges jsonb,
    tasks_data jsonb,
    markdown_content text,
    file_path character varying(512),
    meta_data jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: diary_exports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.diary_exports (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    format public.exportformat NOT NULL,
    date_from date NOT NULL,
    date_to date NOT NULL,
    file_path character varying(512),
    file_size integer,
    privacy_filter_applied boolean,
    redacted_fields jsonb,
    share_token character varying(64),
    share_url character varying(512),
    share_expires_at timestamp with time zone,
    share_access_count integer,
    is_public boolean,
    is_backup boolean,
    is_encrypted boolean,
    encryption_algorithm character varying(50),
    meta_data jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: dina_parameters; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dina_parameters (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    slip double precision NOT NULL,
    guess double precision NOT NULL,
    calibrated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: dormitory_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dormitory_info (
    id uuid NOT NULL,
    university_id uuid,
    name character varying(255) NOT NULL,
    accommodation_type public.accommodationtype NOT NULL,
    city character varying(100) NOT NULL,
    district character varying(100),
    address text,
    total_capacity integer,
    available_spaces integer,
    gender character varying(20),
    room_types jsonb,
    single_rooms integer,
    double_rooms integer,
    triple_rooms integer,
    quad_rooms integer,
    price_min integer,
    price_max integer,
    price_avg integer,
    deposit_required integer,
    meals_included boolean,
    meal_plan_cost integer,
    wifi_included boolean,
    laundry_facilities boolean,
    study_rooms boolean,
    common_areas boolean,
    kitchen_access boolean,
    gym boolean,
    library boolean,
    prayer_room boolean,
    furniture_included boolean,
    air_conditioning boolean,
    heating boolean,
    private_bathroom boolean,
    security_24_7 boolean,
    cctv boolean,
    key_card_access boolean,
    curfew character varying(100),
    visitors_allowed boolean,
    smoking_allowed boolean,
    pets_allowed boolean,
    application_period_start character varying(50),
    application_period_end character varying(50),
    application_requirements character varying[],
    priority_criteria character varying[],
    distance_to_campus_km double precision,
    transportation_to_campus character varying[],
    description text,
    amenities character varying[],
    photos character varying[],
    phone character varying(50),
    email character varying(255),
    website character varying(255),
    cleanliness_rating double precision,
    location_rating double precision,
    facilities_rating double precision,
    value_rating double precision,
    overall_rating double precision,
    verified boolean,
    year integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: duel_matches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.duel_matches (
    id character varying NOT NULL,
    session_id character varying NOT NULL,
    question_id character varying NOT NULL,
    question_order integer NOT NULL,
    player1_answer character varying(1),
    player1_time_ms integer,
    player1_correct boolean,
    player2_answer character varying(1),
    player2_time_ms integer,
    player2_correct boolean,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: duel_ratings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.duel_ratings (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    elo_rating double precision NOT NULL,
    wins integer NOT NULL,
    losses integer NOT NULL,
    draws integer NOT NULL,
    peak_rating double precision NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.duel_ratings FORCE ROW LEVEL SECURITY;


--
-- Name: duel_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.duel_sessions (
    id character varying NOT NULL,
    player1_id character varying NOT NULL,
    player2_id character varying,
    subject character varying(50) NOT NULL,
    question_count integer NOT NULL,
    time_per_question_sec integer NOT NULL,
    status character varying(20) NOT NULL,
    player1_score integer NOT NULL,
    player2_score integer NOT NULL,
    winner_id character varying,
    player1_elo_change double precision NOT NULL,
    player2_elo_change double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    started_at timestamp with time zone,
    finished_at timestamp with time zone
);


--
-- Name: duels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.duels (
    id integer NOT NULL,
    player1_id character varying NOT NULL,
    player2_id character varying NOT NULL,
    topic_id character varying NOT NULL,
    status character varying(20),
    winner_id character varying,
    player1_score integer,
    player2_score integer,
    elo_delta integer,
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone
);


--
-- Name: duels_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.duels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: duels_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.duels_id_seq OWNED BY public.duels.id;


--
-- Name: dungeon_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dungeon_progress (
    user_id character varying NOT NULL,
    topic_id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    attempt_count integer DEFAULT 0 NOT NULL,
    best_score integer DEFAULT 0 NOT NULL,
    last_score integer DEFAULT 0 NOT NULL,
    completed boolean DEFAULT false NOT NULL,
    first_attempt timestamp with time zone DEFAULT now() NOT NULL,
    last_attempt timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.dungeon_progress FORCE ROW LEVEL SECURITY;


--
-- Name: eba_content_analytics; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: eba_content_collections; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: eba_subject_taxonomy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.eba_subject_taxonomy (
    id character varying NOT NULL,
    subject character varying(50) NOT NULL,
    topic character varying(200) NOT NULL,
    subtopics character varying[],
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: eba_video_recommendations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.eba_video_recommendations (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.eba_video_recommendations FORCE ROW LEVEL SECURITY;


--
-- Name: eba_video_usage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.eba_video_usage (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.eba_video_usage FORCE ROW LEVEL SECURITY;


--
-- Name: eba_video_watches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.eba_video_watches (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    eba_video_id character varying NOT NULL,
    session_start timestamp with time zone,
    session_end timestamp with time zone,
    last_updated timestamp with time zone,
    last_position integer,
    watch_percentage double precision,
    completed boolean,
    completed_at timestamp with time zone,
    total_watch_time integer,
    created_at timestamp with time zone
);

ALTER TABLE ONLY public.eba_video_watches FORCE ROW LEVEL SECURITY;


--
-- Name: eba_videos; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: educational_contents; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: educational_record_access_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.educational_record_access_logs (
    id integer NOT NULL,
    log_id character varying(36) NOT NULL,
    student_id character varying NOT NULL,
    accessor_id character varying NOT NULL,
    accessor_role character varying(50),
    record_type public.educationalrecordtype,
    access_purpose character varying(200),
    access_timestamp timestamp without time zone DEFAULT now() NOT NULL,
    ip_address character varying(50),
    user_agent character varying(500),
    legitimate_educational_interest boolean CONSTRAINT educational_record_access_l_legitimate_educational_int_not_null NOT NULL,
    consent_id character varying(36)
);


--
-- Name: educational_record_access_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.educational_record_access_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: educational_record_access_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.educational_record_access_logs_id_seq OWNED BY public.educational_record_access_logs.id;


--
-- Name: emotional_states; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.emotional_states (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    confidence_level integer NOT NULL,
    frustration_score double precision,
    retry_count integer,
    error_count integer,
    flow_state boolean,
    productivity_score double precision,
    tasks_completed integer,
    trigger_factors jsonb,
    task_type character varying(100),
    self_awareness_score double precision,
    predicted_state character varying(50),
    actual_state character varying(50),
    context_notes text,
    meta_data jsonb
);


--
-- Name: error_clusters; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.error_clusters (
    id character varying NOT NULL,
    subject character varying(50) NOT NULL,
    topic_ids jsonb NOT NULL,
    error_pattern character varying(100) NOT NULL,
    student_count integer NOT NULL,
    recommended_remediation jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: exam_questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.exam_questions (
    id character varying NOT NULL,
    exam_session_id character varying NOT NULL,
    question_id character varying NOT NULL,
    question_order integer NOT NULL
);


--
-- Name: exam_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.exam_sessions (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.exam_sessions FORCE ROW LEVEL SECURITY;


--
-- Name: fallback_videos; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: fallback_videos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fallback_videos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: fallback_videos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.fallback_videos_id_seq OWNED BY public.fallback_videos.id;


--
-- Name: ferpa_consents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ferpa_consents (
    id integer NOT NULL,
    consent_id character varying(36) NOT NULL,
    student_id character varying NOT NULL,
    parent_id character varying,
    consent_status public.parentalconsentstatus NOT NULL,
    record_types character varying(500),
    allow_third_party_disclosure boolean NOT NULL,
    third_party_institutions text,
    parent_verification_method character varying(100),
    verification_date timestamp without time zone,
    verification_ip character varying(50),
    consent_given_date timestamp without time zone,
    consent_expiry_date timestamp without time zone,
    last_modified timestamp without time zone DEFAULT now() NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: ferpa_consents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ferpa_consents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ferpa_consents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ferpa_consents_id_seq OWNED BY public.ferpa_consents.id;


--
-- Name: file_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.file_versions (
    id character varying NOT NULL,
    file_id character varying NOT NULL,
    version_number integer NOT NULL,
    file_path character varying(500) NOT NULL,
    file_url character varying(500),
    file_size_bytes integer NOT NULL,
    uploaded_by character varying NOT NULL,
    status public.fileversionstatus,
    change_description text,
    meta_data jsonb,
    created_at timestamp with time zone
);


--
-- Name: forum_questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.forum_questions (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    question_bank_id character varying,
    subject_area character varying(50) NOT NULL,
    topic character varying(100),
    question_type character varying(30) NOT NULL,
    title character varying(200) NOT NULL,
    body text,
    status character varying(20) NOT NULL,
    solution_count integer NOT NULL,
    accepted_solution_id character varying,
    xp_awarded boolean NOT NULL,
    flagged boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.forum_questions FORCE ROW LEVEL SECURITY;


--
-- Name: forum_solutions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.forum_solutions (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    solver_id character varying NOT NULL,
    body text NOT NULL,
    image_url character varying(500),
    helpful_count integer NOT NULL,
    not_helpful_count integer NOT NULL,
    is_accepted boolean NOT NULL,
    xp_awarded integer NOT NULL,
    flagged boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: forum_votes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.forum_votes (
    id character varying NOT NULL,
    voter_id character varying NOT NULL,
    solution_id character varying NOT NULL,
    vote_type character varying(15) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: fsrs_cards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fsrs_cards (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.fsrs_cards FORCE ROW LEVEL SECURITY;


--
-- Name: fsrs_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fsrs_reviews (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.fsrs_reviews FORCE ROW LEVEL SECURITY;


--
-- Name: fsrs_schedules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fsrs_schedules (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.fsrs_schedules FORCE ROW LEVEL SECURITY;


--
-- Name: fsrs_student_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fsrs_student_profiles (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    fsrs_parameters json NOT NULL,
    cultural_parameters json NOT NULL,
    total_reviews integer NOT NULL,
    average_retention double precision NOT NULL,
    study_streak_days integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.fsrs_student_profiles FORCE ROW LEVEL SECURITY;


--
-- Name: fsrs_study_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fsrs_study_sessions (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    session_date timestamp with time zone NOT NULL,
    duration_minutes integer NOT NULL,
    cards_reviewed integer NOT NULL,
    correct_reviews integer NOT NULL,
    average_response_time double precision NOT NULL,
    cultural_context json
);

ALTER TABLE ONLY public.fsrs_study_sessions FORCE ROW LEVEL SECURITY;


--
-- Name: fsrs_subject_stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fsrs_subject_stats (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    subject_area public.subjectarea NOT NULL,
    total_cards integer NOT NULL,
    mature_cards integer NOT NULL,
    average_stability double precision NOT NULL,
    average_difficulty double precision NOT NULL,
    retention_rate double precision NOT NULL,
    last_updated timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.fsrs_subject_stats FORCE ROW LEVEL SECURITY;


--
-- Name: goals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.goals (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    specific text,
    measurable text,
    achievable text,
    relevant text,
    time_bound timestamp with time zone,
    progress integer,
    current_value double precision,
    target_value double precision NOT NULL,
    unit character varying(50),
    status public.goalstatus,
    milestones jsonb,
    milestone_celebrations jsonb,
    is_at_risk boolean,
    risk_factors jsonb,
    predicted_completion timestamp with time zone,
    velocity double precision,
    adjustments jsonb,
    lessons_learned jsonb,
    success_factors jsonb,
    challenges_faced jsonb,
    start_date timestamp with time zone DEFAULT now(),
    target_date timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    category character varying(100),
    priority integer,
    meta_data jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: image_uploads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.image_uploads (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    session_id character varying NOT NULL,
    user_id character varying NOT NULL,
    filename character varying(255) NOT NULL,
    file_path character varying(512) NOT NULL,
    file_size integer,
    mime_type character varying(100),
    width integer,
    height integer,
    image_url character varying(512),
    thumbnail_url character varying(512),
    processing_status public.imageprocessingstatus,
    ocr_text text,
    ocr_confidence double precision,
    contains_math boolean,
    math_latex text,
    math_confidence double precision,
    is_handwritten boolean,
    handwriting_quality character varying(50),
    processing_time_ms integer,
    ocr_engine character varying(100),
    error_message text,
    image_description text,
    detected_objects jsonb,
    suggested_subjects jsonb,
    meta_data jsonb,
    created_at timestamp with time zone DEFAULT now(),
    processed_at timestamp with time zone
);

ALTER TABLE ONLY public.image_uploads FORCE ROW LEVEL SECURITY;


--
-- Name: insights; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.insights (
    id character varying NOT NULL,
    diary_entry_id character varying NOT NULL,
    user_id character varying NOT NULL,
    category public.insightcategory NOT NULL,
    pattern text NOT NULL,
    root_cause text,
    correlation text,
    confidence double precision NOT NULL,
    evidence_count integer,
    recommendation text NOT NULL,
    priority integer,
    evidence_data jsonb,
    meta_data jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: invoices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.invoices (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    license_id character varying,
    invoice_no character varying(40) NOT NULL,
    amount_try numeric(12,2) NOT NULL,
    currency character varying(3) DEFAULT 'TRY'::character varying NOT NULL,
    status character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    method character varying(20) DEFAULT 'havale'::character varying NOT NULL,
    issued_at timestamp with time zone,
    paid_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.invoices FORCE ROW LEVEL SECURITY;


--
-- Name: irt_calibration_history; Type: TABLE; Schema: public; Owner: -
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
    difficulty_ci_upper double precision NOT NULL
);


--
-- Name: khan_certificates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.khan_certificates (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    khan_user_id character varying(100),
    badge_id character varying(100) NOT NULL,
    badge_name character varying(200) NOT NULL,
    badge_category character varying(50) NOT NULL,
    description text,
    icon_url character varying(1000),
    verification_url character varying(1000),
    earned_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    last_synced_at timestamp with time zone NOT NULL
);


--
-- Name: khan_contents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.khan_contents (
    id character varying NOT NULL,
    khan_content_id character varying(100) NOT NULL,
    title character varying(500) NOT NULL,
    description text,
    content_type character varying(20) NOT NULL,
    subject character varying(50) NOT NULL,
    topic character varying(200),
    video_url character varying(1000),
    duration_seconds integer,
    thumbnail_url character varying(1000),
    exercise_url character varying(1000),
    problem_count integer,
    language character varying(5) NOT NULL,
    difficulty_level character varying(20),
    last_synced_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: khan_oauth_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.khan_oauth_tokens (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    khan_user_id character varying(100),
    access_token text NOT NULL,
    refresh_token text,
    token_type character varying(20) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    issued_at timestamp with time zone NOT NULL,
    scopes character varying[] NOT NULL,
    is_active boolean NOT NULL,
    last_refreshed_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);

ALTER TABLE ONLY public.khan_oauth_tokens FORCE ROW LEVEL SECURITY;


--
-- Name: khan_user_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.khan_user_progress (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    khan_user_id character varying(100),
    khan_content_id character varying NOT NULL,
    content_type character varying(20) NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    last_accessed timestamp with time zone,
    video_seconds_watched integer NOT NULL,
    video_completed boolean NOT NULL,
    problems_attempted integer NOT NULL,
    problems_correct integer NOT NULL,
    proficiency_level character varying(20),
    energy_points integer NOT NULL,
    badges_earned character varying[] NOT NULL,
    last_synced_at timestamp with time zone,
    sync_conflict boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: kiro2_cat_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kiro2_cat_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id uuid NOT NULL,
    subject_id text NOT NULL,
    theta_final numeric DEFAULT 0.0 NOT NULL,
    se_final numeric DEFAULT 1.0 NOT NULL,
    n_questions smallint DEFAULT '0'::smallint NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    state text DEFAULT 'active'::text NOT NULL,
    termination_reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.kiro2_cat_sessions FORCE ROW LEVEL SECURITY;


--
-- Name: kiro2_learning_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kiro2_learning_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id uuid NOT NULL,
    question_id text NOT NULL,
    session_id uuid,
    event_type text DEFAULT 'cat_answer'::text NOT NULL,
    is_correct boolean,
    theta_after numeric,
    response_ms integer,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.kiro2_learning_events FORCE ROW LEVEL SECURITY;


--
-- Name: knowledge_points; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge_points (
    id character varying NOT NULL,
    topic_id character varying,
    code character varying(50) NOT NULL,
    name_tr character varying(200) NOT NULL,
    name character varying(300),
    subject character varying(50) NOT NULL,
    description text,
    prerequisite_ids json,
    difficulty_range json,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: kvkk_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kvkk_audit_logs (
    id character varying NOT NULL,
    user_id character varying,
    accessed_by character varying,
    action character varying(100) NOT NULL,
    resource_type character varying(100) NOT NULL,
    resource_id character varying,
    purpose public.data_processing_purpose,
    ip_address character varying(45),
    user_agent character varying(500),
    request_method character varying(10),
    request_path character varying(500),
    details json,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: kvkk_consents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kvkk_consents (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    purpose public.data_processing_purpose NOT NULL,
    status public.consent_status NOT NULL,
    consent_text text NOT NULL,
    privacy_policy_version character varying(20) NOT NULL,
    given_at timestamp with time zone DEFAULT now() NOT NULL,
    withdrawn_at timestamp with time zone,
    expires_at timestamp with time zone,
    ip_address character varying(45),
    user_agent character varying(500),
    additional_data json
);

ALTER TABLE ONLY public.kvkk_consents FORCE ROW LEVEL SECURITY;


--
-- Name: kvkk_data_deletion_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kvkk_data_deletion_requests (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    status public.deletion_request_status NOT NULL,
    request_reason text NOT NULL,
    deletion_type character varying(50) NOT NULL,
    data_categories json,
    reviewed_by character varying,
    review_notes text,
    rejection_reason text,
    requested_at timestamp with time zone DEFAULT now() NOT NULL,
    reviewed_at timestamp with time zone,
    processed_at timestamp with time zone,
    completed_at timestamp with time zone
);


--
-- Name: kvkk_data_export_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kvkk_data_export_requests (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    status public.export_request_status NOT NULL,
    request_reason text,
    export_format character varying(20) NOT NULL,
    data_categories json,
    file_path character varying(500),
    file_size_bytes integer,
    download_url character varying(500),
    download_expires_at timestamp with time zone,
    requested_at timestamp with time zone DEFAULT now() NOT NULL,
    processed_at timestamp with time zone,
    completed_at timestamp with time zone,
    error_message text
);

ALTER TABLE ONLY public.kvkk_data_export_requests FORCE ROW LEVEL SECURITY;


--
-- Name: kvkk_privacy_policy_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kvkk_privacy_policy_versions (
    id character varying NOT NULL,
    version character varying(20) NOT NULL,
    title character varying(200) NOT NULL,
    content text NOT NULL,
    is_active boolean NOT NULL,
    effective_date timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by character varying
);


--
-- Name: league_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.league_history (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    week_start timestamp with time zone NOT NULL,
    from_tier character varying(20),
    to_tier character varying(20),
    final_rank integer,
    final_xp integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.league_history FORCE ROW LEVEL SECURITY;


--
-- Name: league_memberships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.league_memberships (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    league_tier character varying(20) NOT NULL,
    weekly_xp integer NOT NULL,
    week_start timestamp with time zone NOT NULL,
    rank integer,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.league_memberships FORCE ROW LEVEL SECURITY;


--
-- Name: learning_analytics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning_analytics (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.learning_analytics FORCE ROW LEVEL SECURITY;


--
-- Name: learning_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning_entries (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    title character varying(255) NOT NULL,
    content text NOT NULL,
    summary text,
    tags character varying[],
    domain character varying(100),
    skill_type character varying(100),
    related_concepts character varying[],
    concept_links jsonb,
    next_review timestamp with time zone,
    review_count integer,
    last_review timestamp with time zone,
    retention_score double precision,
    ease_factor double precision,
    interval_days integer,
    importance integer,
    mastery_level double precision,
    source_type character varying(50),
    source_reference character varying(512),
    meta_data jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: learning_outcomes; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: learning_path_student_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning_path_student_profiles (
    student_id character varying(100) NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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
    daily_streak integer,
    best_streak integer,
    last_study_date date,
    metadata_json json NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    neuro_inclusive_mode boolean NOT NULL
);

ALTER TABLE ONLY public.learning_path_student_profiles FORCE ROW LEVEL SECURITY;


--
-- Name: learning_paths; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning_paths (
    path_id character varying(100) NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.learning_paths FORCE ROW LEVEL SECURITY;


--
-- Name: learning_progress_daily; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning_progress_daily (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.learning_progress_daily FORCE ROW LEVEL SECURITY;


--
-- Name: live_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.live_sessions (
    id character varying NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    session_type public.sessiontype,
    host_id character varying NOT NULL,
    teacher_id character varying,
    scheduled_start timestamp with time zone NOT NULL,
    scheduled_end timestamp with time zone NOT NULL,
    actual_start timestamp with time zone,
    actual_end timestamp with time zone,
    duration_minutes integer,
    status public.sessionstatus,
    platform public.platformtype,
    meeting_id character varying(100),
    meeting_password character varying(100),
    meeting_url character varying(500),
    join_url character varying(500),
    host_url character varying(500),
    zoom_meeting_data jsonb,
    meet_event_data jsonb,
    max_participants integer,
    current_participants integer,
    allow_screen_share boolean,
    allow_whiteboard boolean,
    allow_recording boolean,
    allow_chat boolean,
    is_recorded boolean,
    auto_record boolean,
    enable_waiting_room boolean,
    require_password boolean,
    enable_mute_on_join boolean,
    subject character varying(100),
    topics character varying[],
    meta_data jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: manipulative_activities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.manipulative_activities (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    manipulative_type character varying(50) NOT NULL,
    activity_type character varying(50),
    duration_seconds integer,
    completed boolean,
    attempts integer,
    details json,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE ONLY public.manipulative_activities FORCE ROW LEVEL SECURITY;


--
-- Name: manipulative_activities_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.manipulative_activities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: manipulative_activities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.manipulative_activities_id_seq OWNED BY public.manipulative_activities.id;


--
-- Name: manipulative_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.manipulative_progress (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.manipulative_progress FORCE ROW LEVEL SECURITY;


--
-- Name: manipulative_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.manipulative_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: manipulative_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.manipulative_progress_id_seq OWNED BY public.manipulative_progress.id;


--
-- Name: meb_curriculum_nodes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.meb_curriculum_nodes (
    id character varying NOT NULL,
    code character varying(50) NOT NULL,
    description text NOT NULL,
    grade_level integer NOT NULL,
    subject_area public.subjectarea NOT NULL,
    forbidden_keywords json,
    mandatory_keywords json,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: meb_curriculum_standards; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: mentor_feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mentor_feedback (
    id character varying NOT NULL,
    session_id character varying NOT NULL,
    giver_id character varying NOT NULL,
    receiver_id character varying NOT NULL,
    rating integer NOT NULL,
    tags text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: mentor_pairs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mentor_pairs (
    id character varying NOT NULL,
    mentor_id character varying NOT NULL,
    mentee_id character varying NOT NULL,
    subject_area character varying(50) NOT NULL,
    status character varying(20) NOT NULL,
    session_count integer NOT NULL,
    total_xp_mentor integer NOT NULL,
    total_xp_mentee integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    ended_at timestamp with time zone
);


--
-- Name: mentor_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mentor_sessions (
    id character varying NOT NULL,
    pair_id character varying NOT NULL,
    question_bank_id character varying,
    topic character varying(100),
    status character varying(20) NOT NULL,
    duration_minutes integer,
    mentor_xp integer NOT NULL,
    mentee_xp integer NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    ended_at timestamp with time zone
);


--
-- Name: message_audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.message_audit_log (
    id character varying NOT NULL,
    sender_id character varying NOT NULL,
    content_type character varying(30) NOT NULL,
    content_hash character varying(64) NOT NULL,
    content_length integer NOT NULL,
    flagged boolean NOT NULL,
    flag_reason character varying(20) NOT NULL,
    flag_details jsonb,
    pipeline_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: misconception_matrix; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.misconception_matrix (
    id character varying NOT NULL,
    code character varying(100) NOT NULL,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    subject_area public.subjectarea NOT NULL,
    severity_weight integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: misconception_remedies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.misconception_remedies (
    id character varying NOT NULL,
    misconception_id character varying NOT NULL,
    remedy_type character varying(50) NOT NULL,
    content_text text,
    content_url character varying(500),
    duration_seconds integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: moderation_actions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moderation_actions (
    id character varying NOT NULL,
    moderator_id character varying,
    target_user_id character varying NOT NULL,
    content_id character varying,
    content_type character varying(30),
    action_type character varying(30) NOT NULL,
    reason text NOT NULL,
    report_id character varying,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: moderation_queue; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moderation_queue (
    id uuid NOT NULL,
    review_id uuid NOT NULL,
    priority integer,
    flag_reasons jsonb,
    assigned_to character varying,
    assigned_at timestamp with time zone,
    status character varying(50),
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone
);


--
-- Name: question_bank; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_bank (
    id character varying NOT NULL,
    soru_hash character varying(32) NOT NULL,
    primary_topic_id character varying NOT NULL,
    is_active boolean NOT NULL,
    is_public boolean NOT NULL,
    created_by character varying,
    reviewed_by character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_ai_generated boolean DEFAULT false NOT NULL,
    review_status character varying(20) DEFAULT 'APPROVED'::character varying NOT NULL,
    is_anchor boolean DEFAULT false NOT NULL
);


--
-- Name: question_content; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_content (
    id character varying NOT NULL,
    question_text text NOT NULL,
    question_html text,
    question_latex text,
    question_image_url character varying(500),
    image_ocr_text text,
    image_width integer,
    image_height integer,
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
    structured_explanation json,
    CONSTRAINT check_correct_answer_content CHECK (((correct_answer)::text = ANY ((ARRAY['A'::character varying, 'B'::character varying, 'C'::character varying, 'D'::character varying, 'E'::character varying])::text[])))
);


--
-- Name: question_metadata; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_metadata (
    id character varying NOT NULL,
    secondary_topics json,
    bloom_level integer NOT NULL,
    bloom_category character varying(50) NOT NULL,
    exam_type character varying(20) NOT NULL,
    subject_area character varying(50) NOT NULL,
    grade_level integer NOT NULL,
    osym_format_compliant boolean NOT NULL,
    osym_year integer,
    source_book character varying(300),
    source_page integer,
    pipeline_metadata json,
    misconception_tags json,
    solution_steps json,
    similar_question_ids json,
    morphology_complexity double precision NOT NULL,
    word_count integer NOT NULL,
    unique_word_count integer NOT NULL,
    average_word_length double precision NOT NULL,
    readability_score double precision NOT NULL,
    pedagogical_status character varying(30) DEFAULT 'ACTIVE'::character varying NOT NULL,
    CONSTRAINT check_bloom_level CHECK (((bloom_level >= 1) AND (bloom_level <= 6))),
    CONSTRAINT check_grade_level CHECK (((grade_level >= 9) AND (grade_level <= 12)))
);


--
-- Name: question_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_statistics (
    id character varying NOT NULL,
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
    irt_a numeric(6,4),
    irt_b numeric(6,4),
    irt_c numeric(5,4),
    irt_calibrated boolean DEFAULT false NOT NULL,
    irt_calibrated_at timestamp with time zone,
    irt_n_responses integer DEFAULT 0 NOT NULL,
    irt_method text,
    is_calib_pool boolean DEFAULT false NOT NULL,
    embedding public.vector(1536),
    times_asked integer NOT NULL,
    times_correct integer NOT NULL,
    times_wrong integer NOT NULL,
    times_skipped integer NOT NULL,
    average_response_time double precision NOT NULL,
    median_response_time double precision NOT NULL,
    exposure_rate double precision NOT NULL,
    last_used_date timestamp with time zone,
    quality_score double precision NOT NULL,
    quality_review_status character varying(20) NOT NULL,
    reviewed_at timestamp with time zone,
    CONSTRAINT check_irt_diff CHECK (((irt_difficulty >= ('-3.0'::numeric)::double precision) AND (irt_difficulty <= (3.0)::double precision))),
    CONSTRAINT check_irt_discrim CHECK (((irt_discrimination >= (0.1)::double precision) AND (irt_discrimination <= (3.0)::double precision))),
    CONSTRAINT check_irt_guess CHECK (((irt_guessing >= (0.0)::double precision) AND (irt_guessing <= (1.0)::double precision))),
    CONSTRAINT check_irt_upper CHECK (((irt_upper_asymptote >= (0.0)::double precision) AND (irt_upper_asymptote <= (1.0)::double precision)))
);


--
-- Name: v_safe_for_beta_unfiltered; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_safe_for_beta_unfiltered AS
 SELECT qb.id,
    qb.soru_hash,
    qb.primary_topic_id,
    qb.is_active,
    qb.is_public,
    qb.created_by,
    qb.reviewed_by,
    qb.created_at,
    qb.updated_at,
    qb.is_ai_generated,
    qb.review_status,
    qc.question_text,
    qc.question_html,
    qc.question_latex,
    qc.question_image_url,
    qc.image_ocr_text,
    qc.image_width,
    qc.image_height,
    qc.question_audio_url,
    qc.option_a,
    qc.option_b,
    qc.option_c,
    qc.option_d,
    qc.option_e,
    qc.correct_answer,
    qc.explanation,
    qc.explanation_video_url,
    qc.alternative_solutions,
    qm.secondary_topics,
    qm.bloom_level,
    qm.bloom_category,
    qm.exam_type,
    qm.subject_area,
    qm.grade_level,
    qm.osym_format_compliant,
    qm.osym_year,
    qm.source_book,
    qm.source_page,
    qm.pipeline_metadata,
    qm.misconception_tags,
    qm.solution_steps,
    qm.similar_question_ids,
    qm.morphology_complexity,
    qm.word_count,
    qm.unique_word_count,
    qm.average_word_length,
    qm.readability_score,
    qs.difficulty_level,
    qs.irt_based_difficulty,
    qs.student_success_rate,
    qs.last_difficulty_update,
    qs.difficulty_update_count,
    qs.irt_discrimination,
    qs.irt_difficulty,
    qs.irt_guessing,
    qs.irt_upper_asymptote,
    qs.is_calibrated,
    qs.calibration_sample_size,
    qs.last_calibration_date,
    qs.calibration_quality_score,
    qs.irt_a,
    qs.irt_b,
    qs.irt_c,
    qs.irt_calibrated,
    qs.irt_calibrated_at,
    qs.irt_n_responses,
    qs.irt_method,
    qs.is_calib_pool,
    qs.embedding,
    qs.times_asked,
    qs.times_correct,
    qs.times_wrong,
    qs.times_skipped,
    qs.average_response_time,
    qs.median_response_time,
    qs.exposure_rate,
    qs.last_used_date,
    qs.quality_score,
    qs.quality_review_status,
    qs.reviewed_at
   FROM (((public.question_bank qb
     LEFT JOIN public.question_content qc ON (((qb.id)::text = (qc.id)::text)))
     LEFT JOIN public.question_metadata qm ON (((qb.id)::text = (qm.id)::text)))
     LEFT JOIN public.question_statistics qs ON (((qb.id)::text = (qs.id)::text)));


--
-- Name: v_safe_for_beta; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_safe_for_beta AS
 SELECT id,
    soru_hash,
    primary_topic_id,
    is_active,
    is_public,
    created_by,
    reviewed_by,
    created_at,
    updated_at,
    is_ai_generated,
    review_status,
    question_text,
    question_html,
    question_latex,
    question_image_url,
    image_ocr_text,
    image_width,
    image_height,
    question_audio_url,
    option_a,
    option_b,
    option_c,
    option_d,
    option_e,
    correct_answer,
    explanation,
    explanation_video_url,
    alternative_solutions,
    secondary_topics,
    bloom_level,
    bloom_category,
    exam_type,
    subject_area,
    grade_level,
    osym_format_compliant,
    osym_year,
    source_book,
    source_page,
    pipeline_metadata,
    misconception_tags,
    solution_steps,
    similar_question_ids,
    morphology_complexity,
    word_count,
    unique_word_count,
    average_word_length,
    readability_score,
    difficulty_level,
    irt_based_difficulty,
    student_success_rate,
    last_difficulty_update,
    difficulty_update_count,
    irt_discrimination,
    irt_difficulty,
    irt_guessing,
    irt_upper_asymptote,
    is_calibrated,
    calibration_sample_size,
    last_calibration_date,
    calibration_quality_score,
    irt_a,
    irt_b,
    irt_c,
    irt_calibrated,
    irt_calibrated_at,
    irt_n_responses,
    irt_method,
    is_calib_pool,
    embedding,
    times_asked,
    times_correct,
    times_wrong,
    times_skipped,
    average_response_time,
    median_response_time,
    exposure_rate,
    last_used_date,
    quality_score,
    quality_review_status,
    reviewed_at
   FROM public.v_safe_for_beta_unfiltered
  WHERE (((quality_review_status)::text = ANY (ARRAY[('human_verified'::character varying)::text, ('auto_judged_high'::character varying)::text])) AND ((pipeline_metadata IS NULL) OR (NOT ((pipeline_metadata)::jsonb ? 'demoted_at'::text))) AND ((pipeline_metadata IS NULL) OR (NOT ((pipeline_metadata)::jsonb ? 'ai_extras'::text)) OR (NOT (((pipeline_metadata)::jsonb -> 'ai_extras'::text) ? 'topic_match_quality'::text)) OR ((((pipeline_metadata)::jsonb -> 'ai_extras'::text) ->> 'topic_match_quality'::text) <> 'fallback'::text)) AND ((pipeline_metadata IS NULL) OR (NOT ((pipeline_metadata)::jsonb ? 'match_tier'::text)) OR (((pipeline_metadata)::jsonb ->> 'match_tier'::text) <> ALL (ARRAY['tier1_page_inline'::text, 'tier1b_position_page_inline'::text]))) AND ((pipeline_metadata IS NOT NULL) AND ((((pipeline_metadata)::jsonb ->> 'student_coherent'::text) = 'true'::text) OR ((pipeline_metadata)::jsonb ? 'verified_provisional'::text) OR ((pipeline_metadata)::jsonb ? 'consensus_2signal_run'::text) OR ((pipeline_metadata)::jsonb ? 'math_promote_run'::text) OR ((pipeline_metadata)::jsonb ? 'verbal_promote_run'::text))) AND ((is_ai_generated = false) OR ((review_status)::text = 'APPROVED'::text)));


--
-- Name: mv_safe_for_beta; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.mv_safe_for_beta AS
 SELECT id
   FROM public.v_safe_for_beta
  WITH NO DATA;


--
-- Name: nano_skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nano_skills (
    id character varying NOT NULL,
    knowledge_point_id character varying NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    subject character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    title character varying(200) NOT NULL,
    message text NOT NULL,
    notification_type character varying(20) NOT NULL,
    is_read boolean NOT NULL,
    action_url character varying(500),
    created_at timestamp without time zone NOT NULL
);

ALTER TABLE ONLY public.notifications FORCE ROW LEVEL SECURITY;


--
-- Name: oba_challenge_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.oba_challenge_progress (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    challenge_id character varying NOT NULL,
    student_id character varying NOT NULL,
    contribution integer NOT NULL,
    contribution_ratio double precision NOT NULL,
    xp_earned integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.oba_challenge_progress FORCE ROW LEVEL SECURITY;


--
-- Name: oba_challenges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.oba_challenges (
    id character varying NOT NULL,
    oba_id character varying NOT NULL,
    title character varying(200) NOT NULL,
    description character varying(500),
    challenge_type character varying(30) NOT NULL,
    target_value integer NOT NULL,
    current_value integer NOT NULL,
    bonus_xp_per_member integer NOT NULL,
    status character varying(20) NOT NULL,
    completed boolean NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: oba_uyeler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.oba_uyeler (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    oba_id integer NOT NULL,
    user_id character varying NOT NULL,
    role character varying(10),
    joined_at timestamp with time zone DEFAULT now()
);

ALTER TABLE ONLY public.oba_uyeler FORCE ROW LEVEL SECURITY;


--
-- Name: oba_uyeler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.oba_uyeler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: oba_uyeler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.oba_uyeler_id_seq OWNED BY public.oba_uyeler.id;


--
-- Name: obalar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.obalar (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description character varying,
    xp_pool integer,
    max_members integer,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: obalar_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.obalar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: obalar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.obalar_id_seq OWNED BY public.obalar.id;


--
-- Name: offline_sync_packages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.offline_sync_packages (
    package_id character varying NOT NULL,
    student_id character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    consumed_at timestamp with time zone,
    question_ids jsonb
);


--
-- Name: org_memberships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.org_memberships (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    user_id character varying NOT NULL,
    org_role character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.org_memberships FORCE ROW LEVEL SECURITY;


--
-- Name: COLUMN org_memberships.org_role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.org_memberships.org_role IS 'SCHOOL_ADMIN | TEACHER | STUDENT | PARENT | OBSERVER';


--
-- Name: organization_licenses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organization_licenses (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    plan_id character varying NOT NULL,
    seat_count integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'trial'::character varying NOT NULL,
    term_start timestamp with time zone,
    term_end timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.organization_licenses FORCE ROW LEVEL SECURITY;


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organizations (
    id character varying NOT NULL,
    name character varying(300) NOT NULL,
    org_type character varying(30) NOT NULL,
    status character varying(20) NOT NULL,
    kvkk_role character varying(20) NOT NULL,
    kvkk_verbis_no character varying(50),
    license_seats integer NOT NULL,
    license_expires_at timestamp with time zone,
    dpa_signed_at timestamp with time zone,
    contact_email character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.organizations FORCE ROW LEVEL SECURITY;


--
-- Name: COLUMN organizations.org_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.organizations.org_type IS 'dershane | ozel_okul | meb_okul | kurumsal';


--
-- Name: COLUMN organizations.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.organizations.status IS 'active | suspended | trial | closed';


--
-- Name: osb_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.osb_settings (
    id uuid NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    osb_mode_enabled boolean NOT NULL,
    consistent_layout_enabled boolean NOT NULL,
    layout_type character varying(20) NOT NULL,
    predictable_elements boolean NOT NULL,
    fixed_navigation_enabled boolean NOT NULL,
    navigation_position character varying(20) NOT NULL,
    navigation_variant character varying(20) NOT NULL,
    consistent_colors_enabled boolean NOT NULL,
    theme_changes_disabled boolean NOT NULL,
    high_contrast_mode boolean NOT NULL,
    standard_icons_enabled boolean NOT NULL,
    show_icon_labels boolean NOT NULL,
    icon_size character varying(10) NOT NULL,
    reduced_motion boolean NOT NULL,
    no_animations boolean NOT NULL,
    no_shadows boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);

ALTER TABLE ONLY public.osb_settings FORCE ROW LEVEL SECURITY;


--
-- Name: osym_linguistic_trends; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.osym_linguistic_trends (
    id integer NOT NULL,
    year integer NOT NULL,
    exam_type character varying(50) NOT NULL,
    subject character varying(50) NOT NULL,
    avg_word_length double precision NOT NULL,
    avg_words_per_sentence double precision NOT NULL,
    atesman_readability_index double precision NOT NULL,
    question_length_chars integer NOT NULL,
    created_at timestamp without time zone,
    cognitive_load_score double precision
);


--
-- Name: osym_linguistic_trends_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.osym_linguistic_trends_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: osym_linguistic_trends_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.osym_linguistic_trends_id_seq OWNED BY public.osym_linguistic_trends.id;


--
-- Name: osym_questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.osym_questions (
    id integer NOT NULL,
    question_id character varying(16) NOT NULL,
    stem text NOT NULL,
    key character varying(1) NOT NULL,
    distractors json NOT NULL,
    year integer NOT NULL,
    exam_type character varying(10) NOT NULL,
    subject character varying(50) NOT NULL,
    topic character varying(100),
    subtopic character varying(100),
    has_image boolean,
    image_url character varying(500),
    has_formula boolean,
    formula_latex text,
    visual_content json,
    bloom_level integer,
    bloom_category character varying(50),
    bloom_confidence double precision,
    irt_difficulty double precision,
    irt_discrimination double precision,
    irt_guessing double precision,
    irt_upper_asymptote double precision,
    irt_calibrated boolean,
    irt_sample_size integer,
    quality_score double precision,
    bleu_score double precision,
    rouge_score double precision,
    bert_score double precision,
    status character varying(20),
    reviewed_by character varying,
    review_notes text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    scraped_at timestamp without time zone,
    raw_text text,
    source_url character varying(500)
);


--
-- Name: osym_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.osym_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: osym_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.osym_questions_id_seq OWNED BY public.osym_questions.id;


--
-- Name: osym_standards; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: parent_approvals; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN parent_approvals.request_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.parent_approvals.request_type IS 'ekstra_ders_izni, sinav_kayit, ozel_egitim';


--
-- Name: COLUMN parent_approvals.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.parent_approvals.status IS 'beklemede, onaylandi, reddedildi';


--
-- Name: parent_child; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parent_child (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    parent_id character varying NOT NULL,
    child_id character varying NOT NULL,
    approved boolean NOT NULL,
    relation_type character varying(50),
    approved_at timestamp without time zone,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE ONLY public.parent_child FORCE ROW LEVEL SECURITY;


--
-- Name: parent_child_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.parent_child_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: parent_child_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.parent_child_id_seq OWNED BY public.parent_child.id;


--
-- Name: parent_link_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parent_link_codes (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    code character varying(6) NOT NULL,
    student_id character varying NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    consumed boolean NOT NULL,
    consumed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE ONLY public.parent_link_codes FORCE ROW LEVEL SECURITY;


--
-- Name: parent_link_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.parent_link_codes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: parent_link_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.parent_link_codes_id_seq OWNED BY public.parent_link_codes.id;


--
-- Name: parent_notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parent_notifications (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    parent_id character varying NOT NULL,
    child_id character varying NOT NULL,
    title character varying(200) NOT NULL,
    message text NOT NULL,
    notification_type character varying(50) NOT NULL,
    is_read boolean,
    created_at timestamp without time zone,
    read_at timestamp without time zone
);

ALTER TABLE ONLY public.parent_notifications FORCE ROW LEVEL SECURITY;


--
-- Name: parent_notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.parent_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: parent_notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.parent_notifications_id_seq OWNED BY public.parent_notifications.id;


--
-- Name: parent_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parent_profiles (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    children_ids json,
    email_notifications boolean NOT NULL,
    sms_notifications boolean NOT NULL,
    weekly_reports boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: parent_reports; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN parent_reports.report_period; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.parent_reports.report_period IS 'e.g., 2025-W47';


--
-- Name: COLUMN parent_reports.average_success_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.parent_reports.average_success_rate IS '0-100';


--
-- Name: parent_social_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parent_social_settings (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    parent_id character varying NOT NULL,
    student_id character varying NOT NULL,
    social_enabled boolean NOT NULL,
    chat_enabled boolean NOT NULL,
    study_rooms_enabled boolean NOT NULL,
    duels_enabled boolean NOT NULL,
    forum_enabled boolean NOT NULL,
    notifications_enabled boolean NOT NULL,
    visibility_level character varying(20) NOT NULL,
    max_daily_messages integer NOT NULL,
    allowed_hours_start integer NOT NULL,
    allowed_hours_end integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.parent_social_settings FORCE ROW LEVEL SECURITY;


--
-- Name: peer_comparisons; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.peer_comparisons (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    success_rate_percentile double precision,
    speed_percentile double precision,
    quality_percentile double precision,
    overall_percentile double precision,
    strengths jsonb,
    improvements jsonb,
    best_practices jsonb,
    is_anonymized boolean,
    noise_added boolean,
    k_anonymity integer,
    peer_group_size integer,
    peer_group_avg_success_rate double precision,
    meta_data jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: peer_recommendations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.peer_recommendations (
    id character varying NOT NULL,
    cluster_id character varying NOT NULL,
    source_topic character varying(200) NOT NULL,
    target_topic character varying(200) NOT NULL,
    improvement_rate double precision NOT NULL,
    sample_size integer NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: performance_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.performance_history (
    id uuid NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    score integer NOT NULL,
    questions_answered integer,
    correct_answers integer,
    subject character varying(100),
    difficulty character varying(50),
    streak_at_time integer,
    recorded_at timestamp without time zone NOT NULL
);

ALTER TABLE ONLY public.performance_history FORCE ROW LEVEL SECURITY;


--
-- Name: plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plans (
    id character varying NOT NULL,
    code character varying(40) NOT NULL,
    name character varying(120) NOT NULL,
    price_try numeric(12,2) DEFAULT '0'::numeric NOT NULL,
    billing_period character varying(12) DEFAULT 'yearly'::character varying NOT NULL,
    seat_limit integer,
    features json,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: point_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.point_transactions (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    points integer NOT NULL,
    reason character varying(255) NOT NULL,
    meta_data json,
    "timestamp" timestamp without time zone NOT NULL
);

ALTER TABLE ONLY public.point_transactions FORCE ROW LEVEL SECURITY;


--
-- Name: pomodoro_participants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pomodoro_participants (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    room_id character varying NOT NULL,
    student_id character varying NOT NULL,
    status character varying(20) NOT NULL,
    rounds_completed integer NOT NULL,
    total_work_minutes integer NOT NULL,
    xp_earned integer NOT NULL,
    joined_at timestamp with time zone DEFAULT now() NOT NULL,
    left_at timestamp with time zone
);

ALTER TABLE ONLY public.pomodoro_participants FORCE ROW LEVEL SECURITY;


--
-- Name: pomodoro_rooms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pomodoro_rooms (
    id character varying NOT NULL,
    subject_area character varying(50) NOT NULL,
    topic character varying(100),
    status character varying(20) NOT NULL,
    max_participants integer NOT NULL,
    current_participants integer NOT NULL,
    work_minutes integer NOT NULL,
    break_minutes integer NOT NULL,
    total_rounds integer NOT NULL,
    current_round integer NOT NULL,
    started_at timestamp with time zone,
    ended_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: program_score_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.program_score_history (
    id uuid NOT NULL,
    program_id uuid NOT NULL,
    year integer NOT NULL,
    base_score double precision,
    top_score double precision,
    median_score double precision,
    total_quota integer,
    filled_quota integer,
    min_rank integer,
    max_rank integer,
    source character varying(100),
    created_at timestamp with time zone
);


--
-- Name: q_matrix; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.q_matrix (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    nano_skill_id character varying NOT NULL,
    is_required boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: quality_gate_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quality_gate_results (
    id character varying NOT NULL,
    run_id character varying NOT NULL,
    gate_name character varying(100) NOT NULL,
    status character varying(20) NOT NULL,
    score double precision NOT NULL,
    threshold double precision NOT NULL,
    blocking boolean NOT NULL,
    message text NOT NULL,
    issues_count integer NOT NULL,
    auto_fixed boolean NOT NULL,
    issues json,
    metrics json,
    details json,
    execution_time_ms double precision NOT NULL,
    retries integer NOT NULL,
    started_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: quality_gates_override_audit; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quality_gates_override_audit (
    id character varying NOT NULL,
    gate_name character varying(100) NOT NULL,
    run_id character varying,
    requestor character varying(255) NOT NULL,
    reason text NOT NULL,
    ticket_id character varying(100),
    status character varying(20) NOT NULL,
    approver character varying(255),
    approver_comments text,
    approved_at timestamp with time zone,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: quality_gates_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quality_gates_runs (
    id character varying NOT NULL,
    pipeline_name character varying(100) NOT NULL,
    status character varying(20) NOT NULL,
    total_score double precision NOT NULL,
    passed_gates integer NOT NULL,
    failed_gates integer NOT NULL,
    skipped_gates integer NOT NULL,
    total_execution_time_ms double precision NOT NULL,
    parallel_execution_used boolean NOT NULL,
    fail_fast_mode boolean NOT NULL,
    commit_hash character varying(40),
    branch character varying(200),
    repository character varying(500),
    triggered_by character varying(255),
    trigger_type character varying(50),
    overridden boolean NOT NULL,
    override_reason text,
    override_approver character varying(255),
    config_snapshot json,
    started_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: question_generation_batches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_generation_batches (
    id integer NOT NULL,
    task_id character varying(100) NOT NULL,
    batch_size integer NOT NULL,
    exam_type character varying(10) NOT NULL,
    subject character varying(50) NOT NULL,
    generation_method character varying(50) NOT NULL,
    status character varying(20),
    progress double precision,
    completed_count integer,
    failed_count integer,
    generated_question_ids json,
    errors json,
    created_at timestamp without time zone,
    started_at timestamp without time zone,
    completed_at timestamp without time zone
);


--
-- Name: question_generation_batches_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.question_generation_batches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: question_generation_batches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.question_generation_batches_id_seq OWNED BY public.question_generation_batches.id;


--
-- Name: question_generation_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_generation_logs (
    id integer NOT NULL,
    question_id character varying(16),
    generation_method character varying(50),
    prompt_used text,
    model_version character varying(50),
    temperature double precision,
    initial_quality_score double precision,
    final_quality_score double precision,
    human_review_score double precision,
    ab_test_group character varying(10),
    ab_test_id character varying(50),
    generated_at timestamp without time zone
);


--
-- Name: question_generation_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.question_generation_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: question_generation_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.question_generation_logs_id_seq OWNED BY public.question_generation_logs.id;


--
-- Name: question_knowledge_mappings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_knowledge_mappings (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    knowledge_point_id character varying NOT NULL,
    weight double precision NOT NULL,
    is_primary boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: question_performance_analytics; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: question_tag_associations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_tag_associations (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    tag_id character varying NOT NULL,
    weight double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: question_tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_tags (
    id character varying NOT NULL,
    tag_name character varying(100) NOT NULL,
    tag_category character varying(50) NOT NULL,
    description text,
    usage_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: quiz_questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quiz_questions (
    id integer NOT NULL,
    quiz_id character varying(100) NOT NULL,
    question_id character varying NOT NULL,
    order_number integer NOT NULL,
    points double precision NOT NULL
);


--
-- Name: quiz_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quiz_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quiz_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quiz_questions_id_seq OWNED BY public.quiz_questions.id;


--
-- Name: quiz_submissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quiz_submissions (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.quiz_submissions FORCE ROW LEVEL SECURITY;


--
-- Name: quiz_submissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quiz_submissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quiz_submissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quiz_submissions_id_seq OWNED BY public.quiz_submissions.id;


--
-- Name: quizzes; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: realm_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.realm_progress (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    realm_id integer NOT NULL,
    bkt_score real,
    quest_stop integer,
    xp_earned integer,
    completed_at timestamp with time zone,
    unlocked_at timestamp with time zone DEFAULT now()
);

ALTER TABLE ONLY public.realm_progress FORCE ROW LEVEL SECURITY;


--
-- Name: realm_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.realm_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: realm_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.realm_progress_id_seq OWNED BY public.realm_progress.id;


--
-- Name: realms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.realms (
    id integer NOT NULL,
    slug character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    era character varying(150),
    npc_name character varying(100),
    npc_title character varying(100),
    tech_stack json,
    color_primary character varying(7),
    color_secondary character varying(7),
    order_index integer,
    is_active boolean
);


--
-- Name: realms_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.realms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: realms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.realms_id_seq OWNED BY public.realms.id;


--
-- Name: reasoning_cache; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reasoning_cache (
    id uuid NOT NULL,
    problem_hash character varying(64) NOT NULL,
    problem_embedding public.vector(1536),
    problem_text text NOT NULL,
    reasoning_data json NOT NULL,
    provider character varying(50),
    hit_count integer,
    last_hit timestamp without time zone,
    confidence double precision,
    was_verified boolean,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone
);


--
-- Name: COLUMN reasoning_cache.reasoning_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_cache.reasoning_data IS 'Full reasoning result';


--
-- Name: COLUMN reasoning_cache.hit_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_cache.hit_count IS 'Number of cache hits';


--
-- Name: reasoning_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reasoning_sessions (
    id uuid NOT NULL,
    problem text NOT NULL,
    problem_type character varying(50),
    problem_embedding public.vector(768),
    context text,
    provider public.llmproviderenum,
    model_name character varying(100),
    use_ensemble boolean,
    status public.reasoningsessionstatus,
    understanding text,
    final_answer text,
    verification text,
    confidence double precision,
    total_steps integer,
    latency_ms double precision,
    tokens_used integer,
    cost_usd double precision,
    ensemble_scores json,
    winning_provider character varying(50),
    user_id character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    completed_at timestamp without time zone
);


--
-- Name: COLUMN reasoning_sessions.problem; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.problem IS 'Original problem text';


--
-- Name: COLUMN reasoning_sessions.problem_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.problem_type IS 'Problem type: math, logic, etc.';


--
-- Name: COLUMN reasoning_sessions.problem_embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.problem_embedding IS 'Embedding of the problem text';


--
-- Name: COLUMN reasoning_sessions.context; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.context IS 'Additional context';


--
-- Name: COLUMN reasoning_sessions.provider; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.provider IS 'LLM provider used';


--
-- Name: COLUMN reasoning_sessions.model_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.model_name IS 'Specific model used';


--
-- Name: COLUMN reasoning_sessions.use_ensemble; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.use_ensemble IS 'Whether ensemble was used';


--
-- Name: COLUMN reasoning_sessions.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.status IS 'Session status';


--
-- Name: COLUMN reasoning_sessions.understanding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.understanding IS 'Problem understanding';


--
-- Name: COLUMN reasoning_sessions.final_answer; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.final_answer IS 'Final answer';


--
-- Name: COLUMN reasoning_sessions.verification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.verification IS 'Verification result';


--
-- Name: COLUMN reasoning_sessions.confidence; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.confidence IS 'Confidence score 0-1';


--
-- Name: COLUMN reasoning_sessions.total_steps; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.total_steps IS 'Total reasoning steps';


--
-- Name: COLUMN reasoning_sessions.latency_ms; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.latency_ms IS 'Total latency in ms';


--
-- Name: COLUMN reasoning_sessions.tokens_used; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.tokens_used IS 'Total tokens used';


--
-- Name: COLUMN reasoning_sessions.cost_usd; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.cost_usd IS 'Total cost in USD';


--
-- Name: COLUMN reasoning_sessions.ensemble_scores; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.ensemble_scores IS 'Scores from each provider';


--
-- Name: COLUMN reasoning_sessions.winning_provider; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.winning_provider IS 'Winning provider in ensemble';


--
-- Name: COLUMN reasoning_sessions.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_sessions.user_id IS 'User who initiated the session';


--
-- Name: reasoning_steps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reasoning_steps (
    id uuid NOT NULL,
    session_id uuid NOT NULL,
    step_number integer NOT NULL,
    step_type public.reasoningsteptypeenum,
    description text NOT NULL,
    reasoning text,
    result text,
    parent_step_id uuid,
    confidence double precision,
    is_verified boolean,
    verification_result text,
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    latency_ms double precision,
    created_at timestamp without time zone
);


--
-- Name: COLUMN reasoning_steps.step_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_steps.step_number IS 'Step order (1, 2, 3...)';


--
-- Name: COLUMN reasoning_steps.step_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_steps.step_type IS 'Type of reasoning step';


--
-- Name: COLUMN reasoning_steps.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_steps.description IS 'What this step does';


--
-- Name: COLUMN reasoning_steps.reasoning; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_steps.reasoning IS 'Why this step is needed';


--
-- Name: COLUMN reasoning_steps.result; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_steps.result IS 'Result of this step';


--
-- Name: COLUMN reasoning_steps.confidence; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_steps.confidence IS 'Confidence 0-1';


--
-- Name: COLUMN reasoning_steps.is_verified; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reasoning_steps.is_verified IS 'Has been verified';


--
-- Name: recording_bookmarks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recording_bookmarks (
    id character varying NOT NULL,
    recording_id character varying NOT NULL,
    user_id character varying NOT NULL,
    timestamp_seconds integer NOT NULL,
    title character varying(255),
    note text,
    created_at timestamp with time zone
);


--
-- Name: recording_views; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recording_views (
    id character varying NOT NULL,
    recording_id character varying NOT NULL,
    user_id character varying,
    started_at timestamp with time zone,
    ended_at timestamp with time zone,
    duration_watched_seconds integer,
    watch_percentage double precision,
    last_position_seconds integer,
    completed boolean,
    session_id character varying(255),
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: reflections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reflections (
    id character varying NOT NULL,
    diary_entry_id character varying NOT NULL,
    user_id character varying NOT NULL,
    what_went_well text,
    what_could_improve text,
    what_did_i_learn text,
    what_will_i_do_differently text,
    additional_notes text,
    depth public.reflectiondepth,
    depth_score double precision,
    extracted_learnings jsonb,
    action_items jsonb,
    meta_data jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: refresh_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.refresh_tokens (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.refresh_tokens FORCE ROW LEVEL SECURITY;


--
-- Name: review_ratings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.review_ratings (
    id uuid NOT NULL,
    review_id uuid NOT NULL,
    category character varying(50) NOT NULL,
    rating double precision NOT NULL,
    comment text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: review_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.review_reports (
    id uuid NOT NULL,
    review_id uuid NOT NULL,
    reporter_id character varying NOT NULL,
    reason character varying(50) NOT NULL,
    description text,
    status character varying(50),
    resolved_by character varying,
    resolved_at timestamp with time zone,
    resolution_notes text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: review_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.review_statistics (
    id uuid NOT NULL,
    review_type character varying(50) NOT NULL,
    university_id uuid,
    department_id uuid,
    dormitory_id uuid,
    total_reviews integer,
    verified_reviews integer,
    average_rating double precision,
    rating_1_count integer,
    rating_2_count integer,
    rating_3_count integer,
    rating_4_count integer,
    rating_5_count integer,
    category_averages jsonb,
    total_helpful_votes integer,
    total_views integer,
    positive_percentage double precision,
    negative_percentage double precision,
    top_tags jsonb,
    last_updated timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: review_votes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.review_votes (
    id uuid NOT NULL,
    review_id uuid NOT NULL,
    user_id character varying NOT NULL,
    is_helpful boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: room_analytics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.room_analytics (
    id character varying NOT NULL,
    room_id character varying NOT NULL,
    total_members integer,
    active_members_today integer,
    active_members_week integer,
    total_messages integer,
    messages_today integer,
    messages_week integer,
    total_files integer,
    total_storage_bytes integer,
    total_study_sessions integer,
    total_study_hours double precision,
    average_session_duration double precision,
    most_active_day character varying(20),
    most_active_hour integer,
    average_response_time_minutes double precision,
    most_used_tags jsonb,
    top_contributors jsonb,
    metrics jsonb,
    last_calculated_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: room_chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.room_chat_messages (
    id character varying NOT NULL,
    room_id character varying NOT NULL,
    user_id character varying NOT NULL,
    message text NOT NULL,
    message_type public.messagetype,
    mentions character varying[],
    reactions jsonb,
    file_id character varying,
    reply_to_id character varying,
    is_edited boolean,
    edited_at timestamp with time zone,
    is_deleted boolean,
    deleted_at timestamp with time zone,
    deleted_by character varying,
    is_pinned boolean,
    pinned_at timestamp with time zone,
    pinned_by character varying,
    read_by character varying[],
    meta_data jsonb,
    created_at timestamp with time zone
);


--
-- Name: room_invitations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.room_invitations (
    id character varying NOT NULL,
    room_id character varying NOT NULL,
    inviter_id character varying NOT NULL,
    invitee_id character varying,
    invitee_email character varying(255),
    message text,
    is_accepted boolean,
    is_declined boolean,
    accepted_at timestamp with time zone,
    declined_at timestamp with time zone,
    expires_at timestamp with time zone,
    invitation_code character varying(100),
    created_at timestamp with time zone
);


--
-- Name: room_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.room_members (
    id character varying NOT NULL,
    room_id character varying NOT NULL,
    user_id character varying NOT NULL,
    role public.memberrole,
    status public.memberstatus,
    can_send_messages boolean,
    can_share_files boolean,
    can_invite_members boolean,
    can_delete_messages boolean,
    can_delete_files boolean,
    joined_at timestamp with time zone,
    invited_by character varying,
    last_seen_at timestamp with time zone,
    is_online boolean,
    mute_notifications boolean,
    messages_sent integer,
    files_shared integer,
    study_hours double precision,
    nickname character varying(100),
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: room_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.room_settings (
    id character varying NOT NULL,
    room_id character varying NOT NULL,
    slow_mode_seconds integer,
    link_preview boolean,
    allow_emojis boolean,
    allow_gifs boolean,
    max_file_size_mb integer,
    allowed_file_types character varying[],
    require_file_approval boolean,
    notify_on_mention boolean,
    notify_on_file_upload boolean,
    notify_on_member_join boolean,
    default_pomodoro_duration integer,
    default_break_duration integer,
    theme_color character varying(20),
    custom_settings jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: room_study_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.room_study_sessions (
    id character varying NOT NULL,
    room_id character varying NOT NULL,
    user_id character varying NOT NULL,
    started_at timestamp with time zone,
    ended_at timestamp with time zone,
    duration_minutes integer,
    topic character varying(255),
    notes text,
    pomodoros_completed integer,
    breaks_taken integer,
    created_at timestamp with time zone
);


--
-- Name: salary_expectations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.salary_expectations (
    id uuid NOT NULL,
    department_id uuid NOT NULL,
    career_opportunity_id uuid,
    experience_level public.experiencelevel NOT NULL,
    min_salary integer NOT NULL,
    max_salary integer NOT NULL,
    average_salary integer NOT NULL,
    median_salary integer,
    region character varying(50),
    city character varying(100),
    industry_type public.industrytype,
    average_bonus_percentage double precision,
    stock_options_common boolean,
    remote_work_percentage double precision,
    year integer NOT NULL,
    sample_size integer,
    data_source character varying(100),
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying(255) NOT NULL,
    applied_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    description text
);


--
-- Name: scholarship_programs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scholarship_programs (
    id uuid NOT NULL,
    university_id uuid,
    name character varying(255) NOT NULL,
    scholarship_type public.scholarshiptype NOT NULL,
    provider character varying(255),
    coverage_percentage double precision,
    covers_tuition boolean,
    covers_accommodation boolean,
    covers_meals boolean,
    covers_books boolean,
    covers_transportation boolean,
    amount_min integer,
    amount_max integer,
    amount_avg integer,
    monthly_stipend integer,
    min_exam_score double precision,
    min_high_school_gpa double precision,
    min_university_gpa double precision,
    income_limit integer,
    citizenship_required character varying(100),
    age_limit integer,
    eligibility_criteria character varying[],
    required_documents character varying[],
    special_requirements text,
    application_period_start character varying(50),
    application_period_end character varying(50),
    application_process text,
    application_url character varying(255),
    selection_criteria jsonb,
    number_of_recipients integer,
    acceptance_rate double precision,
    renewable boolean,
    max_duration_years integer,
    renewal_requirements character varying[],
    service_obligation boolean,
    service_duration_years integer,
    gpa_requirement double precision,
    additional_benefits character varying[],
    networking_opportunities boolean,
    career_support boolean,
    total_recipients integer,
    success_rate double precision,
    description text,
    terms_and_conditions text,
    contact_person character varying(255),
    phone character varying(50),
    email character varying(255),
    website character varying(255),
    active boolean,
    year integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: screen_shares; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.screen_shares (
    id character varying NOT NULL,
    session_id character varying NOT NULL,
    user_id character varying NOT NULL,
    share_type public.screensharetype,
    window_title character varying(255),
    application_name character varying(255),
    started_at timestamp with time zone,
    ended_at timestamp with time zone,
    duration_seconds integer,
    meta_data jsonb,
    created_at timestamp with time zone
);


--
-- Name: sector_analyses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sector_analyses (
    id uuid NOT NULL,
    industry_type public.industrytype NOT NULL,
    sector_name character varying(200) NOT NULL,
    related_department_ids character varying[],
    market_size_billion_tl double precision,
    total_employment integer,
    year integer NOT NULL,
    annual_growth_rate double precision,
    job_growth_rate double precision,
    growth_trend character varying(20),
    total_job_openings integer,
    unemployment_rate double precision,
    competition_level character varying(20),
    in_demand_skills character varying[],
    emerging_technologies character varying[],
    future_outlook text,
    future_demand_prediction character varying(20),
    automation_risk character varying(20),
    regional_distribution jsonb,
    key_trends text[],
    challenges text[],
    opportunities text[],
    data_source character varying(100),
    last_analyzed timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: session_analytics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_analytics (
    id character varying NOT NULL,
    session_id character varying NOT NULL,
    total_participants integer,
    peak_concurrent_participants integer,
    average_duration_minutes double precision,
    total_chat_messages integer,
    total_questions integer,
    total_screen_shares integer,
    whiteboard_used boolean,
    average_connection_quality character varying(50),
    recording_duration_seconds integer,
    recording_views integer,
    average_rating double precision,
    total_ratings integer,
    metrics jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: session_chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_chat_messages (
    id character varying NOT NULL,
    session_id character varying NOT NULL,
    user_id character varying NOT NULL,
    message text NOT NULL,
    message_type character varying(50),
    recipient_id character varying,
    is_private boolean,
    meta_data jsonb,
    is_deleted boolean,
    deleted_by character varying,
    created_at timestamp with time zone
);


--
-- Name: session_participants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_participants (
    id character varying NOT NULL,
    session_id character varying NOT NULL,
    user_id character varying NOT NULL,
    role public.participantrole,
    joined_at timestamp with time zone,
    left_at timestamp with time zone,
    duration_minutes integer,
    is_present boolean,
    is_muted boolean,
    is_video_on boolean,
    is_sharing_screen boolean,
    can_share_screen boolean,
    can_use_whiteboard boolean,
    can_chat boolean,
    can_unmute_self boolean,
    questions_asked integer,
    hands_raised integer,
    connection_quality character varying(50),
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: session_recordings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_recordings (
    id character varying NOT NULL,
    session_id character varying NOT NULL,
    title character varying(255),
    description text,
    file_path character varying(500),
    file_url character varying(500),
    file_size_bytes integer,
    duration_seconds integer,
    resolution character varying(20),
    format character varying(20),
    started_at timestamp with time zone,
    ended_at timestamp with time zone,
    status public.recordingstatus,
    platform_recording_id character varying(255),
    platform_download_url character varying(500),
    platform_passcode character varying(100),
    processing_started_at timestamp with time zone,
    processing_completed_at timestamp with time zone,
    processing_error text,
    thumbnail_url character varying(500),
    transcript_url character varying(500),
    has_transcript boolean,
    is_public boolean,
    requires_authentication boolean,
    allowed_users character varying[],
    view_count integer,
    download_count integer,
    average_watch_percentage double precision,
    meta_data jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sessions (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    hashed_token character varying(64) NOT NULL,
    device_info json,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    last_activity_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL
);

ALTER TABLE ONLY public.sessions FORCE ROW LEVEL SECURITY;


--
-- Name: COLUMN sessions.device_info; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sessions.device_info IS 'Device/browser info';


--
-- Name: shared_files; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shared_files (
    id character varying NOT NULL,
    room_id character varying NOT NULL,
    uploaded_by character varying NOT NULL,
    filename character varying(255) NOT NULL,
    original_filename character varying(255) NOT NULL,
    file_path character varying(500) NOT NULL,
    file_url character varying(500),
    file_type public.filetype NOT NULL,
    mime_type character varying(100),
    file_size_bytes integer NOT NULL,
    description text,
    tags character varying[],
    thumbnail_url character varying(500),
    preview_available boolean,
    version_number integer,
    parent_file_id character varying,
    download_count integer,
    last_downloaded_at timestamp with time zone,
    is_scanned boolean,
    scan_result character varying(50),
    scanned_at timestamp with time zone,
    is_deleted boolean,
    deleted_at timestamp with time zone,
    deleted_by character varying,
    meta_data jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: solution_duel_submissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.solution_duel_submissions (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    duel_id character varying NOT NULL,
    student_id character varying NOT NULL,
    body text NOT NULL,
    image_url character varying(500),
    vote_count integer NOT NULL,
    flagged boolean NOT NULL,
    submitted_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.solution_duel_submissions FORCE ROW LEVEL SECURITY;


--
-- Name: solution_duel_votes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.solution_duel_votes (
    id character varying NOT NULL,
    duel_id character varying NOT NULL,
    voter_id character varying NOT NULL,
    voted_for_id character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: solution_duels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.solution_duels (
    id character varying NOT NULL,
    question_bank_id character varying NOT NULL,
    subject_area character varying(50) NOT NULL,
    challenger_id character varying NOT NULL,
    opponent_id character varying,
    status character varying(20) NOT NULL,
    solve_time_seconds integer NOT NULL,
    voting_ends_at timestamp with time zone,
    winner_id character varying,
    winner_xp integer NOT NULL,
    loser_xp integer NOT NULL,
    started_at timestamp with time zone,
    ended_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: solution_steps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.solution_steps (
    id character varying NOT NULL,
    message_id character varying NOT NULL,
    step_number integer NOT NULL,
    title character varying(255),
    content text NOT NULL,
    step_type character varying(50),
    latex_formula text,
    calculation_result character varying(255),
    is_alternative_method boolean,
    alternative_method_name character varying(100),
    meta_data jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: streak_daily_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.streak_daily_log (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    pair_id character varying NOT NULL,
    student_id character varying NOT NULL,
    log_date date NOT NULL,
    completed boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.streak_daily_log FORCE ROW LEVEL SECURITY;


--
-- Name: streak_pairs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.streak_pairs (
    id character varying NOT NULL,
    student_a_id character varying NOT NULL,
    student_b_id character varying NOT NULL,
    status character varying(20) NOT NULL,
    current_streak integer NOT NULL,
    max_streak integer NOT NULL,
    total_xp_earned integer NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    broken_at timestamp with time zone
);


--
-- Name: streak_tracking; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.streak_tracking (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    current_streak integer NOT NULL,
    best_streak integer NOT NULL,
    streak_start_date timestamp without time zone,
    last_correct_answer timestamp without time zone,
    milestones_reached json,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);

ALTER TABLE ONLY public.streak_tracking FORCE ROW LEVEL SECURITY;


--
-- Name: streaks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.streaks (
    user_id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    current_streak integer,
    largest_streak integer,
    freeze_count integer,
    last_activity date,
    total_days_active integer
);

ALTER TABLE ONLY public.streaks FORCE ROW LEVEL SECURITY;


--
-- Name: student_abilities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_abilities (
    student_id character varying NOT NULL,
    subject_id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    theta real,
    theta_se real,
    updated_at timestamp with time zone DEFAULT now()
);

ALTER TABLE ONLY public.student_abilities FORCE ROW LEVEL SECURITY;


--
-- Name: student_answers; Type: TABLE; Schema: public; Owner: -
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
    error_type character varying(20),
    answered_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_selected_answer CHECK (((selected_answer IS NULL) OR ((selected_answer)::text = ANY ((ARRAY['A'::character varying, 'B'::character varying, 'C'::character varying, 'D'::character varying, 'E'::character varying])::text[]))))
);


--
-- Name: COLUMN student_answers.error_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.student_answers.error_type IS 'concept|procedural|careless|knowledge_gap';


--
-- Name: student_engagement_signals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_engagement_signals (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    signal_type character varying(50) NOT NULL,
    value double precision NOT NULL,
    recorded_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.student_engagement_signals FORCE ROW LEVEL SECURITY;


--
-- Name: student_goals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_goals (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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
    updated_at timestamp without time zone NOT NULL
);

ALTER TABLE ONLY public.student_goals FORCE ROW LEVEL SECURITY;


--
-- Name: student_grades; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN student_grades.subject; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.student_grades.subject IS 'Matematik, Türkçe, etc.';


--
-- Name: COLUMN student_grades.grade_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.student_grades.grade_type IS 'yazili, sözlü, proje, performans';


--
-- Name: COLUMN student_grades.grade_value; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.student_grades.grade_value IS '0-100 or other scale';


--
-- Name: COLUMN student_grades.weight; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.student_grades.weight IS 'Weight in final grade calculation';


--
-- Name: COLUMN student_grades.academic_year; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.student_grades.academic_year IS '2024-2025';


--
-- Name: COLUMN student_grades.semester; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.student_grades.semester IS '1 or 2';


--
-- Name: student_knowledge_states; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_knowledge_states (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    knowledge_point_id character varying NOT NULL,
    subject character varying(50) NOT NULL,
    mastery_level double precision NOT NULL,
    confidence double precision,
    response_count integer NOT NULL,
    last_assessed timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.student_knowledge_states FORCE ROW LEVEL SECURITY;


--
-- Name: student_learning_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_learning_profiles (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.student_learning_profiles FORCE ROW LEVEL SECURITY;


--
-- Name: student_nano_skill_mastery; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_nano_skill_mastery (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    nano_skill_id character varying NOT NULL,
    mastery double precision NOT NULL,
    confidence double precision NOT NULL,
    response_count integer NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.student_nano_skill_mastery FORCE ROW LEVEL SECURITY;


--
-- Name: student_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_profiles (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    grade_level integer NOT NULL,
    school_name character varying(200),
    target_university character varying(200),
    target_department character varying(200),
    hedef_sinav character varying(20),
    veli_onay boolean NOT NULL,
    veli_email character varying(255),
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


--
-- Name: student_question_flags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_question_flags (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    question_id character varying NOT NULL,
    flag_type character varying(32) NOT NULL,
    note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    resolved_at timestamp with time zone,
    resolution character varying(32),
    resolved_by character varying
);


--
-- Name: student_question_responses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_question_responses (
    id integer NOT NULL,
    student_id character varying NOT NULL,
    question_id character varying(16) NOT NULL,
    selected_answer character varying(1),
    is_correct boolean,
    response_time_seconds integer,
    exam_session_id character varying,
    attempt_number integer,
    answered_at timestamp without time zone
);


--
-- Name: student_question_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.student_question_responses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: student_question_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.student_question_responses_id_seq OWNED BY public.student_question_responses.id;


--
-- Name: student_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_reviews (
    id uuid NOT NULL,
    user_id character varying NOT NULL,
    review_type character varying(50) NOT NULL,
    university_id uuid,
    department_id uuid,
    professor_id character varying,
    course_id character varying,
    dormitory_id uuid,
    title character varying(255) NOT NULL,
    content text NOT NULL,
    overall_rating double precision NOT NULL,
    pros jsonb,
    cons jsonb,
    tags jsonb,
    student_year integer,
    enrollment_year integer,
    is_current_student boolean,
    is_alumni boolean,
    status character varying(20),
    moderation_notes text,
    moderated_by character varying,
    moderated_at timestamp with time zone,
    spam_score double precision,
    quality_score double precision,
    contains_profanity boolean,
    contains_contact_info boolean,
    is_too_short boolean,
    is_verified boolean,
    verification_method character varying(100),
    verified_at timestamp with time zone,
    helpful_count integer,
    not_helpful_count integer,
    report_count integer,
    view_count integer,
    language character varying(10),
    ip_address character varying(50),
    user_agent character varying(255),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    published_at timestamp with time zone
);


--
-- Name: study_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.study_plans (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    yks_date date NOT NULL,
    is_active boolean NOT NULL,
    total_weeks integer NOT NULL,
    target_net double precision,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.study_plans FORCE ROW LEVEL SECURITY;


--
-- Name: study_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.study_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: study_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.study_plans_id_seq OWNED BY public.study_plans.id;


--
-- Name: study_rooms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.study_rooms (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    topic character varying(255),
    owner_id character varying NOT NULL,
    status public.roomstatus,
    visibility public.roomvisibility,
    password_hash character varying(255),
    max_members integer,
    current_member_count integer,
    allow_file_sharing boolean,
    allow_member_invites boolean,
    require_approval boolean,
    enable_moderation boolean,
    mute_new_members boolean,
    scheduled_study_times jsonb,
    tags character varying[],
    total_messages integer,
    total_files integer,
    total_study_hours double precision,
    room_image_url character varying(500),
    meta_data jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);

ALTER TABLE ONLY public.study_rooms FORCE ROW LEVEL SECURITY;


--
-- Name: study_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.study_sessions (
    id character varying(36) NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying(100) NOT NULL,
    started_at timestamp without time zone NOT NULL,
    ended_at timestamp without time zone,
    duration_minutes integer,
    topics_studied json,
    questions_answered integer,
    correct_count integer
);

ALTER TABLE ONLY public.study_sessions FORCE ROW LEVEL SECURITY;


--
-- Name: sub_problems; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sub_problems (
    id uuid NOT NULL,
    session_id uuid NOT NULL,
    order_index integer NOT NULL,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    dependencies character varying[],
    difficulty double precision,
    estimated_steps integer,
    is_solved boolean,
    solution text,
    solution_steps json,
    created_at timestamp without time zone,
    solved_at timestamp without time zone
);


--
-- Name: COLUMN sub_problems.order_index; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sub_problems.order_index IS 'Order in solving sequence';


--
-- Name: COLUMN sub_problems.title; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sub_problems.title IS 'Sub-problem title';


--
-- Name: COLUMN sub_problems.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sub_problems.description IS 'Detailed description';


--
-- Name: COLUMN sub_problems.dependencies; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sub_problems.dependencies IS 'IDs of dependent sub-problems';


--
-- Name: COLUMN sub_problems.difficulty; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sub_problems.difficulty IS 'Difficulty 0-1';


--
-- Name: COLUMN sub_problems.solution_steps; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sub_problems.solution_steps IS 'Steps used to solve';


--
-- Name: system_configurations; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: teacher_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_assignments (
    id character varying NOT NULL,
    teacher_user_id character varying NOT NULL,
    baslik character varying(200) NOT NULL,
    aciklama text,
    sinif character varying(50),
    teslim_tarihi timestamp without time zone,
    durum character varying(20) NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: teacher_availability; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_availability (
    id character varying NOT NULL,
    teacher_id character varying NOT NULL,
    day_of_week public.dayofweek NOT NULL,
    start_time time without time zone NOT NULL,
    end_time time without time zone NOT NULL,
    specific_date date,
    valid_from date,
    valid_until date,
    status public.timeslotstatus,
    max_students integer,
    current_bookings integer,
    notes text,
    is_recurring boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: teacher_certifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_certifications (
    id character varying NOT NULL,
    teacher_id character varying NOT NULL,
    certification_type public.certificationtype NOT NULL,
    title character varying(255) NOT NULL,
    issuing_organization character varying(255),
    issue_date date,
    expiry_date date,
    credential_id character varying(100),
    document_url character varying(500),
    description text,
    verification_status public.verificationstatus,
    verified_at timestamp with time zone,
    verified_by character varying,
    rejection_reason text,
    is_featured boolean,
    display_order integer,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: teacher_classroom_students; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_classroom_students (
    id character varying NOT NULL,
    classroom_id character varying NOT NULL,
    student_user_id character varying NOT NULL,
    joined_at timestamp without time zone NOT NULL
);


--
-- Name: teacher_classrooms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_classrooms (
    id character varying NOT NULL,
    teacher_user_id character varying NOT NULL,
    sinif_adi character varying(100) NOT NULL,
    seviye character varying(10) NOT NULL,
    ders character varying(50) NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: teacher_contents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_contents (
    id character varying NOT NULL,
    teacher_user_id character varying NOT NULL,
    baslik character varying(200) NOT NULL,
    aciklama text,
    tip character varying(20) NOT NULL,
    konu character varying(100),
    sinif character varying(50),
    goruntulenme integer NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: teacher_exam_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_exam_configs (
    id character varying NOT NULL,
    teacher_user_id character varying NOT NULL,
    baslik character varying(200) NOT NULL,
    aciklama text,
    sinav_tipi character varying(10) NOT NULL,
    soru_sayisi integer NOT NULL,
    sure_dakika integer NOT NULL,
    durum character varying(20) NOT NULL,
    created_at timestamp without time zone NOT NULL
);


--
-- Name: teacher_expertise; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_expertise (
    id character varying NOT NULL,
    teacher_id character varying NOT NULL,
    subject public.subjectexpertise NOT NULL,
    grade_levels character varying[],
    proficiency_level character varying(50),
    years_teaching_subject integer,
    specializations jsonb,
    exam_types jsonb,
    is_verified boolean,
    verified_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: teacher_pool_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_pool_profiles (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    full_name character varying(255) NOT NULL,
    title character varying(100),
    bio text,
    profile_photo_url character varying(500),
    phone character varying(20),
    email character varying(255),
    city character varying(100),
    district character varying(100),
    years_of_experience integer,
    education_level character varying(100),
    university character varying(255),
    department character varying(255),
    graduation_year integer,
    status public.teacherstatus NOT NULL,
    verification_status public.verificationstatus,
    verified_at timestamp with time zone,
    verified_by character varying,
    average_rating double precision,
    total_reviews integer,
    total_sessions integer,
    total_students integer,
    hourly_rate double precision,
    currency character varying(10),
    is_accepting_students boolean,
    max_students integer,
    online_teaching boolean,
    in_person_teaching boolean,
    application_notes text,
    admin_notes text,
    rejection_reason text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);

ALTER TABLE ONLY public.teacher_pool_profiles FORCE ROW LEVEL SECURITY;


--
-- Name: teacher_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_profiles (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    school_name character varying(200) NOT NULL,
    subject_areas json,
    experience_years integer NOT NULL,
    education_level character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: teacher_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_reviews (
    id character varying NOT NULL,
    teacher_id character varying NOT NULL,
    student_id character varying NOT NULL,
    appointment_id character varying,
    overall_rating integer NOT NULL,
    teaching_quality integer,
    communication integer,
    punctuality integer,
    helpfulness integer,
    title character varying(255),
    content text,
    teacher_response text,
    responded_at timestamp with time zone,
    is_verified boolean,
    is_featured boolean,
    is_hidden boolean,
    helpful_count integer,
    not_helpful_count integer,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: teacher_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_statistics (
    id character varying NOT NULL,
    teacher_id character varying NOT NULL,
    total_sessions integer,
    completed_sessions integer,
    cancelled_sessions integer,
    no_show_sessions integer,
    total_students integer,
    active_students integer,
    average_rating double precision,
    total_reviews integer,
    five_star_count integer,
    four_star_count integer,
    three_star_count integer,
    two_star_count integer,
    one_star_count integer,
    average_response_time_minutes integer,
    total_earnings double precision,
    this_month_earnings double precision,
    total_teaching_hours double precision,
    this_month_hours double precision,
    subject_stats jsonb,
    monthly_data jsonb,
    last_calculated_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: topic_completions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.topic_completions (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying(100) NOT NULL,
    node_id character varying(100) NOT NULL,
    completed boolean NOT NULL,
    completion_date timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);

ALTER TABLE ONLY public.topic_completions FORCE ROW LEVEL SECURITY;


--
-- Name: topic_completions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.topic_completions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: topic_completions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.topic_completions_id_seq OWNED BY public.topic_completions.id;


--
-- Name: topic_hierarchy; Type: TABLE; Schema: public; Owner: -
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
    difficulty_level double precision DEFAULT '0.5'::double precision,
    subject_area character varying(50),
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_osym_relevance CHECK (((osym_relevance >= (0.0)::double precision) AND (osym_relevance <= (1.0)::double precision))),
    CONSTRAINT check_topic_level CHECK (((level >= 1) AND (level <= 5)))
);


--
-- Name: topic_prerequisites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.topic_prerequisites (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    topic_id text NOT NULL,
    prereq_id text NOT NULL,
    prereq_type text DEFAULT 'hard'::text NOT NULL,
    strength numeric DEFAULT 1.0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: topic_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.topic_progress (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying(100) NOT NULL,
    node_id character varying(100) NOT NULL,
    progress integer NOT NULL,
    time_spent integer NOT NULL,
    completed boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    CONSTRAINT check_progress_percentage CHECK (((progress >= 0) AND (progress <= 100)))
);

ALTER TABLE ONLY public.topic_progress FORCE ROW LEVEL SECURITY;


--
-- Name: topic_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.topic_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: topic_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.topic_progress_id_seq OWNED BY public.topic_progress.id;


--
-- Name: universities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.universities (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    short_name character varying(50),
    university_type public.universitytype NOT NULL,
    city character varying(100) NOT NULL,
    district character varying(100),
    address text,
    postal_code character varying(10),
    latitude double precision,
    longitude double precision,
    phone character varying(20),
    email character varying(100),
    website character varying(255),
    established_year integer,
    rector character varying(100),
    total_students integer,
    total_faculty integer,
    world_ranking integer,
    turkey_ranking integer,
    description text,
    campus_info jsonb,
    facilities character varying[],
    social_media jsonb,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: university_programs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.university_programs (
    id uuid NOT NULL,
    university_id uuid NOT NULL,
    department_id uuid NOT NULL,
    program_code character varying(50),
    program_name character varying(255) NOT NULL,
    program_type public.programtype,
    year integer NOT NULL,
    score_type public.scoretype NOT NULL,
    base_score double precision,
    top_score double precision,
    median_score double precision,
    total_quota integer,
    general_quota integer,
    special_quota integer,
    filled_quota integer,
    acceptance_rate double precision,
    competition_ratio double precision,
    min_rank integer,
    max_rank integer,
    median_rank integer,
    scholarship boolean,
    scholarship_percentage double precision,
    tuition_fee integer,
    has_language_prep boolean,
    prep_mandatory boolean,
    special_conditions jsonb,
    bonus_coefficients jsonb,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: university_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.university_statistics (
    id uuid NOT NULL,
    university_id uuid NOT NULL,
    year integer NOT NULL,
    total_campuses integer,
    total_campus_area_sqm integer,
    total_student_clubs integer,
    has_health_center boolean,
    has_career_center boolean,
    city character varying(100),
    avg_monthly_cost integer,
    avg_rent integer,
    cost_of_living_index double precision,
    total_dormitory_capacity integer,
    avg_dormitory_cost integer,
    dormitory_types character varying[],
    total_scholarships integer,
    full_scholarships integer,
    partial_scholarships integer,
    avg_scholarship_amount integer,
    scholarship_acceptance_rate double precision,
    affordability_score double precision,
    last_updated timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: user_achievements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_achievements (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.user_achievements FORCE ROW LEVEL SECURITY;


--
-- Name: user_badges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_badges (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    user_id character varying NOT NULL,
    badge_id character varying NOT NULL,
    earned_at timestamp with time zone DEFAULT now(),
    auto_awarded boolean
);

ALTER TABLE ONLY public.user_badges FORCE ROW LEVEL SECURITY;


--
-- Name: user_theta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_theta (
    user_id character varying(255) NOT NULL,
    subject_area character varying(50) NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    theta_estimate double precision DEFAULT '0'::double precision NOT NULL,
    theta_se double precision DEFAULT '0.5'::double precision NOT NULL,
    response_count integer DEFAULT 0 NOT NULL,
    last_updated timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.user_theta FORCE ROW LEVEL SECURITY;


--
-- Name: user_university_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_university_preferences (
    id uuid NOT NULL,
    user_id character varying NOT NULL,
    preferred_cities character varying[],
    preferred_university_types character varying[],
    preferred_score_types character varying[],
    yks_score double precision,
    score_type character varying(10),
    career_interests character varying[],
    target_departments character varying[],
    max_tuition_fee integer,
    needs_scholarship boolean,
    preferences jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    secret_2fa character varying(32),
    is_2fa_enabled boolean NOT NULL,
    backup_codes_hashed json,
    is_premium boolean NOT NULL,
    premium_expires_at timestamp with time zone,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    role public.userrole NOT NULL,
    phone character varying(20),
    birth_date date,
    total_xp integer NOT NULL,
    level integer NOT NULL,
    virtual_currency integer DEFAULT 0 NOT NULL,
    last_level_up_at timestamp with time zone,
    is_active boolean NOT NULL,
    is_verified boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_login timestamp with time zone,
    elo_rating integer NOT NULL,
    is_parent boolean NOT NULL
);


--
-- Name: COLUMN users.secret_2fa; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.secret_2fa IS 'TOTP secret key for 2FA';


--
-- Name: COLUMN users.is_2fa_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.is_2fa_enabled IS '2FA enabled status';


--
-- Name: COLUMN users.backup_codes_hashed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.backup_codes_hashed IS 'Hashed backup codes for 2FA recovery';


--
-- Name: COLUMN users.is_premium; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.is_premium IS 'Premium subscription status';


--
-- Name: COLUMN users.premium_expires_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.premium_expires_at IS 'Premium subscription expiry';


--
-- Name: COLUMN users.virtual_currency; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.virtual_currency IS 'KiroCoin/Zihin Puani vb.';


--
-- Name: veli_consent; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.veli_consent (
    id character varying(36) NOT NULL,
    child_user_id character varying NOT NULL,
    veli_email character varying(255) NOT NULL,
    status character varying(20) NOT NULL,
    token_hash character varying(64),
    token_expires_at timestamp with time zone,
    requested_at timestamp with time zone NOT NULL,
    granted_at timestamp with time zone,
    withdrawn_at timestamp with time zone,
    consent_text text NOT NULL,
    consent_version character varying(20) NOT NULL,
    ip_address character varying(45),
    user_agent character varying(500),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: video_analytics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.video_analytics (
    id character varying NOT NULL,
    video_id character varying NOT NULL,
    user_id character varying,
    session_id character varying(100) NOT NULL,
    started_at timestamp with time zone NOT NULL,
    ended_at timestamp with time zone,
    watch_duration_seconds double precision NOT NULL,
    completion_percentage double precision NOT NULL,
    paused_count integer NOT NULL,
    seeked_count integer NOT NULL,
    playback_speed double precision NOT NULL,
    selected_quality character varying(20),
    quality_changes integer NOT NULL,
    device_type character varying(50),
    browser character varying(100),
    os character varying(100),
    ip_address character varying(45),
    country character varying(2),
    average_bandwidth_mbps double precision,
    buffering_count integer NOT NULL,
    buffering_duration_seconds double precision NOT NULL,
    liked boolean NOT NULL,
    bookmarked boolean NOT NULL,
    shared boolean NOT NULL,
    reported boolean NOT NULL,
    helpful_rating integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_completion CHECK (((completion_percentage >= (0.0)::double precision) AND (completion_percentage <= (100.0)::double precision))),
    CONSTRAINT check_playback_speed CHECK ((playback_speed > (0)::double precision)),
    CONSTRAINT check_rating CHECK (((helpful_rating IS NULL) OR ((helpful_rating >= 1) AND (helpful_rating <= 5)))),
    CONSTRAINT check_watch_duration CHECK ((watch_duration_seconds >= (0)::double precision))
);


--
-- Name: video_analytics_summary; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.video_analytics_summary (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    period_type character varying(10) NOT NULL,
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    total_videos_watched integer,
    total_watch_time integer,
    total_videos_completed integer,
    average_completion_rate double precision,
    total_notes integer,
    total_bookmarks integer,
    average_playback_speed double precision,
    source_breakdown jsonb,
    subject_breakdown jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: video_bookmarks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.video_bookmarks (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    video_id character varying(100) NOT NULL,
    video_source character varying(20) NOT NULL,
    session_id character varying,
    "timestamp" integer NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    bookmark_type character varying(20),
    is_public boolean,
    share_count integer,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: video_completion_milestones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.video_completion_milestones (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    video_id character varying(100) NOT NULL,
    video_source character varying(20) NOT NULL,
    milestone_percentage integer NOT NULL,
    achieved_at timestamp with time zone,
    badge_awarded boolean,
    badge_id character varying
);


--
-- Name: video_notes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.video_notes (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    video_id character varying(100) NOT NULL,
    video_source character varying(20) NOT NULL,
    session_id character varying,
    content text NOT NULL,
    "timestamp" integer NOT NULL,
    is_important boolean,
    tags character varying[],
    video_caption text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: video_solutions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.video_solutions (
    id character varying NOT NULL,
    question_id character varying NOT NULL,
    uploaded_by character varying NOT NULL,
    original_filename character varying(500) NOT NULL,
    original_format public.videoformat NOT NULL,
    original_size_bytes integer NOT NULL,
    original_duration_seconds double precision NOT NULL,
    original_url character varying(1000) NOT NULL,
    cdn_url character varying(1000),
    is_format_valid boolean NOT NULL,
    validation_errors json,
    compressed_size_bytes integer,
    compression_ratio double precision,
    hls_playlist_url character varying(1000),
    dash_manifest_url character varying(1000),
    available_qualities json,
    total_views integer NOT NULL,
    total_watch_time_seconds double precision NOT NULL,
    average_completion_rate double precision NOT NULL,
    thumbnail_url character varying(1000),
    thumbnail_generated_at timestamp with time zone,
    title character varying(500) NOT NULL,
    description text,
    solution_method character varying(100),
    difficulty_level character varying(20),
    language character varying(10) NOT NULL,
    instructor_name character varying(200),
    instructor_title character varying(200),
    processing_status public.videoprocessingstatus NOT NULL,
    processing_started_at timestamp with time zone,
    processing_completed_at timestamp with time zone,
    processing_error text,
    quality_score double precision NOT NULL,
    is_approved boolean NOT NULL,
    approved_by character varying,
    approved_at timestamp with time zone,
    moderation_notes text,
    has_subtitles boolean NOT NULL,
    has_transcript boolean NOT NULL,
    has_audio_description boolean NOT NULL,
    is_active boolean NOT NULL,
    is_public boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_completion_rate CHECK (((average_completion_rate >= (0.0)::double precision) AND (average_completion_rate <= (1.0)::double precision))),
    CONSTRAINT check_quality_score CHECK (((quality_score >= (0.0)::double precision) AND (quality_score <= (100.0)::double precision))),
    CONSTRAINT check_video_duration CHECK ((original_duration_seconds > (0)::double precision)),
    CONSTRAINT check_video_size CHECK ((original_size_bytes > 0))
);


--
-- Name: video_transcripts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.video_transcripts (
    id character varying NOT NULL,
    video_id character varying NOT NULL,
    language character varying(10) NOT NULL,
    full_text text NOT NULL,
    timestamped_segments json NOT NULL,
    transcript_status public.transcriptstatus NOT NULL,
    auto_generated_by character varying(100),
    auto_generation_confidence double precision,
    auto_generated_at timestamp with time zone,
    manually_edited_by character varying,
    manually_edited_at timestamp with time zone,
    edit_count integer NOT NULL,
    verified_by character varying,
    verified_at timestamp with time zone,
    keywords json,
    topics json,
    math_formulas json,
    word_count integer NOT NULL,
    average_words_per_minute double precision NOT NULL,
    readability_score double precision NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_readability CHECK (((readability_score >= (0.0)::double precision) AND (readability_score <= (100.0)::double precision))),
    CONSTRAINT check_word_count CHECK ((word_count >= 0)),
    CONSTRAINT check_wpm CHECK ((average_words_per_minute >= (0)::double precision))
);


--
-- Name: video_watch_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.video_watch_sessions (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    video_id character varying(100) NOT NULL,
    video_source character varying(20) NOT NULL,
    watch_duration integer,
    video_duration integer NOT NULL,
    completion_percentage double precision,
    last_position integer,
    watched_segments jsonb,
    pause_count integer,
    seek_count integer,
    playback_speed double precision,
    dropped_at integer,
    is_completed boolean,
    completed_at timestamp with time zone,
    started_at timestamp with time zone,
    last_updated timestamp with time zone
);


--
-- Name: weekly_goals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weekly_goals (
    id integer NOT NULL,
    plan_id integer NOT NULL,
    week_number integer NOT NULL,
    topics json,
    target_questions integer NOT NULL,
    target_reviews integer NOT NULL,
    completed_questions integer NOT NULL,
    completed_reviews integer NOT NULL,
    accuracy_rate double precision,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: weekly_goals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.weekly_goals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weekly_goals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.weekly_goals_id_seq OWNED BY public.weekly_goals.id;


--
-- Name: weekly_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weekly_progress (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
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

ALTER TABLE ONLY public.weekly_progress FORCE ROW LEVEL SECURITY;


--
-- Name: weekly_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.weekly_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weekly_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.weekly_progress_id_seq OWNED BY public.weekly_progress.id;


--
-- Name: weekly_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weekly_reports (
    id integer NOT NULL,
    child_id character varying NOT NULL,
    week_start timestamp without time zone NOT NULL,
    week_end timestamp without time zone NOT NULL,
    total_study_time integer,
    exams_taken integer,
    average_score double precision,
    subjects_studied character varying(500),
    achievements text,
    generated_at timestamp without time zone,
    sent_to_parents boolean
);


--
-- Name: weekly_reports_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.weekly_reports_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weekly_reports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.weekly_reports_id_seq OWNED BY public.weekly_reports.id;


--
-- Name: whiteboard_equations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.whiteboard_equations (
    id character varying NOT NULL,
    whiteboard_id character varying NOT NULL,
    user_id character varying NOT NULL,
    page_number integer,
    x double precision NOT NULL,
    y double precision NOT NULL,
    latex_code text NOT NULL,
    rendered_svg text,
    font_size integer,
    color character varying(20),
    width double precision,
    height double precision,
    z_index integer,
    is_deleted boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: whiteboard_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.whiteboard_sessions (
    id character varying NOT NULL,
    session_id character varying NOT NULL,
    name character varying(255),
    page_count integer,
    current_page integer,
    background_color character varying(20),
    grid_enabled boolean,
    is_active boolean,
    snapshot_url character varying(500),
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: whiteboard_strokes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.whiteboard_strokes (
    id character varying NOT NULL,
    whiteboard_id character varying NOT NULL,
    user_id character varying NOT NULL,
    page_number integer,
    tool_type public.whiteboardtooltype NOT NULL,
    color character varying(20),
    width double precision,
    opacity double precision,
    path_data jsonb,
    shape_type character varying(50),
    shape_data jsonb,
    text_content text,
    font_size integer,
    font_family character varying(100),
    z_index integer,
    is_deleted boolean,
    created_at timestamp with time zone
);


--
-- Name: xp_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.xp_transactions (
    id integer NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    amount integer NOT NULL,
    source character varying(50) NOT NULL,
    topic_id character varying,
    created_at timestamp with time zone DEFAULT now()
);

ALTER TABLE ONLY public.xp_transactions FORCE ROW LEVEL SECURITY;


--
-- Name: xp_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.xp_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: xp_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.xp_transactions_id_seq OWNED BY public.xp_transactions.id;


--
-- Name: yks_exam_goals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.yks_exam_goals (
    user_id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    exam_type character varying(20) DEFAULT 'TYT'::character varying NOT NULL,
    exam_date date NOT NULL,
    daily_minutes integer DEFAULT 120 NOT NULL,
    target_university character varying(200),
    target_department character varying(200),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT yks_exam_goals_daily_minutes_check CHECK (((daily_minutes >= 30) AND (daily_minutes <= 480))),
    CONSTRAINT yks_exam_goals_exam_type_check CHECK (((exam_type)::text = ANY ((ARRAY['TYT'::character varying, 'AYT_SAY'::character varying, 'AYT_EA'::character varying, 'AYT_SOZ'::character varying])::text[])))
);

ALTER TABLE ONLY public.yks_exam_goals FORCE ROW LEVEL SECURITY;


--
-- Name: zpd_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.zpd_history (
    id character varying NOT NULL,
    organization_id character varying DEFAULT 'org_legacy_default'::character varying NOT NULL,
    student_id character varying NOT NULL,
    topic_id character varying NOT NULL,
    zone character varying(20) NOT NULL,
    p_learn real,
    theta real,
    scaffold_level integer,
    recorded_at timestamp with time zone DEFAULT now()
);

ALTER TABLE ONLY public.zpd_history FORCE ROW LEVEL SECURITY;


--
-- Name: coppa_parental_consents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coppa_parental_consents ALTER COLUMN id SET DEFAULT nextval('public.coppa_parental_consents_id_seq'::regclass);


--
-- Name: daily_quests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_quests ALTER COLUMN id SET DEFAULT nextval('public.daily_quests_id_seq'::regclass);


--
-- Name: data_processing_agreements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_processing_agreements ALTER COLUMN id SET DEFAULT nextval('public.data_processing_agreements_id_seq'::regclass);


--
-- Name: data_retention_policies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_retention_policies ALTER COLUMN id SET DEFAULT nextval('public.data_retention_policies_id_seq'::regclass);


--
-- Name: duels id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duels ALTER COLUMN id SET DEFAULT nextval('public.duels_id_seq'::regclass);


--
-- Name: educational_record_access_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.educational_record_access_logs ALTER COLUMN id SET DEFAULT nextval('public.educational_record_access_logs_id_seq'::regclass);


--
-- Name: fallback_videos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fallback_videos ALTER COLUMN id SET DEFAULT nextval('public.fallback_videos_id_seq'::regclass);


--
-- Name: ferpa_consents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ferpa_consents ALTER COLUMN id SET DEFAULT nextval('public.ferpa_consents_id_seq'::regclass);


--
-- Name: manipulative_activities id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manipulative_activities ALTER COLUMN id SET DEFAULT nextval('public.manipulative_activities_id_seq'::regclass);


--
-- Name: manipulative_progress id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manipulative_progress ALTER COLUMN id SET DEFAULT nextval('public.manipulative_progress_id_seq'::regclass);


--
-- Name: oba_uyeler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oba_uyeler ALTER COLUMN id SET DEFAULT nextval('public.oba_uyeler_id_seq'::regclass);


--
-- Name: obalar id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.obalar ALTER COLUMN id SET DEFAULT nextval('public.obalar_id_seq'::regclass);


--
-- Name: osym_linguistic_trends id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.osym_linguistic_trends ALTER COLUMN id SET DEFAULT nextval('public.osym_linguistic_trends_id_seq'::regclass);


--
-- Name: osym_questions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.osym_questions ALTER COLUMN id SET DEFAULT nextval('public.osym_questions_id_seq'::regclass);


--
-- Name: parent_child id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_child ALTER COLUMN id SET DEFAULT nextval('public.parent_child_id_seq'::regclass);


--
-- Name: parent_link_codes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_link_codes ALTER COLUMN id SET DEFAULT nextval('public.parent_link_codes_id_seq'::regclass);


--
-- Name: parent_notifications id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_notifications ALTER COLUMN id SET DEFAULT nextval('public.parent_notifications_id_seq'::regclass);


--
-- Name: question_generation_batches id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_generation_batches ALTER COLUMN id SET DEFAULT nextval('public.question_generation_batches_id_seq'::regclass);


--
-- Name: question_generation_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_generation_logs ALTER COLUMN id SET DEFAULT nextval('public.question_generation_logs_id_seq'::regclass);


--
-- Name: quiz_questions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_questions ALTER COLUMN id SET DEFAULT nextval('public.quiz_questions_id_seq'::regclass);


--
-- Name: quiz_submissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_submissions ALTER COLUMN id SET DEFAULT nextval('public.quiz_submissions_id_seq'::regclass);


--
-- Name: realm_progress id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.realm_progress ALTER COLUMN id SET DEFAULT nextval('public.realm_progress_id_seq'::regclass);


--
-- Name: realms id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.realms ALTER COLUMN id SET DEFAULT nextval('public.realms_id_seq'::regclass);


--
-- Name: student_question_responses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_question_responses ALTER COLUMN id SET DEFAULT nextval('public.student_question_responses_id_seq'::regclass);


--
-- Name: study_plans id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_plans ALTER COLUMN id SET DEFAULT nextval('public.study_plans_id_seq'::regclass);


--
-- Name: topic_completions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_completions ALTER COLUMN id SET DEFAULT nextval('public.topic_completions_id_seq'::regclass);


--
-- Name: topic_progress id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_progress ALTER COLUMN id SET DEFAULT nextval('public.topic_progress_id_seq'::regclass);


--
-- Name: weekly_goals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_goals ALTER COLUMN id SET DEFAULT nextval('public.weekly_goals_id_seq'::regclass);


--
-- Name: weekly_progress id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_progress ALTER COLUMN id SET DEFAULT nextval('public.weekly_progress_id_seq'::regclass);


--
-- Name: weekly_reports id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_reports ALTER COLUMN id SET DEFAULT nextval('public.weekly_reports_id_seq'::regclass);


--
-- Name: xp_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.xp_transactions ALTER COLUMN id SET DEFAULT nextval('public.xp_transactions_id_seq'::regclass);


--
-- Name: api_keys api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_pkey PRIMARY KEY (id);


--
-- Name: appointment_reminders appointment_reminders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointment_reminders
    ADD CONSTRAINT appointment_reminders_pkey PRIMARY KEY (id);


--
-- Name: appointments appointments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: badges badges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.badges
    ADD CONSTRAINT badges_pkey PRIMARY KEY (id);


--
-- Name: badges badges_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.badges
    ADD CONSTRAINT badges_slug_key UNIQUE (slug);


--
-- Name: billing_data_processing_agreements billing_data_processing_agreements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_data_processing_agreements
    ADD CONSTRAINT billing_data_processing_agreements_pkey PRIMARY KEY (id);


--
-- Name: bkt_states bkt_states_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bkt_states
    ADD CONSTRAINT bkt_states_pkey PRIMARY KEY (student_id, topic_id);


--
-- Name: blocked_users blocked_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blocked_users
    ADD CONSTRAINT blocked_users_pkey PRIMARY KEY (id);


--
-- Name: campus_info campus_info_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campus_info
    ADD CONSTRAINT campus_info_pkey PRIMARY KEY (id);


--
-- Name: career_opportunities career_opportunities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.career_opportunities
    ADD CONSTRAINT career_opportunities_pkey PRIMARY KEY (id);


--
-- Name: chat_analytics chat_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_analytics
    ADD CONSTRAINT chat_analytics_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: city_living_costs city_living_costs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.city_living_costs
    ADD CONSTRAINT city_living_costs_pkey PRIMARY KEY (id);


--
-- Name: class_reports class_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_reports
    ADD CONSTRAINT class_reports_pkey PRIMARY KEY (id);


--
-- Name: classrooms classrooms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classrooms
    ADD CONSTRAINT classrooms_pkey PRIMARY KEY (id);


--
-- Name: coaching_events coaching_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coaching_events
    ADD CONSTRAINT coaching_events_pkey PRIMARY KEY (id);


--
-- Name: content_reports content_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_reports
    ADD CONSTRAINT content_reports_pkey PRIMARY KEY (id);


--
-- Name: coppa_parental_consents coppa_parental_consents_consent_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coppa_parental_consents
    ADD CONSTRAINT coppa_parental_consents_consent_id_key UNIQUE (consent_id);


--
-- Name: coppa_parental_consents coppa_parental_consents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coppa_parental_consents
    ADD CONSTRAINT coppa_parental_consents_pkey PRIMARY KEY (id);


--
-- Name: curriculum_alignments curriculum_alignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.curriculum_alignments
    ADD CONSTRAINT curriculum_alignments_pkey PRIMARY KEY (id);


--
-- Name: curriculum_update_requests curriculum_update_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.curriculum_update_requests
    ADD CONSTRAINT curriculum_update_requests_pkey PRIMARY KEY (id);


--
-- Name: daily_plans daily_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_plans
    ADD CONSTRAINT daily_plans_pkey PRIMARY KEY (id);


--
-- Name: daily_plans daily_plans_user_id_plan_date_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_plans
    ADD CONSTRAINT daily_plans_user_id_plan_date_key UNIQUE (user_id, plan_date);


--
-- Name: daily_quests daily_quests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_quests
    ADD CONSTRAINT daily_quests_pkey PRIMARY KEY (id);


--
-- Name: daily_quests daily_quests_quest_date_student_id_quest_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_quests
    ADD CONSTRAINT daily_quests_quest_date_student_id_quest_type_key UNIQUE (quest_date, student_id, quest_type);


--
-- Name: data_processing_agreements data_processing_agreements_agreement_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_processing_agreements
    ADD CONSTRAINT data_processing_agreements_agreement_id_key UNIQUE (agreement_id);


--
-- Name: data_processing_agreements data_processing_agreements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_processing_agreements
    ADD CONSTRAINT data_processing_agreements_pkey PRIMARY KEY (id);


--
-- Name: data_retention_policies data_retention_policies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_retention_policies
    ADD CONSTRAINT data_retention_policies_pkey PRIMARY KEY (id);


--
-- Name: data_retention_policies data_retention_policies_policy_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_retention_policies
    ADD CONSTRAINT data_retention_policies_policy_id_key UNIQUE (policy_id);


--
-- Name: department_curricula department_curricula_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.department_curricula
    ADD CONSTRAINT department_curricula_pkey PRIMARY KEY (id);


--
-- Name: department_statistics department_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.department_statistics
    ADD CONSTRAINT department_statistics_pkey PRIMARY KEY (id);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (id);


--
-- Name: diary_entries diary_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diary_entries
    ADD CONSTRAINT diary_entries_pkey PRIMARY KEY (id);


--
-- Name: diary_exports diary_exports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diary_exports
    ADD CONSTRAINT diary_exports_pkey PRIMARY KEY (id);


--
-- Name: dina_parameters dina_parameters_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dina_parameters
    ADD CONSTRAINT dina_parameters_pkey PRIMARY KEY (id);


--
-- Name: dina_parameters dina_parameters_question_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dina_parameters
    ADD CONSTRAINT dina_parameters_question_id_key UNIQUE (question_id);


--
-- Name: dormitory_info dormitory_info_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dormitory_info
    ADD CONSTRAINT dormitory_info_pkey PRIMARY KEY (id);


--
-- Name: duel_matches duel_matches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duel_matches
    ADD CONSTRAINT duel_matches_pkey PRIMARY KEY (id);


--
-- Name: duel_ratings duel_ratings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duel_ratings
    ADD CONSTRAINT duel_ratings_pkey PRIMARY KEY (id);


--
-- Name: duel_ratings duel_ratings_student_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duel_ratings
    ADD CONSTRAINT duel_ratings_student_id_key UNIQUE (student_id);


--
-- Name: duel_sessions duel_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duel_sessions
    ADD CONSTRAINT duel_sessions_pkey PRIMARY KEY (id);


--
-- Name: duels duels_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duels
    ADD CONSTRAINT duels_pkey PRIMARY KEY (id);


--
-- Name: dungeon_progress dungeon_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dungeon_progress
    ADD CONSTRAINT dungeon_progress_pkey PRIMARY KEY (user_id, topic_id);


--
-- Name: eba_content_analytics eba_content_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_content_analytics
    ADD CONSTRAINT eba_content_analytics_pkey PRIMARY KEY (id);


--
-- Name: eba_content_collections eba_content_collections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_content_collections
    ADD CONSTRAINT eba_content_collections_pkey PRIMARY KEY (id);


--
-- Name: eba_subject_taxonomy eba_subject_taxonomy_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_subject_taxonomy
    ADD CONSTRAINT eba_subject_taxonomy_pkey PRIMARY KEY (id);


--
-- Name: eba_video_recommendations eba_video_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_recommendations
    ADD CONSTRAINT eba_video_recommendations_pkey PRIMARY KEY (id);


--
-- Name: eba_video_usage eba_video_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_usage
    ADD CONSTRAINT eba_video_usage_pkey PRIMARY KEY (id);


--
-- Name: eba_video_watches eba_video_watches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_watches
    ADD CONSTRAINT eba_video_watches_pkey PRIMARY KEY (id);


--
-- Name: eba_videos eba_videos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_videos
    ADD CONSTRAINT eba_videos_pkey PRIMARY KEY (id);


--
-- Name: educational_contents educational_contents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.educational_contents
    ADD CONSTRAINT educational_contents_pkey PRIMARY KEY (id);


--
-- Name: educational_record_access_logs educational_record_access_logs_log_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.educational_record_access_logs
    ADD CONSTRAINT educational_record_access_logs_log_id_key UNIQUE (log_id);


--
-- Name: educational_record_access_logs educational_record_access_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.educational_record_access_logs
    ADD CONSTRAINT educational_record_access_logs_pkey PRIMARY KEY (id);


--
-- Name: emotional_states emotional_states_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emotional_states
    ADD CONSTRAINT emotional_states_pkey PRIMARY KEY (id);


--
-- Name: error_clusters error_clusters_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.error_clusters
    ADD CONSTRAINT error_clusters_pkey PRIMARY KEY (id);


--
-- Name: exam_questions exam_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exam_questions
    ADD CONSTRAINT exam_questions_pkey PRIMARY KEY (id);


--
-- Name: exam_sessions exam_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exam_sessions
    ADD CONSTRAINT exam_sessions_pkey PRIMARY KEY (id);


--
-- Name: fallback_videos fallback_videos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fallback_videos
    ADD CONSTRAINT fallback_videos_pkey PRIMARY KEY (id);


--
-- Name: fallback_videos fallback_videos_video_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fallback_videos
    ADD CONSTRAINT fallback_videos_video_id_key UNIQUE (video_id);


--
-- Name: ferpa_consents ferpa_consents_consent_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ferpa_consents
    ADD CONSTRAINT ferpa_consents_consent_id_key UNIQUE (consent_id);


--
-- Name: ferpa_consents ferpa_consents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ferpa_consents
    ADD CONSTRAINT ferpa_consents_pkey PRIMARY KEY (id);


--
-- Name: file_versions file_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_versions
    ADD CONSTRAINT file_versions_pkey PRIMARY KEY (id);


--
-- Name: forum_questions forum_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forum_questions
    ADD CONSTRAINT forum_questions_pkey PRIMARY KEY (id);


--
-- Name: forum_solutions forum_solutions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forum_solutions
    ADD CONSTRAINT forum_solutions_pkey PRIMARY KEY (id);


--
-- Name: forum_votes forum_votes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forum_votes
    ADD CONSTRAINT forum_votes_pkey PRIMARY KEY (id);


--
-- Name: fsrs_cards fsrs_cards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_cards
    ADD CONSTRAINT fsrs_cards_pkey PRIMARY KEY (id);


--
-- Name: fsrs_reviews fsrs_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_reviews
    ADD CONSTRAINT fsrs_reviews_pkey PRIMARY KEY (id);


--
-- Name: fsrs_schedules fsrs_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_schedules
    ADD CONSTRAINT fsrs_schedules_pkey PRIMARY KEY (id);


--
-- Name: fsrs_student_profiles fsrs_student_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_student_profiles
    ADD CONSTRAINT fsrs_student_profiles_pkey PRIMARY KEY (id);


--
-- Name: fsrs_student_profiles fsrs_student_profiles_student_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_student_profiles
    ADD CONSTRAINT fsrs_student_profiles_student_id_key UNIQUE (student_id);


--
-- Name: fsrs_study_sessions fsrs_study_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_study_sessions
    ADD CONSTRAINT fsrs_study_sessions_pkey PRIMARY KEY (id);


--
-- Name: fsrs_subject_stats fsrs_subject_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_subject_stats
    ADD CONSTRAINT fsrs_subject_stats_pkey PRIMARY KEY (id);


--
-- Name: goals goals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goals
    ADD CONSTRAINT goals_pkey PRIMARY KEY (id);


--
-- Name: image_uploads image_uploads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image_uploads
    ADD CONSTRAINT image_uploads_pkey PRIMARY KEY (id);


--
-- Name: insights insights_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.insights
    ADD CONSTRAINT insights_pkey PRIMARY KEY (id);


--
-- Name: invoices invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_pkey PRIMARY KEY (id);


--
-- Name: irt_calibration_history irt_calibration_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.irt_calibration_history
    ADD CONSTRAINT irt_calibration_history_pkey PRIMARY KEY (id);


--
-- Name: khan_certificates khan_certificates_badge_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.khan_certificates
    ADD CONSTRAINT khan_certificates_badge_id_key UNIQUE (badge_id);


--
-- Name: khan_certificates khan_certificates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.khan_certificates
    ADD CONSTRAINT khan_certificates_pkey PRIMARY KEY (id);


--
-- Name: khan_contents khan_contents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.khan_contents
    ADD CONSTRAINT khan_contents_pkey PRIMARY KEY (id);


--
-- Name: khan_oauth_tokens khan_oauth_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.khan_oauth_tokens
    ADD CONSTRAINT khan_oauth_tokens_pkey PRIMARY KEY (id);


--
-- Name: khan_user_progress khan_user_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.khan_user_progress
    ADD CONSTRAINT khan_user_progress_pkey PRIMARY KEY (id);


--
-- Name: kiro2_cat_sessions kiro2_cat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kiro2_cat_sessions
    ADD CONSTRAINT kiro2_cat_sessions_pkey PRIMARY KEY (id);


--
-- Name: kiro2_learning_events kiro2_learning_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kiro2_learning_events
    ADD CONSTRAINT kiro2_learning_events_pkey PRIMARY KEY (id);


--
-- Name: knowledge_points knowledge_points_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_points
    ADD CONSTRAINT knowledge_points_pkey PRIMARY KEY (id);


--
-- Name: kvkk_audit_logs kvkk_audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_audit_logs
    ADD CONSTRAINT kvkk_audit_logs_pkey PRIMARY KEY (id);


--
-- Name: kvkk_consents kvkk_consents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_consents
    ADD CONSTRAINT kvkk_consents_pkey PRIMARY KEY (id);


--
-- Name: kvkk_data_deletion_requests kvkk_data_deletion_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_data_deletion_requests
    ADD CONSTRAINT kvkk_data_deletion_requests_pkey PRIMARY KEY (id);


--
-- Name: kvkk_data_export_requests kvkk_data_export_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_data_export_requests
    ADD CONSTRAINT kvkk_data_export_requests_pkey PRIMARY KEY (id);


--
-- Name: kvkk_privacy_policy_versions kvkk_privacy_policy_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_privacy_policy_versions
    ADD CONSTRAINT kvkk_privacy_policy_versions_pkey PRIMARY KEY (id);


--
-- Name: kvkk_privacy_policy_versions kvkk_privacy_policy_versions_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_privacy_policy_versions
    ADD CONSTRAINT kvkk_privacy_policy_versions_version_key UNIQUE (version);


--
-- Name: league_history league_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.league_history
    ADD CONSTRAINT league_history_pkey PRIMARY KEY (id);


--
-- Name: league_memberships league_memberships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.league_memberships
    ADD CONSTRAINT league_memberships_pkey PRIMARY KEY (id);


--
-- Name: learning_analytics learning_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_analytics
    ADD CONSTRAINT learning_analytics_pkey PRIMARY KEY (id);


--
-- Name: learning_entries learning_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_entries
    ADD CONSTRAINT learning_entries_pkey PRIMARY KEY (id);


--
-- Name: learning_outcomes learning_outcomes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_outcomes
    ADD CONSTRAINT learning_outcomes_pkey PRIMARY KEY (id);


--
-- Name: learning_path_student_profiles learning_path_student_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_path_student_profiles
    ADD CONSTRAINT learning_path_student_profiles_pkey PRIMARY KEY (student_id);


--
-- Name: learning_paths learning_paths_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_paths
    ADD CONSTRAINT learning_paths_pkey PRIMARY KEY (path_id);


--
-- Name: learning_progress_daily learning_progress_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_progress_daily
    ADD CONSTRAINT learning_progress_daily_pkey PRIMARY KEY (id);


--
-- Name: learning_progress_daily learning_progress_daily_user_id_log_date_subject_activity_t_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_progress_daily
    ADD CONSTRAINT learning_progress_daily_user_id_log_date_subject_activity_t_key UNIQUE (user_id, log_date, subject, activity_type);


--
-- Name: live_sessions live_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.live_sessions
    ADD CONSTRAINT live_sessions_pkey PRIMARY KEY (id);


--
-- Name: manipulative_activities manipulative_activities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manipulative_activities
    ADD CONSTRAINT manipulative_activities_pkey PRIMARY KEY (id);


--
-- Name: manipulative_progress manipulative_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manipulative_progress
    ADD CONSTRAINT manipulative_progress_pkey PRIMARY KEY (id);


--
-- Name: meb_curriculum_nodes meb_curriculum_nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meb_curriculum_nodes
    ADD CONSTRAINT meb_curriculum_nodes_pkey PRIMARY KEY (id);


--
-- Name: meb_curriculum_standards meb_curriculum_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meb_curriculum_standards
    ADD CONSTRAINT meb_curriculum_standards_pkey PRIMARY KEY (id);


--
-- Name: mentor_feedback mentor_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mentor_feedback
    ADD CONSTRAINT mentor_feedback_pkey PRIMARY KEY (id);


--
-- Name: mentor_pairs mentor_pairs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mentor_pairs
    ADD CONSTRAINT mentor_pairs_pkey PRIMARY KEY (id);


--
-- Name: mentor_sessions mentor_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mentor_sessions
    ADD CONSTRAINT mentor_sessions_pkey PRIMARY KEY (id);


--
-- Name: message_audit_log message_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_audit_log
    ADD CONSTRAINT message_audit_log_pkey PRIMARY KEY (id);


--
-- Name: misconception_matrix misconception_matrix_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.misconception_matrix
    ADD CONSTRAINT misconception_matrix_pkey PRIMARY KEY (id);


--
-- Name: misconception_remedies misconception_remedies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.misconception_remedies
    ADD CONSTRAINT misconception_remedies_pkey PRIMARY KEY (id);


--
-- Name: moderation_actions moderation_actions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moderation_actions
    ADD CONSTRAINT moderation_actions_pkey PRIMARY KEY (id);


--
-- Name: moderation_queue moderation_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moderation_queue
    ADD CONSTRAINT moderation_queue_pkey PRIMARY KEY (id);


--
-- Name: nano_skills nano_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nano_skills
    ADD CONSTRAINT nano_skills_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: oba_challenge_progress oba_challenge_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oba_challenge_progress
    ADD CONSTRAINT oba_challenge_progress_pkey PRIMARY KEY (id);


--
-- Name: oba_challenges oba_challenges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oba_challenges
    ADD CONSTRAINT oba_challenges_pkey PRIMARY KEY (id);


--
-- Name: oba_uyeler oba_uyeler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oba_uyeler
    ADD CONSTRAINT oba_uyeler_pkey PRIMARY KEY (id);


--
-- Name: oba_uyeler oba_uyeler_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oba_uyeler
    ADD CONSTRAINT oba_uyeler_user_id_key UNIQUE (user_id);


--
-- Name: obalar obalar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.obalar
    ADD CONSTRAINT obalar_pkey PRIMARY KEY (id);


--
-- Name: offline_sync_packages offline_sync_packages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.offline_sync_packages
    ADD CONSTRAINT offline_sync_packages_pkey PRIMARY KEY (package_id);


--
-- Name: org_memberships org_memberships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_memberships
    ADD CONSTRAINT org_memberships_pkey PRIMARY KEY (id);


--
-- Name: organization_licenses organization_licenses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_licenses
    ADD CONSTRAINT organization_licenses_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: osb_settings osb_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.osb_settings
    ADD CONSTRAINT osb_settings_pkey PRIMARY KEY (id);


--
-- Name: osb_settings osb_settings_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.osb_settings
    ADD CONSTRAINT osb_settings_user_id_key UNIQUE (user_id);


--
-- Name: osym_linguistic_trends osym_linguistic_trends_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.osym_linguistic_trends
    ADD CONSTRAINT osym_linguistic_trends_pkey PRIMARY KEY (id);


--
-- Name: osym_questions osym_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.osym_questions
    ADD CONSTRAINT osym_questions_pkey PRIMARY KEY (id);


--
-- Name: osym_standards osym_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.osym_standards
    ADD CONSTRAINT osym_standards_pkey PRIMARY KEY (id);


--
-- Name: parent_approvals parent_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_approvals
    ADD CONSTRAINT parent_approvals_pkey PRIMARY KEY (id);


--
-- Name: parent_child parent_child_parent_id_child_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_child
    ADD CONSTRAINT parent_child_parent_id_child_id_key UNIQUE (parent_id, child_id);


--
-- Name: parent_child parent_child_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_child
    ADD CONSTRAINT parent_child_pkey PRIMARY KEY (id);


--
-- Name: parent_link_codes parent_link_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_link_codes
    ADD CONSTRAINT parent_link_codes_pkey PRIMARY KEY (id);


--
-- Name: parent_notifications parent_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_notifications
    ADD CONSTRAINT parent_notifications_pkey PRIMARY KEY (id);


--
-- Name: parent_profiles parent_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_profiles
    ADD CONSTRAINT parent_profiles_pkey PRIMARY KEY (id);


--
-- Name: parent_profiles parent_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_profiles
    ADD CONSTRAINT parent_profiles_user_id_key UNIQUE (user_id);


--
-- Name: parent_reports parent_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_reports
    ADD CONSTRAINT parent_reports_pkey PRIMARY KEY (id);


--
-- Name: parent_social_settings parent_social_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_social_settings
    ADD CONSTRAINT parent_social_settings_pkey PRIMARY KEY (id);


--
-- Name: peer_comparisons peer_comparisons_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.peer_comparisons
    ADD CONSTRAINT peer_comparisons_pkey PRIMARY KEY (id);


--
-- Name: peer_recommendations peer_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.peer_recommendations
    ADD CONSTRAINT peer_recommendations_pkey PRIMARY KEY (id);


--
-- Name: performance_history performance_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_history
    ADD CONSTRAINT performance_history_pkey PRIMARY KEY (id);


--
-- Name: plans plans_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plans
    ADD CONSTRAINT plans_code_key UNIQUE (code);


--
-- Name: plans plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plans
    ADD CONSTRAINT plans_pkey PRIMARY KEY (id);


--
-- Name: point_transactions point_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.point_transactions
    ADD CONSTRAINT point_transactions_pkey PRIMARY KEY (id);


--
-- Name: pomodoro_participants pomodoro_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pomodoro_participants
    ADD CONSTRAINT pomodoro_participants_pkey PRIMARY KEY (id);


--
-- Name: pomodoro_rooms pomodoro_rooms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pomodoro_rooms
    ADD CONSTRAINT pomodoro_rooms_pkey PRIMARY KEY (id);


--
-- Name: program_score_history program_score_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.program_score_history
    ADD CONSTRAINT program_score_history_pkey PRIMARY KEY (id);


--
-- Name: q_matrix q_matrix_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.q_matrix
    ADD CONSTRAINT q_matrix_pkey PRIMARY KEY (id);


--
-- Name: quality_gate_results quality_gate_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quality_gate_results
    ADD CONSTRAINT quality_gate_results_pkey PRIMARY KEY (id);


--
-- Name: quality_gates_override_audit quality_gates_override_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quality_gates_override_audit
    ADD CONSTRAINT quality_gates_override_audit_pkey PRIMARY KEY (id);


--
-- Name: quality_gates_runs quality_gates_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quality_gates_runs
    ADD CONSTRAINT quality_gates_runs_pkey PRIMARY KEY (id);


--
-- Name: question_bank question_bank_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_bank
    ADD CONSTRAINT question_bank_pkey PRIMARY KEY (id);


--
-- Name: question_content question_content_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_content
    ADD CONSTRAINT question_content_pkey PRIMARY KEY (id);


--
-- Name: question_generation_batches question_generation_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_generation_batches
    ADD CONSTRAINT question_generation_batches_pkey PRIMARY KEY (id);


--
-- Name: question_generation_logs question_generation_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_generation_logs
    ADD CONSTRAINT question_generation_logs_pkey PRIMARY KEY (id);


--
-- Name: question_knowledge_mappings question_knowledge_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_knowledge_mappings
    ADD CONSTRAINT question_knowledge_mappings_pkey PRIMARY KEY (id);


--
-- Name: question_metadata question_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_metadata
    ADD CONSTRAINT question_metadata_pkey PRIMARY KEY (id);


--
-- Name: question_performance_analytics question_performance_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_performance_analytics
    ADD CONSTRAINT question_performance_analytics_pkey PRIMARY KEY (id);


--
-- Name: question_statistics question_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_statistics
    ADD CONSTRAINT question_statistics_pkey PRIMARY KEY (id);


--
-- Name: question_tag_associations question_tag_associations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_tag_associations
    ADD CONSTRAINT question_tag_associations_pkey PRIMARY KEY (id);


--
-- Name: question_tags question_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_tags
    ADD CONSTRAINT question_tags_pkey PRIMARY KEY (id);


--
-- Name: question_tags question_tags_tag_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_tags
    ADD CONSTRAINT question_tags_tag_name_key UNIQUE (tag_name);


--
-- Name: quiz_questions quiz_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_pkey PRIMARY KEY (id);


--
-- Name: quiz_submissions quiz_submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_submissions
    ADD CONSTRAINT quiz_submissions_pkey PRIMARY KEY (id);


--
-- Name: quizzes quizzes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quizzes
    ADD CONSTRAINT quizzes_pkey PRIMARY KEY (id);


--
-- Name: realm_progress realm_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.realm_progress
    ADD CONSTRAINT realm_progress_pkey PRIMARY KEY (id);


--
-- Name: realm_progress realm_progress_student_id_realm_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.realm_progress
    ADD CONSTRAINT realm_progress_student_id_realm_id_key UNIQUE (student_id, realm_id);


--
-- Name: realms realms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.realms
    ADD CONSTRAINT realms_pkey PRIMARY KEY (id);


--
-- Name: realms realms_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.realms
    ADD CONSTRAINT realms_slug_key UNIQUE (slug);


--
-- Name: reasoning_cache reasoning_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reasoning_cache
    ADD CONSTRAINT reasoning_cache_pkey PRIMARY KEY (id);


--
-- Name: reasoning_sessions reasoning_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reasoning_sessions
    ADD CONSTRAINT reasoning_sessions_pkey PRIMARY KEY (id);


--
-- Name: reasoning_steps reasoning_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reasoning_steps
    ADD CONSTRAINT reasoning_steps_pkey PRIMARY KEY (id);


--
-- Name: recording_bookmarks recording_bookmarks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recording_bookmarks
    ADD CONSTRAINT recording_bookmarks_pkey PRIMARY KEY (id);


--
-- Name: recording_views recording_views_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recording_views
    ADD CONSTRAINT recording_views_pkey PRIMARY KEY (id);


--
-- Name: reflections reflections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reflections
    ADD CONSTRAINT reflections_pkey PRIMARY KEY (id);


--
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- Name: review_ratings review_ratings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_ratings
    ADD CONSTRAINT review_ratings_pkey PRIMARY KEY (id);


--
-- Name: review_reports review_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_reports
    ADD CONSTRAINT review_reports_pkey PRIMARY KEY (id);


--
-- Name: review_statistics review_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_statistics
    ADD CONSTRAINT review_statistics_pkey PRIMARY KEY (id);


--
-- Name: review_votes review_votes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_votes
    ADD CONSTRAINT review_votes_pkey PRIMARY KEY (id);


--
-- Name: room_analytics room_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_analytics
    ADD CONSTRAINT room_analytics_pkey PRIMARY KEY (id);


--
-- Name: room_analytics room_analytics_room_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_analytics
    ADD CONSTRAINT room_analytics_room_id_key UNIQUE (room_id);


--
-- Name: room_chat_messages room_chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_chat_messages
    ADD CONSTRAINT room_chat_messages_pkey PRIMARY KEY (id);


--
-- Name: room_invitations room_invitations_invitation_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_invitations
    ADD CONSTRAINT room_invitations_invitation_code_key UNIQUE (invitation_code);


--
-- Name: room_invitations room_invitations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_invitations
    ADD CONSTRAINT room_invitations_pkey PRIMARY KEY (id);


--
-- Name: room_members room_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_members
    ADD CONSTRAINT room_members_pkey PRIMARY KEY (id);


--
-- Name: room_settings room_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_settings
    ADD CONSTRAINT room_settings_pkey PRIMARY KEY (id);


--
-- Name: room_settings room_settings_room_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_settings
    ADD CONSTRAINT room_settings_room_id_key UNIQUE (room_id);


--
-- Name: room_study_sessions room_study_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_study_sessions
    ADD CONSTRAINT room_study_sessions_pkey PRIMARY KEY (id);


--
-- Name: salary_expectations salary_expectations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salary_expectations
    ADD CONSTRAINT salary_expectations_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: scholarship_programs scholarship_programs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarship_programs
    ADD CONSTRAINT scholarship_programs_pkey PRIMARY KEY (id);


--
-- Name: screen_shares screen_shares_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.screen_shares
    ADD CONSTRAINT screen_shares_pkey PRIMARY KEY (id);


--
-- Name: sector_analyses sector_analyses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sector_analyses
    ADD CONSTRAINT sector_analyses_pkey PRIMARY KEY (id);


--
-- Name: session_analytics session_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_analytics
    ADD CONSTRAINT session_analytics_pkey PRIMARY KEY (id);


--
-- Name: session_analytics session_analytics_session_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_analytics
    ADD CONSTRAINT session_analytics_session_id_key UNIQUE (session_id);


--
-- Name: session_chat_messages session_chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_chat_messages
    ADD CONSTRAINT session_chat_messages_pkey PRIMARY KEY (id);


--
-- Name: session_participants session_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_participants
    ADD CONSTRAINT session_participants_pkey PRIMARY KEY (id);


--
-- Name: session_recordings session_recordings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_recordings
    ADD CONSTRAINT session_recordings_pkey PRIMARY KEY (id);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: shared_files shared_files_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shared_files
    ADD CONSTRAINT shared_files_pkey PRIMARY KEY (id);


--
-- Name: solution_duel_submissions solution_duel_submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_duel_submissions
    ADD CONSTRAINT solution_duel_submissions_pkey PRIMARY KEY (id);


--
-- Name: solution_duel_votes solution_duel_votes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_duel_votes
    ADD CONSTRAINT solution_duel_votes_pkey PRIMARY KEY (id);


--
-- Name: solution_duels solution_duels_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_duels
    ADD CONSTRAINT solution_duels_pkey PRIMARY KEY (id);


--
-- Name: solution_steps solution_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_steps
    ADD CONSTRAINT solution_steps_pkey PRIMARY KEY (id);


--
-- Name: streak_daily_log streak_daily_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streak_daily_log
    ADD CONSTRAINT streak_daily_log_pkey PRIMARY KEY (id);


--
-- Name: streak_pairs streak_pairs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streak_pairs
    ADD CONSTRAINT streak_pairs_pkey PRIMARY KEY (id);


--
-- Name: streak_tracking streak_tracking_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streak_tracking
    ADD CONSTRAINT streak_tracking_pkey PRIMARY KEY (id);


--
-- Name: streaks streaks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streaks
    ADD CONSTRAINT streaks_pkey PRIMARY KEY (user_id);


--
-- Name: student_abilities student_abilities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_abilities
    ADD CONSTRAINT student_abilities_pkey PRIMARY KEY (student_id, subject_id);


--
-- Name: student_answers student_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_answers
    ADD CONSTRAINT student_answers_pkey PRIMARY KEY (id);


--
-- Name: student_engagement_signals student_engagement_signals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_engagement_signals
    ADD CONSTRAINT student_engagement_signals_pkey PRIMARY KEY (id);


--
-- Name: student_goals student_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_goals
    ADD CONSTRAINT student_goals_pkey PRIMARY KEY (id);


--
-- Name: student_grades student_grades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_grades
    ADD CONSTRAINT student_grades_pkey PRIMARY KEY (id);


--
-- Name: student_knowledge_states student_knowledge_states_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_knowledge_states
    ADD CONSTRAINT student_knowledge_states_pkey PRIMARY KEY (id);


--
-- Name: student_learning_profiles student_learning_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_learning_profiles
    ADD CONSTRAINT student_learning_profiles_pkey PRIMARY KEY (id);


--
-- Name: student_nano_skill_mastery student_nano_skill_mastery_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_nano_skill_mastery
    ADD CONSTRAINT student_nano_skill_mastery_pkey PRIMARY KEY (id);


--
-- Name: student_profiles student_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_pkey PRIMARY KEY (id);


--
-- Name: student_profiles student_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_user_id_key UNIQUE (user_id);


--
-- Name: student_question_flags student_question_flags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_question_flags
    ADD CONSTRAINT student_question_flags_pkey PRIMARY KEY (id);


--
-- Name: student_question_responses student_question_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_question_responses
    ADD CONSTRAINT student_question_responses_pkey PRIMARY KEY (id);


--
-- Name: student_reviews student_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_reviews
    ADD CONSTRAINT student_reviews_pkey PRIMARY KEY (id);


--
-- Name: study_plans study_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_plans
    ADD CONSTRAINT study_plans_pkey PRIMARY KEY (id);


--
-- Name: study_rooms study_rooms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_rooms
    ADD CONSTRAINT study_rooms_pkey PRIMARY KEY (id);


--
-- Name: study_sessions study_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_sessions
    ADD CONSTRAINT study_sessions_pkey PRIMARY KEY (id);


--
-- Name: sub_problems sub_problems_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sub_problems
    ADD CONSTRAINT sub_problems_pkey PRIMARY KEY (id);


--
-- Name: system_configurations system_configurations_config_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_configurations
    ADD CONSTRAINT system_configurations_config_key_key UNIQUE (config_key);


--
-- Name: system_configurations system_configurations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_configurations
    ADD CONSTRAINT system_configurations_pkey PRIMARY KEY (id);


--
-- Name: teacher_assignments teacher_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_assignments
    ADD CONSTRAINT teacher_assignments_pkey PRIMARY KEY (id);


--
-- Name: teacher_availability teacher_availability_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_availability
    ADD CONSTRAINT teacher_availability_pkey PRIMARY KEY (id);


--
-- Name: teacher_certifications teacher_certifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_certifications
    ADD CONSTRAINT teacher_certifications_pkey PRIMARY KEY (id);


--
-- Name: teacher_classroom_students teacher_classroom_students_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_classroom_students
    ADD CONSTRAINT teacher_classroom_students_pkey PRIMARY KEY (id);


--
-- Name: teacher_classrooms teacher_classrooms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_classrooms
    ADD CONSTRAINT teacher_classrooms_pkey PRIMARY KEY (id);


--
-- Name: teacher_contents teacher_contents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_contents
    ADD CONSTRAINT teacher_contents_pkey PRIMARY KEY (id);


--
-- Name: teacher_exam_configs teacher_exam_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_exam_configs
    ADD CONSTRAINT teacher_exam_configs_pkey PRIMARY KEY (id);


--
-- Name: teacher_expertise teacher_expertise_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_expertise
    ADD CONSTRAINT teacher_expertise_pkey PRIMARY KEY (id);


--
-- Name: teacher_pool_profiles teacher_pool_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_pool_profiles
    ADD CONSTRAINT teacher_pool_profiles_pkey PRIMARY KEY (id);


--
-- Name: teacher_pool_profiles teacher_pool_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_pool_profiles
    ADD CONSTRAINT teacher_pool_profiles_user_id_key UNIQUE (user_id);


--
-- Name: teacher_profiles teacher_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_profiles
    ADD CONSTRAINT teacher_profiles_pkey PRIMARY KEY (id);


--
-- Name: teacher_profiles teacher_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_profiles
    ADD CONSTRAINT teacher_profiles_user_id_key UNIQUE (user_id);


--
-- Name: teacher_reviews teacher_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_reviews
    ADD CONSTRAINT teacher_reviews_pkey PRIMARY KEY (id);


--
-- Name: teacher_statistics teacher_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_statistics
    ADD CONSTRAINT teacher_statistics_pkey PRIMARY KEY (id);


--
-- Name: teacher_statistics teacher_statistics_teacher_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_statistics
    ADD CONSTRAINT teacher_statistics_teacher_id_key UNIQUE (teacher_id);


--
-- Name: topic_completions topic_completions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_completions
    ADD CONSTRAINT topic_completions_pkey PRIMARY KEY (id);


--
-- Name: topic_hierarchy topic_hierarchy_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_hierarchy
    ADD CONSTRAINT topic_hierarchy_code_key UNIQUE (code);


--
-- Name: topic_hierarchy topic_hierarchy_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_hierarchy
    ADD CONSTRAINT topic_hierarchy_pkey PRIMARY KEY (id);


--
-- Name: topic_prerequisites topic_prerequisites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_prerequisites
    ADD CONSTRAINT topic_prerequisites_pkey PRIMARY KEY (id);


--
-- Name: topic_progress topic_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_progress
    ADD CONSTRAINT topic_progress_pkey PRIMARY KEY (id);


--
-- Name: universities universities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universities
    ADD CONSTRAINT universities_pkey PRIMARY KEY (id);


--
-- Name: university_programs university_programs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.university_programs
    ADD CONSTRAINT university_programs_pkey PRIMARY KEY (id);


--
-- Name: university_statistics university_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.university_statistics
    ADD CONSTRAINT university_statistics_pkey PRIMARY KEY (id);


--
-- Name: blocked_users uq_block_pair; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blocked_users
    ADD CONSTRAINT uq_block_pair UNIQUE (blocker_id, blocked_id);


--
-- Name: solution_duel_votes uq_duel_vote; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_duel_votes
    ADD CONSTRAINT uq_duel_vote UNIQUE (duel_id, voter_id);


--
-- Name: eba_content_analytics uq_eba_analytics; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_content_analytics
    ADD CONSTRAINT uq_eba_analytics UNIQUE (analysis_date, category, grade_level);


--
-- Name: eba_video_usage uq_eba_video_usage; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_usage
    ADD CONSTRAINT uq_eba_video_usage UNIQUE (video_id, student_id, started_at);


--
-- Name: exam_questions uq_exam_question_order; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exam_questions
    ADD CONSTRAINT uq_exam_question_order UNIQUE (exam_session_id, question_order);


--
-- Name: forum_votes uq_forum_vote; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forum_votes
    ADD CONSTRAINT uq_forum_vote UNIQUE (voter_id, solution_id);


--
-- Name: fsrs_schedules uq_fsrs_schedule; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_schedules
    ADD CONSTRAINT uq_fsrs_schedule UNIQUE (student_id, schedule_date);


--
-- Name: fsrs_subject_stats uq_fsrs_subject_stats; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_subject_stats
    ADD CONSTRAINT uq_fsrs_subject_stats UNIQUE (student_id, subject_area);


--
-- Name: invoices uq_invoice_no; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT uq_invoice_no UNIQUE (invoice_no);


--
-- Name: learning_analytics uq_learning_analytics; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_analytics
    ADD CONSTRAINT uq_learning_analytics UNIQUE (student_id, date, subject_area);


--
-- Name: org_memberships uq_org_membership; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_memberships
    ADD CONSTRAINT uq_org_membership UNIQUE (organization_id, user_id);


--
-- Name: parent_social_settings uq_parent_student_settings; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_social_settings
    ADD CONSTRAINT uq_parent_student_settings UNIQUE (parent_id, student_id);


--
-- Name: q_matrix uq_qmatrix_question_skill; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.q_matrix
    ADD CONSTRAINT uq_qmatrix_question_skill UNIQUE (question_id, nano_skill_id);


--
-- Name: question_performance_analytics uq_question_analytics; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_performance_analytics
    ADD CONSTRAINT uq_question_analytics UNIQUE (question_id, analysis_date, period_type);


--
-- Name: question_knowledge_mappings uq_question_knowledge_mapping; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_knowledge_mappings
    ADD CONSTRAINT uq_question_knowledge_mapping UNIQUE (question_id, knowledge_point_id);


--
-- Name: question_tag_associations uq_question_tag; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_tag_associations
    ADD CONSTRAINT uq_question_tag UNIQUE (question_id, tag_id);


--
-- Name: student_answers uq_student_answer; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_answers
    ADD CONSTRAINT uq_student_answer UNIQUE (exam_session_id, question_id);


--
-- Name: student_question_flags uq_student_flags_user_question_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_question_flags
    ADD CONSTRAINT uq_student_flags_user_question_type UNIQUE (user_id, question_id, flag_type);


--
-- Name: student_knowledge_states uq_student_knowledge_state; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_knowledge_states
    ADD CONSTRAINT uq_student_knowledge_state UNIQUE (student_id, knowledge_point_id);


--
-- Name: student_nano_skill_mastery uq_student_nano_skill; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_nano_skill_mastery
    ADD CONSTRAINT uq_student_nano_skill UNIQUE (student_id, nano_skill_id);


--
-- Name: weekly_progress uq_weekly_progress; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_progress
    ADD CONSTRAINT uq_weekly_progress UNIQUE (user_id, year, week_number);


--
-- Name: user_achievements user_achievements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_pkey PRIMARY KEY (id);


--
-- Name: user_badges user_badges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_badges
    ADD CONSTRAINT user_badges_pkey PRIMARY KEY (id);


--
-- Name: user_badges user_badges_user_id_badge_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_badges
    ADD CONSTRAINT user_badges_user_id_badge_id_key UNIQUE (user_id, badge_id);


--
-- Name: user_theta user_theta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_theta
    ADD CONSTRAINT user_theta_pkey PRIMARY KEY (user_id, subject_area);


--
-- Name: user_university_preferences user_university_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_university_preferences
    ADD CONSTRAINT user_university_preferences_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: veli_consent veli_consent_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.veli_consent
    ADD CONSTRAINT veli_consent_pkey PRIMARY KEY (id);


--
-- Name: video_analytics video_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_analytics
    ADD CONSTRAINT video_analytics_pkey PRIMARY KEY (id);


--
-- Name: video_analytics_summary video_analytics_summary_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_analytics_summary
    ADD CONSTRAINT video_analytics_summary_pkey PRIMARY KEY (id);


--
-- Name: video_bookmarks video_bookmarks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_bookmarks
    ADD CONSTRAINT video_bookmarks_pkey PRIMARY KEY (id);


--
-- Name: video_completion_milestones video_completion_milestones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_completion_milestones
    ADD CONSTRAINT video_completion_milestones_pkey PRIMARY KEY (id);


--
-- Name: video_notes video_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_notes
    ADD CONSTRAINT video_notes_pkey PRIMARY KEY (id);


--
-- Name: video_solutions video_solutions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_solutions
    ADD CONSTRAINT video_solutions_pkey PRIMARY KEY (id);


--
-- Name: video_transcripts video_transcripts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_transcripts
    ADD CONSTRAINT video_transcripts_pkey PRIMARY KEY (id);


--
-- Name: video_watch_sessions video_watch_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_watch_sessions
    ADD CONSTRAINT video_watch_sessions_pkey PRIMARY KEY (id);


--
-- Name: weekly_goals weekly_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_goals
    ADD CONSTRAINT weekly_goals_pkey PRIMARY KEY (id);


--
-- Name: weekly_progress weekly_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_progress
    ADD CONSTRAINT weekly_progress_pkey PRIMARY KEY (id);


--
-- Name: weekly_reports weekly_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_reports
    ADD CONSTRAINT weekly_reports_pkey PRIMARY KEY (id);


--
-- Name: whiteboard_equations whiteboard_equations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.whiteboard_equations
    ADD CONSTRAINT whiteboard_equations_pkey PRIMARY KEY (id);


--
-- Name: whiteboard_sessions whiteboard_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.whiteboard_sessions
    ADD CONSTRAINT whiteboard_sessions_pkey PRIMARY KEY (id);


--
-- Name: whiteboard_strokes whiteboard_strokes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.whiteboard_strokes
    ADD CONSTRAINT whiteboard_strokes_pkey PRIMARY KEY (id);


--
-- Name: xp_transactions xp_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.xp_transactions
    ADD CONSTRAINT xp_transactions_pkey PRIMARY KEY (id);


--
-- Name: yks_exam_goals yks_exam_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.yks_exam_goals
    ADD CONSTRAINT yks_exam_goals_pkey PRIMARY KEY (user_id);


--
-- Name: zpd_history zpd_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zpd_history
    ADD CONSTRAINT zpd_history_pkey PRIMARY KEY (id);


--
-- Name: idx_alignment_meb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alignment_meb ON public.curriculum_alignments USING btree (meb_standard_id);


--
-- Name: idx_alignment_osym; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alignment_osym ON public.curriculum_alignments USING btree (osym_standard_id);


--
-- Name: idx_alignment_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alignment_score ON public.curriculum_alignments USING btree (alignment_score);


--
-- Name: idx_analytics_completion; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_completion ON public.video_analytics USING btree (completion_percentage);


--
-- Name: idx_analytics_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_created ON public.video_analytics USING btree (created_at);


--
-- Name: idx_analytics_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_session ON public.video_analytics USING btree (session_id);


--
-- Name: idx_analytics_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_user ON public.video_analytics USING btree (user_id);


--
-- Name: idx_analytics_video; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analytics_video ON public.video_analytics USING btree (video_id);


--
-- Name: idx_api_key_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_active ON public.api_keys USING btree (is_active);


--
-- Name: idx_api_key_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_expires ON public.api_keys USING btree (expires_at);


--
-- Name: idx_api_key_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_hash ON public.api_keys USING btree (key_hash);


--
-- Name: idx_api_key_prefix; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_prefix ON public.api_keys USING btree (key_prefix);


--
-- Name: idx_api_key_revoked; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_revoked ON public.api_keys USING btree (revoked);


--
-- Name: idx_api_key_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_user ON public.api_keys USING btree (user_id);


--
-- Name: idx_approval_parent_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_approval_parent_status ON public.parent_approvals USING btree (parent_user_id, status);


--
-- Name: idx_approval_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_approval_student ON public.parent_approvals USING btree (student_user_id);


--
-- Name: idx_audit_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_action ON public.audit_logs USING btree (action);


--
-- Name: idx_audit_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_created ON public.audit_logs USING btree (created_at);


--
-- Name: idx_audit_resource; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_resource ON public.audit_logs USING btree (resource_type, resource_id);


--
-- Name: idx_audit_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_user ON public.audit_logs USING btree (user_id);


--
-- Name: idx_base_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_base_score ON public.university_programs USING btree (year, score_type, base_score);


--
-- Name: idx_batch_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_batch_status ON public.question_generation_batches USING btree (status, created_at);


--
-- Name: idx_billing_dpa_org; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_billing_dpa_org ON public.billing_data_processing_agreements USING btree (organization_id);


--
-- Name: idx_campus_info_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_campus_info_city ON public.campus_info USING btree (city);


--
-- Name: idx_campus_info_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_campus_info_type ON public.campus_info USING btree (campus_type);


--
-- Name: idx_campus_info_university; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_campus_info_university ON public.campus_info USING btree (university_id);


--
-- Name: idx_chat_analytics_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_analytics_date ON public.chat_analytics USING btree (date);


--
-- Name: idx_chat_analytics_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_analytics_period ON public.chat_analytics USING btree (period_type);


--
-- Name: idx_chat_analytics_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_analytics_user ON public.chat_analytics USING btree (user_id);


--
-- Name: idx_chat_messages_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_messages_created ON public.chat_messages USING btree (created_at);


--
-- Name: idx_chat_messages_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_messages_role ON public.chat_messages USING btree (role);


--
-- Name: idx_chat_messages_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_messages_session ON public.chat_messages USING btree (session_id);


--
-- Name: idx_chat_sessions_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_sessions_created ON public.chat_sessions USING btree (created_at);


--
-- Name: idx_chat_sessions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_sessions_status ON public.chat_sessions USING btree (status);


--
-- Name: idx_chat_sessions_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_sessions_subject ON public.chat_sessions USING btree (subject_type);


--
-- Name: idx_chat_sessions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_sessions_user ON public.chat_sessions USING btree (user_id);


--
-- Name: idx_city_living_cost_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_city_living_cost_city ON public.city_living_costs USING btree (city);


--
-- Name: idx_city_living_cost_city_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_city_living_cost_city_year ON public.city_living_costs USING btree (city, year);


--
-- Name: idx_city_living_cost_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_city_living_cost_year ON public.city_living_costs USING btree (year);


--
-- Name: idx_class_report_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_class_report_period ON public.class_reports USING btree (report_period);


--
-- Name: idx_class_report_teacher; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_class_report_teacher ON public.class_reports USING btree (teacher_user_id, created_at);


--
-- Name: idx_classroom_grade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classroom_grade ON public.classrooms USING btree (grade_level);


--
-- Name: idx_classroom_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classroom_subject ON public.classrooms USING btree (subject_area);


--
-- Name: idx_classroom_teacher; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classroom_teacher ON public.classrooms USING btree (teacher_id);


--
-- Name: idx_completion_student_node; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_completion_student_node ON public.topic_completions USING btree (student_id, node_id);


--
-- Name: idx_config_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_config_key ON public.system_configurations USING btree (config_key);


--
-- Name: idx_content_difficulty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content_difficulty ON public.educational_contents USING btree (difficulty_level);


--
-- Name: idx_content_grade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content_grade ON public.educational_contents USING btree (grade_level);


--
-- Name: idx_content_platform; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content_platform ON public.educational_contents USING btree (source_platform);


--
-- Name: idx_content_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content_score ON public.educational_contents USING btree (educational_score);


--
-- Name: idx_content_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content_subject ON public.educational_contents USING btree (subject_area);


--
-- Name: idx_content_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content_topic ON public.educational_contents USING btree (topic);


--
-- Name: idx_daily_plans_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daily_plans_organization_id ON public.daily_plans USING btree (organization_id);


--
-- Name: idx_daily_plans_user_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daily_plans_user_date ON public.daily_plans USING btree (user_id, plan_date DESC);


--
-- Name: idx_data_processing_agreements_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_data_processing_agreements_organization_id ON public.data_processing_agreements USING btree (organization_id);


--
-- Name: idx_diary_entries_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_diary_entries_date ON public.diary_entries USING btree (date);


--
-- Name: idx_diary_entries_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_diary_entries_user ON public.diary_entries USING btree (user_id);


--
-- Name: idx_diary_entries_user_date; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_diary_entries_user_date ON public.diary_entries USING btree (user_id, date);


--
-- Name: idx_diary_exports_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_diary_exports_created ON public.diary_exports USING btree (created_at);


--
-- Name: idx_diary_exports_share_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_diary_exports_share_token ON public.diary_exports USING btree (share_token);


--
-- Name: idx_diary_exports_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_diary_exports_user ON public.diary_exports USING btree (user_id);


--
-- Name: idx_dormitory_info_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dormitory_info_city ON public.dormitory_info USING btree (city);


--
-- Name: idx_dormitory_info_price; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dormitory_info_price ON public.dormitory_info USING btree (price_avg);


--
-- Name: idx_dormitory_info_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dormitory_info_type ON public.dormitory_info USING btree (accommodation_type);


--
-- Name: idx_dormitory_info_university; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dormitory_info_university ON public.dormitory_info USING btree (university_id);


--
-- Name: idx_dungeon_progress_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dungeon_progress_user ON public.dungeon_progress USING btree (user_id);


--
-- Name: idx_eba_analytics_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_analytics_category ON public.eba_content_analytics USING btree (category);


--
-- Name: idx_eba_analytics_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_analytics_date ON public.eba_content_analytics USING btree (analysis_date);


--
-- Name: idx_eba_analytics_grade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_analytics_grade ON public.eba_content_analytics USING btree (grade_level);


--
-- Name: idx_eba_collection_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_collection_category ON public.eba_content_collections USING btree (category);


--
-- Name: idx_eba_collection_featured; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_collection_featured ON public.eba_content_collections USING btree (is_featured);


--
-- Name: idx_eba_collection_grade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_collection_grade ON public.eba_content_collections USING btree (grade_level);


--
-- Name: idx_eba_rec_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_rec_created ON public.eba_video_recommendations USING btree (created_at);


--
-- Name: idx_eba_rec_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_rec_score ON public.eba_video_recommendations USING btree (recommendation_score);


--
-- Name: idx_eba_rec_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_rec_student ON public.eba_video_recommendations USING btree (student_id);


--
-- Name: idx_eba_rec_video; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_rec_video ON public.eba_video_recommendations USING btree (video_id);


--
-- Name: idx_eba_usage_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_usage_started ON public.eba_video_usage USING btree (started_at);


--
-- Name: idx_eba_usage_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_usage_student ON public.eba_video_usage USING btree (student_id);


--
-- Name: idx_eba_usage_video; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_usage_video ON public.eba_video_usage USING btree (video_id);


--
-- Name: idx_eba_video_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_video_category ON public.eba_videos USING btree (category);


--
-- Name: idx_eba_video_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_video_created ON public.eba_videos USING btree (created_at);


--
-- Name: idx_eba_video_difficulty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_video_difficulty ON public.eba_videos USING btree (difficulty_level);


--
-- Name: idx_eba_video_grade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_video_grade ON public.eba_videos USING btree (grade_level);


--
-- Name: idx_eba_video_moderation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_video_moderation ON public.eba_videos USING btree (moderation_status);


--
-- Name: idx_eba_video_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eba_video_quality ON public.eba_videos USING btree (quality_score);


--
-- Name: idx_emotional_states_confidence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emotional_states_confidence ON public.emotional_states USING btree (confidence_level);


--
-- Name: idx_emotional_states_flow; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emotional_states_flow ON public.emotional_states USING btree (flow_state);


--
-- Name: idx_emotional_states_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emotional_states_timestamp ON public.emotional_states USING btree ("timestamp");


--
-- Name: idx_emotional_states_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emotional_states_user ON public.emotional_states USING btree (user_id);


--
-- Name: idx_exam_question_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exam_question_order ON public.exam_questions USING btree (question_order);


--
-- Name: idx_exam_question_question; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exam_question_question ON public.exam_questions USING btree (question_id);


--
-- Name: idx_exam_question_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exam_question_session ON public.exam_questions USING btree (exam_session_id);


--
-- Name: idx_exam_session_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exam_session_created ON public.exam_sessions USING btree (created_at);


--
-- Name: idx_exam_session_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exam_session_status ON public.exam_sessions USING btree (status);


--
-- Name: idx_exam_session_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exam_session_student ON public.exam_sessions USING btree (student_id);


--
-- Name: idx_exam_session_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exam_session_type ON public.exam_sessions USING btree (exam_type);


--
-- Name: idx_fallback_final_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fallback_final_score ON public.fallback_videos USING btree (final_score);


--
-- Name: idx_fallback_is_example; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fallback_is_example ON public.fallback_videos USING btree (is_example);


--
-- Name: idx_fallback_subject_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fallback_subject_topic ON public.fallback_videos USING btree (subject, topic);


--
-- Name: idx_fsrs_card_due; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_card_due ON public.fsrs_cards USING btree (due_date);


--
-- Name: idx_fsrs_card_state; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_card_state ON public.fsrs_cards USING btree (state);


--
-- Name: idx_fsrs_card_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_card_student ON public.fsrs_cards USING btree (student_id);


--
-- Name: idx_fsrs_card_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_card_subject ON public.fsrs_cards USING btree (subject_area);


--
-- Name: idx_fsrs_profile_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_profile_student ON public.fsrs_student_profiles USING btree (student_id);


--
-- Name: idx_fsrs_review_card; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_review_card ON public.fsrs_reviews USING btree (card_id);


--
-- Name: idx_fsrs_review_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_review_date ON public.fsrs_reviews USING btree (review_date);


--
-- Name: idx_fsrs_review_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_review_student ON public.fsrs_reviews USING btree (student_id);


--
-- Name: idx_fsrs_schedule_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_schedule_date ON public.fsrs_schedules USING btree (schedule_date);


--
-- Name: idx_fsrs_schedule_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_schedule_student ON public.fsrs_schedules USING btree (student_id);


--
-- Name: idx_fsrs_session_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_session_date ON public.fsrs_study_sessions USING btree (session_date);


--
-- Name: idx_fsrs_session_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_session_student ON public.fsrs_study_sessions USING btree (student_id);


--
-- Name: idx_fsrs_stats_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_stats_student ON public.fsrs_subject_stats USING btree (student_id);


--
-- Name: idx_fsrs_stats_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fsrs_stats_subject ON public.fsrs_subject_stats USING btree (subject_area);


--
-- Name: idx_goals_at_risk; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_goals_at_risk ON public.goals USING btree (is_at_risk);


--
-- Name: idx_goals_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_goals_status ON public.goals USING btree (status);


--
-- Name: idx_goals_target_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_goals_target_date ON public.goals USING btree (target_date);


--
-- Name: idx_goals_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_goals_user ON public.goals USING btree (user_id);


--
-- Name: idx_grade_academic_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_grade_academic_year ON public.student_grades USING btree (academic_year, semester);


--
-- Name: idx_grade_student_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_grade_student_subject ON public.student_grades USING btree (student_user_id, subject);


--
-- Name: idx_grade_teacher; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_grade_teacher ON public.student_grades USING btree (teacher_user_id);


--
-- Name: idx_history_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_history_year ON public.program_score_history USING btree (program_id, year);


--
-- Name: idx_image_uploads_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_image_uploads_created ON public.image_uploads USING btree (created_at);


--
-- Name: idx_image_uploads_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_image_uploads_session ON public.image_uploads USING btree (session_id);


--
-- Name: idx_image_uploads_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_image_uploads_status ON public.image_uploads USING btree (processing_status);


--
-- Name: idx_image_uploads_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_image_uploads_user ON public.image_uploads USING btree (user_id);


--
-- Name: idx_insights_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_insights_category ON public.insights USING btree (category);


--
-- Name: idx_insights_confidence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_insights_confidence ON public.insights USING btree (confidence);


--
-- Name: idx_insights_diary_entry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_insights_diary_entry ON public.insights USING btree (diary_entry_id);


--
-- Name: idx_insights_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_insights_user ON public.insights USING btree (user_id);


--
-- Name: idx_invoice_org; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_invoice_org ON public.invoices USING btree (organization_id);


--
-- Name: idx_invoice_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_invoice_status ON public.invoices USING btree (status);


--
-- Name: idx_kiro2_cat_sessions_user_state; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_kiro2_cat_sessions_user_state ON public.kiro2_cat_sessions USING btree (user_id, state, completed_at DESC);


--
-- Name: idx_kiro2_cat_sessions_user_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_kiro2_cat_sessions_user_subject ON public.kiro2_cat_sessions USING btree (user_id, subject_id);


--
-- Name: idx_learning_analytics_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_learning_analytics_date ON public.learning_analytics USING btree (date);


--
-- Name: idx_learning_analytics_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_learning_analytics_student ON public.learning_analytics USING btree (student_id);


--
-- Name: idx_learning_analytics_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_learning_analytics_subject ON public.learning_analytics USING btree (subject_area);


--
-- Name: idx_learning_entries_domain; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_learning_entries_domain ON public.learning_entries USING btree (domain);


--
-- Name: idx_learning_entries_next_review; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_learning_entries_next_review ON public.learning_entries USING btree (next_review);


--
-- Name: idx_learning_entries_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_learning_entries_tags ON public.learning_entries USING gin (tags);


--
-- Name: idx_learning_entries_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_learning_entries_user ON public.learning_entries USING btree (user_id);


--
-- Name: idx_learning_events_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_learning_events_session ON public.kiro2_learning_events USING btree (session_id);


--
-- Name: idx_learning_events_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_learning_events_user ON public.kiro2_learning_events USING btree (user_id, occurred_at DESC);


--
-- Name: idx_lp_student_learning_style; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lp_student_learning_style ON public.learning_path_student_profiles USING btree (learning_style);


--
-- Name: idx_manip_activity_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_manip_activity_created ON public.manipulative_activities USING btree (created_at);


--
-- Name: idx_manip_activity_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_manip_activity_user ON public.manipulative_activities USING btree (user_id);


--
-- Name: idx_manip_activity_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_manip_activity_user_created ON public.manipulative_activities USING btree (user_id, created_at);


--
-- Name: idx_manip_progress_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_manip_progress_type ON public.manipulative_progress USING btree (manipulative_type);


--
-- Name: idx_manip_progress_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_manip_progress_user ON public.manipulative_progress USING btree (user_id);


--
-- Name: idx_manip_progress_user_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_manip_progress_user_type ON public.manipulative_progress USING btree (user_id, manipulative_type);


--
-- Name: idx_meb_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meb_active ON public.meb_curriculum_standards USING btree (is_active);


--
-- Name: idx_meb_grade_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meb_grade_level ON public.meb_curriculum_standards USING btree (grade_level);


--
-- Name: idx_meb_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meb_subject ON public.meb_curriculum_standards USING btree (subject);


--
-- Name: idx_meb_subject_grade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meb_subject_grade ON public.meb_curriculum_standards USING btree (subject, grade_level);


--
-- Name: idx_moderation_queue_assigned; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_moderation_queue_assigned ON public.moderation_queue USING btree (assigned_to);


--
-- Name: idx_moderation_queue_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_moderation_queue_priority ON public.moderation_queue USING btree (priority);


--
-- Name: idx_moderation_queue_review; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_moderation_queue_review ON public.moderation_queue USING btree (review_id);


--
-- Name: idx_moderation_queue_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_moderation_queue_status ON public.moderation_queue USING btree (status);


--
-- Name: idx_org_license_org; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_license_org ON public.organization_licenses USING btree (organization_id);


--
-- Name: idx_org_license_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_license_status ON public.organization_licenses USING btree (status);


--
-- Name: idx_org_membership_org; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_membership_org ON public.org_memberships USING btree (organization_id);


--
-- Name: idx_org_membership_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_membership_role ON public.org_memberships USING btree (organization_id, org_role);


--
-- Name: idx_org_membership_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_membership_user ON public.org_memberships USING btree (user_id);


--
-- Name: idx_org_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_status ON public.organizations USING btree (status);


--
-- Name: idx_org_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_type ON public.organizations USING btree (org_type);


--
-- Name: idx_osym_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_osym_active ON public.osym_standards USING btree (is_active);


--
-- Name: idx_osym_bloom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_osym_bloom ON public.osym_questions USING btree (bloom_level, bloom_category);


--
-- Name: idx_osym_exam_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_osym_exam_type ON public.osym_standards USING btree (exam_type);


--
-- Name: idx_osym_irt_difficulty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_osym_irt_difficulty ON public.osym_questions USING btree (irt_difficulty);


--
-- Name: idx_osym_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_osym_priority ON public.osym_standards USING btree (priority_level);


--
-- Name: idx_osym_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_osym_quality ON public.osym_questions USING btree (quality_score);


--
-- Name: idx_osym_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_osym_status ON public.osym_questions USING btree (status);


--
-- Name: idx_osym_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_osym_subject ON public.osym_standards USING btree (subject);


--
-- Name: idx_osym_subject_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_osym_subject_topic ON public.osym_questions USING btree (subject, topic);


--
-- Name: idx_osym_year_exam; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_osym_year_exam ON public.osym_questions USING btree (year, exam_type);


--
-- Name: idx_outcome_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_outcome_code ON public.learning_outcomes USING btree (code);


--
-- Name: idx_outcome_meb_standard; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_outcome_meb_standard ON public.learning_outcomes USING btree (meb_standard_id);


--
-- Name: idx_outcome_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_outcome_subject ON public.learning_outcomes USING btree (subject);


--
-- Name: idx_parent_report_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parent_report_parent ON public.parent_reports USING btree (parent_user_id, created_at);


--
-- Name: idx_parent_report_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parent_report_period ON public.parent_reports USING btree (report_period);


--
-- Name: idx_parent_report_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parent_report_student ON public.parent_reports USING btree (student_user_id);


--
-- Name: idx_path_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_path_created_at ON public.learning_paths USING btree (created_at);


--
-- Name: idx_path_student_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_path_student_subject ON public.learning_paths USING btree (student_id, subject);


--
-- Name: idx_peer_comparisons_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_peer_comparisons_period ON public.peer_comparisons USING btree (period_start, period_end);


--
-- Name: idx_peer_comparisons_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_peer_comparisons_user ON public.peer_comparisons USING btree (user_id);


--
-- Name: idx_program_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_program_search ON public.university_programs USING btree (university_id, department_id, year, score_type);


--
-- Name: idx_progress_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_progress_organization_id ON public.learning_progress_daily USING btree (organization_id);


--
-- Name: idx_progress_student_node; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_progress_student_node ON public.topic_progress USING btree (student_id, node_id);


--
-- Name: idx_progress_user_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_progress_user_date ON public.learning_progress_daily USING btree (user_id, log_date DESC);


--
-- Name: idx_qb_primary_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qb_primary_topic ON public.question_bank USING btree (primary_topic_id) WHERE (primary_topic_id IS NOT NULL);


--
-- Name: idx_qb_soru_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qb_soru_hash ON public.question_bank USING btree (soru_hash);


--
-- Name: idx_qg_override_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_override_created ON public.quality_gates_override_audit USING btree (created_at);


--
-- Name: idx_qg_override_gate; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_override_gate ON public.quality_gates_override_audit USING btree (gate_name);


--
-- Name: idx_qg_override_requestor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_override_requestor ON public.quality_gates_override_audit USING btree (requestor);


--
-- Name: idx_qg_override_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_override_status ON public.quality_gates_override_audit USING btree (status);


--
-- Name: idx_qg_result_gate; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_result_gate ON public.quality_gate_results USING btree (gate_name);


--
-- Name: idx_qg_result_run; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_result_run ON public.quality_gate_results USING btree (run_id);


--
-- Name: idx_qg_result_run_gate; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_result_run_gate ON public.quality_gate_results USING btree (run_id, gate_name);


--
-- Name: idx_qg_result_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_result_status ON public.quality_gate_results USING btree (status);


--
-- Name: idx_qg_run_branch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_run_branch ON public.quality_gates_runs USING btree (branch);


--
-- Name: idx_qg_run_commit; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_run_commit ON public.quality_gates_runs USING btree (commit_hash);


--
-- Name: idx_qg_run_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_run_started ON public.quality_gates_runs USING btree (started_at);


--
-- Name: idx_qg_run_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_run_status ON public.quality_gates_runs USING btree (status);


--
-- Name: idx_qg_run_triggered_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qg_run_triggered_by ON public.quality_gates_runs USING btree (triggered_by);


--
-- Name: idx_qmatrix_pair; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_qmatrix_pair ON public.q_matrix USING btree (question_id, nano_skill_id);


--
-- Name: idx_qperf_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qperf_date ON public.question_performance_analytics USING btree (analysis_date);


--
-- Name: idx_qperf_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qperf_period ON public.question_performance_analytics USING btree (period_type);


--
-- Name: idx_qperf_question; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qperf_question ON public.question_performance_analytics USING btree (question_id);


--
-- Name: idx_qtag_question; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qtag_question ON public.question_tag_associations USING btree (question_id);


--
-- Name: idx_qtag_tag; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qtag_tag ON public.question_tag_associations USING btree (tag_id);


--
-- Name: idx_question_responses; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_question_responses ON public.student_question_responses USING btree (question_id, is_correct);


--
-- Name: idx_quiz_question_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_quiz_question_order ON public.quiz_questions USING btree (quiz_id, order_number);


--
-- Name: idx_quiz_student_quiz; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_quiz_student_quiz ON public.quiz_submissions USING btree (student_id, quiz_id);


--
-- Name: idx_quiz_subject_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_quiz_subject_topic ON public.quizzes USING btree (subject, topic);


--
-- Name: idx_quiz_submitted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_quiz_submitted_at ON public.quiz_submissions USING btree (submitted_at);


--
-- Name: idx_reasoning_cache_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reasoning_cache_expires ON public.reasoning_cache USING btree (expires_at);


--
-- Name: idx_reasoning_cache_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reasoning_cache_hash ON public.reasoning_cache USING btree (problem_hash);


--
-- Name: idx_reasoning_sessions_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reasoning_sessions_created ON public.reasoning_sessions USING btree (created_at);


--
-- Name: idx_reasoning_sessions_provider; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reasoning_sessions_provider ON public.reasoning_sessions USING btree (provider);


--
-- Name: idx_reasoning_sessions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reasoning_sessions_status ON public.reasoning_sessions USING btree (status);


--
-- Name: idx_reasoning_sessions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reasoning_sessions_user ON public.reasoning_sessions USING btree (user_id);


--
-- Name: idx_reasoning_steps_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reasoning_steps_number ON public.reasoning_steps USING btree (session_id, step_number);


--
-- Name: idx_reasoning_steps_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reasoning_steps_session ON public.reasoning_steps USING btree (session_id);


--
-- Name: idx_reasoning_steps_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reasoning_steps_type ON public.reasoning_steps USING btree (step_type);


--
-- Name: idx_reflections_depth; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reflections_depth ON public.reflections USING btree (depth);


--
-- Name: idx_reflections_diary_entry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reflections_diary_entry ON public.reflections USING btree (diary_entry_id);


--
-- Name: idx_reflections_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reflections_user ON public.reflections USING btree (user_id);


--
-- Name: idx_refresh_token_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refresh_token_expires ON public.refresh_tokens USING btree (expires_at);


--
-- Name: idx_refresh_token_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refresh_token_hash ON public.refresh_tokens USING btree (token_hash);


--
-- Name: idx_refresh_token_jti; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refresh_token_jti ON public.refresh_tokens USING btree (jti);


--
-- Name: idx_refresh_token_revoked; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refresh_token_revoked ON public.refresh_tokens USING btree (revoked);


--
-- Name: idx_refresh_token_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refresh_token_user ON public.refresh_tokens USING btree (user_id);


--
-- Name: idx_refresh_token_user_device; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refresh_token_user_device ON public.refresh_tokens USING btree (user_id, device_id);


--
-- Name: idx_review_ratings_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_ratings_category ON public.review_ratings USING btree (category);


--
-- Name: idx_review_ratings_rating; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_ratings_rating ON public.review_ratings USING btree (rating);


--
-- Name: idx_review_ratings_review; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_ratings_review ON public.review_ratings USING btree (review_id);


--
-- Name: idx_review_ratings_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_review_ratings_unique ON public.review_ratings USING btree (review_id, category);


--
-- Name: idx_review_reports_reason; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_reports_reason ON public.review_reports USING btree (reason);


--
-- Name: idx_review_reports_reporter; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_reports_reporter ON public.review_reports USING btree (reporter_id);


--
-- Name: idx_review_reports_review; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_reports_review ON public.review_reports USING btree (review_id);


--
-- Name: idx_review_reports_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_reports_status ON public.review_reports USING btree (status);


--
-- Name: idx_review_statistics_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_statistics_department ON public.review_statistics USING btree (department_id);


--
-- Name: idx_review_statistics_rating; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_statistics_rating ON public.review_statistics USING btree (average_rating);


--
-- Name: idx_review_statistics_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_statistics_type ON public.review_statistics USING btree (review_type);


--
-- Name: idx_review_statistics_university; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_statistics_university ON public.review_statistics USING btree (university_id);


--
-- Name: idx_review_votes_review; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_votes_review ON public.review_votes USING btree (review_id);


--
-- Name: idx_review_votes_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_review_votes_unique ON public.review_votes USING btree (review_id, user_id);


--
-- Name: idx_review_votes_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_review_votes_user ON public.review_votes USING btree (user_id);


--
-- Name: idx_salary_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_salary_city ON public.salary_expectations USING btree (city, experience_level);


--
-- Name: idx_salary_dept_exp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_salary_dept_exp ON public.salary_expectations USING btree (department_id, experience_level, year);


--
-- Name: idx_scholarship_program_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholarship_program_active ON public.scholarship_programs USING btree (active);


--
-- Name: idx_scholarship_program_coverage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholarship_program_coverage ON public.scholarship_programs USING btree (coverage_percentage);


--
-- Name: idx_scholarship_program_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholarship_program_type ON public.scholarship_programs USING btree (scholarship_type);


--
-- Name: idx_scholarship_program_university; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholarship_program_university ON public.scholarship_programs USING btree (university_id);


--
-- Name: idx_session_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_session_active ON public.sessions USING btree (is_active, expires_at);


--
-- Name: idx_session_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_session_expires_at ON public.sessions USING btree (expires_at);


--
-- Name: idx_session_student_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_session_student_started ON public.study_sessions USING btree (student_id, started_at);


--
-- Name: idx_session_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_session_user_id ON public.sessions USING btree (user_id);


--
-- Name: idx_solution_steps_message; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_solution_steps_message ON public.solution_steps USING btree (message_id);


--
-- Name: idx_solution_steps_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_solution_steps_number ON public.solution_steps USING btree (step_number);


--
-- Name: idx_student_answer_answered_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_answer_answered_at ON public.student_answers USING btree (answered_at);


--
-- Name: idx_student_answer_incorrect; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_answer_incorrect ON public.student_answers USING btree (is_correct) WHERE (is_correct = false);


--
-- Name: idx_student_answer_question; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_answer_question ON public.student_answers USING btree (question_id);


--
-- Name: idx_student_answer_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_answer_session ON public.student_answers USING btree (exam_session_id);


--
-- Name: idx_student_exam_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_exam_target ON public.learning_path_student_profiles USING btree (exam_target);


--
-- Name: idx_student_grade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_grade ON public.learning_path_student_profiles USING btree (grade);


--
-- Name: idx_student_grade_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_grade_level ON public.student_profiles USING btree (grade_level);


--
-- Name: idx_student_grade_style; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_grade_style ON public.student_profiles USING btree (grade_level, learning_style);


--
-- Name: idx_student_last_activity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_last_activity ON public.learning_path_student_profiles USING btree (last_activity_at);


--
-- Name: idx_student_learning_style; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_learning_style ON public.student_profiles USING btree (learning_style);


--
-- Name: idx_student_question; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_question ON public.student_question_responses USING btree (student_id, question_id);


--
-- Name: idx_student_reviews_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_reviews_created ON public.student_reviews USING btree (created_at);


--
-- Name: idx_student_reviews_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_reviews_department ON public.student_reviews USING btree (department_id);


--
-- Name: idx_student_reviews_rating; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_reviews_rating ON public.student_reviews USING btree (overall_rating);


--
-- Name: idx_student_reviews_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_reviews_status ON public.student_reviews USING btree (status);


--
-- Name: idx_student_reviews_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_reviews_type ON public.student_reviews USING btree (review_type);


--
-- Name: idx_student_reviews_university; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_reviews_university ON public.student_reviews USING btree (university_id);


--
-- Name: idx_student_reviews_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_reviews_user ON public.student_reviews USING btree (user_id);


--
-- Name: idx_student_reviews_verified; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_reviews_verified ON public.student_reviews USING btree (is_verified);


--
-- Name: idx_student_user_grade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_user_grade ON public.student_profiles USING btree (user_id, grade_level);


--
-- Name: idx_student_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_user_id ON public.learning_path_student_profiles USING btree (user_id);


--
-- Name: idx_sub_problems_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sub_problems_order ON public.sub_problems USING btree (session_id, order_index);


--
-- Name: idx_sub_problems_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sub_problems_session ON public.sub_problems USING btree (session_id);


--
-- Name: idx_sub_problems_solved; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sub_problems_solved ON public.sub_problems USING btree (is_solved);


--
-- Name: idx_tag_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tag_category ON public.question_tags USING btree (tag_category);


--
-- Name: idx_tag_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tag_name ON public.question_tags USING btree (tag_name);


--
-- Name: idx_topic_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_topic_code ON public.topic_hierarchy USING btree (code);


--
-- Name: idx_topic_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_topic_level ON public.topic_hierarchy USING btree (level);


--
-- Name: idx_topic_meb_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_topic_meb_code ON public.topic_hierarchy USING btree (meb_code);


--
-- Name: idx_topic_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_topic_parent ON public.topic_hierarchy USING btree (parent_id);


--
-- Name: idx_topic_prereqs_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_topic_prereqs_active ON public.topic_prerequisites USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_topic_prereqs_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_topic_prereqs_topic ON public.topic_prerequisites USING btree (topic_id);


--
-- Name: idx_transcript_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transcript_active ON public.video_transcripts USING btree (is_active);


--
-- Name: idx_transcript_language; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transcript_language ON public.video_transcripts USING btree (language);


--
-- Name: idx_transcript_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transcript_status ON public.video_transcripts USING btree (transcript_status);


--
-- Name: idx_transcript_video; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transcript_video ON public.video_transcripts USING btree (video_id);


--
-- Name: idx_university_statistics_university; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_university_statistics_university ON public.university_statistics USING btree (university_id);


--
-- Name: idx_university_statistics_university_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_university_statistics_university_year ON public.university_statistics USING btree (university_id, year);


--
-- Name: idx_university_statistics_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_university_statistics_year ON public.university_statistics USING btree (year);


--
-- Name: idx_update_req_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_update_req_status ON public.curriculum_update_requests USING btree (status);


--
-- Name: idx_update_req_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_update_req_subject ON public.curriculum_update_requests USING btree (subject);


--
-- Name: idx_update_req_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_update_req_type ON public.curriculum_update_requests USING btree (update_type);


--
-- Name: idx_user_created_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_created_active ON public.users USING btree (created_at, is_active);


--
-- Name: idx_user_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_created_at ON public.users USING btree (created_at);


--
-- Name: idx_user_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_email ON public.users USING btree (email);


--
-- Name: idx_user_email_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_email_role ON public.users USING btree (email, role);


--
-- Name: idx_user_period; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_user_period ON public.video_analytics_summary USING btree (user_id, period_type, period_start);


--
-- Name: idx_user_premium_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_premium_expires ON public.users USING btree (is_premium, premium_expires_at);


--
-- Name: idx_user_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_role ON public.users USING btree (role);


--
-- Name: idx_user_role_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_role_active ON public.users USING btree (role, is_active);


--
-- Name: idx_user_theta_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_theta_user ON public.user_theta USING btree (user_id);


--
-- Name: idx_user_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_username ON public.users USING btree (username);


--
-- Name: idx_user_video_milestone; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_user_video_milestone ON public.video_completion_milestones USING btree (user_id, video_id, milestone_percentage);


--
-- Name: idx_video_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_video_active ON public.video_solutions USING btree (is_active);


--
-- Name: idx_video_approved; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_video_approved ON public.video_solutions USING btree (is_approved);


--
-- Name: idx_video_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_video_created ON public.video_solutions USING btree (created_at);


--
-- Name: idx_video_question; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_video_question ON public.video_solutions USING btree (question_id);


--
-- Name: idx_video_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_video_status ON public.video_solutions USING btree (processing_status);


--
-- Name: idx_video_uploader; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_video_uploader ON public.video_solutions USING btree (uploaded_by);


--
-- Name: idx_weekly_progress_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_weekly_progress_user ON public.weekly_progress USING btree (user_id);


--
-- Name: idx_weekly_progress_year_week; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_weekly_progress_year_week ON public.weekly_progress USING btree (year, week_number);


--
-- Name: idx_yks_exam_goals_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_yks_exam_goals_organization_id ON public.yks_exam_goals USING btree (organization_id);


--
-- Name: ix_api_keys_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_keys_expires_at ON public.api_keys USING btree (expires_at);


--
-- Name: ix_api_keys_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_keys_is_active ON public.api_keys USING btree (is_active);


--
-- Name: ix_api_keys_key_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_api_keys_key_hash ON public.api_keys USING btree (key_hash);


--
-- Name: ix_api_keys_key_prefix; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_keys_key_prefix ON public.api_keys USING btree (key_prefix);


--
-- Name: ix_api_keys_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_keys_organization_id ON public.api_keys USING btree (organization_id);


--
-- Name: ix_api_keys_revoked; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_keys_revoked ON public.api_keys USING btree (revoked);


--
-- Name: ix_api_keys_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_keys_user_id ON public.api_keys USING btree (user_id);


--
-- Name: ix_audit_logs_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_organization_id ON public.audit_logs USING btree (organization_id);


--
-- Name: ix_billing_data_processing_agreements_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_billing_data_processing_agreements_organization_id ON public.billing_data_processing_agreements USING btree (organization_id);


--
-- Name: ix_bkt_states_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bkt_states_organization_id ON public.bkt_states USING btree (organization_id);


--
-- Name: ix_blocked_users_blocked_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_blocked_users_blocked_id ON public.blocked_users USING btree (blocked_id);


--
-- Name: ix_blocked_users_blocker_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_blocked_users_blocker_id ON public.blocked_users USING btree (blocker_id);


--
-- Name: ix_career_opportunities_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_career_opportunities_department_id ON public.career_opportunities USING btree (department_id);


--
-- Name: ix_career_opportunities_industry_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_career_opportunities_industry_type ON public.career_opportunities USING btree (industry_type);


--
-- Name: ix_chat_analytics_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chat_analytics_organization_id ON public.chat_analytics USING btree (organization_id);


--
-- Name: ix_chat_sessions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chat_sessions_organization_id ON public.chat_sessions USING btree (organization_id);


--
-- Name: ix_classrooms_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_classrooms_is_active ON public.classrooms USING btree (is_active);


--
-- Name: ix_classrooms_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_classrooms_organization_id ON public.classrooms USING btree (organization_id);


--
-- Name: ix_coaching_events_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_coaching_events_organization_id ON public.coaching_events USING btree (organization_id);


--
-- Name: ix_coaching_events_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_coaching_events_student_id ON public.coaching_events USING btree (student_id);


--
-- Name: ix_content_reports_reported_content_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_content_reports_reported_content_id ON public.content_reports USING btree (reported_content_id);


--
-- Name: ix_content_reports_reporter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_content_reports_reporter_id ON public.content_reports USING btree (reporter_id);


--
-- Name: ix_content_reports_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_content_reports_status ON public.content_reports USING btree (status);


--
-- Name: ix_daily_quests_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_daily_quests_organization_id ON public.daily_quests USING btree (organization_id);


--
-- Name: ix_department_curricula_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_department_curricula_department_id ON public.department_curricula USING btree (department_id);


--
-- Name: ix_department_statistics_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_department_statistics_department_id ON public.department_statistics USING btree (department_id);


--
-- Name: ix_department_statistics_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_department_statistics_year ON public.department_statistics USING btree (year);


--
-- Name: ix_departments_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_departments_is_active ON public.departments USING btree (is_active);


--
-- Name: ix_departments_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_departments_name ON public.departments USING btree (name);


--
-- Name: ix_diary_entries_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_diary_entries_date ON public.diary_entries USING btree (date);


--
-- Name: ix_diary_exports_share_token; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_diary_exports_share_token ON public.diary_exports USING btree (share_token);


--
-- Name: ix_duel_ratings_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_duel_ratings_organization_id ON public.duel_ratings USING btree (organization_id);


--
-- Name: ix_dungeon_progress_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dungeon_progress_organization_id ON public.dungeon_progress USING btree (organization_id);


--
-- Name: ix_eba_content_collections_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_eba_content_collections_is_active ON public.eba_content_collections USING btree (is_active);


--
-- Name: ix_eba_subject_taxonomy_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_eba_subject_taxonomy_subject ON public.eba_subject_taxonomy USING btree (subject);


--
-- Name: ix_eba_video_recommendations_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_eba_video_recommendations_organization_id ON public.eba_video_recommendations USING btree (organization_id);


--
-- Name: ix_eba_video_usage_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_eba_video_usage_organization_id ON public.eba_video_usage USING btree (organization_id);


--
-- Name: ix_eba_video_watches_eba_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_eba_video_watches_eba_video_id ON public.eba_video_watches USING btree (eba_video_id);


--
-- Name: ix_eba_video_watches_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_eba_video_watches_organization_id ON public.eba_video_watches USING btree (organization_id);


--
-- Name: ix_eba_video_watches_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_eba_video_watches_user_id ON public.eba_video_watches USING btree (user_id);


--
-- Name: ix_eba_videos_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_eba_videos_is_active ON public.eba_videos USING btree (is_active);


--
-- Name: ix_educational_contents_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_educational_contents_is_active ON public.educational_contents USING btree (is_active);


--
-- Name: ix_error_clusters_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_error_clusters_subject ON public.error_clusters USING btree (subject);


--
-- Name: ix_exam_sessions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_exam_sessions_organization_id ON public.exam_sessions USING btree (organization_id);


--
-- Name: ix_fallback_videos_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fallback_videos_subject ON public.fallback_videos USING btree (subject);


--
-- Name: ix_fallback_videos_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fallback_videos_topic ON public.fallback_videos USING btree (topic);


--
-- Name: ix_forum_questions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forum_questions_organization_id ON public.forum_questions USING btree (organization_id);


--
-- Name: ix_forum_questions_question_bank_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forum_questions_question_bank_id ON public.forum_questions USING btree (question_bank_id);


--
-- Name: ix_forum_questions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forum_questions_status ON public.forum_questions USING btree (status);


--
-- Name: ix_forum_questions_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forum_questions_student_id ON public.forum_questions USING btree (student_id);


--
-- Name: ix_forum_questions_subject_area; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forum_questions_subject_area ON public.forum_questions USING btree (subject_area);


--
-- Name: ix_forum_solutions_question_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forum_solutions_question_id ON public.forum_solutions USING btree (question_id);


--
-- Name: ix_forum_solutions_solver_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forum_solutions_solver_id ON public.forum_solutions USING btree (solver_id);


--
-- Name: ix_forum_votes_solution_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forum_votes_solution_id ON public.forum_votes USING btree (solution_id);


--
-- Name: ix_forum_votes_voter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forum_votes_voter_id ON public.forum_votes USING btree (voter_id);


--
-- Name: ix_fsrs_cards_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fsrs_cards_organization_id ON public.fsrs_cards USING btree (organization_id);


--
-- Name: ix_fsrs_reviews_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fsrs_reviews_organization_id ON public.fsrs_reviews USING btree (organization_id);


--
-- Name: ix_fsrs_schedules_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fsrs_schedules_organization_id ON public.fsrs_schedules USING btree (organization_id);


--
-- Name: ix_fsrs_student_profiles_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fsrs_student_profiles_organization_id ON public.fsrs_student_profiles USING btree (organization_id);


--
-- Name: ix_fsrs_study_sessions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fsrs_study_sessions_organization_id ON public.fsrs_study_sessions USING btree (organization_id);


--
-- Name: ix_fsrs_subject_stats_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fsrs_subject_stats_organization_id ON public.fsrs_subject_stats USING btree (organization_id);


--
-- Name: ix_image_uploads_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_image_uploads_organization_id ON public.image_uploads USING btree (organization_id);


--
-- Name: ix_invoices_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_invoices_organization_id ON public.invoices USING btree (organization_id);


--
-- Name: ix_khan_certificates_badge_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_khan_certificates_badge_category ON public.khan_certificates USING btree (badge_category);


--
-- Name: ix_khan_certificates_khan_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_khan_certificates_khan_user_id ON public.khan_certificates USING btree (khan_user_id);


--
-- Name: ix_khan_certificates_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_khan_certificates_user_id ON public.khan_certificates USING btree (user_id);


--
-- Name: ix_khan_contents_content_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_khan_contents_content_type ON public.khan_contents USING btree (content_type);


--
-- Name: ix_khan_contents_khan_content_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_khan_contents_khan_content_id ON public.khan_contents USING btree (khan_content_id);


--
-- Name: ix_khan_contents_language; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_khan_contents_language ON public.khan_contents USING btree (language);


--
-- Name: ix_khan_contents_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_khan_contents_subject ON public.khan_contents USING btree (subject);


--
-- Name: ix_khan_oauth_tokens_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_khan_oauth_tokens_organization_id ON public.khan_oauth_tokens USING btree (organization_id);


--
-- Name: ix_khan_oauth_tokens_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_khan_oauth_tokens_user_id ON public.khan_oauth_tokens USING btree (user_id);


--
-- Name: ix_khan_user_progress_khan_content_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_khan_user_progress_khan_content_id ON public.khan_user_progress USING btree (khan_content_id);


--
-- Name: ix_khan_user_progress_khan_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_khan_user_progress_khan_user_id ON public.khan_user_progress USING btree (khan_user_id);


--
-- Name: ix_khan_user_progress_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_khan_user_progress_user_id ON public.khan_user_progress USING btree (user_id);


--
-- Name: ix_kiro2_cat_sessions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kiro2_cat_sessions_organization_id ON public.kiro2_cat_sessions USING btree (organization_id);


--
-- Name: ix_kiro2_learning_events_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kiro2_learning_events_organization_id ON public.kiro2_learning_events USING btree (organization_id);


--
-- Name: ix_knowledge_points_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_knowledge_points_code ON public.knowledge_points USING btree (code);


--
-- Name: ix_knowledge_points_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_knowledge_points_is_active ON public.knowledge_points USING btree (is_active);


--
-- Name: ix_knowledge_points_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_knowledge_points_subject ON public.knowledge_points USING btree (subject);


--
-- Name: ix_knowledge_points_topic_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_knowledge_points_topic_id ON public.knowledge_points USING btree (topic_id);


--
-- Name: ix_kvkk_audit_logs_accessed_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kvkk_audit_logs_accessed_by ON public.kvkk_audit_logs USING btree (accessed_by);


--
-- Name: ix_kvkk_audit_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kvkk_audit_logs_created_at ON public.kvkk_audit_logs USING btree (created_at);


--
-- Name: ix_kvkk_audit_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kvkk_audit_logs_user_id ON public.kvkk_audit_logs USING btree (user_id);


--
-- Name: ix_kvkk_consents_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kvkk_consents_organization_id ON public.kvkk_consents USING btree (organization_id);


--
-- Name: ix_kvkk_consents_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kvkk_consents_user_id ON public.kvkk_consents USING btree (user_id);


--
-- Name: ix_kvkk_data_deletion_requests_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kvkk_data_deletion_requests_user_id ON public.kvkk_data_deletion_requests USING btree (user_id);


--
-- Name: ix_kvkk_data_export_requests_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kvkk_data_export_requests_organization_id ON public.kvkk_data_export_requests USING btree (organization_id);


--
-- Name: ix_kvkk_data_export_requests_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kvkk_data_export_requests_user_id ON public.kvkk_data_export_requests USING btree (user_id);


--
-- Name: ix_kvkk_privacy_policy_versions_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kvkk_privacy_policy_versions_is_active ON public.kvkk_privacy_policy_versions USING btree (is_active);


--
-- Name: ix_league_history_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_league_history_organization_id ON public.league_history USING btree (organization_id);


--
-- Name: ix_league_history_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_league_history_student_id ON public.league_history USING btree (student_id);


--
-- Name: ix_league_memberships_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_league_memberships_organization_id ON public.league_memberships USING btree (organization_id);


--
-- Name: ix_league_memberships_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_league_memberships_student_id ON public.league_memberships USING btree (student_id);


--
-- Name: ix_learning_analytics_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_learning_analytics_organization_id ON public.learning_analytics USING btree (organization_id);


--
-- Name: ix_learning_path_student_profiles_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_learning_path_student_profiles_organization_id ON public.learning_path_student_profiles USING btree (organization_id);


--
-- Name: ix_learning_path_student_profiles_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_learning_path_student_profiles_student_id ON public.learning_path_student_profiles USING btree (student_id);


--
-- Name: ix_learning_path_student_profiles_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_learning_path_student_profiles_user_id ON public.learning_path_student_profiles USING btree (user_id);


--
-- Name: ix_learning_paths_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_learning_paths_organization_id ON public.learning_paths USING btree (organization_id);


--
-- Name: ix_learning_paths_path_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_learning_paths_path_id ON public.learning_paths USING btree (path_id);


--
-- Name: ix_learning_paths_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_learning_paths_student_id ON public.learning_paths USING btree (student_id);


--
-- Name: ix_learning_paths_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_learning_paths_subject ON public.learning_paths USING btree (subject);


--
-- Name: ix_manipulative_activities_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_manipulative_activities_created_at ON public.manipulative_activities USING btree (created_at);


--
-- Name: ix_manipulative_activities_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_manipulative_activities_id ON public.manipulative_activities USING btree (id);


--
-- Name: ix_manipulative_activities_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_manipulative_activities_organization_id ON public.manipulative_activities USING btree (organization_id);


--
-- Name: ix_manipulative_activities_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_manipulative_activities_user_id ON public.manipulative_activities USING btree (user_id);


--
-- Name: ix_manipulative_progress_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_manipulative_progress_id ON public.manipulative_progress USING btree (id);


--
-- Name: ix_manipulative_progress_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_manipulative_progress_organization_id ON public.manipulative_progress USING btree (organization_id);


--
-- Name: ix_manipulative_progress_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_manipulative_progress_user_id ON public.manipulative_progress USING btree (user_id);


--
-- Name: ix_meb_curriculum_nodes_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_meb_curriculum_nodes_code ON public.meb_curriculum_nodes USING btree (code);


--
-- Name: ix_meb_curriculum_standards_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_meb_curriculum_standards_is_active ON public.meb_curriculum_standards USING btree (is_active);


--
-- Name: ix_mentor_feedback_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mentor_feedback_session_id ON public.mentor_feedback USING btree (session_id);


--
-- Name: ix_mentor_pairs_mentee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mentor_pairs_mentee_id ON public.mentor_pairs USING btree (mentee_id);


--
-- Name: ix_mentor_pairs_mentor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mentor_pairs_mentor_id ON public.mentor_pairs USING btree (mentor_id);


--
-- Name: ix_mentor_pairs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mentor_pairs_status ON public.mentor_pairs USING btree (status);


--
-- Name: ix_mentor_pairs_subject_area; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mentor_pairs_subject_area ON public.mentor_pairs USING btree (subject_area);


--
-- Name: ix_mentor_sessions_pair_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mentor_sessions_pair_id ON public.mentor_sessions USING btree (pair_id);


--
-- Name: ix_message_audit_log_flagged; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_message_audit_log_flagged ON public.message_audit_log USING btree (flagged);


--
-- Name: ix_message_audit_log_sender_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_message_audit_log_sender_id ON public.message_audit_log USING btree (sender_id);


--
-- Name: ix_misconception_matrix_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_misconception_matrix_code ON public.misconception_matrix USING btree (code);


--
-- Name: ix_moderation_actions_action_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_moderation_actions_action_type ON public.moderation_actions USING btree (action_type);


--
-- Name: ix_moderation_actions_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_moderation_actions_expires_at ON public.moderation_actions USING btree (expires_at);


--
-- Name: ix_moderation_actions_target_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_moderation_actions_target_user_id ON public.moderation_actions USING btree (target_user_id);


--
-- Name: ix_nano_skills_knowledge_point_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_nano_skills_knowledge_point_id ON public.nano_skills USING btree (knowledge_point_id);


--
-- Name: ix_notifications_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_created_at ON public.notifications USING btree (created_at);


--
-- Name: ix_notifications_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_id ON public.notifications USING btree (id);


--
-- Name: ix_notifications_is_read; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_is_read ON public.notifications USING btree (is_read);


--
-- Name: ix_notifications_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_organization_id ON public.notifications USING btree (organization_id);


--
-- Name: ix_notifications_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: ix_oba_challenge_progress_challenge_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_oba_challenge_progress_challenge_id ON public.oba_challenge_progress USING btree (challenge_id);


--
-- Name: ix_oba_challenge_progress_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_oba_challenge_progress_organization_id ON public.oba_challenge_progress USING btree (organization_id);


--
-- Name: ix_oba_challenge_progress_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_oba_challenge_progress_student_id ON public.oba_challenge_progress USING btree (student_id);


--
-- Name: ix_oba_challenges_oba_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_oba_challenges_oba_id ON public.oba_challenges USING btree (oba_id);


--
-- Name: ix_oba_challenges_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_oba_challenges_status ON public.oba_challenges USING btree (status);


--
-- Name: ix_oba_uyeler_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_oba_uyeler_organization_id ON public.oba_uyeler USING btree (organization_id);


--
-- Name: ix_offline_sync_packages_consumed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_offline_sync_packages_consumed_at ON public.offline_sync_packages USING btree (consumed_at);


--
-- Name: ix_offline_sync_packages_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_offline_sync_packages_student_id ON public.offline_sync_packages USING btree (student_id);


--
-- Name: ix_org_memberships_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_org_memberships_is_active ON public.org_memberships USING btree (is_active);


--
-- Name: ix_organization_licenses_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_organization_licenses_organization_id ON public.organization_licenses USING btree (organization_id);


--
-- Name: ix_osb_settings_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_osb_settings_organization_id ON public.osb_settings USING btree (organization_id);


--
-- Name: ix_osym_linguistic_trends_exam_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_osym_linguistic_trends_exam_type ON public.osym_linguistic_trends USING btree (exam_type);


--
-- Name: ix_osym_linguistic_trends_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_osym_linguistic_trends_id ON public.osym_linguistic_trends USING btree (id);


--
-- Name: ix_osym_linguistic_trends_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_osym_linguistic_trends_subject ON public.osym_linguistic_trends USING btree (subject);


--
-- Name: ix_osym_linguistic_trends_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_osym_linguistic_trends_year ON public.osym_linguistic_trends USING btree (year);


--
-- Name: ix_osym_questions_exam_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_osym_questions_exam_type ON public.osym_questions USING btree (exam_type);


--
-- Name: ix_osym_questions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_osym_questions_id ON public.osym_questions USING btree (id);


--
-- Name: ix_osym_questions_question_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_osym_questions_question_id ON public.osym_questions USING btree (question_id);


--
-- Name: ix_osym_questions_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_osym_questions_subject ON public.osym_questions USING btree (subject);


--
-- Name: ix_osym_questions_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_osym_questions_year ON public.osym_questions USING btree (year);


--
-- Name: ix_osym_standards_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_osym_standards_is_active ON public.osym_standards USING btree (is_active);


--
-- Name: ix_parent_child_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_parent_child_organization_id ON public.parent_child USING btree (organization_id);


--
-- Name: ix_parent_link_codes_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_parent_link_codes_code ON public.parent_link_codes USING btree (code);


--
-- Name: ix_parent_link_codes_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_parent_link_codes_organization_id ON public.parent_link_codes USING btree (organization_id);


--
-- Name: ix_parent_link_codes_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_parent_link_codes_student_id ON public.parent_link_codes USING btree (student_id);


--
-- Name: ix_parent_notifications_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_parent_notifications_id ON public.parent_notifications USING btree (id);


--
-- Name: ix_parent_notifications_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_parent_notifications_organization_id ON public.parent_notifications USING btree (organization_id);


--
-- Name: ix_parent_profiles_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_parent_profiles_organization_id ON public.parent_profiles USING btree (organization_id);


--
-- Name: ix_parent_social_settings_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_parent_social_settings_organization_id ON public.parent_social_settings USING btree (organization_id);


--
-- Name: ix_parent_social_settings_parent_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_parent_social_settings_parent_id ON public.parent_social_settings USING btree (parent_id);


--
-- Name: ix_parent_social_settings_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_parent_social_settings_student_id ON public.parent_social_settings USING btree (student_id);


--
-- Name: ix_peer_recommendations_cluster_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_peer_recommendations_cluster_id ON public.peer_recommendations USING btree (cluster_id);


--
-- Name: ix_performance_history_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_performance_history_organization_id ON public.performance_history USING btree (organization_id);


--
-- Name: ix_performance_history_recorded_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_performance_history_recorded_at ON public.performance_history USING btree (recorded_at);


--
-- Name: ix_performance_history_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_performance_history_user_id ON public.performance_history USING btree (user_id);


--
-- Name: ix_plans_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_plans_is_active ON public.plans USING btree (is_active);


--
-- Name: ix_point_transactions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_point_transactions_organization_id ON public.point_transactions USING btree (organization_id);


--
-- Name: ix_point_transactions_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_point_transactions_timestamp ON public.point_transactions USING btree ("timestamp");


--
-- Name: ix_point_transactions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_point_transactions_user_id ON public.point_transactions USING btree (user_id);


--
-- Name: ix_pomodoro_participants_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pomodoro_participants_organization_id ON public.pomodoro_participants USING btree (organization_id);


--
-- Name: ix_pomodoro_participants_room_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pomodoro_participants_room_id ON public.pomodoro_participants USING btree (room_id);


--
-- Name: ix_pomodoro_participants_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pomodoro_participants_student_id ON public.pomodoro_participants USING btree (student_id);


--
-- Name: ix_pomodoro_rooms_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pomodoro_rooms_status ON public.pomodoro_rooms USING btree (status);


--
-- Name: ix_pomodoro_rooms_subject_area; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pomodoro_rooms_subject_area ON public.pomodoro_rooms USING btree (subject_area);


--
-- Name: ix_program_score_history_program_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_program_score_history_program_id ON public.program_score_history USING btree (program_id);


--
-- Name: ix_program_score_history_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_program_score_history_year ON public.program_score_history USING btree (year);


--
-- Name: ix_q_matrix_question_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_q_matrix_question_id ON public.q_matrix USING btree (question_id);


--
-- Name: ix_quality_gate_results_gate_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quality_gate_results_gate_name ON public.quality_gate_results USING btree (gate_name);


--
-- Name: ix_quality_gate_results_run_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quality_gate_results_run_id ON public.quality_gate_results USING btree (run_id);


--
-- Name: ix_quality_gates_override_audit_gate_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quality_gates_override_audit_gate_name ON public.quality_gates_override_audit USING btree (gate_name);


--
-- Name: ix_quality_gates_override_audit_requestor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quality_gates_override_audit_requestor ON public.quality_gates_override_audit USING btree (requestor);


--
-- Name: ix_quality_gates_runs_branch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quality_gates_runs_branch ON public.quality_gates_runs USING btree (branch);


--
-- Name: ix_quality_gates_runs_commit_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quality_gates_runs_commit_hash ON public.quality_gates_runs USING btree (commit_hash);


--
-- Name: ix_quality_gates_runs_triggered_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quality_gates_runs_triggered_by ON public.quality_gates_runs USING btree (triggered_by);


--
-- Name: ix_question_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_question_embedding_hnsw ON public.question_statistics USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: ix_question_generation_batches_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_question_generation_batches_id ON public.question_generation_batches USING btree (id);


--
-- Name: ix_question_generation_batches_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_question_generation_batches_status ON public.question_generation_batches USING btree (status);


--
-- Name: ix_question_generation_batches_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_question_generation_batches_task_id ON public.question_generation_batches USING btree (task_id);


--
-- Name: ix_question_generation_logs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_question_generation_logs_id ON public.question_generation_logs USING btree (id);


--
-- Name: ix_question_knowledge_mappings_knowledge_point_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_question_knowledge_mappings_knowledge_point_id ON public.question_knowledge_mappings USING btree (knowledge_point_id);


--
-- Name: ix_question_knowledge_mappings_question_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_question_knowledge_mappings_question_id ON public.question_knowledge_mappings USING btree (question_id);


--
-- Name: ix_quiz_questions_question_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_questions_question_id ON public.quiz_questions USING btree (question_id);


--
-- Name: ix_quiz_questions_quiz_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_questions_quiz_id ON public.quiz_questions USING btree (quiz_id);


--
-- Name: ix_quiz_submissions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_submissions_organization_id ON public.quiz_submissions USING btree (organization_id);


--
-- Name: ix_quiz_submissions_quiz_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_submissions_quiz_id ON public.quiz_submissions USING btree (quiz_id);


--
-- Name: ix_quiz_submissions_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_submissions_student_id ON public.quiz_submissions USING btree (student_id);


--
-- Name: ix_quizzes_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quizzes_subject ON public.quizzes USING btree (subject);


--
-- Name: ix_quizzes_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quizzes_topic ON public.quizzes USING btree (topic);


--
-- Name: ix_rc_problem_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rc_problem_embedding_hnsw ON public.reasoning_cache USING hnsw (problem_embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: ix_realm_progress_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_realm_progress_organization_id ON public.realm_progress USING btree (organization_id);


--
-- Name: ix_reasoning_cache_problem_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_reasoning_cache_problem_hash ON public.reasoning_cache USING btree (problem_hash);


--
-- Name: ix_refresh_tokens_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_refresh_tokens_expires_at ON public.refresh_tokens USING btree (expires_at);


--
-- Name: ix_refresh_tokens_jti; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_refresh_tokens_jti ON public.refresh_tokens USING btree (jti);


--
-- Name: ix_refresh_tokens_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_refresh_tokens_organization_id ON public.refresh_tokens USING btree (organization_id);


--
-- Name: ix_refresh_tokens_revoked; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_refresh_tokens_revoked ON public.refresh_tokens USING btree (revoked);


--
-- Name: ix_refresh_tokens_token_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_refresh_tokens_token_hash ON public.refresh_tokens USING btree (token_hash);


--
-- Name: ix_refresh_tokens_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_refresh_tokens_user_id ON public.refresh_tokens USING btree (user_id);


--
-- Name: ix_rs_problem_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rs_problem_embedding_hnsw ON public.reasoning_sessions USING hnsw (problem_embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: ix_salary_expectations_career_opportunity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_salary_expectations_career_opportunity_id ON public.salary_expectations USING btree (career_opportunity_id);


--
-- Name: ix_salary_expectations_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_salary_expectations_city ON public.salary_expectations USING btree (city);


--
-- Name: ix_salary_expectations_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_salary_expectations_department_id ON public.salary_expectations USING btree (department_id);


--
-- Name: ix_salary_expectations_experience_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_salary_expectations_experience_level ON public.salary_expectations USING btree (experience_level);


--
-- Name: ix_salary_expectations_industry_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_salary_expectations_industry_type ON public.salary_expectations USING btree (industry_type);


--
-- Name: ix_salary_expectations_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_salary_expectations_year ON public.salary_expectations USING btree (year);


--
-- Name: ix_sector_analyses_industry_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sector_analyses_industry_type ON public.sector_analyses USING btree (industry_type);


--
-- Name: ix_sector_analyses_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sector_analyses_year ON public.sector_analyses USING btree (year);


--
-- Name: ix_sessions_hashed_token; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_sessions_hashed_token ON public.sessions USING btree (hashed_token);


--
-- Name: ix_sessions_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_is_active ON public.sessions USING btree (is_active);


--
-- Name: ix_sessions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_organization_id ON public.sessions USING btree (organization_id);


--
-- Name: ix_solution_duel_submissions_duel_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_solution_duel_submissions_duel_id ON public.solution_duel_submissions USING btree (duel_id);


--
-- Name: ix_solution_duel_submissions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_solution_duel_submissions_organization_id ON public.solution_duel_submissions USING btree (organization_id);


--
-- Name: ix_solution_duel_votes_duel_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_solution_duel_votes_duel_id ON public.solution_duel_votes USING btree (duel_id);


--
-- Name: ix_solution_duels_challenger_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_solution_duels_challenger_id ON public.solution_duels USING btree (challenger_id);


--
-- Name: ix_solution_duels_opponent_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_solution_duels_opponent_id ON public.solution_duels USING btree (opponent_id);


--
-- Name: ix_solution_duels_question_bank_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_solution_duels_question_bank_id ON public.solution_duels USING btree (question_bank_id);


--
-- Name: ix_solution_duels_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_solution_duels_status ON public.solution_duels USING btree (status);


--
-- Name: ix_solution_duels_subject_area; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_solution_duels_subject_area ON public.solution_duels USING btree (subject_area);


--
-- Name: ix_streak_daily_log_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_streak_daily_log_organization_id ON public.streak_daily_log USING btree (organization_id);


--
-- Name: ix_streak_daily_log_pair_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_streak_daily_log_pair_id ON public.streak_daily_log USING btree (pair_id);


--
-- Name: ix_streak_pairs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_streak_pairs_status ON public.streak_pairs USING btree (status);


--
-- Name: ix_streak_pairs_student_a_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_streak_pairs_student_a_id ON public.streak_pairs USING btree (student_a_id);


--
-- Name: ix_streak_pairs_student_b_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_streak_pairs_student_b_id ON public.streak_pairs USING btree (student_b_id);


--
-- Name: ix_streak_tracking_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_streak_tracking_organization_id ON public.streak_tracking USING btree (organization_id);


--
-- Name: ix_streak_tracking_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_streak_tracking_user_id ON public.streak_tracking USING btree (user_id);


--
-- Name: ix_streaks_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_streaks_organization_id ON public.streaks USING btree (organization_id);


--
-- Name: ix_student_abilities_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_abilities_organization_id ON public.student_abilities USING btree (organization_id);


--
-- Name: ix_student_engagement_signals_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_engagement_signals_organization_id ON public.student_engagement_signals USING btree (organization_id);


--
-- Name: ix_student_engagement_signals_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_engagement_signals_student_id ON public.student_engagement_signals USING btree (student_id);


--
-- Name: ix_student_goals_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_goals_id ON public.student_goals USING btree (id);


--
-- Name: ix_student_goals_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_goals_organization_id ON public.student_goals USING btree (organization_id);


--
-- Name: ix_student_goals_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_goals_user_id ON public.student_goals USING btree (user_id);


--
-- Name: ix_student_knowledge_states_knowledge_point_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_knowledge_states_knowledge_point_id ON public.student_knowledge_states USING btree (knowledge_point_id);


--
-- Name: ix_student_knowledge_states_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_knowledge_states_organization_id ON public.student_knowledge_states USING btree (organization_id);


--
-- Name: ix_student_knowledge_states_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_knowledge_states_student_id ON public.student_knowledge_states USING btree (student_id);


--
-- Name: ix_student_learning_profiles_hybrid_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_learning_profiles_hybrid_code ON public.student_learning_profiles USING btree (hybrid_code);


--
-- Name: ix_student_learning_profiles_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_learning_profiles_id ON public.student_learning_profiles USING btree (id);


--
-- Name: ix_student_learning_profiles_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_learning_profiles_organization_id ON public.student_learning_profiles USING btree (organization_id);


--
-- Name: ix_student_learning_profiles_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_student_learning_profiles_student_id ON public.student_learning_profiles USING btree (student_id);


--
-- Name: ix_student_nano_skill_mastery_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_nano_skill_mastery_organization_id ON public.student_nano_skill_mastery USING btree (organization_id);


--
-- Name: ix_student_profiles_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_profiles_organization_id ON public.student_profiles USING btree (organization_id);


--
-- Name: ix_student_question_responses_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_question_responses_id ON public.student_question_responses USING btree (id);


--
-- Name: ix_study_plans_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_study_plans_is_active ON public.study_plans USING btree (is_active);


--
-- Name: ix_study_plans_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_study_plans_organization_id ON public.study_plans USING btree (organization_id);


--
-- Name: ix_study_rooms_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_study_rooms_organization_id ON public.study_rooms USING btree (organization_id);


--
-- Name: ix_study_sessions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_study_sessions_organization_id ON public.study_sessions USING btree (organization_id);


--
-- Name: ix_study_sessions_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_study_sessions_student_id ON public.study_sessions USING btree (student_id);


--
-- Name: ix_teacher_assignments_teacher_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_teacher_assignments_teacher_user_id ON public.teacher_assignments USING btree (teacher_user_id);


--
-- Name: ix_teacher_classroom_students_classroom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_teacher_classroom_students_classroom_id ON public.teacher_classroom_students USING btree (classroom_id);


--
-- Name: ix_teacher_classrooms_teacher_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_teacher_classrooms_teacher_user_id ON public.teacher_classrooms USING btree (teacher_user_id);


--
-- Name: ix_teacher_contents_teacher_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_teacher_contents_teacher_user_id ON public.teacher_contents USING btree (teacher_user_id);


--
-- Name: ix_teacher_exam_configs_teacher_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_teacher_exam_configs_teacher_user_id ON public.teacher_exam_configs USING btree (teacher_user_id);


--
-- Name: ix_teacher_pool_profiles_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_teacher_pool_profiles_organization_id ON public.teacher_pool_profiles USING btree (organization_id);


--
-- Name: ix_teacher_profiles_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_teacher_profiles_organization_id ON public.teacher_profiles USING btree (organization_id);


--
-- Name: ix_topic_completions_node_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_topic_completions_node_id ON public.topic_completions USING btree (node_id);


--
-- Name: ix_topic_completions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_topic_completions_organization_id ON public.topic_completions USING btree (organization_id);


--
-- Name: ix_topic_completions_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_topic_completions_student_id ON public.topic_completions USING btree (student_id);


--
-- Name: ix_topic_progress_node_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_topic_progress_node_id ON public.topic_progress USING btree (node_id);


--
-- Name: ix_topic_progress_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_topic_progress_organization_id ON public.topic_progress USING btree (organization_id);


--
-- Name: ix_topic_progress_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_topic_progress_student_id ON public.topic_progress USING btree (student_id);


--
-- Name: ix_universities_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_universities_city ON public.universities USING btree (city);


--
-- Name: ix_universities_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_universities_is_active ON public.universities USING btree (is_active);


--
-- Name: ix_universities_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_universities_name ON public.universities USING btree (name);


--
-- Name: ix_universities_university_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_universities_university_type ON public.universities USING btree (university_type);


--
-- Name: ix_university_programs_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_university_programs_department_id ON public.university_programs USING btree (department_id);


--
-- Name: ix_university_programs_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_university_programs_is_active ON public.university_programs USING btree (is_active);


--
-- Name: ix_university_programs_program_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_university_programs_program_code ON public.university_programs USING btree (program_code);


--
-- Name: ix_university_programs_program_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_university_programs_program_type ON public.university_programs USING btree (program_type);


--
-- Name: ix_university_programs_score_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_university_programs_score_type ON public.university_programs USING btree (score_type);


--
-- Name: ix_university_programs_university_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_university_programs_university_id ON public.university_programs USING btree (university_id);


--
-- Name: ix_university_programs_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_university_programs_year ON public.university_programs USING btree (year);


--
-- Name: ix_user_achievements_achievement_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_achievements_achievement_id ON public.user_achievements USING btree (achievement_id);


--
-- Name: ix_user_achievements_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_achievements_organization_id ON public.user_achievements USING btree (organization_id);


--
-- Name: ix_user_achievements_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_achievements_user_id ON public.user_achievements USING btree (user_id);


--
-- Name: ix_user_badges_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_badges_organization_id ON public.user_badges USING btree (organization_id);


--
-- Name: ix_user_theta_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_theta_organization_id ON public.user_theta USING btree (organization_id);


--
-- Name: ix_user_university_preferences_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_university_preferences_user_id ON public.user_university_preferences USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_is_active ON public.users USING btree (is_active);


--
-- Name: ix_users_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_organization_id ON public.users USING btree (organization_id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_veli_consent_child_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_veli_consent_child_user_id ON public.veli_consent USING btree (child_user_id);


--
-- Name: ix_veli_consent_token_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_veli_consent_token_hash ON public.veli_consent USING btree (token_hash);


--
-- Name: ix_video_analytics_summary_period_start; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_analytics_summary_period_start ON public.video_analytics_summary USING btree (period_start);


--
-- Name: ix_video_analytics_summary_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_analytics_summary_user_id ON public.video_analytics_summary USING btree (user_id);


--
-- Name: ix_video_bookmarks_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_bookmarks_created_at ON public.video_bookmarks USING btree (created_at);


--
-- Name: ix_video_bookmarks_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_bookmarks_user_id ON public.video_bookmarks USING btree (user_id);


--
-- Name: ix_video_bookmarks_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_bookmarks_video_id ON public.video_bookmarks USING btree (video_id);


--
-- Name: ix_video_completion_milestones_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_completion_milestones_user_id ON public.video_completion_milestones USING btree (user_id);


--
-- Name: ix_video_completion_milestones_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_completion_milestones_video_id ON public.video_completion_milestones USING btree (video_id);


--
-- Name: ix_video_notes_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_notes_created_at ON public.video_notes USING btree (created_at);


--
-- Name: ix_video_notes_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_notes_user_id ON public.video_notes USING btree (user_id);


--
-- Name: ix_video_notes_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_notes_video_id ON public.video_notes USING btree (video_id);


--
-- Name: ix_video_solutions_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_solutions_is_active ON public.video_solutions USING btree (is_active);


--
-- Name: ix_video_transcripts_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_transcripts_is_active ON public.video_transcripts USING btree (is_active);


--
-- Name: ix_video_watch_sessions_started_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_watch_sessions_started_at ON public.video_watch_sessions USING btree (started_at);


--
-- Name: ix_video_watch_sessions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_watch_sessions_user_id ON public.video_watch_sessions USING btree (user_id);


--
-- Name: ix_video_watch_sessions_video_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_video_watch_sessions_video_id ON public.video_watch_sessions USING btree (video_id);


--
-- Name: ix_weekly_progress_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_weekly_progress_id ON public.weekly_progress USING btree (id);


--
-- Name: ix_weekly_progress_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_weekly_progress_organization_id ON public.weekly_progress USING btree (organization_id);


--
-- Name: ix_weekly_progress_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_weekly_progress_user_id ON public.weekly_progress USING btree (user_id);


--
-- Name: ix_weekly_reports_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_weekly_reports_id ON public.weekly_reports USING btree (id);


--
-- Name: ix_xp_transactions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_xp_transactions_organization_id ON public.xp_transactions USING btree (organization_id);


--
-- Name: ix_zpd_history_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_zpd_history_organization_id ON public.zpd_history USING btree (organization_id);


--
-- Name: ix_zpd_history_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_zpd_history_student_id ON public.zpd_history USING btree (student_id);


--
-- Name: ix_zpd_history_topic_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_zpd_history_topic_id ON public.zpd_history USING btree (topic_id);


--
-- Name: uq_qb_soru_hash_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_qb_soru_hash_active ON public.question_bank USING btree (soru_hash) WHERE (is_active = true);


--
-- Name: ux_mv_safe_for_beta_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_mv_safe_for_beta_id ON public.mv_safe_for_beta USING btree (id);


--
-- Name: api_keys api_keys_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: api_keys api_keys_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: appointment_reminders appointment_reminders_appointment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointment_reminders
    ADD CONSTRAINT appointment_reminders_appointment_id_fkey FOREIGN KEY (appointment_id) REFERENCES public.appointments(id) ON DELETE CASCADE;


--
-- Name: appointment_reminders appointment_reminders_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointment_reminders
    ADD CONSTRAINT appointment_reminders_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: appointments appointments_availability_slot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_availability_slot_id_fkey FOREIGN KEY (availability_slot_id) REFERENCES public.teacher_availability(id) ON DELETE CASCADE;


--
-- Name: appointments appointments_cancelled_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_cancelled_by_fkey FOREIGN KEY (cancelled_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: appointments appointments_confirmed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_confirmed_by_fkey FOREIGN KEY (confirmed_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: appointments appointments_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: appointments appointments_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teacher_pool_profiles(id) ON DELETE CASCADE;


--
-- Name: audit_logs audit_logs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: billing_data_processing_agreements billing_data_processing_agreements_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_data_processing_agreements
    ADD CONSTRAINT billing_data_processing_agreements_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: bkt_states bkt_states_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bkt_states
    ADD CONSTRAINT bkt_states_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: bkt_states bkt_states_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bkt_states
    ADD CONSTRAINT bkt_states_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: campus_info campus_info_university_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campus_info
    ADD CONSTRAINT campus_info_university_id_fkey FOREIGN KEY (university_id) REFERENCES public.universities(id) ON DELETE CASCADE;


--
-- Name: career_opportunities career_opportunities_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.career_opportunities
    ADD CONSTRAINT career_opportunities_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE CASCADE;


--
-- Name: chat_analytics chat_analytics_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_analytics
    ADD CONSTRAINT chat_analytics_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: chat_analytics chat_analytics_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_analytics
    ADD CONSTRAINT chat_analytics_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: chat_messages chat_messages_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_image_id_fkey FOREIGN KEY (image_id) REFERENCES public.image_uploads(id) ON DELETE SET NULL;


--
-- Name: chat_messages chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: chat_sessions chat_sessions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: chat_sessions chat_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: class_reports class_reports_teacher_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_reports
    ADD CONSTRAINT class_reports_teacher_user_id_fkey FOREIGN KEY (teacher_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: classrooms classrooms_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classrooms
    ADD CONSTRAINT classrooms_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: classrooms classrooms_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classrooms
    ADD CONSTRAINT classrooms_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teacher_profiles(id) ON DELETE CASCADE;


--
-- Name: coaching_events coaching_events_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coaching_events
    ADD CONSTRAINT coaching_events_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: coppa_parental_consents coppa_parental_consents_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coppa_parental_consents
    ADD CONSTRAINT coppa_parental_consents_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: coppa_parental_consents coppa_parental_consents_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coppa_parental_consents
    ADD CONSTRAINT coppa_parental_consents_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: curriculum_alignments curriculum_alignments_meb_standard_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.curriculum_alignments
    ADD CONSTRAINT curriculum_alignments_meb_standard_id_fkey FOREIGN KEY (meb_standard_id) REFERENCES public.meb_curriculum_standards(id) ON DELETE CASCADE;


--
-- Name: curriculum_alignments curriculum_alignments_osym_standard_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.curriculum_alignments
    ADD CONSTRAINT curriculum_alignments_osym_standard_id_fkey FOREIGN KEY (osym_standard_id) REFERENCES public.osym_standards(id) ON DELETE CASCADE;


--
-- Name: daily_plans daily_plans_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_plans
    ADD CONSTRAINT daily_plans_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: daily_plans daily_plans_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_plans
    ADD CONSTRAINT daily_plans_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: daily_quests daily_quests_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_quests
    ADD CONSTRAINT daily_quests_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: daily_quests daily_quests_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_quests
    ADD CONSTRAINT daily_quests_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: data_retention_policies data_retention_policies_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_retention_policies
    ADD CONSTRAINT data_retention_policies_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: department_curricula department_curricula_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.department_curricula
    ADD CONSTRAINT department_curricula_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE CASCADE;


--
-- Name: department_statistics department_statistics_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.department_statistics
    ADD CONSTRAINT department_statistics_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE CASCADE;


--
-- Name: diary_entries diary_entries_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diary_entries
    ADD CONSTRAINT diary_entries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: diary_exports diary_exports_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diary_exports
    ADD CONSTRAINT diary_exports_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: dormitory_info dormitory_info_university_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dormitory_info
    ADD CONSTRAINT dormitory_info_university_id_fkey FOREIGN KEY (university_id) REFERENCES public.universities(id) ON DELETE CASCADE;


--
-- Name: duel_matches duel_matches_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duel_matches
    ADD CONSTRAINT duel_matches_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.duel_sessions(id) ON DELETE CASCADE;


--
-- Name: duel_ratings duel_ratings_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duel_ratings
    ADD CONSTRAINT duel_ratings_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: duel_ratings duel_ratings_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duel_ratings
    ADD CONSTRAINT duel_ratings_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: duel_sessions duel_sessions_player1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duel_sessions
    ADD CONSTRAINT duel_sessions_player1_id_fkey FOREIGN KEY (player1_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: duel_sessions duel_sessions_player2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duel_sessions
    ADD CONSTRAINT duel_sessions_player2_id_fkey FOREIGN KEY (player2_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: duels duels_player1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duels
    ADD CONSTRAINT duels_player1_id_fkey FOREIGN KEY (player1_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: duels duels_player2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duels
    ADD CONSTRAINT duels_player2_id_fkey FOREIGN KEY (player2_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: duels duels_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.duels
    ADD CONSTRAINT duels_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topic_hierarchy(id) ON DELETE CASCADE;


--
-- Name: dungeon_progress dungeon_progress_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dungeon_progress
    ADD CONSTRAINT dungeon_progress_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: dungeon_progress dungeon_progress_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dungeon_progress
    ADD CONSTRAINT dungeon_progress_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topic_hierarchy(id) ON DELETE CASCADE;


--
-- Name: dungeon_progress dungeon_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dungeon_progress
    ADD CONSTRAINT dungeon_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: eba_content_collections eba_content_collections_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_content_collections
    ADD CONSTRAINT eba_content_collections_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: eba_video_recommendations eba_video_recommendations_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_recommendations
    ADD CONSTRAINT eba_video_recommendations_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: eba_video_recommendations eba_video_recommendations_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_recommendations
    ADD CONSTRAINT eba_video_recommendations_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: eba_video_recommendations eba_video_recommendations_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_recommendations
    ADD CONSTRAINT eba_video_recommendations_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.eba_videos(id) ON DELETE CASCADE;


--
-- Name: eba_video_usage eba_video_usage_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_usage
    ADD CONSTRAINT eba_video_usage_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: eba_video_usage eba_video_usage_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_usage
    ADD CONSTRAINT eba_video_usage_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: eba_video_usage eba_video_usage_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_usage
    ADD CONSTRAINT eba_video_usage_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.eba_videos(id) ON DELETE CASCADE;


--
-- Name: eba_video_watches eba_video_watches_eba_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_watches
    ADD CONSTRAINT eba_video_watches_eba_video_id_fkey FOREIGN KEY (eba_video_id) REFERENCES public.eba_videos(id) ON DELETE CASCADE;


--
-- Name: eba_video_watches eba_video_watches_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_watches
    ADD CONSTRAINT eba_video_watches_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: eba_video_watches eba_video_watches_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_video_watches
    ADD CONSTRAINT eba_video_watches_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: eba_videos eba_videos_moderated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eba_videos
    ADD CONSTRAINT eba_videos_moderated_by_fkey FOREIGN KEY (moderated_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: educational_record_access_logs educational_record_access_logs_accessor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.educational_record_access_logs
    ADD CONSTRAINT educational_record_access_logs_accessor_id_fkey FOREIGN KEY (accessor_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: educational_record_access_logs educational_record_access_logs_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.educational_record_access_logs
    ADD CONSTRAINT educational_record_access_logs_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: emotional_states emotional_states_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emotional_states
    ADD CONSTRAINT emotional_states_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: exam_questions exam_questions_exam_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exam_questions
    ADD CONSTRAINT exam_questions_exam_session_id_fkey FOREIGN KEY (exam_session_id) REFERENCES public.exam_sessions(id) ON DELETE CASCADE;


--
-- Name: exam_questions exam_questions_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exam_questions
    ADD CONSTRAINT exam_questions_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: exam_sessions exam_sessions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exam_sessions
    ADD CONSTRAINT exam_sessions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: exam_sessions exam_sessions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exam_sessions
    ADD CONSTRAINT exam_sessions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: ferpa_consents ferpa_consents_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ferpa_consents
    ADD CONSTRAINT ferpa_consents_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: ferpa_consents ferpa_consents_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ferpa_consents
    ADD CONSTRAINT ferpa_consents_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: file_versions file_versions_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_versions
    ADD CONSTRAINT file_versions_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.shared_files(id) ON DELETE CASCADE;


--
-- Name: file_versions file_versions_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_versions
    ADD CONSTRAINT file_versions_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: data_processing_agreements fk_data_processing_agreements_organization; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_processing_agreements
    ADD CONSTRAINT fk_data_processing_agreements_organization FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: forum_questions forum_questions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forum_questions
    ADD CONSTRAINT forum_questions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: fsrs_cards fsrs_cards_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_cards
    ADD CONSTRAINT fsrs_cards_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: fsrs_cards fsrs_cards_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_cards
    ADD CONSTRAINT fsrs_cards_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: fsrs_reviews fsrs_reviews_card_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_reviews
    ADD CONSTRAINT fsrs_reviews_card_id_fkey FOREIGN KEY (card_id) REFERENCES public.fsrs_cards(id) ON DELETE CASCADE;


--
-- Name: fsrs_reviews fsrs_reviews_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_reviews
    ADD CONSTRAINT fsrs_reviews_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: fsrs_reviews fsrs_reviews_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_reviews
    ADD CONSTRAINT fsrs_reviews_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: fsrs_schedules fsrs_schedules_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_schedules
    ADD CONSTRAINT fsrs_schedules_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: fsrs_schedules fsrs_schedules_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_schedules
    ADD CONSTRAINT fsrs_schedules_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: fsrs_student_profiles fsrs_student_profiles_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_student_profiles
    ADD CONSTRAINT fsrs_student_profiles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: fsrs_student_profiles fsrs_student_profiles_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_student_profiles
    ADD CONSTRAINT fsrs_student_profiles_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: fsrs_study_sessions fsrs_study_sessions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_study_sessions
    ADD CONSTRAINT fsrs_study_sessions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: fsrs_study_sessions fsrs_study_sessions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_study_sessions
    ADD CONSTRAINT fsrs_study_sessions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: fsrs_subject_stats fsrs_subject_stats_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_subject_stats
    ADD CONSTRAINT fsrs_subject_stats_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: fsrs_subject_stats fsrs_subject_stats_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fsrs_subject_stats
    ADD CONSTRAINT fsrs_subject_stats_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: goals goals_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goals
    ADD CONSTRAINT goals_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: image_uploads image_uploads_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image_uploads
    ADD CONSTRAINT image_uploads_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: image_uploads image_uploads_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image_uploads
    ADD CONSTRAINT image_uploads_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: image_uploads image_uploads_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image_uploads
    ADD CONSTRAINT image_uploads_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: insights insights_diary_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.insights
    ADD CONSTRAINT insights_diary_entry_id_fkey FOREIGN KEY (diary_entry_id) REFERENCES public.diary_entries(id) ON DELETE CASCADE;


--
-- Name: insights insights_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.insights
    ADD CONSTRAINT insights_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: invoices invoices_license_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_license_id_fkey FOREIGN KEY (license_id) REFERENCES public.organization_licenses(id) ON DELETE SET NULL;


--
-- Name: invoices invoices_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: irt_calibration_history irt_calibration_history_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.irt_calibration_history
    ADD CONSTRAINT irt_calibration_history_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: khan_certificates khan_certificates_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.khan_certificates
    ADD CONSTRAINT khan_certificates_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: khan_oauth_tokens khan_oauth_tokens_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.khan_oauth_tokens
    ADD CONSTRAINT khan_oauth_tokens_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: khan_oauth_tokens khan_oauth_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.khan_oauth_tokens
    ADD CONSTRAINT khan_oauth_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: khan_user_progress khan_user_progress_khan_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.khan_user_progress
    ADD CONSTRAINT khan_user_progress_khan_content_id_fkey FOREIGN KEY (khan_content_id) REFERENCES public.khan_contents(id) ON DELETE CASCADE;


--
-- Name: khan_user_progress khan_user_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.khan_user_progress
    ADD CONSTRAINT khan_user_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: kiro2_cat_sessions kiro2_cat_sessions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kiro2_cat_sessions
    ADD CONSTRAINT kiro2_cat_sessions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: kiro2_learning_events kiro2_learning_events_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kiro2_learning_events
    ADD CONSTRAINT kiro2_learning_events_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: kvkk_audit_logs kvkk_audit_logs_accessed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_audit_logs
    ADD CONSTRAINT kvkk_audit_logs_accessed_by_fkey FOREIGN KEY (accessed_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: kvkk_audit_logs kvkk_audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_audit_logs
    ADD CONSTRAINT kvkk_audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: kvkk_consents kvkk_consents_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_consents
    ADD CONSTRAINT kvkk_consents_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: kvkk_consents kvkk_consents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_consents
    ADD CONSTRAINT kvkk_consents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: kvkk_data_deletion_requests kvkk_data_deletion_requests_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_data_deletion_requests
    ADD CONSTRAINT kvkk_data_deletion_requests_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: kvkk_data_deletion_requests kvkk_data_deletion_requests_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_data_deletion_requests
    ADD CONSTRAINT kvkk_data_deletion_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: kvkk_data_export_requests kvkk_data_export_requests_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_data_export_requests
    ADD CONSTRAINT kvkk_data_export_requests_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: kvkk_data_export_requests kvkk_data_export_requests_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_data_export_requests
    ADD CONSTRAINT kvkk_data_export_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: kvkk_privacy_policy_versions kvkk_privacy_policy_versions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kvkk_privacy_policy_versions
    ADD CONSTRAINT kvkk_privacy_policy_versions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: league_history league_history_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.league_history
    ADD CONSTRAINT league_history_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: league_memberships league_memberships_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.league_memberships
    ADD CONSTRAINT league_memberships_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: learning_analytics learning_analytics_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_analytics
    ADD CONSTRAINT learning_analytics_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: learning_analytics learning_analytics_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_analytics
    ADD CONSTRAINT learning_analytics_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: learning_entries learning_entries_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_entries
    ADD CONSTRAINT learning_entries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: learning_outcomes learning_outcomes_meb_standard_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_outcomes
    ADD CONSTRAINT learning_outcomes_meb_standard_id_fkey FOREIGN KEY (meb_standard_id) REFERENCES public.meb_curriculum_standards(id) ON DELETE CASCADE;


--
-- Name: learning_path_student_profiles learning_path_student_profiles_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_path_student_profiles
    ADD CONSTRAINT learning_path_student_profiles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: learning_path_student_profiles learning_path_student_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_path_student_profiles
    ADD CONSTRAINT learning_path_student_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: learning_paths learning_paths_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_paths
    ADD CONSTRAINT learning_paths_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: learning_paths learning_paths_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_paths
    ADD CONSTRAINT learning_paths_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.learning_path_student_profiles(student_id) ON DELETE CASCADE;


--
-- Name: learning_progress_daily learning_progress_daily_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_progress_daily
    ADD CONSTRAINT learning_progress_daily_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: learning_progress_daily learning_progress_daily_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_progress_daily
    ADD CONSTRAINT learning_progress_daily_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: live_sessions live_sessions_host_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.live_sessions
    ADD CONSTRAINT live_sessions_host_id_fkey FOREIGN KEY (host_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: live_sessions live_sessions_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.live_sessions
    ADD CONSTRAINT live_sessions_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teacher_profiles(id) ON DELETE CASCADE;


--
-- Name: manipulative_activities manipulative_activities_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manipulative_activities
    ADD CONSTRAINT manipulative_activities_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: manipulative_activities manipulative_activities_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manipulative_activities
    ADD CONSTRAINT manipulative_activities_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: manipulative_progress manipulative_progress_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manipulative_progress
    ADD CONSTRAINT manipulative_progress_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: manipulative_progress manipulative_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manipulative_progress
    ADD CONSTRAINT manipulative_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: misconception_remedies misconception_remedies_misconception_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.misconception_remedies
    ADD CONSTRAINT misconception_remedies_misconception_id_fkey FOREIGN KEY (misconception_id) REFERENCES public.misconception_matrix(id) ON DELETE CASCADE;


--
-- Name: moderation_queue moderation_queue_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moderation_queue
    ADD CONSTRAINT moderation_queue_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: moderation_queue moderation_queue_review_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moderation_queue
    ADD CONSTRAINT moderation_queue_review_id_fkey FOREIGN KEY (review_id) REFERENCES public.student_reviews(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: oba_challenge_progress oba_challenge_progress_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oba_challenge_progress
    ADD CONSTRAINT oba_challenge_progress_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: oba_uyeler oba_uyeler_oba_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oba_uyeler
    ADD CONSTRAINT oba_uyeler_oba_id_fkey FOREIGN KEY (oba_id) REFERENCES public.obalar(id) ON DELETE CASCADE;


--
-- Name: oba_uyeler oba_uyeler_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oba_uyeler
    ADD CONSTRAINT oba_uyeler_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: oba_uyeler oba_uyeler_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oba_uyeler
    ADD CONSTRAINT oba_uyeler_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: offline_sync_packages offline_sync_packages_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.offline_sync_packages
    ADD CONSTRAINT offline_sync_packages_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: org_memberships org_memberships_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_memberships
    ADD CONSTRAINT org_memberships_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: org_memberships org_memberships_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_memberships
    ADD CONSTRAINT org_memberships_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: organization_licenses organization_licenses_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_licenses
    ADD CONSTRAINT organization_licenses_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: organization_licenses organization_licenses_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_licenses
    ADD CONSTRAINT organization_licenses_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.plans(id) ON DELETE RESTRICT;


--
-- Name: osb_settings osb_settings_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.osb_settings
    ADD CONSTRAINT osb_settings_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: osb_settings osb_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.osb_settings
    ADD CONSTRAINT osb_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: osym_questions osym_questions_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.osym_questions
    ADD CONSTRAINT osym_questions_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: parent_approvals parent_approvals_parent_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_approvals
    ADD CONSTRAINT parent_approvals_parent_user_id_fkey FOREIGN KEY (parent_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_approvals parent_approvals_student_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_approvals
    ADD CONSTRAINT parent_approvals_student_user_id_fkey FOREIGN KEY (student_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_child parent_child_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_child
    ADD CONSTRAINT parent_child_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_child parent_child_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_child
    ADD CONSTRAINT parent_child_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: parent_child parent_child_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_child
    ADD CONSTRAINT parent_child_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_link_codes parent_link_codes_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_link_codes
    ADD CONSTRAINT parent_link_codes_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: parent_link_codes parent_link_codes_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_link_codes
    ADD CONSTRAINT parent_link_codes_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_notifications parent_notifications_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_notifications
    ADD CONSTRAINT parent_notifications_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_notifications parent_notifications_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_notifications
    ADD CONSTRAINT parent_notifications_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: parent_notifications parent_notifications_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_notifications
    ADD CONSTRAINT parent_notifications_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_profiles parent_profiles_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_profiles
    ADD CONSTRAINT parent_profiles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: parent_profiles parent_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_profiles
    ADD CONSTRAINT parent_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_reports parent_reports_parent_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_reports
    ADD CONSTRAINT parent_reports_parent_user_id_fkey FOREIGN KEY (parent_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_reports parent_reports_student_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_reports
    ADD CONSTRAINT parent_reports_student_user_id_fkey FOREIGN KEY (student_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: parent_social_settings parent_social_settings_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parent_social_settings
    ADD CONSTRAINT parent_social_settings_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: peer_comparisons peer_comparisons_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.peer_comparisons
    ADD CONSTRAINT peer_comparisons_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: performance_history performance_history_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_history
    ADD CONSTRAINT performance_history_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: performance_history performance_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_history
    ADD CONSTRAINT performance_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: point_transactions point_transactions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.point_transactions
    ADD CONSTRAINT point_transactions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: point_transactions point_transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.point_transactions
    ADD CONSTRAINT point_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: pomodoro_participants pomodoro_participants_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pomodoro_participants
    ADD CONSTRAINT pomodoro_participants_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: program_score_history program_score_history_program_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.program_score_history
    ADD CONSTRAINT program_score_history_program_id_fkey FOREIGN KEY (program_id) REFERENCES public.university_programs(id) ON DELETE CASCADE;


--
-- Name: q_matrix q_matrix_nano_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.q_matrix
    ADD CONSTRAINT q_matrix_nano_skill_id_fkey FOREIGN KEY (nano_skill_id) REFERENCES public.nano_skills(id) ON DELETE CASCADE;


--
-- Name: quality_gate_results quality_gate_results_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quality_gate_results
    ADD CONSTRAINT quality_gate_results_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.quality_gates_runs(id) ON DELETE CASCADE;


--
-- Name: quality_gates_override_audit quality_gates_override_audit_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quality_gates_override_audit
    ADD CONSTRAINT quality_gates_override_audit_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.quality_gates_runs(id) ON DELETE SET NULL;


--
-- Name: question_bank question_bank_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_bank
    ADD CONSTRAINT question_bank_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: question_bank question_bank_primary_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_bank
    ADD CONSTRAINT question_bank_primary_topic_id_fkey FOREIGN KEY (primary_topic_id) REFERENCES public.topic_hierarchy(id) ON DELETE CASCADE;


--
-- Name: question_bank question_bank_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_bank
    ADD CONSTRAINT question_bank_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: question_content question_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_content
    ADD CONSTRAINT question_content_id_fkey FOREIGN KEY (id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: question_generation_logs question_generation_logs_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_generation_logs
    ADD CONSTRAINT question_generation_logs_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.osym_questions(question_id) ON DELETE CASCADE;


--
-- Name: question_knowledge_mappings question_knowledge_mappings_knowledge_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_knowledge_mappings
    ADD CONSTRAINT question_knowledge_mappings_knowledge_point_id_fkey FOREIGN KEY (knowledge_point_id) REFERENCES public.knowledge_points(id) ON DELETE CASCADE;


--
-- Name: question_metadata question_metadata_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_metadata
    ADD CONSTRAINT question_metadata_id_fkey FOREIGN KEY (id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: question_performance_analytics question_performance_analytics_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_performance_analytics
    ADD CONSTRAINT question_performance_analytics_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: question_statistics question_statistics_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_statistics
    ADD CONSTRAINT question_statistics_id_fkey FOREIGN KEY (id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: question_tag_associations question_tag_associations_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_tag_associations
    ADD CONSTRAINT question_tag_associations_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: question_tag_associations question_tag_associations_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_tag_associations
    ADD CONSTRAINT question_tag_associations_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.question_tags(id) ON DELETE CASCADE;


--
-- Name: quiz_questions quiz_questions_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: quiz_questions quiz_questions_quiz_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_quiz_id_fkey FOREIGN KEY (quiz_id) REFERENCES public.quizzes(id) ON DELETE CASCADE;


--
-- Name: quiz_submissions quiz_submissions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_submissions
    ADD CONSTRAINT quiz_submissions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: quiz_submissions quiz_submissions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_submissions
    ADD CONSTRAINT quiz_submissions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.learning_path_student_profiles(student_id) ON DELETE CASCADE;


--
-- Name: realm_progress realm_progress_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.realm_progress
    ADD CONSTRAINT realm_progress_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: realm_progress realm_progress_realm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.realm_progress
    ADD CONSTRAINT realm_progress_realm_id_fkey FOREIGN KEY (realm_id) REFERENCES public.realms(id) ON DELETE CASCADE;


--
-- Name: realm_progress realm_progress_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.realm_progress
    ADD CONSTRAINT realm_progress_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: reasoning_sessions reasoning_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reasoning_sessions
    ADD CONSTRAINT reasoning_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: reasoning_steps reasoning_steps_parent_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reasoning_steps
    ADD CONSTRAINT reasoning_steps_parent_step_id_fkey FOREIGN KEY (parent_step_id) REFERENCES public.reasoning_steps(id) ON DELETE SET NULL;


--
-- Name: reasoning_steps reasoning_steps_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reasoning_steps
    ADD CONSTRAINT reasoning_steps_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.reasoning_sessions(id) ON DELETE CASCADE;


--
-- Name: recording_bookmarks recording_bookmarks_recording_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recording_bookmarks
    ADD CONSTRAINT recording_bookmarks_recording_id_fkey FOREIGN KEY (recording_id) REFERENCES public.session_recordings(id) ON DELETE CASCADE;


--
-- Name: recording_bookmarks recording_bookmarks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recording_bookmarks
    ADD CONSTRAINT recording_bookmarks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: recording_views recording_views_recording_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recording_views
    ADD CONSTRAINT recording_views_recording_id_fkey FOREIGN KEY (recording_id) REFERENCES public.session_recordings(id) ON DELETE CASCADE;


--
-- Name: recording_views recording_views_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recording_views
    ADD CONSTRAINT recording_views_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: reflections reflections_diary_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reflections
    ADD CONSTRAINT reflections_diary_entry_id_fkey FOREIGN KEY (diary_entry_id) REFERENCES public.diary_entries(id) ON DELETE CASCADE;


--
-- Name: reflections reflections_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reflections
    ADD CONSTRAINT reflections_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: refresh_tokens refresh_tokens_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: refresh_tokens refresh_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: review_ratings review_ratings_review_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_ratings
    ADD CONSTRAINT review_ratings_review_id_fkey FOREIGN KEY (review_id) REFERENCES public.student_reviews(id) ON DELETE CASCADE;


--
-- Name: review_reports review_reports_reporter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_reports
    ADD CONSTRAINT review_reports_reporter_id_fkey FOREIGN KEY (reporter_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: review_reports review_reports_resolved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_reports
    ADD CONSTRAINT review_reports_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: review_reports review_reports_review_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_reports
    ADD CONSTRAINT review_reports_review_id_fkey FOREIGN KEY (review_id) REFERENCES public.student_reviews(id) ON DELETE CASCADE;


--
-- Name: review_statistics review_statistics_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_statistics
    ADD CONSTRAINT review_statistics_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE CASCADE;


--
-- Name: review_statistics review_statistics_dormitory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_statistics
    ADD CONSTRAINT review_statistics_dormitory_id_fkey FOREIGN KEY (dormitory_id) REFERENCES public.dormitory_info(id) ON DELETE CASCADE;


--
-- Name: review_statistics review_statistics_university_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_statistics
    ADD CONSTRAINT review_statistics_university_id_fkey FOREIGN KEY (university_id) REFERENCES public.universities(id) ON DELETE CASCADE;


--
-- Name: review_votes review_votes_review_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_votes
    ADD CONSTRAINT review_votes_review_id_fkey FOREIGN KEY (review_id) REFERENCES public.student_reviews(id) ON DELETE CASCADE;


--
-- Name: review_votes review_votes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_votes
    ADD CONSTRAINT review_votes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: room_analytics room_analytics_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_analytics
    ADD CONSTRAINT room_analytics_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.study_rooms(id) ON DELETE CASCADE;


--
-- Name: room_chat_messages room_chat_messages_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_chat_messages
    ADD CONSTRAINT room_chat_messages_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: room_chat_messages room_chat_messages_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_chat_messages
    ADD CONSTRAINT room_chat_messages_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.shared_files(id) ON DELETE CASCADE;


--
-- Name: room_chat_messages room_chat_messages_pinned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_chat_messages
    ADD CONSTRAINT room_chat_messages_pinned_by_fkey FOREIGN KEY (pinned_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: room_chat_messages room_chat_messages_reply_to_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_chat_messages
    ADD CONSTRAINT room_chat_messages_reply_to_id_fkey FOREIGN KEY (reply_to_id) REFERENCES public.room_chat_messages(id) ON DELETE CASCADE;


--
-- Name: room_chat_messages room_chat_messages_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_chat_messages
    ADD CONSTRAINT room_chat_messages_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.study_rooms(id) ON DELETE CASCADE;


--
-- Name: room_chat_messages room_chat_messages_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_chat_messages
    ADD CONSTRAINT room_chat_messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: room_invitations room_invitations_invitee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_invitations
    ADD CONSTRAINT room_invitations_invitee_id_fkey FOREIGN KEY (invitee_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: room_invitations room_invitations_inviter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_invitations
    ADD CONSTRAINT room_invitations_inviter_id_fkey FOREIGN KEY (inviter_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: room_invitations room_invitations_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_invitations
    ADD CONSTRAINT room_invitations_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.study_rooms(id) ON DELETE CASCADE;


--
-- Name: room_members room_members_invited_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_members
    ADD CONSTRAINT room_members_invited_by_fkey FOREIGN KEY (invited_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: room_members room_members_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_members
    ADD CONSTRAINT room_members_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.study_rooms(id) ON DELETE CASCADE;


--
-- Name: room_members room_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_members
    ADD CONSTRAINT room_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: room_settings room_settings_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_settings
    ADD CONSTRAINT room_settings_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.study_rooms(id) ON DELETE CASCADE;


--
-- Name: room_study_sessions room_study_sessions_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_study_sessions
    ADD CONSTRAINT room_study_sessions_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.study_rooms(id) ON DELETE CASCADE;


--
-- Name: room_study_sessions room_study_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.room_study_sessions
    ADD CONSTRAINT room_study_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: salary_expectations salary_expectations_career_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salary_expectations
    ADD CONSTRAINT salary_expectations_career_opportunity_id_fkey FOREIGN KEY (career_opportunity_id) REFERENCES public.career_opportunities(id) ON DELETE CASCADE;


--
-- Name: salary_expectations salary_expectations_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salary_expectations
    ADD CONSTRAINT salary_expectations_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE CASCADE;


--
-- Name: scholarship_programs scholarship_programs_university_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarship_programs
    ADD CONSTRAINT scholarship_programs_university_id_fkey FOREIGN KEY (university_id) REFERENCES public.universities(id) ON DELETE CASCADE;


--
-- Name: screen_shares screen_shares_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.screen_shares
    ADD CONSTRAINT screen_shares_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.live_sessions(id) ON DELETE CASCADE;


--
-- Name: screen_shares screen_shares_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.screen_shares
    ADD CONSTRAINT screen_shares_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: session_analytics session_analytics_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_analytics
    ADD CONSTRAINT session_analytics_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.live_sessions(id) ON DELETE CASCADE;


--
-- Name: session_chat_messages session_chat_messages_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_chat_messages
    ADD CONSTRAINT session_chat_messages_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: session_chat_messages session_chat_messages_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_chat_messages
    ADD CONSTRAINT session_chat_messages_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: session_chat_messages session_chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_chat_messages
    ADD CONSTRAINT session_chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.live_sessions(id) ON DELETE CASCADE;


--
-- Name: session_chat_messages session_chat_messages_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_chat_messages
    ADD CONSTRAINT session_chat_messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: session_participants session_participants_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_participants
    ADD CONSTRAINT session_participants_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.live_sessions(id) ON DELETE CASCADE;


--
-- Name: session_participants session_participants_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_participants
    ADD CONSTRAINT session_participants_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: session_recordings session_recordings_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_recordings
    ADD CONSTRAINT session_recordings_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.live_sessions(id) ON DELETE CASCADE;


--
-- Name: sessions sessions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: shared_files shared_files_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shared_files
    ADD CONSTRAINT shared_files_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: shared_files shared_files_parent_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shared_files
    ADD CONSTRAINT shared_files_parent_file_id_fkey FOREIGN KEY (parent_file_id) REFERENCES public.shared_files(id) ON DELETE CASCADE;


--
-- Name: shared_files shared_files_room_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shared_files
    ADD CONSTRAINT shared_files_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.study_rooms(id) ON DELETE CASCADE;


--
-- Name: shared_files shared_files_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shared_files
    ADD CONSTRAINT shared_files_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: solution_duel_submissions solution_duel_submissions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_duel_submissions
    ADD CONSTRAINT solution_duel_submissions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: solution_steps solution_steps_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_steps
    ADD CONSTRAINT solution_steps_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.chat_messages(id) ON DELETE CASCADE;


--
-- Name: streak_daily_log streak_daily_log_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streak_daily_log
    ADD CONSTRAINT streak_daily_log_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: streak_tracking streak_tracking_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streak_tracking
    ADD CONSTRAINT streak_tracking_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: streak_tracking streak_tracking_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streak_tracking
    ADD CONSTRAINT streak_tracking_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: streaks streaks_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streaks
    ADD CONSTRAINT streaks_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: streaks streaks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streaks
    ADD CONSTRAINT streaks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_abilities student_abilities_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_abilities
    ADD CONSTRAINT student_abilities_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: student_abilities student_abilities_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_abilities
    ADD CONSTRAINT student_abilities_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_answers student_answers_exam_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_answers
    ADD CONSTRAINT student_answers_exam_session_id_fkey FOREIGN KEY (exam_session_id) REFERENCES public.exam_sessions(id) ON DELETE CASCADE;


--
-- Name: student_answers student_answers_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_answers
    ADD CONSTRAINT student_answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: student_engagement_signals student_engagement_signals_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_engagement_signals
    ADD CONSTRAINT student_engagement_signals_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: student_goals student_goals_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_goals
    ADD CONSTRAINT student_goals_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: student_goals student_goals_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_goals
    ADD CONSTRAINT student_goals_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_grades student_grades_student_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_grades
    ADD CONSTRAINT student_grades_student_user_id_fkey FOREIGN KEY (student_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_grades student_grades_teacher_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_grades
    ADD CONSTRAINT student_grades_teacher_user_id_fkey FOREIGN KEY (teacher_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_knowledge_states student_knowledge_states_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_knowledge_states
    ADD CONSTRAINT student_knowledge_states_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: student_knowledge_states student_knowledge_states_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_knowledge_states
    ADD CONSTRAINT student_knowledge_states_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_learning_profiles student_learning_profiles_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_learning_profiles
    ADD CONSTRAINT student_learning_profiles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: student_learning_profiles student_learning_profiles_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_learning_profiles
    ADD CONSTRAINT student_learning_profiles_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_nano_skill_mastery student_nano_skill_mastery_nano_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_nano_skill_mastery
    ADD CONSTRAINT student_nano_skill_mastery_nano_skill_id_fkey FOREIGN KEY (nano_skill_id) REFERENCES public.nano_skills(id) ON DELETE CASCADE;


--
-- Name: student_nano_skill_mastery student_nano_skill_mastery_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_nano_skill_mastery
    ADD CONSTRAINT student_nano_skill_mastery_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: student_nano_skill_mastery student_nano_skill_mastery_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_nano_skill_mastery
    ADD CONSTRAINT student_nano_skill_mastery_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_profiles student_profiles_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: student_profiles student_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_question_flags student_question_flags_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_question_flags
    ADD CONSTRAINT student_question_flags_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: student_question_flags student_question_flags_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_question_flags
    ADD CONSTRAINT student_question_flags_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_question_responses student_question_responses_exam_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_question_responses
    ADD CONSTRAINT student_question_responses_exam_session_id_fkey FOREIGN KEY (exam_session_id) REFERENCES public.exam_sessions(id) ON DELETE CASCADE;


--
-- Name: student_question_responses student_question_responses_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_question_responses
    ADD CONSTRAINT student_question_responses_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.osym_questions(question_id) ON DELETE CASCADE;


--
-- Name: student_question_responses student_question_responses_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_question_responses
    ADD CONSTRAINT student_question_responses_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_reviews student_reviews_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_reviews
    ADD CONSTRAINT student_reviews_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE CASCADE;


--
-- Name: student_reviews student_reviews_dormitory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_reviews
    ADD CONSTRAINT student_reviews_dormitory_id_fkey FOREIGN KEY (dormitory_id) REFERENCES public.dormitory_info(id) ON DELETE CASCADE;


--
-- Name: student_reviews student_reviews_moderated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_reviews
    ADD CONSTRAINT student_reviews_moderated_by_fkey FOREIGN KEY (moderated_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: student_reviews student_reviews_university_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_reviews
    ADD CONSTRAINT student_reviews_university_id_fkey FOREIGN KEY (university_id) REFERENCES public.universities(id) ON DELETE CASCADE;


--
-- Name: student_reviews student_reviews_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_reviews
    ADD CONSTRAINT student_reviews_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: study_plans study_plans_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_plans
    ADD CONSTRAINT study_plans_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: study_plans study_plans_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_plans
    ADD CONSTRAINT study_plans_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: study_rooms study_rooms_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_rooms
    ADD CONSTRAINT study_rooms_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: study_rooms study_rooms_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_rooms
    ADD CONSTRAINT study_rooms_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: study_sessions study_sessions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_sessions
    ADD CONSTRAINT study_sessions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: study_sessions study_sessions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_sessions
    ADD CONSTRAINT study_sessions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.learning_path_student_profiles(student_id) ON DELETE CASCADE;


--
-- Name: sub_problems sub_problems_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sub_problems
    ADD CONSTRAINT sub_problems_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.reasoning_sessions(id) ON DELETE CASCADE;


--
-- Name: teacher_availability teacher_availability_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_availability
    ADD CONSTRAINT teacher_availability_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teacher_pool_profiles(id) ON DELETE CASCADE;


--
-- Name: teacher_certifications teacher_certifications_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_certifications
    ADD CONSTRAINT teacher_certifications_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teacher_pool_profiles(id) ON DELETE CASCADE;


--
-- Name: teacher_certifications teacher_certifications_verified_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_certifications
    ADD CONSTRAINT teacher_certifications_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: teacher_classroom_students teacher_classroom_students_classroom_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_classroom_students
    ADD CONSTRAINT teacher_classroom_students_classroom_id_fkey FOREIGN KEY (classroom_id) REFERENCES public.teacher_classrooms(id) ON DELETE CASCADE;


--
-- Name: teacher_expertise teacher_expertise_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_expertise
    ADD CONSTRAINT teacher_expertise_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teacher_pool_profiles(id) ON DELETE CASCADE;


--
-- Name: teacher_pool_profiles teacher_pool_profiles_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_pool_profiles
    ADD CONSTRAINT teacher_pool_profiles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: teacher_pool_profiles teacher_pool_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_pool_profiles
    ADD CONSTRAINT teacher_pool_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: teacher_pool_profiles teacher_pool_profiles_verified_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_pool_profiles
    ADD CONSTRAINT teacher_pool_profiles_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: teacher_profiles teacher_profiles_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_profiles
    ADD CONSTRAINT teacher_profiles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: teacher_profiles teacher_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_profiles
    ADD CONSTRAINT teacher_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: teacher_reviews teacher_reviews_appointment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_reviews
    ADD CONSTRAINT teacher_reviews_appointment_id_fkey FOREIGN KEY (appointment_id) REFERENCES public.appointments(id) ON DELETE CASCADE;


--
-- Name: teacher_reviews teacher_reviews_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_reviews
    ADD CONSTRAINT teacher_reviews_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: teacher_reviews teacher_reviews_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_reviews
    ADD CONSTRAINT teacher_reviews_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teacher_pool_profiles(id) ON DELETE CASCADE;


--
-- Name: teacher_statistics teacher_statistics_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_statistics
    ADD CONSTRAINT teacher_statistics_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teacher_pool_profiles(id) ON DELETE CASCADE;


--
-- Name: topic_completions topic_completions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_completions
    ADD CONSTRAINT topic_completions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: topic_completions topic_completions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_completions
    ADD CONSTRAINT topic_completions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.learning_path_student_profiles(student_id) ON DELETE CASCADE;


--
-- Name: topic_hierarchy topic_hierarchy_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_hierarchy
    ADD CONSTRAINT topic_hierarchy_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.topic_hierarchy(id) ON DELETE CASCADE;


--
-- Name: topic_prerequisites topic_prerequisites_prereq_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_prerequisites
    ADD CONSTRAINT topic_prerequisites_prereq_id_fkey FOREIGN KEY (prereq_id) REFERENCES public.topic_hierarchy(id) ON DELETE CASCADE;


--
-- Name: topic_prerequisites topic_prerequisites_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_prerequisites
    ADD CONSTRAINT topic_prerequisites_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topic_hierarchy(id) ON DELETE CASCADE;


--
-- Name: topic_progress topic_progress_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_progress
    ADD CONSTRAINT topic_progress_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: topic_progress topic_progress_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_progress
    ADD CONSTRAINT topic_progress_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.learning_path_student_profiles(student_id) ON DELETE CASCADE;


--
-- Name: university_programs university_programs_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.university_programs
    ADD CONSTRAINT university_programs_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE CASCADE;


--
-- Name: university_programs university_programs_university_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.university_programs
    ADD CONSTRAINT university_programs_university_id_fkey FOREIGN KEY (university_id) REFERENCES public.universities(id) ON DELETE CASCADE;


--
-- Name: university_statistics university_statistics_university_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.university_statistics
    ADD CONSTRAINT university_statistics_university_id_fkey FOREIGN KEY (university_id) REFERENCES public.universities(id) ON DELETE CASCADE;


--
-- Name: user_achievements user_achievements_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: user_achievements user_achievements_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_badges user_badges_badge_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_badges
    ADD CONSTRAINT user_badges_badge_id_fkey FOREIGN KEY (badge_id) REFERENCES public.badges(id) ON DELETE CASCADE;


--
-- Name: user_badges user_badges_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_badges
    ADD CONSTRAINT user_badges_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: user_badges user_badges_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_badges
    ADD CONSTRAINT user_badges_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_theta user_theta_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_theta
    ADD CONSTRAINT user_theta_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: user_university_preferences user_university_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_university_preferences
    ADD CONSTRAINT user_university_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: users users_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: video_analytics_summary video_analytics_summary_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_analytics_summary
    ADD CONSTRAINT video_analytics_summary_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: video_analytics video_analytics_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_analytics
    ADD CONSTRAINT video_analytics_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: video_analytics video_analytics_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_analytics
    ADD CONSTRAINT video_analytics_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.video_solutions(id) ON DELETE CASCADE;


--
-- Name: video_bookmarks video_bookmarks_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_bookmarks
    ADD CONSTRAINT video_bookmarks_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.video_watch_sessions(id) ON DELETE CASCADE;


--
-- Name: video_bookmarks video_bookmarks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_bookmarks
    ADD CONSTRAINT video_bookmarks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: video_completion_milestones video_completion_milestones_badge_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_completion_milestones
    ADD CONSTRAINT video_completion_milestones_badge_id_fkey FOREIGN KEY (badge_id) REFERENCES public.user_badges(id) ON DELETE CASCADE;


--
-- Name: video_completion_milestones video_completion_milestones_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_completion_milestones
    ADD CONSTRAINT video_completion_milestones_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: video_notes video_notes_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_notes
    ADD CONSTRAINT video_notes_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.video_watch_sessions(id) ON DELETE CASCADE;


--
-- Name: video_notes video_notes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_notes
    ADD CONSTRAINT video_notes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: video_solutions video_solutions_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_solutions
    ADD CONSTRAINT video_solutions_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: video_solutions video_solutions_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_solutions
    ADD CONSTRAINT video_solutions_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question_bank(id) ON DELETE CASCADE;


--
-- Name: video_solutions video_solutions_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_solutions
    ADD CONSTRAINT video_solutions_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: video_transcripts video_transcripts_manually_edited_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_transcripts
    ADD CONSTRAINT video_transcripts_manually_edited_by_fkey FOREIGN KEY (manually_edited_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: video_transcripts video_transcripts_verified_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_transcripts
    ADD CONSTRAINT video_transcripts_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: video_transcripts video_transcripts_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_transcripts
    ADD CONSTRAINT video_transcripts_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.video_solutions(id) ON DELETE CASCADE;


--
-- Name: video_watch_sessions video_watch_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_watch_sessions
    ADD CONSTRAINT video_watch_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: weekly_goals weekly_goals_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_goals
    ADD CONSTRAINT weekly_goals_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.study_plans(id) ON DELETE CASCADE;


--
-- Name: weekly_progress weekly_progress_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_progress
    ADD CONSTRAINT weekly_progress_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: weekly_progress weekly_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_progress
    ADD CONSTRAINT weekly_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: weekly_reports weekly_reports_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_reports
    ADD CONSTRAINT weekly_reports_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: whiteboard_equations whiteboard_equations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.whiteboard_equations
    ADD CONSTRAINT whiteboard_equations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: whiteboard_equations whiteboard_equations_whiteboard_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.whiteboard_equations
    ADD CONSTRAINT whiteboard_equations_whiteboard_id_fkey FOREIGN KEY (whiteboard_id) REFERENCES public.whiteboard_sessions(id) ON DELETE CASCADE;


--
-- Name: whiteboard_sessions whiteboard_sessions_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.whiteboard_sessions
    ADD CONSTRAINT whiteboard_sessions_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.live_sessions(id) ON DELETE CASCADE;


--
-- Name: whiteboard_strokes whiteboard_strokes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.whiteboard_strokes
    ADD CONSTRAINT whiteboard_strokes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: whiteboard_strokes whiteboard_strokes_whiteboard_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.whiteboard_strokes
    ADD CONSTRAINT whiteboard_strokes_whiteboard_id_fkey FOREIGN KEY (whiteboard_id) REFERENCES public.whiteboard_sessions(id) ON DELETE CASCADE;


--
-- Name: xp_transactions xp_transactions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.xp_transactions
    ADD CONSTRAINT xp_transactions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: xp_transactions xp_transactions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.xp_transactions
    ADD CONSTRAINT xp_transactions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: yks_exam_goals yks_exam_goals_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.yks_exam_goals
    ADD CONSTRAINT yks_exam_goals_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: yks_exam_goals yks_exam_goals_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.yks_exam_goals
    ADD CONSTRAINT yks_exam_goals_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: zpd_history zpd_history_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zpd_history
    ADD CONSTRAINT zpd_history_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: zpd_history zpd_history_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zpd_history
    ADD CONSTRAINT zpd_history_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: api_keys; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

--
-- Name: audit_logs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

--
-- Name: bkt_states; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.bkt_states ENABLE ROW LEVEL SECURITY;

--
-- Name: chat_analytics; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.chat_analytics ENABLE ROW LEVEL SECURITY;

--
-- Name: chat_sessions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;

--
-- Name: classrooms; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.classrooms ENABLE ROW LEVEL SECURITY;

--
-- Name: coaching_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.coaching_events ENABLE ROW LEVEL SECURITY;

--
-- Name: daily_plans; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.daily_plans ENABLE ROW LEVEL SECURITY;

--
-- Name: daily_quests; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.daily_quests ENABLE ROW LEVEL SECURITY;

--
-- Name: data_processing_agreements; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.data_processing_agreements ENABLE ROW LEVEL SECURITY;

--
-- Name: duel_ratings; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.duel_ratings ENABLE ROW LEVEL SECURITY;

--
-- Name: dungeon_progress; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.dungeon_progress ENABLE ROW LEVEL SECURITY;

--
-- Name: eba_video_recommendations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.eba_video_recommendations ENABLE ROW LEVEL SECURITY;

--
-- Name: eba_video_usage; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.eba_video_usage ENABLE ROW LEVEL SECURITY;

--
-- Name: eba_video_watches; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.eba_video_watches ENABLE ROW LEVEL SECURITY;

--
-- Name: exam_sessions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.exam_sessions ENABLE ROW LEVEL SECURITY;

--
-- Name: forum_questions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.forum_questions ENABLE ROW LEVEL SECURITY;

--
-- Name: fsrs_cards; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.fsrs_cards ENABLE ROW LEVEL SECURITY;

--
-- Name: fsrs_reviews; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.fsrs_reviews ENABLE ROW LEVEL SECURITY;

--
-- Name: fsrs_schedules; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.fsrs_schedules ENABLE ROW LEVEL SECURITY;

--
-- Name: fsrs_student_profiles; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.fsrs_student_profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: fsrs_study_sessions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.fsrs_study_sessions ENABLE ROW LEVEL SECURITY;

--
-- Name: fsrs_subject_stats; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.fsrs_subject_stats ENABLE ROW LEVEL SECURITY;

--
-- Name: image_uploads; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.image_uploads ENABLE ROW LEVEL SECURITY;

--
-- Name: invoices; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.invoices ENABLE ROW LEVEL SECURITY;

--
-- Name: khan_oauth_tokens; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.khan_oauth_tokens ENABLE ROW LEVEL SECURITY;

--
-- Name: kiro2_cat_sessions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.kiro2_cat_sessions ENABLE ROW LEVEL SECURITY;

--
-- Name: kiro2_learning_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.kiro2_learning_events ENABLE ROW LEVEL SECURITY;

--
-- Name: kvkk_consents; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.kvkk_consents ENABLE ROW LEVEL SECURITY;

--
-- Name: kvkk_data_export_requests; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.kvkk_data_export_requests ENABLE ROW LEVEL SECURITY;

--
-- Name: league_history; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.league_history ENABLE ROW LEVEL SECURITY;

--
-- Name: league_memberships; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.league_memberships ENABLE ROW LEVEL SECURITY;

--
-- Name: learning_analytics; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.learning_analytics ENABLE ROW LEVEL SECURITY;

--
-- Name: learning_path_student_profiles; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.learning_path_student_profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: learning_paths; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.learning_paths ENABLE ROW LEVEL SECURITY;

--
-- Name: learning_progress_daily; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.learning_progress_daily ENABLE ROW LEVEL SECURITY;

--
-- Name: manipulative_activities; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.manipulative_activities ENABLE ROW LEVEL SECURITY;

--
-- Name: manipulative_progress; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.manipulative_progress ENABLE ROW LEVEL SECURITY;

--
-- Name: notifications; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

--
-- Name: oba_challenge_progress; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.oba_challenge_progress ENABLE ROW LEVEL SECURITY;

--
-- Name: oba_uyeler; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.oba_uyeler ENABLE ROW LEVEL SECURITY;

--
-- Name: org_memberships; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.org_memberships ENABLE ROW LEVEL SECURITY;

--
-- Name: organization_licenses; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.organization_licenses ENABLE ROW LEVEL SECURITY;

--
-- Name: organizations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

--
-- Name: osb_settings; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.osb_settings ENABLE ROW LEVEL SECURITY;

--
-- Name: parent_child; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.parent_child ENABLE ROW LEVEL SECURITY;

--
-- Name: parent_link_codes; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.parent_link_codes ENABLE ROW LEVEL SECURITY;

--
-- Name: parent_notifications; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.parent_notifications ENABLE ROW LEVEL SECURITY;

--
-- Name: parent_social_settings; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.parent_social_settings ENABLE ROW LEVEL SECURITY;

--
-- Name: performance_history; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.performance_history ENABLE ROW LEVEL SECURITY;

--
-- Name: point_transactions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.point_transactions ENABLE ROW LEVEL SECURITY;

--
-- Name: pomodoro_participants; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.pomodoro_participants ENABLE ROW LEVEL SECURITY;

--
-- Name: quiz_submissions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.quiz_submissions ENABLE ROW LEVEL SECURITY;

--
-- Name: realm_progress; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.realm_progress ENABLE ROW LEVEL SECURITY;

--
-- Name: refresh_tokens; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.refresh_tokens ENABLE ROW LEVEL SECURITY;

--
-- Name: sessions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;

--
-- Name: solution_duel_submissions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.solution_duel_submissions ENABLE ROW LEVEL SECURITY;

--
-- Name: streak_daily_log; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.streak_daily_log ENABLE ROW LEVEL SECURITY;

--
-- Name: streak_tracking; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.streak_tracking ENABLE ROW LEVEL SECURITY;

--
-- Name: streaks; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.streaks ENABLE ROW LEVEL SECURITY;

--
-- Name: student_abilities; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.student_abilities ENABLE ROW LEVEL SECURITY;

--
-- Name: student_engagement_signals; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.student_engagement_signals ENABLE ROW LEVEL SECURITY;

--
-- Name: student_goals; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.student_goals ENABLE ROW LEVEL SECURITY;

--
-- Name: student_knowledge_states; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.student_knowledge_states ENABLE ROW LEVEL SECURITY;

--
-- Name: student_learning_profiles; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.student_learning_profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: student_nano_skill_mastery; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.student_nano_skill_mastery ENABLE ROW LEVEL SECURITY;

--
-- Name: study_plans; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.study_plans ENABLE ROW LEVEL SECURITY;

--
-- Name: study_rooms; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.study_rooms ENABLE ROW LEVEL SECURITY;

--
-- Name: study_sessions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.study_sessions ENABLE ROW LEVEL SECURITY;

--
-- Name: teacher_pool_profiles; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.teacher_pool_profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: api_keys tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.api_keys USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: audit_logs tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.audit_logs USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: bkt_states tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.bkt_states USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: chat_analytics tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.chat_analytics USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: chat_sessions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.chat_sessions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: classrooms tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.classrooms USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: coaching_events tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.coaching_events USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: daily_plans tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.daily_plans USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: daily_quests tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.daily_quests USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: data_processing_agreements tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.data_processing_agreements USING (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((organization_id)::text = current_setting('app.current_org_id'::text, true)))) WITH CHECK (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((organization_id)::text = current_setting('app.current_org_id'::text, true))));


--
-- Name: duel_ratings tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.duel_ratings USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: dungeon_progress tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.dungeon_progress USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: eba_video_recommendations tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.eba_video_recommendations USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: eba_video_usage tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.eba_video_usage USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: eba_video_watches tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.eba_video_watches USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: exam_sessions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.exam_sessions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: forum_questions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.forum_questions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: fsrs_cards tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.fsrs_cards USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: fsrs_reviews tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.fsrs_reviews USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: fsrs_schedules tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.fsrs_schedules USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: fsrs_student_profiles tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.fsrs_student_profiles USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: fsrs_study_sessions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.fsrs_study_sessions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: fsrs_subject_stats tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.fsrs_subject_stats USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: image_uploads tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.image_uploads USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: invoices tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.invoices USING (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((organization_id)::text = current_setting('app.current_org_id'::text, true)))) WITH CHECK (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((organization_id)::text = current_setting('app.current_org_id'::text, true))));


--
-- Name: khan_oauth_tokens tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.khan_oauth_tokens USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: kiro2_cat_sessions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.kiro2_cat_sessions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: kiro2_learning_events tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.kiro2_learning_events USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: kvkk_consents tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.kvkk_consents USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: kvkk_data_export_requests tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.kvkk_data_export_requests USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: league_history tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.league_history USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: league_memberships tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.league_memberships USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: learning_analytics tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.learning_analytics USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: learning_path_student_profiles tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.learning_path_student_profiles USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: learning_paths tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.learning_paths USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: learning_progress_daily tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.learning_progress_daily USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: manipulative_activities tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.manipulative_activities USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: manipulative_progress tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.manipulative_progress USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: notifications tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.notifications USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: oba_challenge_progress tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.oba_challenge_progress USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: oba_uyeler tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.oba_uyeler USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: org_memberships tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.org_memberships USING (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((organization_id)::text = current_setting('app.current_org_id'::text, true)))) WITH CHECK (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((organization_id)::text = current_setting('app.current_org_id'::text, true))));


--
-- Name: organization_licenses tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.organization_licenses USING (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((organization_id)::text = current_setting('app.current_org_id'::text, true)))) WITH CHECK (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((organization_id)::text = current_setting('app.current_org_id'::text, true))));


--
-- Name: organizations tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.organizations USING (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((id)::text = current_setting('app.current_org_id'::text, true)))) WITH CHECK (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((id)::text = current_setting('app.current_org_id'::text, true))));


--
-- Name: osb_settings tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.osb_settings USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: parent_child tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.parent_child USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: parent_link_codes tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.parent_link_codes USING (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((organization_id)::text = current_setting('app.current_org_id'::text, true)))) WITH CHECK (((current_setting('app.current_org_id'::text, true) IS NULL) OR (current_setting('app.current_org_id'::text, true) = ''::text) OR ((organization_id)::text = current_setting('app.current_org_id'::text, true))));


--
-- Name: parent_notifications tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.parent_notifications USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: parent_social_settings tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.parent_social_settings USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: performance_history tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.performance_history USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: point_transactions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.point_transactions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: pomodoro_participants tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.pomodoro_participants USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: quiz_submissions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.quiz_submissions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: realm_progress tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.realm_progress USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: refresh_tokens tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.refresh_tokens USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: sessions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.sessions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: solution_duel_submissions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.solution_duel_submissions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: streak_daily_log tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.streak_daily_log USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: streak_tracking tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.streak_tracking USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: streaks tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.streaks USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: student_abilities tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.student_abilities USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: student_engagement_signals tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.student_engagement_signals USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: student_goals tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.student_goals USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: student_knowledge_states tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.student_knowledge_states USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: student_learning_profiles tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.student_learning_profiles USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: student_nano_skill_mastery tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.student_nano_skill_mastery USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: study_plans tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.study_plans USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: study_rooms tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.study_rooms USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: study_sessions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.study_sessions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: teacher_pool_profiles tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.teacher_pool_profiles USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: topic_completions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.topic_completions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: topic_progress tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.topic_progress USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: user_achievements tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.user_achievements USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: user_badges tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.user_badges USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: user_theta tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.user_theta USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: weekly_progress tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.weekly_progress USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: xp_transactions tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.xp_transactions USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: yks_exam_goals tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.yks_exam_goals USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: zpd_history tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY tenant_isolation ON public.zpd_history USING (((organization_id)::text = current_setting('app.current_org_id'::text, true))) WITH CHECK (((organization_id)::text = current_setting('app.current_org_id'::text, true)));


--
-- Name: topic_completions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.topic_completions ENABLE ROW LEVEL SECURITY;

--
-- Name: topic_progress; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.topic_progress ENABLE ROW LEVEL SECURITY;

--
-- Name: user_achievements; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_achievements ENABLE ROW LEVEL SECURITY;

--
-- Name: user_badges; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_badges ENABLE ROW LEVEL SECURITY;

--
-- Name: user_theta; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_theta ENABLE ROW LEVEL SECURITY;

--
-- Name: weekly_progress; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.weekly_progress ENABLE ROW LEVEL SECURITY;

--
-- Name: xp_transactions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.xp_transactions ENABLE ROW LEVEL SECURITY;

--
-- Name: yks_exam_goals; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.yks_exam_goals ENABLE ROW LEVEL SECURITY;

--
-- Name: zpd_history; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.zpd_history ENABLE ROW LEVEL SECURITY;

--
-- PostgreSQL database dump complete
--



-- baseline sonrasi: alembic kendi oturumunda alembic_version'a niteliksiz
-- erisiyor; pg_dump'in bosalttigi search_path'i geri ver.
SELECT pg_catalog.set_config('search_path', 'public', false);
