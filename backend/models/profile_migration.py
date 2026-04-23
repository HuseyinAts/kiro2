"""
Helper utilities for migrating legacy student profiles to canonical model.

This module provides tools for migrating data from deprecated profile models
(StudentProfile, StudentLearningProfile) to LearningPathStudentProfile.

Usage:
    from backend.models.profile_migration import ProfileMigrationService
    from backend.core.database import get_db

    db = next(get_db())
    service = ProfileMigrationService(db)
    stats = service.migrate_all()
    print(f"Migrated {stats['student_profiles_migrated']} profiles")
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from .learning_path_models import LearningPathStudentProfile
from .student_learning_profile import StudentLearningProfile
from .user_models import StudentProfile

logger = logging.getLogger(__name__)


class ProfileMigrationService:
    """Service for migrating legacy student profiles to canonical model."""

    def __init__(self, db: Session):
        """
        Initialize migration service.

        Args:
            db: Database session
        """
        self.db = db

    def migrate_student_profile(
        self,
        legacy_profile: StudentProfile
    ) -> LearningPathStudentProfile:
        """
        Migrate a single StudentProfile to canonical model.

        Args:
            legacy_profile: Legacy StudentProfile instance

        Returns:
            New LearningPathStudentProfile instance (not committed)
        """
        try:
            canonical = LearningPathStudentProfile(
                student_id=legacy_profile.id,
                user_id=legacy_profile.user_id,
                name=f"{legacy_profile.user.first_name} {legacy_profile.user.last_name}" if hasattr(legacy_profile, 'user') and legacy_profile.user else "",
                grade=str(legacy_profile.grade_level),
                exam_target=legacy_profile.hedef_sinav or "YKS",
                learning_style=legacy_profile.learning_style.value if legacy_profile.learning_style else "mixed",
                available_time=legacy_profile.study_hours_per_day * 60 if legacy_profile.study_hours_per_day else 60,
                target_university=legacy_profile.target_university,
                target_department=legacy_profile.target_department,
                total_study_time_minutes=legacy_profile.total_study_hours * 60 if legacy_profile.total_study_hours else 0,
                created_at=legacy_profile.created_at,
                updated_at=legacy_profile.updated_at,
            )

            logger.info(f"Migrated StudentProfile {legacy_profile.id} -> {canonical.student_id}")
            return canonical

        except Exception as e:
            logger.error(f"Error migrating StudentProfile {legacy_profile.id}: {e}")
            raise

    def migrate_student_learning_profile(
        self,
        legacy_profile: StudentLearningProfile
    ) -> LearningPathStudentProfile:
        """
        Migrate a single StudentLearningProfile to canonical model.

        Args:
            legacy_profile: Legacy StudentLearningProfile instance

        Returns:
            New LearningPathStudentProfile instance (not committed)
        """
        try:
            canonical = LearningPathStudentProfile(
                student_id=legacy_profile.id,
                user_id=legacy_profile.student_id,
                name="",  # Will need to fetch from User
                grade="12",  # Default
                exam_target="YKS",  # Default
                learning_style=legacy_profile.dominant_vark_style or "mixed",
                vark_visual_score=legacy_profile.vark_visual,
                vark_auditory_score=legacy_profile.vark_auditory,
                vark_reading_score=legacy_profile.vark_reading,
                vark_kinesthetic_score=legacy_profile.vark_kinesthetic,
                felder_active_reflective=legacy_profile.felder_active_reflective,
                felder_sensing_intuitive=legacy_profile.felder_sensing_intuitive,
                felder_visual_verbal=legacy_profile.felder_visual_verbal,
                felder_sequential_global=legacy_profile.felder_sequential_global,
                created_at=legacy_profile.detected_at,
                updated_at=legacy_profile.updated_at,
            )

            logger.info(f"Migrated StudentLearningProfile {legacy_profile.id} -> {canonical.student_id}")
            return canonical

        except Exception as e:
            logger.error(f"Error migrating StudentLearningProfile {legacy_profile.id}: {e}")
            raise

    def migrate_all(
        self,
        batch_size: int = 100,
        skip_existing: bool = True
    ) -> dict[str, Any]:
        """
        Migrate all legacy profiles.

        Args:
            batch_size: Number of records to process at a time
            skip_existing: Skip if canonical profile already exists

        Returns:
            Migration statistics dictionary with keys:
                - student_profiles_migrated: int
                - student_learning_profiles_migrated: int
                - errors: List[str]
                - skipped: int
        """
        stats: dict[str, Any] = {
            "student_profiles_migrated": 0,
            "student_learning_profiles_migrated": 0,
            "errors": [],
            "skipped": 0,
        }

        # Migrate StudentProfile
        try:
            logger.info("Starting StudentProfile migration...")
            legacy_profiles = self.db.query(StudentProfile).all()
            logger.info(f"Found {len(legacy_profiles)} StudentProfile records")

            for legacy in legacy_profiles:
                try:
                    # Check for existing canonical profile
                    if skip_existing:
                        existing = self.db.query(LearningPathStudentProfile).filter(
                            LearningPathStudentProfile.student_id == legacy.id
                        ).first()

                        if existing:
                            logger.debug(f"Skipping StudentProfile {legacy.id} - already exists")
                            stats["skipped"] += 1
                            continue

                    canonical = self.migrate_student_profile(legacy)
                    self.db.add(canonical)
                    stats["student_profiles_migrated"] += 1

                except Exception as e:
                    error_msg = f"StudentProfile {legacy.id}: {e!s}"
                    stats["errors"].append(error_msg)
                    logger.error(error_msg)

        except Exception as e:
            error_msg = f"Failed to query StudentProfile: {e}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)

        # Migrate StudentLearningProfile
        try:
            logger.info("Starting StudentLearningProfile migration...")
            learning_profiles = self.db.query(StudentLearningProfile).all()
            logger.info(f"Found {len(learning_profiles)} StudentLearningProfile records")

            for legacy in learning_profiles:
                try:
                    # Check for existing canonical profile
                    if skip_existing:
                        existing = self.db.query(LearningPathStudentProfile).filter(
                            LearningPathStudentProfile.student_id == legacy.id
                        ).first()

                        if existing:
                            logger.debug(f"Skipping StudentLearningProfile {legacy.id} - already exists")
                            stats["skipped"] += 1
                            continue

                    canonical = self.migrate_student_learning_profile(legacy)
                    self.db.add(canonical)
                    stats["student_learning_profiles_migrated"] += 1

                except Exception as e:
                    error_msg = f"StudentLearningProfile {legacy.id}: {e!s}"
                    stats["errors"].append(error_msg)
                    logger.error(error_msg)

        except Exception as e:
            error_msg = f"Failed to query StudentLearningProfile: {e}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)

        # Commit all changes
        try:
            self.db.commit()
            logger.info(f"Migration complete: {stats}")
        except Exception as e:
            self.db.rollback()
            error_msg = f"Commit failed: {e!s}"
            stats["errors"].append(error_msg)
            logger.error(error_msg)

        return stats

    def migrate_specific_student(
        self,
        student_id: str
    ) -> LearningPathStudentProfile | None:
        """
        Migrate a specific student by ID.

        Searches both legacy tables and migrates if found.

        Args:
            student_id: Student ID to migrate

        Returns:
            Migrated LearningPathStudentProfile or None if not found
        """
        # Check StudentProfile
        student_profile = self.db.query(StudentProfile).filter(
            StudentProfile.id == student_id
        ).first()

        if student_profile:
            logger.info(f"Found student in StudentProfile: {student_id}")
            canonical = self.migrate_student_profile(student_profile)
            self.db.add(canonical)
            self.db.commit()
            return canonical

        # Check StudentLearningProfile
        learning_profile = self.db.query(StudentLearningProfile).filter(
            StudentLearningProfile.id == student_id
        ).first()

        if learning_profile:
            logger.info(f"Found student in StudentLearningProfile: {student_id}")
            canonical = self.migrate_student_learning_profile(learning_profile)
            self.db.add(canonical)
            self.db.commit()
            return canonical

        logger.warning(f"Student {student_id} not found in legacy tables")
        return None


def check_migration_status(db: Session) -> dict[str, Any]:
    """
    Check the current migration status.

    Args:
        db: Database session

    Returns:
        Status information dictionary with keys:
            - canonical_profiles: int
            - legacy_student_profiles: int
            - legacy_learning_profiles: int
            - migration_complete: bool
            - migration_percentage: float
    """
    try:
        canonical_count = db.query(LearningPathStudentProfile).count()
        legacy_sp_count = db.query(StudentProfile).count()
        legacy_slp_count = db.query(StudentLearningProfile).count()

        total_legacy = legacy_sp_count + legacy_slp_count
        migration_percentage = (canonical_count / total_legacy * 100) if total_legacy > 0 else 100.0

        return {
            "canonical_profiles": canonical_count,
            "legacy_student_profiles": legacy_sp_count,
            "legacy_learning_profiles": legacy_slp_count,
            "migration_complete": canonical_count > 0 and total_legacy == 0,
            "migration_percentage": round(migration_percentage, 2),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat(),
        }


def validate_canonical_profile(
    profile: LearningPathStudentProfile
) -> dict[str, Any]:
    """
    Validate a canonical profile for completeness.

    Args:
        profile: LearningPathStudentProfile to validate

    Returns:
        Validation results dictionary with keys:
            - is_valid: bool
            - warnings: List[str]
            - missing_fields: List[str]
    """
    warnings = []
    missing_fields = []

    # Check required fields
    if not profile.name or profile.name.strip() == "":
        missing_fields.append("name")

    if not profile.user_id:
        warnings.append("No user_id - profile not linked to User")

    # Check optional but recommended fields
    if not profile.target_university:
        warnings.append("No target_university")

    if not profile.target_department:
        warnings.append("No target_department")

    # Check VARK scores
    vark_scores = [
        profile.vark_visual_score,
        profile.vark_auditory_score,
        profile.vark_reading_score,
        profile.vark_kinesthetic_score
    ]
    if all(s is None for s in vark_scores):
        warnings.append("No VARK scores")

    # Check Felder-Silverman scores
    felder_scores = [
        profile.felder_active_reflective,
        profile.felder_sensing_intuitive,
        profile.felder_visual_verbal,
        profile.felder_sequential_global
    ]
    if all(s is None for s in felder_scores):
        warnings.append("No Felder-Silverman scores")

    is_valid = len(missing_fields) == 0

    return {
        "is_valid": is_valid,
        "warnings": warnings,
        "missing_fields": missing_fields,
    }
