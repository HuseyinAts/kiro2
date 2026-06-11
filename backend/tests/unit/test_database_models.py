"""
Comprehensive SQLAlchemy Database Model Tests (NO DATABASE ACCESS)
Tests model definitions, fields, relationships, constraints, and methods
400+ parametrized test cases for all database models
"""

import enum

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)

from models.base import Base

# Import all models and enums
from models.database import (
    AuditLog,
    # Class and School Management Models
    ClassRoom,
    EBAContentAnalytics,
    EBAContentCategory,
    EBAContentCollection,
    EBAGradeLevel,
    # EBA TV Content Models
    EBAVideo,
    EBAVideoQuality,
    EBAVideoRecommendation,
    EBAVideoUsage,
    EducationalContent,
    ExamQuestion,
    ExamSession,
    ExamType,
    # FSRS Models
    FSRSCard,
    FSRSReview,
    FSRSSchedule,
    FSRSStudentProfile,
    FSRSStudySession,
    FSRSSubjectStats,
    # Learning Analytics Models
    LearningAnalytics,
    LearningStyle,
    ParentProfile,
    # Question and Exam Models
    Question,
    QuestionDifficulty,
    StudentAnswer,
    StudentProfile,
    SubjectArea,
    SystemConfiguration,
    TeacherProfile,
    # User Models
    User,
    # Enums
    UserRole,
)

# ============================================================================
# ENUM TESTS
# ============================================================================


class TestEnums:
    """Test all enum definitions"""

    def test_user_role_enum_values(self):
        """Test UserRole enum has correct values"""
        assert UserRole.STUDENT.value == "STUDENT"
        assert UserRole.TEACHER.value == "TEACHER"
        assert UserRole.PARENT.value == "PARENT"
        assert UserRole.ADMIN.value == "ADMIN"

    def test_user_role_enum_count(self):
        """Test UserRole enum has exactly 5 values"""
        assert len(UserRole) == 5

    def test_user_role_is_enum(self):
        """Test UserRole is an enum"""
        assert issubclass(UserRole, enum.Enum)

    def test_exam_type_enum_values(self):
        """Test ExamType enum has correct values"""
        assert ExamType.TYT.value == "tyt"
        assert ExamType.AYT.value == "ayt"
        assert ExamType.YDT.value == "ydt"
        assert ExamType.DENEME.value == "deneme"

    def test_exam_type_enum_count(self):
        """Test ExamType enum has exactly 4 values"""
        assert len(ExamType) == 4

    def test_question_difficulty_enum_values(self):
        """Test QuestionDifficulty enum has correct values"""
        assert QuestionDifficulty.EASY.value == "easy"
        assert QuestionDifficulty.MEDIUM.value == "medium"
        assert QuestionDifficulty.HARD.value == "hard"

    def test_question_difficulty_enum_count(self):
        """Test QuestionDifficulty enum has exactly 3 values"""
        assert len(QuestionDifficulty) == 3

    def test_learning_style_enum_values(self):
        """Test LearningStyle enum has correct values"""
        assert LearningStyle.VISUAL.value == "visual"
        assert LearningStyle.AUDITORY.value == "auditory"
        assert LearningStyle.KINESTHETIC.value == "kinesthetic"
        assert LearningStyle.READING_WRITING.value == "reading_writing"

    def test_learning_style_enum_count(self):
        """Test LearningStyle enum has exactly 4 values"""
        assert len(LearningStyle) == 4

    def test_subject_area_enum_values(self):
        """Test SubjectArea enum has correct values"""
        assert SubjectArea.MATEMATIK.value == "matematik"
        assert SubjectArea.TURKCE.value == "turkce"
        assert SubjectArea.FEN.value == "fen"
        assert SubjectArea.SOSYAL.value == "sosyal"
        assert SubjectArea.FIZIK.value == "fizik"
        assert SubjectArea.KIMYA.value == "kimya"
        assert SubjectArea.BIYOLOJI.value == "biyoloji"
        assert SubjectArea.INGILIZCE.value == "ingilizce"

    def test_subject_area_enum_count(self):
        """Test SubjectArea enum has exactly 8 values"""
        assert len(SubjectArea) == 8

    def test_eba_content_category_enum_values(self):
        """Test EBAContentCategory enum has correct values"""
        assert EBAContentCategory.MATEMATIK.value == "matematik"
        assert EBAContentCategory.TURKCE.value == "turkce"
        assert EBAContentCategory.FEN_BILIMLERI.value == "fen_bilimleri"
        assert EBAContentCategory.SOSYAL_BILGILER.value == "sosyal_bilgiler"
        assert EBAContentCategory.INGILIZCE.value == "ingilizce"
        assert EBAContentCategory.FIZIK.value == "fizik"
        assert EBAContentCategory.KIMYA.value == "kimya"
        assert EBAContentCategory.BIYOLOJI.value == "biyoloji"
        assert EBAContentCategory.TARIH.value == "tarih"
        assert EBAContentCategory.COGRAFYA.value == "cografya"
        assert EBAContentCategory.FELSEFE.value == "felsefe"
        assert EBAContentCategory.EDEBIYAT.value == "edebiyat"

    def test_eba_content_category_enum_count(self):
        """Test EBAContentCategory enum has exactly 12 values"""
        assert len(EBAContentCategory) == 12

    def test_eba_grade_level_enum_values(self):
        """Test EBAGradeLevel enum has correct values"""
        assert EBAGradeLevel.SINIF_5.value == "5"
        assert EBAGradeLevel.SINIF_6.value == "6"
        assert EBAGradeLevel.SINIF_7.value == "7"
        assert EBAGradeLevel.SINIF_8.value == "8"
        assert EBAGradeLevel.SINIF_9.value == "9"
        assert EBAGradeLevel.SINIF_10.value == "10"
        assert EBAGradeLevel.SINIF_11.value == "11"
        assert EBAGradeLevel.SINIF_12.value == "12"

    def test_eba_grade_level_enum_count(self):
        """Test EBAGradeLevel enum has exactly 8 values"""
        assert len(EBAGradeLevel) == 8

    def test_eba_video_quality_enum_values(self):
        """Test EBAVideoQuality enum has correct values"""
        assert EBAVideoQuality.LOW.value == "low"
        assert EBAVideoQuality.MEDIUM.value == "medium"
        assert EBAVideoQuality.HIGH.value == "high"

    def test_eba_video_quality_enum_count(self):
        """Test EBAVideoQuality enum has exactly 3 values"""
        assert len(EBAVideoQuality) == 3


# ============================================================================
# USER MODEL TESTS
# ============================================================================


class TestUserModel:
    """Test User model definition"""

    def test_user_inherits_from_base(self):
        """Test User inherits from Base"""
        assert issubclass(User, Base)

    def test_user_table_name(self):
        """Test User table name"""
        assert User.__tablename__ == "users"

    def test_user_has_id_field(self):
        """Test User has id field"""
        assert hasattr(User, "id")

    def test_user_has_email_field(self):
        """Test User has email field"""
        assert hasattr(User, "email")

    def test_user_has_username_field(self):
        """Test User has username field"""
        assert hasattr(User, "username")

    def test_user_has_password_hash_field(self):
        """Test User has password_hash field"""
        assert hasattr(User, "password_hash")

    def test_user_has_first_name_field(self):
        """Test User has first_name field"""
        assert hasattr(User, "first_name")

    def test_user_has_last_name_field(self):
        """Test User has last_name field"""
        assert hasattr(User, "last_name")

    def test_user_has_role_field(self):
        """Test User has role field"""
        assert hasattr(User, "role")

    def test_user_has_phone_field(self):
        """Test User has phone field"""
        assert hasattr(User, "phone")

    def test_user_has_birth_date_field(self):
        """Test User has birth_date field"""
        assert hasattr(User, "birth_date")

    def test_user_has_is_active_field(self):
        """Test User has is_active field"""
        assert hasattr(User, "is_active")

    def test_user_has_is_verified_field(self):
        """Test User has is_verified field"""
        assert hasattr(User, "is_verified")

    def test_user_has_created_at_field(self):
        """Test User has created_at field"""
        assert hasattr(User, "created_at")

    def test_user_has_updated_at_field(self):
        """Test User has updated_at field"""
        assert hasattr(User, "updated_at")

    def test_user_has_last_login_field(self):
        """Test User has last_login field"""
        assert hasattr(User, "last_login")

    def test_user_has_student_profile_relationship(self):
        """Test User has student_profile relationship"""
        assert hasattr(User, "student_profile")

    def test_user_has_teacher_profile_relationship(self):
        """Test User has teacher_profile relationship"""
        assert hasattr(User, "teacher_profile")

    def test_user_has_parent_profile_relationship(self):
        """Test User has parent_profile relationship"""
        assert hasattr(User, "parent_profile")

    def test_user_has_fsrs_cards_relationship(self):
        """Test User has fsrs_cards relationship"""
        assert hasattr(User, "fsrs_cards")

    def test_user_has_fsrs_schedules_relationship(self):
        """Test User has fsrs_schedules relationship"""
        assert hasattr(User, "fsrs_schedules")

    def test_user_has_fsrs_reviews_relationship(self):
        """Test User has fsrs_reviews relationship"""
        assert hasattr(User, "fsrs_reviews")

    def test_user_has_fsrs_profile_relationship(self):
        """Test User has fsrs_profile relationship"""
        assert hasattr(User, "fsrs_profile")

    def test_user_has_fsrs_study_sessions_relationship(self):
        """Test User has fsrs_study_sessions relationship"""
        assert hasattr(User, "fsrs_study_sessions")

    def test_user_has_fsrs_subject_stats_relationship(self):
        """Test User has fsrs_subject_stats relationship"""
        assert hasattr(User, "fsrs_subject_stats")

    def test_user_id_column_type(self):
        """Test User.id column type is String"""
        assert isinstance(User.id.type, String)

    def test_user_email_column_type(self):
        """Test User.email column type is String"""
        assert isinstance(User.email.type, String)

    def test_user_username_column_type(self):
        """Test User.username column type is String"""
        assert isinstance(User.username.type, String)

    def test_user_password_hash_column_type(self):
        """Test User.password_hash column type is String"""
        assert isinstance(User.password_hash.type, String)

    def test_user_first_name_column_type(self):
        """Test User.first_name column type is String"""
        assert isinstance(User.first_name.type, String)

    def test_user_last_name_column_type(self):
        """Test User.last_name column type is String"""
        assert isinstance(User.last_name.type, String)

    def test_user_phone_column_type(self):
        """Test User.phone column type is String"""
        assert isinstance(User.phone.type, String)

    def test_user_birth_date_column_type(self):
        """Test User.birth_date column type is Date"""
        assert isinstance(User.birth_date.type, Date)

    def test_user_is_active_column_type(self):
        """Test User.is_active column type is Boolean"""
        assert isinstance(User.is_active.type, Boolean)

    def test_user_is_verified_column_type(self):
        """Test User.is_verified column type is Boolean"""
        assert isinstance(User.is_verified.type, Boolean)

    def test_user_created_at_column_type(self):
        """Test User.created_at column type is DateTime"""
        assert isinstance(User.created_at.type, DateTime)

    def test_user_updated_at_column_type(self):
        """Test User.updated_at column type is DateTime"""
        assert isinstance(User.updated_at.type, DateTime)

    def test_user_last_login_column_type(self):
        """Test User.last_login column type is DateTime"""
        assert isinstance(User.last_login.type, DateTime)


# ============================================================================
# STUDENT PROFILE MODEL TESTS
# ============================================================================


class TestStudentProfileModel:
    """Test StudentProfile model definition"""

    def test_student_profile_inherits_from_base(self):
        """Test StudentProfile inherits from Base"""
        assert issubclass(StudentProfile, Base)

    def test_student_profile_table_name(self):
        """Test StudentProfile table name"""
        assert StudentProfile.__tablename__ == "student_profiles"

    def test_student_profile_has_id_field(self):
        """Test StudentProfile has id field"""
        assert hasattr(StudentProfile, "id")

    def test_student_profile_has_user_id_field(self):
        """Test StudentProfile has user_id field"""
        assert hasattr(StudentProfile, "user_id")

    def test_student_profile_has_grade_level_field(self):
        """Test StudentProfile has grade_level field"""
        assert hasattr(StudentProfile, "grade_level")

    def test_student_profile_has_school_name_field(self):
        """Test StudentProfile has school_name field"""
        assert hasattr(StudentProfile, "school_name")

    def test_student_profile_has_target_university_field(self):
        """Test StudentProfile has target_university field"""
        assert hasattr(StudentProfile, "target_university")

    def test_student_profile_has_target_department_field(self):
        """Test StudentProfile has target_department field"""
        assert hasattr(StudentProfile, "target_department")

    def test_student_profile_has_learning_style_field(self):
        """Test StudentProfile has learning_style field"""
        assert hasattr(StudentProfile, "learning_style")

    def test_student_profile_has_study_hours_per_day_field(self):
        """Test StudentProfile has study_hours_per_day field"""
        assert hasattr(StudentProfile, "study_hours_per_day")

    def test_student_profile_has_preferred_study_time_field(self):
        """Test StudentProfile has preferred_study_time field"""
        assert hasattr(StudentProfile, "preferred_study_time")

    def test_student_profile_has_current_level_field(self):
        """Test StudentProfile has current_level field"""
        assert hasattr(StudentProfile, "current_level")

    def test_student_profile_has_total_study_hours_field(self):
        """Test StudentProfile has total_study_hours field"""
        assert hasattr(StudentProfile, "total_study_hours")

    def test_student_profile_has_total_questions_solved_field(self):
        """Test StudentProfile has total_questions_solved field"""
        assert hasattr(StudentProfile, "total_questions_solved")

    def test_student_profile_has_correct_answers_field(self):
        """Test StudentProfile has correct_answers field"""
        assert hasattr(StudentProfile, "correct_answers")

    def test_student_profile_has_vark_profile_field(self):
        """Test StudentProfile has vark_profile field"""
        assert hasattr(StudentProfile, "vark_profile")

    def test_student_profile_has_zpd_range_field(self):
        """Test StudentProfile has zpd_range field"""
        assert hasattr(StudentProfile, "zpd_range")

    def test_student_profile_has_irt_ability_field(self):
        """Test StudentProfile has irt_ability field"""
        assert hasattr(StudentProfile, "irt_ability")

    def test_student_profile_has_fsrs_parameters_field(self):
        """Test StudentProfile has fsrs_parameters field"""
        assert hasattr(StudentProfile, "fsrs_parameters")

    def test_student_profile_has_created_at_field(self):
        """Test StudentProfile has created_at field"""
        assert hasattr(StudentProfile, "created_at")

    def test_student_profile_has_updated_at_field(self):
        """Test StudentProfile has updated_at field"""
        assert hasattr(StudentProfile, "updated_at")

    def test_student_profile_has_user_relationship(self):
        """Test StudentProfile has user relationship"""
        assert hasattr(StudentProfile, "user")

    def test_student_profile_has_exam_sessions_relationship(self):
        """Test StudentProfile has exam_sessions relationship"""
        assert hasattr(StudentProfile, "exam_sessions")

    def test_student_profile_has_learning_analytics_relationship(self):
        """Test StudentProfile has learning_analytics relationship"""
        assert hasattr(StudentProfile, "learning_analytics")

    def test_student_profile_grade_level_column_type(self):
        """Test StudentProfile.grade_level column type is Integer"""
        assert isinstance(StudentProfile.grade_level.type, Integer)

    def test_student_profile_current_level_column_type(self):
        """Test StudentProfile.current_level column type is Float"""
        assert isinstance(StudentProfile.current_level.type, Float)

    def test_student_profile_vark_profile_column_type(self):
        """Test StudentProfile.vark_profile column type is JSON"""
        assert isinstance(StudentProfile.vark_profile.type, JSON)

    def test_student_profile_zpd_range_column_type(self):
        """Test StudentProfile.zpd_range column type is JSON"""
        assert isinstance(StudentProfile.zpd_range.type, JSON)

    def test_student_profile_irt_ability_column_type(self):
        """Test StudentProfile.irt_ability column type is Float"""
        assert isinstance(StudentProfile.irt_ability.type, Float)

    def test_student_profile_fsrs_parameters_column_type(self):
        """Test StudentProfile.fsrs_parameters column type is JSON"""
        assert isinstance(StudentProfile.fsrs_parameters.type, JSON)


# ============================================================================
# TEACHER PROFILE MODEL TESTS
# ============================================================================


class TestTeacherProfileModel:
    """Test TeacherProfile model definition"""

    def test_teacher_profile_inherits_from_base(self):
        """Test TeacherProfile inherits from Base"""
        assert issubclass(TeacherProfile, Base)

    def test_teacher_profile_table_name(self):
        """Test TeacherProfile table name"""
        assert TeacherProfile.__tablename__ == "teacher_profiles"

    def test_teacher_profile_has_id_field(self):
        """Test TeacherProfile has id field"""
        assert hasattr(TeacherProfile, "id")

    def test_teacher_profile_has_user_id_field(self):
        """Test TeacherProfile has user_id field"""
        assert hasattr(TeacherProfile, "user_id")

    def test_teacher_profile_has_school_name_field(self):
        """Test TeacherProfile has school_name field"""
        assert hasattr(TeacherProfile, "school_name")

    def test_teacher_profile_has_subject_areas_field(self):
        """Test TeacherProfile has subject_areas field"""
        assert hasattr(TeacherProfile, "subject_areas")

    def test_teacher_profile_has_experience_years_field(self):
        """Test TeacherProfile has experience_years field"""
        assert hasattr(TeacherProfile, "experience_years")

    def test_teacher_profile_has_education_level_field(self):
        """Test TeacherProfile has education_level field"""
        assert hasattr(TeacherProfile, "education_level")

    def test_teacher_profile_has_created_at_field(self):
        """Test TeacherProfile has created_at field"""
        assert hasattr(TeacherProfile, "created_at")

    def test_teacher_profile_has_updated_at_field(self):
        """Test TeacherProfile has updated_at field"""
        assert hasattr(TeacherProfile, "updated_at")

    def test_teacher_profile_has_user_relationship(self):
        """Test TeacherProfile has user relationship"""
        assert hasattr(TeacherProfile, "user")

    def test_teacher_profile_has_classes_relationship(self):
        """Test TeacherProfile has classes relationship"""
        assert hasattr(TeacherProfile, "classes")

    def test_teacher_profile_experience_years_column_type(self):
        """Test TeacherProfile.experience_years column type is Integer"""
        assert isinstance(TeacherProfile.experience_years.type, Integer)

    def test_teacher_profile_subject_areas_column_type(self):
        """Test TeacherProfile.subject_areas column type is JSON"""
        assert isinstance(TeacherProfile.subject_areas.type, JSON)


# ============================================================================
# PARENT PROFILE MODEL TESTS
# ============================================================================


class TestParentProfileModel:
    """Test ParentProfile model definition"""

    def test_parent_profile_inherits_from_base(self):
        """Test ParentProfile inherits from Base"""
        assert issubclass(ParentProfile, Base)

    def test_parent_profile_table_name(self):
        """Test ParentProfile table name"""
        assert ParentProfile.__tablename__ == "parent_profiles"

    def test_parent_profile_has_id_field(self):
        """Test ParentProfile has id field"""
        assert hasattr(ParentProfile, "id")

    def test_parent_profile_has_user_id_field(self):
        """Test ParentProfile has user_id field"""
        assert hasattr(ParentProfile, "user_id")

    def test_parent_profile_has_children_ids_field(self):
        """Test ParentProfile has children_ids field"""
        assert hasattr(ParentProfile, "children_ids")

    def test_parent_profile_has_email_notifications_field(self):
        """Test ParentProfile has email_notifications field"""
        assert hasattr(ParentProfile, "email_notifications")

    def test_parent_profile_has_sms_notifications_field(self):
        """Test ParentProfile has sms_notifications field"""
        assert hasattr(ParentProfile, "sms_notifications")

    def test_parent_profile_has_weekly_reports_field(self):
        """Test ParentProfile has weekly_reports field"""
        assert hasattr(ParentProfile, "weekly_reports")

    def test_parent_profile_has_created_at_field(self):
        """Test ParentProfile has created_at field"""
        assert hasattr(ParentProfile, "created_at")

    def test_parent_profile_has_updated_at_field(self):
        """Test ParentProfile has updated_at field"""
        assert hasattr(ParentProfile, "updated_at")

    def test_parent_profile_has_user_relationship(self):
        """Test ParentProfile has user relationship"""
        assert hasattr(ParentProfile, "user")

    def test_parent_profile_children_ids_column_type(self):
        """Test ParentProfile.children_ids column type is JSON"""
        assert isinstance(ParentProfile.children_ids.type, JSON)

    def test_parent_profile_email_notifications_column_type(self):
        """Test ParentProfile.email_notifications column type is Boolean"""
        assert isinstance(ParentProfile.email_notifications.type, Boolean)

    def test_parent_profile_sms_notifications_column_type(self):
        """Test ParentProfile.sms_notifications column type is Boolean"""
        assert isinstance(ParentProfile.sms_notifications.type, Boolean)

    def test_parent_profile_weekly_reports_column_type(self):
        """Test ParentProfile.weekly_reports column type is Boolean"""
        assert isinstance(ParentProfile.weekly_reports.type, Boolean)


# ============================================================================
# QUESTION MODEL TESTS
# ============================================================================


class TestQuestionModel:
    """Test Question model definition"""

    def test_question_inherits_from_base(self):
        """Test Question inherits from Base"""
        assert issubclass(Question, Base)

    def test_question_table_name(self):
        """Test Question table name"""
        assert Question.__tablename__ == "questions"

    def test_question_has_id_field(self):
        """Test Question has id field"""
        assert hasattr(Question, "id")

    def test_question_has_question_text_field(self):
        """Test Question has question_text field"""
        assert hasattr(Question, "question_text")

    def test_question_has_question_image_url_field(self):
        """Test Question has question_image_url field"""
        assert hasattr(Question, "question_image_url")

    def test_question_has_option_a_field(self):
        """Test Question has option_a field"""
        assert hasattr(Question, "option_a")

    def test_question_has_option_b_field(self):
        """Test Question has option_b field"""
        assert hasattr(Question, "option_b")

    def test_question_has_option_c_field(self):
        """Test Question has option_c field"""
        assert hasattr(Question, "option_c")

    def test_question_has_option_d_field(self):
        """Test Question has option_d field"""
        assert hasattr(Question, "option_d")

    def test_question_has_option_e_field(self):
        """Test Question has option_e field"""
        assert hasattr(Question, "option_e")

    def test_question_has_correct_answer_field(self):
        """Test Question has correct_answer field"""
        assert hasattr(Question, "correct_answer")

    def test_question_has_explanation_field(self):
        """Test Question has explanation field"""
        assert hasattr(Question, "explanation")

    def test_question_has_exam_type_field(self):
        """Test Question has exam_type field"""
        assert hasattr(Question, "exam_type")

    def test_question_has_subject_area_field(self):
        """Test Question has subject_area field"""
        assert hasattr(Question, "subject_area")

    def test_question_has_topic_field(self):
        """Test Question has topic field"""
        assert hasattr(Question, "topic")

    def test_question_has_subtopic_field(self):
        """Test Question has subtopic field"""
        assert hasattr(Question, "subtopic")

    def test_question_has_difficulty_field(self):
        """Test Question has difficulty field"""
        assert hasattr(Question, "difficulty")

    def test_question_has_irt_difficulty_field(self):
        """Test Question has irt_difficulty field"""
        assert hasattr(Question, "irt_difficulty")

    def test_question_has_irt_discrimination_field(self):
        """Test Question has irt_discrimination field"""
        assert hasattr(Question, "irt_discrimination")

    def test_question_has_irt_guessing_field(self):
        """Test Question has irt_guessing field"""
        assert hasattr(Question, "irt_guessing")

    def test_question_has_morphology_complexity_field(self):
        """Test Question has morphology_complexity field"""
        assert hasattr(Question, "morphology_complexity")

    def test_question_has_readability_score_field(self):
        """Test Question has readability_score field"""
        assert hasattr(Question, "readability_score")

    def test_question_has_times_asked_field(self):
        """Test Question has times_asked field"""
        assert hasattr(Question, "times_asked")

    def test_question_has_times_correct_field(self):
        """Test Question has times_correct field"""
        assert hasattr(Question, "times_correct")

    def test_question_has_average_response_time_field(self):
        """Test Question has average_response_time field"""
        assert hasattr(Question, "average_response_time")

    def test_question_has_created_by_field(self):
        """Test Question has created_by field"""
        assert hasattr(Question, "created_by")

    def test_question_has_created_at_field(self):
        """Test Question has created_at field"""
        assert hasattr(Question, "created_at")

    def test_question_has_updated_at_field(self):
        """Test Question has updated_at field"""
        assert hasattr(Question, "updated_at")

    def test_question_has_is_active_field(self):
        """Test Question has is_active field"""
        assert hasattr(Question, "is_active")

    def test_question_exam_questions_relationship_moved(self):
        """Exam relationships moved from Question to QuestionBankItem"""
        assert not hasattr(Question, "exam_questions")

    def test_question_student_answers_relationship_moved(self):
        """Exam relationships moved from Question to QuestionBankItem"""
        assert not hasattr(Question, "student_answers")

    def test_question_text_column_type(self):
        """Test Question.question_text column type is Text"""
        assert isinstance(Question.question_text.type, Text)

    def test_question_option_a_column_type(self):
        """Test Question.option_a column type is Text"""
        assert isinstance(Question.option_a.type, Text)

    def test_question_irt_difficulty_column_type(self):
        """Test Question.irt_difficulty column type is Float"""
        assert isinstance(Question.irt_difficulty.type, Float)

    def test_question_irt_discrimination_column_type(self):
        """Test Question.irt_discrimination column type is Float"""
        assert isinstance(Question.irt_discrimination.type, Float)

    def test_question_irt_guessing_column_type(self):
        """Test Question.irt_guessing column type is Float"""
        assert isinstance(Question.irt_guessing.type, Float)

    def test_question_morphology_complexity_column_type(self):
        """Test Question.morphology_complexity column type is Float"""
        assert isinstance(Question.morphology_complexity.type, Float)

    def test_question_readability_score_column_type(self):
        """Test Question.readability_score column type is Float"""
        assert isinstance(Question.readability_score.type, Float)

    def test_question_times_asked_column_type(self):
        """Test Question.times_asked column type is Integer"""
        assert isinstance(Question.times_asked.type, Integer)

    def test_question_times_correct_column_type(self):
        """Test Question.times_correct column type is Integer"""
        assert isinstance(Question.times_correct.type, Integer)

    def test_question_average_response_time_column_type(self):
        """Test Question.average_response_time column type is Float"""
        assert isinstance(Question.average_response_time.type, Float)


# ============================================================================
# EXAM SESSION MODEL TESTS
# ============================================================================


class TestExamSessionModel:
    """Test ExamSession model definition"""

    def test_exam_session_inherits_from_base(self):
        """Test ExamSession inherits from Base"""
        assert issubclass(ExamSession, Base)

    def test_exam_session_table_name(self):
        """Test ExamSession table name"""
        assert ExamSession.__tablename__ == "exam_sessions"

    def test_exam_session_has_id_field(self):
        """Test ExamSession has id field"""
        assert hasattr(ExamSession, "id")

    def test_exam_session_has_student_id_field(self):
        """Test ExamSession has student_id field"""
        assert hasattr(ExamSession, "student_id")

    def test_exam_session_has_exam_type_field(self):
        """Test ExamSession has exam_type field"""
        assert hasattr(ExamSession, "exam_type")

    def test_exam_session_has_exam_name_field(self):
        """Test ExamSession has exam_name field"""
        assert hasattr(ExamSession, "exam_name")

    def test_exam_session_has_total_questions_field(self):
        """Test ExamSession has total_questions field"""
        assert hasattr(ExamSession, "total_questions")

    def test_exam_session_has_duration_minutes_field(self):
        """Test ExamSession has duration_minutes field"""
        assert hasattr(ExamSession, "duration_minutes")

    def test_exam_session_has_status_field(self):
        """Test ExamSession has status field"""
        assert hasattr(ExamSession, "status")

    def test_exam_session_has_current_question_index_field(self):
        """Test ExamSession has current_question_index field"""
        assert hasattr(ExamSession, "current_question_index")

    def test_exam_session_has_started_at_field(self):
        """Test ExamSession has started_at field"""
        assert hasattr(ExamSession, "started_at")

    def test_exam_session_has_completed_at_field(self):
        """Test ExamSession has completed_at field"""
        assert hasattr(ExamSession, "completed_at")

    def test_exam_session_has_time_spent_seconds_field(self):
        """Test ExamSession has time_spent_seconds field"""
        assert hasattr(ExamSession, "time_spent_seconds")

    def test_exam_session_has_total_correct_field(self):
        """Test ExamSession has total_correct field"""
        assert hasattr(ExamSession, "total_correct")

    def test_exam_session_has_total_wrong_field(self):
        """Test ExamSession has total_wrong field"""
        assert hasattr(ExamSession, "total_wrong")

    def test_exam_session_has_total_empty_field(self):
        """Test ExamSession has total_empty field"""
        assert hasattr(ExamSession, "total_empty")

    def test_exam_session_has_raw_score_field(self):
        """Test ExamSession has raw_score field"""
        assert hasattr(ExamSession, "raw_score")

    def test_exam_session_has_scaled_score_field(self):
        """Test ExamSession has scaled_score field"""
        assert hasattr(ExamSession, "scaled_score")

    def test_exam_session_has_percentile_field(self):
        """Test ExamSession has percentile field"""
        assert hasattr(ExamSession, "percentile")

    def test_exam_session_has_estimated_ability_field(self):
        """Test ExamSession has estimated_ability field"""
        assert hasattr(ExamSession, "estimated_ability")

    def test_exam_session_has_ability_confidence_field(self):
        """Test ExamSession has ability_confidence field"""
        assert hasattr(ExamSession, "ability_confidence")

    def test_exam_session_has_created_at_field(self):
        """Test ExamSession has created_at field"""
        assert hasattr(ExamSession, "created_at")

    def test_exam_session_has_updated_at_field(self):
        """Test ExamSession has updated_at field"""
        assert hasattr(ExamSession, "updated_at")

    def test_exam_session_has_student_relationship(self):
        """Test ExamSession has student relationship"""
        assert hasattr(ExamSession, "student")

    def test_exam_session_has_exam_questions_relationship(self):
        """Test ExamSession has exam_questions relationship"""
        assert hasattr(ExamSession, "exam_questions")

    def test_exam_session_has_student_answers_relationship(self):
        """Test ExamSession has student_answers relationship"""
        assert hasattr(ExamSession, "student_answers")


# ============================================================================
# EXAM QUESTION MODEL TESTS
# ============================================================================


class TestExamQuestionModel:
    """Test ExamQuestion model definition"""

    def test_exam_question_inherits_from_base(self):
        """Test ExamQuestion inherits from Base"""
        assert issubclass(ExamQuestion, Base)

    def test_exam_question_table_name(self):
        """Test ExamQuestion table name"""
        assert ExamQuestion.__tablename__ == "exam_questions"

    def test_exam_question_has_id_field(self):
        """Test ExamQuestion has id field"""
        assert hasattr(ExamQuestion, "id")

    def test_exam_question_has_exam_session_id_field(self):
        """Test ExamQuestion has exam_session_id field"""
        assert hasattr(ExamQuestion, "exam_session_id")

    def test_exam_question_has_question_id_field(self):
        """Test ExamQuestion has question_id field"""
        assert hasattr(ExamQuestion, "question_id")

    def test_exam_question_has_question_order_field(self):
        """Test ExamQuestion has question_order field"""
        assert hasattr(ExamQuestion, "question_order")

    def test_exam_question_has_exam_session_relationship(self):
        """Test ExamQuestion has exam_session relationship"""
        assert hasattr(ExamQuestion, "exam_session")

    def test_exam_question_has_question_relationship(self):
        """Test ExamQuestion has question relationship"""
        assert hasattr(ExamQuestion, "question")

    def test_exam_question_order_column_type(self):
        """Test ExamQuestion.question_order column type is Integer"""
        assert isinstance(ExamQuestion.question_order.type, Integer)


# ============================================================================
# STUDENT ANSWER MODEL TESTS
# ============================================================================


class TestStudentAnswerModel:
    """Test StudentAnswer model definition"""

    def test_student_answer_inherits_from_base(self):
        """Test StudentAnswer inherits from Base"""
        assert issubclass(StudentAnswer, Base)

    def test_student_answer_table_name(self):
        """Test StudentAnswer table name"""
        assert StudentAnswer.__tablename__ == "student_answers"

    def test_student_answer_has_id_field(self):
        """Test StudentAnswer has id field"""
        assert hasattr(StudentAnswer, "id")

    def test_student_answer_has_exam_session_id_field(self):
        """Test StudentAnswer has exam_session_id field"""
        assert hasattr(StudentAnswer, "exam_session_id")

    def test_student_answer_has_question_id_field(self):
        """Test StudentAnswer has question_id field"""
        assert hasattr(StudentAnswer, "question_id")

    def test_student_answer_has_selected_answer_field(self):
        """Test StudentAnswer has selected_answer field"""
        assert hasattr(StudentAnswer, "selected_answer")

    def test_student_answer_has_is_correct_field(self):
        """Test StudentAnswer has is_correct field"""
        assert hasattr(StudentAnswer, "is_correct")

    def test_student_answer_has_response_time_seconds_field(self):
        """Test StudentAnswer has response_time_seconds field"""
        assert hasattr(StudentAnswer, "response_time_seconds")

    def test_student_answer_has_answer_changes_field(self):
        """Test StudentAnswer has answer_changes field"""
        assert hasattr(StudentAnswer, "answer_changes")

    def test_student_answer_has_time_to_first_answer_field(self):
        """Test StudentAnswer has time_to_first_answer field"""
        assert hasattr(StudentAnswer, "time_to_first_answer")

    def test_student_answer_has_confidence_level_field(self):
        """Test StudentAnswer has confidence_level field"""
        assert hasattr(StudentAnswer, "confidence_level")

    def test_student_answer_has_answered_at_field(self):
        """Test StudentAnswer has answered_at field"""
        assert hasattr(StudentAnswer, "answered_at")

    def test_student_answer_has_exam_session_relationship(self):
        """Test StudentAnswer has exam_session relationship"""
        assert hasattr(StudentAnswer, "exam_session")

    def test_student_answer_has_question_relationship(self):
        """Test StudentAnswer has question relationship"""
        assert hasattr(StudentAnswer, "question")

    def test_student_answer_is_correct_column_type(self):
        """Test StudentAnswer.is_correct column type is Boolean"""
        assert isinstance(StudentAnswer.is_correct.type, Boolean)

    def test_student_answer_response_time_column_type(self):
        """Test StudentAnswer.response_time_seconds column type is Float"""
        assert isinstance(StudentAnswer.response_time_seconds.type, Float)

    def test_student_answer_changes_column_type(self):
        """Test StudentAnswer.answer_changes column type is Integer"""
        assert isinstance(StudentAnswer.answer_changes.type, Integer)


# ============================================================================
# LEARNING ANALYTICS MODEL TESTS
# ============================================================================


class TestLearningAnalyticsModel:
    """Test LearningAnalytics model definition"""

    def test_learning_analytics_inherits_from_base(self):
        """Test LearningAnalytics inherits from Base"""
        assert issubclass(LearningAnalytics, Base)

    def test_learning_analytics_table_name(self):
        """Test LearningAnalytics table name"""
        assert LearningAnalytics.__tablename__ == "learning_analytics"

    def test_learning_analytics_has_id_field(self):
        """Test LearningAnalytics has id field"""
        assert hasattr(LearningAnalytics, "id")

    def test_learning_analytics_has_student_id_field(self):
        """Test LearningAnalytics has student_id field"""
        assert hasattr(LearningAnalytics, "student_id")

    def test_learning_analytics_has_date_field(self):
        """Test LearningAnalytics has date field"""
        assert hasattr(LearningAnalytics, "date")

    def test_learning_analytics_has_subject_area_field(self):
        """Test LearningAnalytics has subject_area field"""
        assert hasattr(LearningAnalytics, "subject_area")

    def test_learning_analytics_has_questions_attempted_field(self):
        """Test LearningAnalytics has questions_attempted field"""
        assert hasattr(LearningAnalytics, "questions_attempted")

    def test_learning_analytics_has_questions_correct_field(self):
        """Test LearningAnalytics has questions_correct field"""
        assert hasattr(LearningAnalytics, "questions_correct")

    def test_learning_analytics_has_average_response_time_field(self):
        """Test LearningAnalytics has average_response_time field"""
        assert hasattr(LearningAnalytics, "average_response_time")

    def test_learning_analytics_has_study_time_minutes_field(self):
        """Test LearningAnalytics has study_time_minutes field"""
        assert hasattr(LearningAnalytics, "study_time_minutes")

    def test_learning_analytics_has_skill_level_field(self):
        """Test LearningAnalytics has skill_level field"""
        assert hasattr(LearningAnalytics, "skill_level")

    def test_learning_analytics_has_improvement_rate_field(self):
        """Test LearningAnalytics has improvement_rate field"""
        assert hasattr(LearningAnalytics, "improvement_rate")

    def test_learning_analytics_has_difficulty_preference_field(self):
        """Test LearningAnalytics has difficulty_preference field"""
        assert hasattr(LearningAnalytics, "difficulty_preference")

    def test_learning_analytics_has_zpd_utilization_field(self):
        """Test LearningAnalytics has zpd_utilization field"""
        assert hasattr(LearningAnalytics, "zpd_utilization")

    def test_learning_analytics_has_fsrs_retention_rate_field(self):
        """Test LearningAnalytics has fsrs_retention_rate field"""
        assert hasattr(LearningAnalytics, "fsrs_retention_rate")

    def test_learning_analytics_has_morphology_awareness_field(self):
        """Test LearningAnalytics has morphology_awareness field"""
        assert hasattr(LearningAnalytics, "morphology_awareness")

    def test_learning_analytics_has_created_at_field(self):
        """Test LearningAnalytics has created_at field"""
        assert hasattr(LearningAnalytics, "created_at")

    def test_learning_analytics_has_student_relationship(self):
        """Test LearningAnalytics has student relationship"""
        assert hasattr(LearningAnalytics, "student")

    def test_learning_analytics_date_column_type(self):
        """Test LearningAnalytics.date column type is Date"""
        assert isinstance(LearningAnalytics.date.type, Date)

    def test_learning_analytics_skill_level_column_type(self):
        """Test LearningAnalytics.skill_level column type is Float"""
        assert isinstance(LearningAnalytics.skill_level.type, Float)


# ============================================================================
# EDUCATIONAL CONTENT MODEL TESTS
# ============================================================================


class TestEducationalContentModel:
    """Test EducationalContent model definition"""

    def test_educational_content_inherits_from_base(self):
        """Test EducationalContent inherits from Base"""
        assert issubclass(EducationalContent, Base)

    def test_educational_content_table_name(self):
        """Test EducationalContent table name"""
        assert EducationalContent.__tablename__ == "educational_contents"

    def test_educational_content_has_id_field(self):
        """Test EducationalContent has id field"""
        assert hasattr(EducationalContent, "id")

    def test_educational_content_has_title_field(self):
        """Test EducationalContent has title field"""
        assert hasattr(EducationalContent, "title")

    def test_educational_content_has_description_field(self):
        """Test EducationalContent has description field"""
        assert hasattr(EducationalContent, "description")

    def test_educational_content_has_content_type_field(self):
        """Test EducationalContent has content_type field"""
        assert hasattr(EducationalContent, "content_type")

    def test_educational_content_has_source_platform_field(self):
        """Test EducationalContent has source_platform field"""
        assert hasattr(EducationalContent, "source_platform")

    def test_educational_content_has_source_url_field(self):
        """Test EducationalContent has source_url field"""
        assert hasattr(EducationalContent, "source_url")

    def test_educational_content_has_source_id_field(self):
        """Test EducationalContent has source_id field"""
        assert hasattr(EducationalContent, "source_id")

    def test_educational_content_has_subject_area_field(self):
        """Test EducationalContent has subject_area field"""
        assert hasattr(EducationalContent, "subject_area")

    def test_educational_content_has_topic_field(self):
        """Test EducationalContent has topic field"""
        assert hasattr(EducationalContent, "topic")

    def test_educational_content_has_subtopic_field(self):
        """Test EducationalContent has subtopic field"""
        assert hasattr(EducationalContent, "subtopic")

    def test_educational_content_has_grade_level_field(self):
        """Test EducationalContent has grade_level field"""
        assert hasattr(EducationalContent, "grade_level")

    def test_educational_content_has_difficulty_level_field(self):
        """Test EducationalContent has difficulty_level field"""
        assert hasattr(EducationalContent, "difficulty_level")

    def test_educational_content_has_educational_score_field(self):
        """Test EducationalContent has educational_score field"""
        assert hasattr(EducationalContent, "educational_score")

    def test_educational_content_has_duration_minutes_field(self):
        """Test EducationalContent has duration_minutes field"""
        assert hasattr(EducationalContent, "duration_minutes")

    def test_educational_content_has_has_subtitles_field(self):
        """Test EducationalContent has has_subtitles field"""
        assert hasattr(EducationalContent, "has_subtitles")

    def test_educational_content_has_has_transcript_field(self):
        """Test EducationalContent has has_transcript field"""
        assert hasattr(EducationalContent, "has_transcript")

    def test_educational_content_has_language_field(self):
        """Test EducationalContent has language field"""
        assert hasattr(EducationalContent, "language")

    def test_educational_content_has_view_count_field(self):
        """Test EducationalContent has view_count field"""
        assert hasattr(EducationalContent, "view_count")

    def test_educational_content_has_like_count_field(self):
        """Test EducationalContent has like_count field"""
        assert hasattr(EducationalContent, "like_count")

    def test_educational_content_has_rating_field(self):
        """Test EducationalContent has rating field"""
        assert hasattr(EducationalContent, "rating")

    def test_educational_content_has_created_at_field(self):
        """Test EducationalContent has created_at field"""
        assert hasattr(EducationalContent, "created_at")

    def test_educational_content_has_updated_at_field(self):
        """Test EducationalContent has updated_at field"""
        assert hasattr(EducationalContent, "updated_at")

    def test_educational_content_has_is_active_field(self):
        """Test EducationalContent has is_active field"""
        assert hasattr(EducationalContent, "is_active")


# ============================================================================
# CLASSROOM MODEL TESTS
# ============================================================================


class TestClassRoomModel:
    """Test ClassRoom model definition"""

    def test_classroom_inherits_from_base(self):
        """Test ClassRoom inherits from Base"""
        assert issubclass(ClassRoom, Base)

    def test_classroom_table_name(self):
        """Test ClassRoom table name"""
        assert ClassRoom.__tablename__ == "classrooms"

    def test_classroom_has_id_field(self):
        """Test ClassRoom has id field"""
        assert hasattr(ClassRoom, "id")

    def test_classroom_has_teacher_id_field(self):
        """Test ClassRoom has teacher_id field"""
        assert hasattr(ClassRoom, "teacher_id")

    def test_classroom_has_class_name_field(self):
        """Test ClassRoom has class_name field"""
        assert hasattr(ClassRoom, "class_name")

    def test_classroom_has_grade_level_field(self):
        """Test ClassRoom has grade_level field"""
        assert hasattr(ClassRoom, "grade_level")

    def test_classroom_has_subject_area_field(self):
        """Test ClassRoom has subject_area field"""
        assert hasattr(ClassRoom, "subject_area")

    def test_classroom_has_school_year_field(self):
        """Test ClassRoom has school_year field"""
        assert hasattr(ClassRoom, "school_year")

    def test_classroom_has_student_ids_field(self):
        """Test ClassRoom has student_ids field"""
        assert hasattr(ClassRoom, "student_ids")

    def test_classroom_has_is_active_field(self):
        """Test ClassRoom has is_active field"""
        assert hasattr(ClassRoom, "is_active")

    def test_classroom_has_max_students_field(self):
        """Test ClassRoom has max_students field"""
        assert hasattr(ClassRoom, "max_students")

    def test_classroom_has_created_at_field(self):
        """Test ClassRoom has created_at field"""
        assert hasattr(ClassRoom, "created_at")

    def test_classroom_has_updated_at_field(self):
        """Test ClassRoom has updated_at field"""
        assert hasattr(ClassRoom, "updated_at")

    def test_classroom_has_teacher_relationship(self):
        """Test ClassRoom has teacher relationship"""
        assert hasattr(ClassRoom, "teacher")


# ============================================================================
# SYSTEM CONFIGURATION MODEL TESTS
# ============================================================================


class TestSystemConfigurationModel:
    """Test SystemConfiguration model definition"""

    def test_system_configuration_inherits_from_base(self):
        """Test SystemConfiguration inherits from Base"""
        assert issubclass(SystemConfiguration, Base)

    def test_system_configuration_table_name(self):
        """Test SystemConfiguration table name"""
        assert SystemConfiguration.__tablename__ == "system_configurations"

    def test_system_configuration_has_id_field(self):
        """Test SystemConfiguration has id field"""
        assert hasattr(SystemConfiguration, "id")

    def test_system_configuration_has_config_key_field(self):
        """Test SystemConfiguration has config_key field"""
        assert hasattr(SystemConfiguration, "config_key")

    def test_system_configuration_has_config_value_field(self):
        """Test SystemConfiguration has config_value field"""
        assert hasattr(SystemConfiguration, "config_value")

    def test_system_configuration_has_config_type_field(self):
        """Test SystemConfiguration has config_type field"""
        assert hasattr(SystemConfiguration, "config_type")

    def test_system_configuration_has_description_field(self):
        """Test SystemConfiguration has description field"""
        assert hasattr(SystemConfiguration, "description")

    def test_system_configuration_has_created_at_field(self):
        """Test SystemConfiguration has created_at field"""
        assert hasattr(SystemConfiguration, "created_at")

    def test_system_configuration_has_updated_at_field(self):
        """Test SystemConfiguration has updated_at field"""
        assert hasattr(SystemConfiguration, "updated_at")


# ============================================================================
# AUDIT LOG MODEL TESTS
# ============================================================================


class TestAuditLogModel:
    """Test AuditLog model definition"""

    def test_audit_log_inherits_from_base(self):
        """Test AuditLog inherits from Base"""
        assert issubclass(AuditLog, Base)

    def test_audit_log_table_name(self):
        """Test AuditLog table name"""
        assert AuditLog.__tablename__ == "audit_logs"

    def test_audit_log_has_id_field(self):
        """Test AuditLog has id field"""
        assert hasattr(AuditLog, "id")

    def test_audit_log_has_user_id_field(self):
        """Test AuditLog has user_id field"""
        assert hasattr(AuditLog, "user_id")

    def test_audit_log_has_action_field(self):
        """Test AuditLog has action field"""
        assert hasattr(AuditLog, "action")

    def test_audit_log_has_resource_type_field(self):
        """Test AuditLog has resource_type field"""
        assert hasattr(AuditLog, "resource_type")

    def test_audit_log_has_resource_id_field(self):
        """Test AuditLog has resource_id field"""
        assert hasattr(AuditLog, "resource_id")

    def test_audit_log_has_old_values_field(self):
        """Test AuditLog has old_values field"""
        assert hasattr(AuditLog, "old_values")

    def test_audit_log_has_new_values_field(self):
        """Test AuditLog has new_values field"""
        assert hasattr(AuditLog, "new_values")

    def test_audit_log_has_ip_address_field(self):
        """Test AuditLog has ip_address field"""
        assert hasattr(AuditLog, "ip_address")

    def test_audit_log_has_user_agent_field(self):
        """Test AuditLog has user_agent field"""
        assert hasattr(AuditLog, "user_agent")

    def test_audit_log_has_created_at_field(self):
        """Test AuditLog has created_at field"""
        assert hasattr(AuditLog, "created_at")

    def test_audit_log_old_values_column_type(self):
        """Test AuditLog.old_values column type is JSON"""
        assert isinstance(AuditLog.old_values.type, JSON)

    def test_audit_log_new_values_column_type(self):
        """Test AuditLog.new_values column type is JSON"""
        assert isinstance(AuditLog.new_values.type, JSON)


# ============================================================================
# EBA VIDEO MODEL TESTS
# ============================================================================


class TestEBAVideoModel:
    """Test EBAVideo model definition"""

    def test_eba_video_inherits_from_base(self):
        """Test EBAVideo inherits from Base"""
        assert issubclass(EBAVideo, Base)

    def test_eba_video_table_name(self):
        """Test EBAVideo table name"""
        assert EBAVideo.__tablename__ == "eba_videos"

    def test_eba_video_has_id_field(self):
        """Test EBAVideo has id field"""
        assert hasattr(EBAVideo, "id")

    def test_eba_video_has_title_field(self):
        """Test EBAVideo has title field"""
        assert hasattr(EBAVideo, "title")

    def test_eba_video_has_description_field(self):
        """Test EBAVideo has description field"""
        assert hasattr(EBAVideo, "description")

    def test_eba_video_has_duration_minutes_field(self):
        """Test EBAVideo has duration_minutes field"""
        assert hasattr(EBAVideo, "duration_minutes")

    def test_eba_video_has_category_field(self):
        """Test EBAVideo has category field"""
        assert hasattr(EBAVideo, "category")

    def test_eba_video_has_grade_level_field(self):
        """Test EBAVideo has grade_level field"""
        assert hasattr(EBAVideo, "grade_level")

    def test_eba_video_has_subject_topics_field(self):
        """Test EBAVideo has subject_topics field"""
        assert hasattr(EBAVideo, "subject_topics")

    def test_eba_video_has_difficulty_level_field(self):
        """Test EBAVideo has difficulty_level field"""
        assert hasattr(EBAVideo, "difficulty_level")

    def test_eba_video_has_video_url_field(self):
        """Test EBAVideo has video_url field"""
        assert hasattr(EBAVideo, "video_url")

    def test_eba_video_has_thumbnail_url_field(self):
        """Test EBAVideo has thumbnail_url field"""
        assert hasattr(EBAVideo, "thumbnail_url")

    def test_eba_video_has_transcript_field(self):
        """Test EBAVideo has transcript field"""
        assert hasattr(EBAVideo, "transcript")

    def test_eba_video_has_quality_score_field(self):
        """Test EBAVideo has quality_score field"""
        assert hasattr(EBAVideo, "quality_score")

    def test_eba_video_has_quality_category_field(self):
        """Test EBAVideo has quality_category field"""
        assert hasattr(EBAVideo, "quality_category")

    def test_eba_video_has_curriculum_alignment_field(self):
        """Test EBAVideo has curriculum_alignment field"""
        assert hasattr(EBAVideo, "curriculum_alignment")

    def test_eba_video_has_accessibility_features_field(self):
        """Test EBAVideo has accessibility_features field"""
        assert hasattr(EBAVideo, "accessibility_features")

    def test_eba_video_has_has_subtitles_field(self):
        """Test EBAVideo has has_subtitles field"""
        assert hasattr(EBAVideo, "has_subtitles")

    def test_eba_video_has_has_transcript_field(self):
        """Test EBAVideo has has_transcript field"""
        assert hasattr(EBAVideo, "has_transcript")

    def test_eba_video_has_view_count_field(self):
        """Test EBAVideo has view_count field"""
        assert hasattr(EBAVideo, "view_count")

    def test_eba_video_has_like_count_field(self):
        """Test EBAVideo has like_count field"""
        assert hasattr(EBAVideo, "like_count")

    def test_eba_video_has_share_count_field(self):
        """Test EBAVideo has share_count field"""
        assert hasattr(EBAVideo, "share_count")

    def test_eba_video_has_bookmark_count_field(self):
        """Test EBAVideo has bookmark_count field"""
        assert hasattr(EBAVideo, "bookmark_count")

    def test_eba_video_has_duration_score_field(self):
        """Test EBAVideo has duration_score field"""
        assert hasattr(EBAVideo, "duration_score")

    def test_eba_video_has_title_clarity_score_field(self):
        """Test EBAVideo has title_clarity_score field"""
        assert hasattr(EBAVideo, "title_clarity_score")

    def test_eba_video_has_description_quality_score_field(self):
        """Test EBAVideo has description_quality_score field"""
        assert hasattr(EBAVideo, "description_quality_score")

    def test_eba_video_has_curriculum_alignment_score_field(self):
        """Test EBAVideo has curriculum_alignment_score field"""
        assert hasattr(EBAVideo, "curriculum_alignment_score")

    def test_eba_video_has_accessibility_score_field(self):
        """Test EBAVideo has accessibility_score field"""
        assert hasattr(EBAVideo, "accessibility_score")

    def test_eba_video_has_moderation_status_field(self):
        """Test EBAVideo has moderation_status field"""
        assert hasattr(EBAVideo, "moderation_status")

    def test_eba_video_has_moderated_by_field(self):
        """Test EBAVideo has moderated_by field"""
        assert hasattr(EBAVideo, "moderated_by")

    def test_eba_video_has_moderation_date_field(self):
        """Test EBAVideo has moderation_date field"""
        assert hasattr(EBAVideo, "moderation_date")

    def test_eba_video_has_moderation_notes_field(self):
        """Test EBAVideo has moderation_notes field"""
        assert hasattr(EBAVideo, "moderation_notes")

    def test_eba_video_has_is_active_field(self):
        """Test EBAVideo has is_active field"""
        assert hasattr(EBAVideo, "is_active")

    def test_eba_video_has_created_at_field(self):
        """Test EBAVideo has created_at field"""
        assert hasattr(EBAVideo, "created_at")

    def test_eba_video_has_updated_at_field(self):
        """Test EBAVideo has updated_at field"""
        assert hasattr(EBAVideo, "updated_at")

    def test_eba_video_has_usage_analytics_relationship(self):
        """Test EBAVideo has usage_analytics relationship"""
        assert hasattr(EBAVideo, "usage_analytics")

    def test_eba_video_has_recommendations_relationship(self):
        """Test EBAVideo has recommendations relationship"""
        assert hasattr(EBAVideo, "recommendations")


# ============================================================================
# FSRS CARD MODEL TESTS
# ============================================================================


class TestFSRSCardModel:
    """Test FSRSCard model definition"""

    def test_fsrs_card_inherits_from_base(self):
        """Test FSRSCard inherits from Base"""
        assert issubclass(FSRSCard, Base)

    def test_fsrs_card_table_name(self):
        """Test FSRSCard table name"""
        assert FSRSCard.__tablename__ == "fsrs_cards"

    def test_fsrs_card_has_id_field(self):
        """Test FSRSCard has id field"""
        assert hasattr(FSRSCard, "id")

    def test_fsrs_card_has_student_id_field(self):
        """Test FSRSCard has student_id field"""
        assert hasattr(FSRSCard, "student_id")

    def test_fsrs_card_has_front_text_field(self):
        """Test FSRSCard has front_text field"""
        assert hasattr(FSRSCard, "front_text")

    def test_fsrs_card_has_back_text_field(self):
        """Test FSRSCard has back_text field"""
        assert hasattr(FSRSCard, "back_text")

    def test_fsrs_card_has_subject_area_field(self):
        """Test FSRSCard has subject_area field"""
        assert hasattr(FSRSCard, "subject_area")

    def test_fsrs_card_has_topic_field(self):
        """Test FSRSCard has topic field"""
        assert hasattr(FSRSCard, "topic")

    def test_fsrs_card_has_stability_field(self):
        """Test FSRSCard has stability field"""
        assert hasattr(FSRSCard, "stability")

    def test_fsrs_card_has_difficulty_field(self):
        """Test FSRSCard has difficulty field"""
        assert hasattr(FSRSCard, "difficulty")

    def test_fsrs_card_has_elapsed_days_field(self):
        """Test FSRSCard has elapsed_days field"""
        assert hasattr(FSRSCard, "elapsed_days")

    def test_fsrs_card_has_scheduled_days_field(self):
        """Test FSRSCard has scheduled_days field"""
        assert hasattr(FSRSCard, "scheduled_days")

    def test_fsrs_card_has_reps_field(self):
        """Test FSRSCard has reps field"""
        assert hasattr(FSRSCard, "reps")

    def test_fsrs_card_has_lapses_field(self):
        """Test FSRSCard has lapses field"""
        assert hasattr(FSRSCard, "lapses")

    def test_fsrs_card_has_state_field(self):
        """Test FSRSCard has state field"""
        assert hasattr(FSRSCard, "state")

    def test_fsrs_card_has_due_date_field(self):
        """Test FSRSCard has due_date field"""
        assert hasattr(FSRSCard, "due_date")

    def test_fsrs_card_has_last_review_field(self):
        """Test FSRSCard has last_review field"""
        assert hasattr(FSRSCard, "last_review")

    def test_fsrs_card_has_cultural_factors_field(self):
        """Test FSRSCard has cultural_factors field"""
        assert hasattr(FSRSCard, "cultural_factors")

    def test_fsrs_card_has_created_at_field(self):
        """Test FSRSCard has created_at field"""
        assert hasattr(FSRSCard, "created_at")

    def test_fsrs_card_has_updated_at_field(self):
        """Test FSRSCard has updated_at field"""
        assert hasattr(FSRSCard, "updated_at")

    def test_fsrs_card_has_student_relationship(self):
        """Test FSRSCard has student relationship"""
        assert hasattr(FSRSCard, "student")

    def test_fsrs_card_has_reviews_relationship(self):
        """Test FSRSCard has reviews relationship"""
        assert hasattr(FSRSCard, "reviews")

    def test_fsrs_card_front_text_column_type(self):
        """Test FSRSCard.front_text column type is Text"""
        assert isinstance(FSRSCard.front_text.type, Text)

    def test_fsrs_card_back_text_column_type(self):
        """Test FSRSCard.back_text column type is Text"""
        assert isinstance(FSRSCard.back_text.type, Text)

    def test_fsrs_card_stability_column_type(self):
        """Test FSRSCard.stability column type is Float"""
        assert isinstance(FSRSCard.stability.type, Float)

    def test_fsrs_card_difficulty_column_type(self):
        """Test FSRSCard.difficulty column type is Float"""
        assert isinstance(FSRSCard.difficulty.type, Float)


# ============================================================================
# FSRS REVIEW MODEL TESTS
# ============================================================================


class TestFSRSReviewModel:
    """Test FSRSReview model definition"""

    def test_fsrs_review_inherits_from_base(self):
        """Test FSRSReview inherits from Base"""
        assert issubclass(FSRSReview, Base)

    def test_fsrs_review_table_name(self):
        """Test FSRSReview table name"""
        assert FSRSReview.__tablename__ == "fsrs_reviews"

    def test_fsrs_review_has_id_field(self):
        """Test FSRSReview has id field"""
        assert hasattr(FSRSReview, "id")

    def test_fsrs_review_has_card_id_field(self):
        """Test FSRSReview has card_id field"""
        assert hasattr(FSRSReview, "card_id")

    def test_fsrs_review_has_student_id_field(self):
        """Test FSRSReview has student_id field"""
        assert hasattr(FSRSReview, "student_id")

    def test_fsrs_review_has_grade_field(self):
        """Test FSRSReview has grade field"""
        assert hasattr(FSRSReview, "grade")

    def test_fsrs_review_has_review_date_field(self):
        """Test FSRSReview has review_date field"""
        assert hasattr(FSRSReview, "review_date")

    def test_fsrs_review_has_response_time_seconds_field(self):
        """Test FSRSReview has response_time_seconds field"""
        assert hasattr(FSRSReview, "response_time_seconds")

    def test_fsrs_review_has_old_stability_field(self):
        """Test FSRSReview has old_stability field"""
        assert hasattr(FSRSReview, "old_stability")

    def test_fsrs_review_has_new_stability_field(self):
        """Test FSRSReview has new_stability field"""
        assert hasattr(FSRSReview, "new_stability")

    def test_fsrs_review_has_old_difficulty_field(self):
        """Test FSRSReview has old_difficulty field"""
        assert hasattr(FSRSReview, "old_difficulty")

    def test_fsrs_review_has_new_difficulty_field(self):
        """Test FSRSReview has new_difficulty field"""
        assert hasattr(FSRSReview, "new_difficulty")

    def test_fsrs_review_has_cultural_adjustment_field(self):
        """Test FSRSReview has cultural_adjustment field"""
        assert hasattr(FSRSReview, "cultural_adjustment")

    def test_fsrs_review_has_card_relationship(self):
        """Test FSRSReview has card relationship"""
        assert hasattr(FSRSReview, "card")

    def test_fsrs_review_has_student_relationship(self):
        """Test FSRSReview has student relationship"""
        assert hasattr(FSRSReview, "student")


# ============================================================================
# FSRS SCHEDULE MODEL TESTS
# ============================================================================


class TestFSRSScheduleModel:
    """Test FSRSSchedule model definition"""

    def test_fsrs_schedule_inherits_from_base(self):
        """Test FSRSSchedule inherits from Base"""
        assert issubclass(FSRSSchedule, Base)

    def test_fsrs_schedule_table_name(self):
        """Test FSRSSchedule table name"""
        assert FSRSSchedule.__tablename__ == "fsrs_schedules"

    def test_fsrs_schedule_has_id_field(self):
        """Test FSRSSchedule has id field"""
        assert hasattr(FSRSSchedule, "id")

    def test_fsrs_schedule_has_student_id_field(self):
        """Test FSRSSchedule has student_id field"""
        assert hasattr(FSRSSchedule, "student_id")

    def test_fsrs_schedule_has_schedule_date_field(self):
        """Test FSRSSchedule has schedule_date field"""
        assert hasattr(FSRSSchedule, "schedule_date")

    def test_fsrs_schedule_has_total_cards_due_field(self):
        """Test FSRSSchedule has total_cards_due field"""
        assert hasattr(FSRSSchedule, "total_cards_due")

    def test_fsrs_schedule_has_new_cards_field(self):
        """Test FSRSSchedule has new_cards field"""
        assert hasattr(FSRSSchedule, "new_cards")

    def test_fsrs_schedule_has_review_cards_field(self):
        """Test FSRSSchedule has review_cards field"""
        assert hasattr(FSRSSchedule, "review_cards")

    def test_fsrs_schedule_has_cards_studied_field(self):
        """Test FSRSSchedule has cards_studied field"""
        assert hasattr(FSRSSchedule, "cards_studied")

    def test_fsrs_schedule_has_study_time_minutes_field(self):
        """Test FSRSSchedule has study_time_minutes field"""
        assert hasattr(FSRSSchedule, "study_time_minutes")

    def test_fsrs_schedule_has_retention_rate_field(self):
        """Test FSRSSchedule has retention_rate field"""
        assert hasattr(FSRSSchedule, "retention_rate")

    def test_fsrs_schedule_has_cultural_period_field(self):
        """Test FSRSSchedule has cultural_period field"""
        assert hasattr(FSRSSchedule, "cultural_period")

    def test_fsrs_schedule_has_adjustment_factor_field(self):
        """Test FSRSSchedule has adjustment_factor field"""
        assert hasattr(FSRSSchedule, "adjustment_factor")

    def test_fsrs_schedule_has_student_relationship(self):
        """Test FSRSSchedule has student relationship"""
        assert hasattr(FSRSSchedule, "student")


# ============================================================================
# FSRS STUDENT PROFILE MODEL TESTS
# ============================================================================


class TestFSRSStudentProfileModel:
    """Test FSRSStudentProfile model definition"""

    def test_fsrs_student_profile_inherits_from_base(self):
        """Test FSRSStudentProfile inherits from Base"""
        assert issubclass(FSRSStudentProfile, Base)

    def test_fsrs_student_profile_table_name(self):
        """Test FSRSStudentProfile table name"""
        assert FSRSStudentProfile.__tablename__ == "fsrs_student_profiles"

    def test_fsrs_student_profile_has_id_field(self):
        """Test FSRSStudentProfile has id field"""
        assert hasattr(FSRSStudentProfile, "id")

    def test_fsrs_student_profile_has_student_id_field(self):
        """Test FSRSStudentProfile has student_id field"""
        assert hasattr(FSRSStudentProfile, "student_id")

    def test_fsrs_student_profile_has_fsrs_parameters_field(self):
        """Test FSRSStudentProfile has fsrs_parameters field"""
        assert hasattr(FSRSStudentProfile, "fsrs_parameters")

    def test_fsrs_student_profile_has_cultural_parameters_field(self):
        """Test FSRSStudentProfile has cultural_parameters field"""
        assert hasattr(FSRSStudentProfile, "cultural_parameters")

    def test_fsrs_student_profile_has_total_reviews_field(self):
        """Test FSRSStudentProfile has total_reviews field"""
        assert hasattr(FSRSStudentProfile, "total_reviews")

    def test_fsrs_student_profile_has_average_retention_field(self):
        """Test FSRSStudentProfile has average_retention field"""
        assert hasattr(FSRSStudentProfile, "average_retention")

    def test_fsrs_student_profile_has_study_streak_days_field(self):
        """Test FSRSStudentProfile has study_streak_days field"""
        assert hasattr(FSRSStudentProfile, "study_streak_days")

    def test_fsrs_student_profile_has_created_at_field(self):
        """Test FSRSStudentProfile has created_at field"""
        assert hasattr(FSRSStudentProfile, "created_at")

    def test_fsrs_student_profile_has_updated_at_field(self):
        """Test FSRSStudentProfile has updated_at field"""
        assert hasattr(FSRSStudentProfile, "updated_at")

    def test_fsrs_student_profile_has_student_relationship(self):
        """Test FSRSStudentProfile has student relationship"""
        assert hasattr(FSRSStudentProfile, "student")


# ============================================================================
# FSRS STUDY SESSION MODEL TESTS
# ============================================================================


class TestFSRSStudySessionModel:
    """Test FSRSStudySession model definition"""

    def test_fsrs_study_session_inherits_from_base(self):
        """Test FSRSStudySession inherits from Base"""
        assert issubclass(FSRSStudySession, Base)

    def test_fsrs_study_session_table_name(self):
        """Test FSRSStudySession table name"""
        assert FSRSStudySession.__tablename__ == "fsrs_study_sessions"

    def test_fsrs_study_session_has_id_field(self):
        """Test FSRSStudySession has id field"""
        assert hasattr(FSRSStudySession, "id")

    def test_fsrs_study_session_has_student_id_field(self):
        """Test FSRSStudySession has student_id field"""
        assert hasattr(FSRSStudySession, "student_id")

    def test_fsrs_study_session_has_session_date_field(self):
        """Test FSRSStudySession has session_date field"""
        assert hasattr(FSRSStudySession, "session_date")

    def test_fsrs_study_session_has_duration_minutes_field(self):
        """Test FSRSStudySession has duration_minutes field"""
        assert hasattr(FSRSStudySession, "duration_minutes")

    def test_fsrs_study_session_has_cards_reviewed_field(self):
        """Test FSRSStudySession has cards_reviewed field"""
        assert hasattr(FSRSStudySession, "cards_reviewed")

    def test_fsrs_study_session_has_correct_reviews_field(self):
        """Test FSRSStudySession has correct_reviews field"""
        assert hasattr(FSRSStudySession, "correct_reviews")

    def test_fsrs_study_session_has_average_response_time_field(self):
        """Test FSRSStudySession has average_response_time field"""
        assert hasattr(FSRSStudySession, "average_response_time")

    def test_fsrs_study_session_has_cultural_context_field(self):
        """Test FSRSStudySession has cultural_context field"""
        assert hasattr(FSRSStudySession, "cultural_context")

    def test_fsrs_study_session_has_student_relationship(self):
        """Test FSRSStudySession has student relationship"""
        assert hasattr(FSRSStudySession, "student")


# ============================================================================
# FSRS SUBJECT STATS MODEL TESTS
# ============================================================================


class TestFSRSSubjectStatsModel:
    """Test FSRSSubjectStats model definition"""

    def test_fsrs_subject_stats_inherits_from_base(self):
        """Test FSRSSubjectStats inherits from Base"""
        assert issubclass(FSRSSubjectStats, Base)

    def test_fsrs_subject_stats_table_name(self):
        """Test FSRSSubjectStats table name"""
        assert FSRSSubjectStats.__tablename__ == "fsrs_subject_stats"

    def test_fsrs_subject_stats_has_id_field(self):
        """Test FSRSSubjectStats has id field"""
        assert hasattr(FSRSSubjectStats, "id")

    def test_fsrs_subject_stats_has_student_id_field(self):
        """Test FSRSSubjectStats has student_id field"""
        assert hasattr(FSRSSubjectStats, "student_id")

    def test_fsrs_subject_stats_has_subject_area_field(self):
        """Test FSRSSubjectStats has subject_area field"""
        assert hasattr(FSRSSubjectStats, "subject_area")

    def test_fsrs_subject_stats_has_total_cards_field(self):
        """Test FSRSSubjectStats has total_cards field"""
        assert hasattr(FSRSSubjectStats, "total_cards")

    def test_fsrs_subject_stats_has_mature_cards_field(self):
        """Test FSRSSubjectStats has mature_cards field"""
        assert hasattr(FSRSSubjectStats, "mature_cards")

    def test_fsrs_subject_stats_has_average_stability_field(self):
        """Test FSRSSubjectStats has average_stability field"""
        assert hasattr(FSRSSubjectStats, "average_stability")

    def test_fsrs_subject_stats_has_average_difficulty_field(self):
        """Test FSRSSubjectStats has average_difficulty field"""
        assert hasattr(FSRSSubjectStats, "average_difficulty")

    def test_fsrs_subject_stats_has_retention_rate_field(self):
        """Test FSRSSubjectStats has retention_rate field"""
        assert hasattr(FSRSSubjectStats, "retention_rate")

    def test_fsrs_subject_stats_has_last_updated_field(self):
        """Test FSRSSubjectStats has last_updated field"""
        assert hasattr(FSRSSubjectStats, "last_updated")

    def test_fsrs_subject_stats_has_student_relationship(self):
        """Test FSRSSubjectStats has student relationship"""
        assert hasattr(FSRSSubjectStats, "student")


# ============================================================================
# EBA VIDEO USAGE MODEL TESTS
# ============================================================================


class TestEBAVideoUsageModel:
    """Test EBAVideoUsage model definition"""

    def test_eba_video_usage_inherits_from_base(self):
        """Test EBAVideoUsage inherits from Base"""
        assert issubclass(EBAVideoUsage, Base)

    def test_eba_video_usage_table_name(self):
        """Test EBAVideoUsage table name"""
        assert EBAVideoUsage.__tablename__ == "eba_video_usage"

    def test_eba_video_usage_has_id_field(self):
        """Test EBAVideoUsage has id field"""
        assert hasattr(EBAVideoUsage, "id")

    def test_eba_video_usage_has_video_id_field(self):
        """Test EBAVideoUsage has video_id field"""
        assert hasattr(EBAVideoUsage, "video_id")

    def test_eba_video_usage_has_student_id_field(self):
        """Test EBAVideoUsage has student_id field"""
        assert hasattr(EBAVideoUsage, "student_id")

    def test_eba_video_usage_has_started_at_field(self):
        """Test EBAVideoUsage has started_at field"""
        assert hasattr(EBAVideoUsage, "started_at")

    def test_eba_video_usage_has_ended_at_field(self):
        """Test EBAVideoUsage has ended_at field"""
        assert hasattr(EBAVideoUsage, "ended_at")

    def test_eba_video_usage_has_watch_duration_seconds_field(self):
        """Test EBAVideoUsage has watch_duration_seconds field"""
        assert hasattr(EBAVideoUsage, "watch_duration_seconds")

    def test_eba_video_usage_has_completion_percentage_field(self):
        """Test EBAVideoUsage has completion_percentage field"""
        assert hasattr(EBAVideoUsage, "completion_percentage")

    def test_eba_video_usage_has_paused_count_field(self):
        """Test EBAVideoUsage has paused_count field"""
        assert hasattr(EBAVideoUsage, "paused_count")

    def test_eba_video_usage_has_rewound_count_field(self):
        """Test EBAVideoUsage has rewound_count field"""
        assert hasattr(EBAVideoUsage, "rewound_count")

    def test_eba_video_usage_has_fast_forwarded_count_field(self):
        """Test EBAVideoUsage has fast_forwarded_count field"""
        assert hasattr(EBAVideoUsage, "fast_forwarded_count")

    def test_eba_video_usage_has_user_rating_field(self):
        """Test EBAVideoUsage has user_rating field"""
        assert hasattr(EBAVideoUsage, "user_rating")

    def test_eba_video_usage_has_user_feedback_field(self):
        """Test EBAVideoUsage has user_feedback field"""
        assert hasattr(EBAVideoUsage, "user_feedback")

    def test_eba_video_usage_has_pre_knowledge_score_field(self):
        """Test EBAVideoUsage has pre_knowledge_score field"""
        assert hasattr(EBAVideoUsage, "pre_knowledge_score")

    def test_eba_video_usage_has_post_knowledge_score_field(self):
        """Test EBAVideoUsage has post_knowledge_score field"""
        assert hasattr(EBAVideoUsage, "post_knowledge_score")

    def test_eba_video_usage_has_learning_effectiveness_field(self):
        """Test EBAVideoUsage has learning_effectiveness field"""
        assert hasattr(EBAVideoUsage, "learning_effectiveness")

    def test_eba_video_usage_has_video_relationship(self):
        """Test EBAVideoUsage has video relationship"""
        assert hasattr(EBAVideoUsage, "video")


# ============================================================================
# EBA VIDEO RECOMMENDATION MODEL TESTS
# ============================================================================


class TestEBAVideoRecommendationModel:
    """Test EBAVideoRecommendation model definition"""

    def test_eba_video_recommendation_inherits_from_base(self):
        """Test EBAVideoRecommendation inherits from Base"""
        assert issubclass(EBAVideoRecommendation, Base)

    def test_eba_video_recommendation_table_name(self):
        """Test EBAVideoRecommendation table name"""
        assert EBAVideoRecommendation.__tablename__ == "eba_video_recommendations"

    def test_eba_video_recommendation_has_id_field(self):
        """Test EBAVideoRecommendation has id field"""
        assert hasattr(EBAVideoRecommendation, "id")

    def test_eba_video_recommendation_has_video_id_field(self):
        """Test EBAVideoRecommendation has video_id field"""
        assert hasattr(EBAVideoRecommendation, "video_id")

    def test_eba_video_recommendation_has_student_id_field(self):
        """Test EBAVideoRecommendation has student_id field"""
        assert hasattr(EBAVideoRecommendation, "student_id")

    def test_eba_video_recommendation_has_recommendation_score_field(self):
        """Test EBAVideoRecommendation has recommendation_score field"""
        assert hasattr(EBAVideoRecommendation, "recommendation_score")

    def test_eba_video_recommendation_has_recommendation_reason_field(self):
        """Test EBAVideoRecommendation has recommendation_reason field"""
        assert hasattr(EBAVideoRecommendation, "recommendation_reason")

    def test_eba_video_recommendation_has_recommendation_category_field(self):
        """Test EBAVideoRecommendation has recommendation_category field"""
        assert hasattr(EBAVideoRecommendation, "recommendation_category")

    def test_eba_video_recommendation_has_learning_style_match_field(self):
        """Test EBAVideoRecommendation has learning_style_match field"""
        assert hasattr(EBAVideoRecommendation, "learning_style_match")

    def test_eba_video_recommendation_has_difficulty_appropriateness_field(self):
        """Test EBAVideoRecommendation has difficulty_appropriateness field"""
        assert hasattr(EBAVideoRecommendation, "difficulty_appropriateness")

    def test_eba_video_recommendation_has_curriculum_relevance_field(self):
        """Test EBAVideoRecommendation has curriculum_relevance field"""
        assert hasattr(EBAVideoRecommendation, "curriculum_relevance")

    def test_eba_video_recommendation_has_shown_to_student_field(self):
        """Test EBAVideoRecommendation has shown_to_student field"""
        assert hasattr(EBAVideoRecommendation, "shown_to_student")

    def test_eba_video_recommendation_has_clicked_by_student_field(self):
        """Test EBAVideoRecommendation has clicked_by_student field"""
        assert hasattr(EBAVideoRecommendation, "clicked_by_student")

    def test_eba_video_recommendation_has_watched_by_student_field(self):
        """Test EBAVideoRecommendation has watched_by_student field"""
        assert hasattr(EBAVideoRecommendation, "watched_by_student")

    def test_eba_video_recommendation_has_created_at_field(self):
        """Test EBAVideoRecommendation has created_at field"""
        assert hasattr(EBAVideoRecommendation, "created_at")

    def test_eba_video_recommendation_has_shown_at_field(self):
        """Test EBAVideoRecommendation has shown_at field"""
        assert hasattr(EBAVideoRecommendation, "shown_at")

    def test_eba_video_recommendation_has_clicked_at_field(self):
        """Test EBAVideoRecommendation has clicked_at field"""
        assert hasattr(EBAVideoRecommendation, "clicked_at")

    def test_eba_video_recommendation_has_video_relationship(self):
        """Test EBAVideoRecommendation has video relationship"""
        assert hasattr(EBAVideoRecommendation, "video")


# ============================================================================
# EBA CONTENT COLLECTION MODEL TESTS
# ============================================================================


class TestEBAContentCollectionModel:
    """Test EBAContentCollection model definition"""

    def test_eba_content_collection_inherits_from_base(self):
        """Test EBAContentCollection inherits from Base"""
        assert issubclass(EBAContentCollection, Base)

    def test_eba_content_collection_table_name(self):
        """Test EBAContentCollection table name"""
        assert EBAContentCollection.__tablename__ == "eba_content_collections"

    def test_eba_content_collection_has_id_field(self):
        """Test EBAContentCollection has id field"""
        assert hasattr(EBAContentCollection, "id")

    def test_eba_content_collection_has_name_field(self):
        """Test EBAContentCollection has name field"""
        assert hasattr(EBAContentCollection, "name")

    def test_eba_content_collection_has_description_field(self):
        """Test EBAContentCollection has description field"""
        assert hasattr(EBAContentCollection, "description")

    def test_eba_content_collection_has_category_field(self):
        """Test EBAContentCollection has category field"""
        assert hasattr(EBAContentCollection, "category")

    def test_eba_content_collection_has_grade_level_field(self):
        """Test EBAContentCollection has grade_level field"""
        assert hasattr(EBAContentCollection, "grade_level")

    def test_eba_content_collection_has_video_ids_field(self):
        """Test EBAContentCollection has video_ids field"""
        assert hasattr(EBAContentCollection, "video_ids")

    def test_eba_content_collection_has_total_videos_field(self):
        """Test EBAContentCollection has total_videos field"""
        assert hasattr(EBAContentCollection, "total_videos")

    def test_eba_content_collection_has_total_duration_minutes_field(self):
        """Test EBAContentCollection has total_duration_minutes field"""
        assert hasattr(EBAContentCollection, "total_duration_minutes")

    def test_eba_content_collection_has_average_quality_score_field(self):
        """Test EBAContentCollection has average_quality_score field"""
        assert hasattr(EBAContentCollection, "average_quality_score")

    def test_eba_content_collection_has_is_active_field(self):
        """Test EBAContentCollection has is_active field"""
        assert hasattr(EBAContentCollection, "is_active")

    def test_eba_content_collection_has_is_featured_field(self):
        """Test EBAContentCollection has is_featured field"""
        assert hasattr(EBAContentCollection, "is_featured")

    def test_eba_content_collection_has_created_by_field(self):
        """Test EBAContentCollection has created_by field"""
        assert hasattr(EBAContentCollection, "created_by")

    def test_eba_content_collection_has_created_at_field(self):
        """Test EBAContentCollection has created_at field"""
        assert hasattr(EBAContentCollection, "created_at")

    def test_eba_content_collection_has_updated_at_field(self):
        """Test EBAContentCollection has updated_at field"""
        assert hasattr(EBAContentCollection, "updated_at")


# ============================================================================
# EBA CONTENT ANALYTICS MODEL TESTS
# ============================================================================


class TestEBAContentAnalyticsModel:
    """Test EBAContentAnalytics model definition"""

    def test_eba_content_analytics_inherits_from_base(self):
        """Test EBAContentAnalytics inherits from Base"""
        assert issubclass(EBAContentAnalytics, Base)

    def test_eba_content_analytics_table_name(self):
        """Test EBAContentAnalytics table name"""
        assert EBAContentAnalytics.__tablename__ == "eba_content_analytics"

    def test_eba_content_analytics_has_id_field(self):
        """Test EBAContentAnalytics has id field"""
        assert hasattr(EBAContentAnalytics, "id")

    def test_eba_content_analytics_has_analysis_date_field(self):
        """Test EBAContentAnalytics has analysis_date field"""
        assert hasattr(EBAContentAnalytics, "analysis_date")

    def test_eba_content_analytics_has_category_field(self):
        """Test EBAContentAnalytics has category field"""
        assert hasattr(EBAContentAnalytics, "category")

    def test_eba_content_analytics_has_grade_level_field(self):
        """Test EBAContentAnalytics has grade_level field"""
        assert hasattr(EBAContentAnalytics, "grade_level")

    def test_eba_content_analytics_has_total_views_field(self):
        """Test EBAContentAnalytics has total_views field"""
        assert hasattr(EBAContentAnalytics, "total_views")

    def test_eba_content_analytics_has_unique_viewers_field(self):
        """Test EBAContentAnalytics has unique_viewers field"""
        assert hasattr(EBAContentAnalytics, "unique_viewers")

    def test_eba_content_analytics_has_total_watch_time_minutes_field(self):
        """Test EBAContentAnalytics has total_watch_time_minutes field"""
        assert hasattr(EBAContentAnalytics, "total_watch_time_minutes")

    def test_eba_content_analytics_has_average_completion_rate_field(self):
        """Test EBAContentAnalytics has average_completion_rate field"""
        assert hasattr(EBAContentAnalytics, "average_completion_rate")

    def test_eba_content_analytics_has_average_user_rating_field(self):
        """Test EBAContentAnalytics has average_user_rating field"""
        assert hasattr(EBAContentAnalytics, "average_user_rating")

    def test_eba_content_analytics_has_total_ratings_field(self):
        """Test EBAContentAnalytics has total_ratings field"""
        assert hasattr(EBAContentAnalytics, "total_ratings")

    def test_eba_content_analytics_has_average_learning_effectiveness_field(self):
        """Test EBAContentAnalytics has average_learning_effectiveness field"""
        assert hasattr(EBAContentAnalytics, "average_learning_effectiveness")

    def test_eba_content_analytics_has_trending_score_field(self):
        """Test EBAContentAnalytics has trending_score field"""
        assert hasattr(EBAContentAnalytics, "trending_score")

    def test_eba_content_analytics_has_engagement_score_field(self):
        """Test EBAContentAnalytics has engagement_score field"""
        assert hasattr(EBAContentAnalytics, "engagement_score")

    def test_eba_content_analytics_has_created_at_field(self):
        """Test EBAContentAnalytics has created_at field"""
        assert hasattr(EBAContentAnalytics, "created_at")
