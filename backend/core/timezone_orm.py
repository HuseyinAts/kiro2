"""
SQLAlchemy ORM Timezone Event Listeners - Phase 3.0
Automatic UTC timestamp management for all database models

This module provides SQLAlchemy event listeners that automatically:
1. Set created_at with UTC timezone on INSERT
2. Update updated_at with UTC timezone on UPDATE
3. Ensure all datetime fields are UTC timezone-aware
4. Prevent timezone-naive datetimes from being saved to database

Integration:
    from core.timezone_orm import setup_timezone_listeners
    from models.base import Base

    # After defining all models, before creating engine
    setup_timezone_listeners(Base)
"""

from datetime import datetime
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session, Mapper
from typing import Any, Dict
import logging

from core.timezone_utils import now_utc, ensure_utc, is_timezone_aware

logger = logging.getLogger(__name__)


# ================================================================
# AUTOMATIC TIMESTAMP LISTENERS
# ================================================================

def before_insert_set_timestamps(mapper: Mapper, connection, target):
    """
    Before INSERT: Automatically set created_at and updated_at to UTC

    This listener fires before any INSERT operation and ensures:
    - created_at is set to current UTC time if not already set
    - updated_at is set to current UTC time if not already set
    - Both fields are timezone-aware

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Model instance being inserted
    """
    current_time = now_utc()

    # Set created_at if field exists and is None
    if hasattr(target, 'created_at') and target.created_at is None:
        target.created_at = current_time
        logger.debug(f"Auto-set created_at for {target.__class__.__name__}: {current_time}")

    # Set updated_at if field exists and is None
    if hasattr(target, 'updated_at') and target.updated_at is None:
        target.updated_at = current_time
        logger.debug(f"Auto-set updated_at for {target.__class__.__name__}: {current_time}")


def before_update_set_timestamp(mapper: Mapper, connection, target):
    """
    Before UPDATE: Automatically update updated_at to current UTC time

    This listener fires before any UPDATE operation and ensures:
    - updated_at is always set to current UTC time
    - Field is timezone-aware

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Model instance being updated
    """
    current_time = now_utc()

    # Always update updated_at on UPDATE operations
    if hasattr(target, 'updated_at'):
        target.updated_at = current_time
        logger.debug(f"Auto-updated updated_at for {target.__class__.__name__}: {current_time}")


def before_insert_ensure_utc(mapper: Mapper, connection, target):
    """
    Before INSERT: Ensure all datetime fields are UTC timezone-aware

    This listener scans all datetime fields in the model and:
    - Converts timezone-naive datetimes to UTC timezone-aware
    - Converts non-UTC timezone-aware datetimes to UTC
    - Logs warnings for timezone-naive datetimes (should not happen)

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Model instance being inserted
    """
    _ensure_all_datetimes_utc(target, operation="INSERT")


def before_update_ensure_utc(mapper: Mapper, connection, target):
    """
    Before UPDATE: Ensure all datetime fields are UTC timezone-aware

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Model instance being updated
    """
    _ensure_all_datetimes_utc(target, operation="UPDATE")


def _ensure_all_datetimes_utc(target: Any, operation: str = "OPERATION"):
    """
    Internal helper: Ensure all datetime fields in model are UTC

    Scans all columns in the model, finds DateTime columns, and ensures
    they are UTC timezone-aware.

    Args:
        target: Model instance
        operation: Operation name for logging (INSERT/UPDATE)
    """
    # Get model inspection
    insp = inspect(target.__class__)

    # Iterate through all columns
    for column in insp.columns:
        # Check if column is DateTime type
        if hasattr(column.type, 'python_type') and column.type.python_type == datetime:
            # Get field value
            field_name = column.key
            field_value = getattr(target, field_name, None)

            if field_value is not None:
                # Check if timezone-naive (THIS SHOULD NOT HAPPEN)
                if not is_timezone_aware(field_value):
                    logger.warning(
                        f"[{operation}] Timezone-naive datetime detected in "
                        f"{target.__class__.__name__}.{field_name}: {field_value}. "
                        f"Converting to UTC. This indicates a bug - all datetimes "
                        f"should be timezone-aware."
                    )

                # Ensure UTC
                utc_value = ensure_utc(field_value)
                setattr(target, field_name, utc_value)

                if field_value != utc_value:
                    logger.debug(
                        f"[{operation}] Converted {target.__class__.__name__}.{field_name} "
                        f"from {field_value} to {utc_value}"
                    )


# ================================================================
# SESSION-LEVEL LISTENERS
# ================================================================

def before_flush_validate_datetimes(session: Session, flush_context, instances):
    """
    Before FLUSH: Validate all datetime fields are timezone-aware

    This listener fires before session flush and validates that all
    datetime fields in all dirty objects are timezone-aware.

    This is a safety net to catch timezone-naive datetimes before they
    reach the database.

    Args:
        session: SQLAlchemy session
        flush_context: Flush context
        instances: Instances being flushed
    """
    for instance in session.dirty | session.new:
        _validate_instance_datetimes(instance)


def _validate_instance_datetimes(instance: Any):
    """
    Internal helper: Validate all datetime fields in instance are timezone-aware

    Raises warning if timezone-naive datetime is found.

    Args:
        instance: Model instance to validate
    """
    insp = inspect(instance.__class__)

    for column in insp.columns:
        if hasattr(column.type, 'python_type') and column.type.python_type == datetime:
            field_name = column.key
            field_value = getattr(instance, field_name, None)

            if field_value is not None and not is_timezone_aware(field_value):
                logger.error(
                    f"TIMEZONE VALIDATION FAILED: {instance.__class__.__name__}.{field_name} "
                    f"has timezone-naive datetime: {field_value}. "
                    f"This will cause database errors. Use now_utc() instead of datetime.now()."
                )


# ================================================================
# LISTENER SETUP
# ================================================================

def setup_timezone_listeners(base_class):
    """
    Setup all timezone-related event listeners for SQLAlchemy models

    This function registers event listeners for all models that inherit from
    the provided base class. It should be called once during application startup,
    after all models are defined but before creating the engine.

    Features:
    - Auto-set created_at and updated_at on INSERT
    - Auto-update updated_at on UPDATE
    - Ensure all datetime fields are UTC timezone-aware
    - Validate datetimes before flush

    Args:
        base_class: SQLAlchemy declarative base class

    Example:
        from sqlalchemy.ext.declarative import declarative_base
        from core.timezone_orm import setup_timezone_listeners

        Base = declarative_base()

        # Define models here...

        # Setup timezone listeners ONCE during app initialization
        setup_timezone_listeners(Base)

        # Create engine and tables
        engine = create_engine(...)
        Base.metadata.create_all(engine)
    """
    # Register mapper-level events (per-model)
    # These fire for each INSERT/UPDATE operation

    @event.listens_for(base_class, 'before_insert', propagate=True)
    def receive_before_insert(mapper, connection, target):
        """Before INSERT: Set timestamps and ensure UTC"""
        before_insert_set_timestamps(mapper, connection, target)
        before_insert_ensure_utc(mapper, connection, target)

    @event.listens_for(base_class, 'before_update', propagate=True)
    def receive_before_update(mapper, connection, target):
        """Before UPDATE: Update timestamp and ensure UTC"""
        before_update_set_timestamp(mapper, connection, target)
        before_update_ensure_utc(mapper, connection, target)

    logger.info(f"Timezone event listeners registered for {base_class.__name__} and all subclasses")
    logger.info("Features enabled: auto-timestamps, UTC enforcement, validation")


def setup_session_timezone_listeners(session_factory):
    """
    Setup session-level timezone listeners

    This function registers event listeners for session events like flush.
    It should be called once during application startup.

    Args:
        session_factory: SQLAlchemy sessionmaker instance

    Example:
        from sqlalchemy.orm import sessionmaker
        from core.timezone_orm import setup_session_timezone_listeners

        SessionLocal = sessionmaker(bind=engine)

        # Setup session listeners
        setup_session_timezone_listeners(SessionLocal)
    """
    @event.listens_for(session_factory, 'before_flush')
    def receive_before_flush(session, flush_context, instances):
        """Before FLUSH: Validate all datetimes"""
        before_flush_validate_datetimes(session, flush_context, instances)

    logger.info("Session-level timezone listeners registered")


# ================================================================
# MANUAL TIMESTAMP HELPERS
# ================================================================

def set_created_timestamp(instance: Any):
    """
    Manually set created_at timestamp to current UTC time

    Use this if you need to explicitly set created_at outside of ORM events.

    Args:
        instance: Model instance

    Example:
        user = User(email="test@example.com")
        set_created_timestamp(user)
        # user.created_at is now set to current UTC time
    """
    if hasattr(instance, 'created_at'):
        instance.created_at = now_utc()


def set_updated_timestamp(instance: Any):
    """
    Manually set updated_at timestamp to current UTC time

    Use this if you need to explicitly update updated_at outside of ORM events.

    Args:
        instance: Model instance

    Example:
        user = get_user_from_db()
        user.email = "new@example.com"
        set_updated_timestamp(user)
        # user.updated_at is now set to current UTC time
    """
    if hasattr(instance, 'updated_at'):
        instance.updated_at = now_utc()


def set_all_timestamps(instance: Any):
    """
    Manually set both created_at and updated_at timestamps

    Args:
        instance: Model instance

    Example:
        user = User(email="test@example.com")
        set_all_timestamps(user)
        # Both created_at and updated_at are set
    """
    set_created_timestamp(instance)
    set_updated_timestamp(instance)


# ================================================================
# DEBUGGING UTILITIES
# ================================================================

def check_instance_timezone_compliance(instance: Any) -> Dict[str, Any]:
    """
    Check if all datetime fields in instance are timezone-aware

    Returns diagnostic information about timezone compliance.

    Args:
        instance: Model instance to check

    Returns:
        dict: Diagnostic information with:
            - compliant: bool (True if all datetimes are timezone-aware UTC)
            - issues: list of issues found
            - field_status: dict of field -> status

    Example:
        user = get_user_from_db()
        report = check_instance_timezone_compliance(user)
        if not report['compliant']:
            print(f"Issues found: {report['issues']}")
    """
    insp = inspect(instance.__class__)
    issues = []
    field_status = {}

    for column in insp.columns:
        if hasattr(column.type, 'python_type') and column.type.python_type == datetime:
            field_name = column.key
            field_value = getattr(instance, field_name, None)

            if field_value is None:
                field_status[field_name] = "null"
            elif not is_timezone_aware(field_value):
                field_status[field_name] = "timezone-naive (VIOLATION)"
                issues.append(f"{field_name}: timezone-naive datetime ({field_value})")
            elif field_value.tzinfo.utcoffset(field_value).total_seconds() != 0:
                field_status[field_name] = "non-UTC timezone (WARNING)"
                issues.append(f"{field_name}: non-UTC timezone ({field_value.tzinfo})")
            else:
                field_status[field_name] = "compliant (UTC timezone-aware)"

    return {
        "compliant": len(issues) == 0,
        "issues": issues,
        "field_status": field_status,
        "model": instance.__class__.__name__,
    }


def audit_session_timezone_compliance(session: Session) -> Dict[str, Any]:
    """
    Audit all instances in session for timezone compliance

    Checks all dirty and new instances in the session.

    Args:
        session: SQLAlchemy session

    Returns:
        dict: Audit report with:
            - total_instances: count of instances checked
            - compliant_instances: count of compliant instances
            - non_compliant_instances: count of non-compliant instances
            - issues: list of all issues found

    Example:
        report = audit_session_timezone_compliance(session)
        if report['non_compliant_instances'] > 0:
            print(f"Found {report['non_compliant_instances']} non-compliant instances")
            print(f"Issues: {report['issues']}")
    """
    all_instances = list(session.dirty | session.new)
    total = len(all_instances)
    compliant = 0
    non_compliant = 0
    all_issues = []

    for instance in all_instances:
        report = check_instance_timezone_compliance(instance)
        if report['compliant']:
            compliant += 1
        else:
            non_compliant += 1
            all_issues.extend(
                [f"{instance.__class__.__name__}: {issue}" for issue in report['issues']]
            )

    return {
        "total_instances": total,
        "compliant_instances": compliant,
        "non_compliant_instances": non_compliant,
        "issues": all_issues,
        "compliance_rate": f"{(compliant / total * 100):.1f}%" if total > 0 else "N/A",
    }


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    # Setup functions
    "setup_timezone_listeners",
    "setup_session_timezone_listeners",

    # Manual timestamp helpers
    "set_created_timestamp",
    "set_updated_timestamp",
    "set_all_timestamps",

    # Debugging utilities
    "check_instance_timezone_compliance",
    "audit_session_timezone_compliance",
]
