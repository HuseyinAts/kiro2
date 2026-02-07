"""
Validators Module
Teknofest 2025 - Eğitim Eylemci Projesi

Input validation utilities for learning path agent
"""

import re
from typing import Dict, Any, Optional

from ..models import LearningStyle, KnowledgeLevel


class ValidationError(Exception):
    """Custom validation error"""

    pass


class StudentDataValidator:
    """Validator for student data inputs"""

    REQUIRED_FIELDS = ["student_id", "name", "grade"]
    VALID_GRADES = ["5", "6", "7", "8", "9", "10", "11", "12"]
    VALID_EXAM_TARGETS = ["LGS", "YKS", "TYT", "AYT", "Genel"]

    @staticmethod
    def validate_student_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate student data dictionary

        Args:
            data: Student data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        for field in StudentDataValidator.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                return False, f"Required field missing: {field}"

        # Validate student_id format
        student_id = data["student_id"]
        if not isinstance(student_id, str) or len(student_id) < 3:
            return False, "student_id must be at least 3 characters"

        # Validate name
        name = data["name"]
        if not isinstance(name, str) or len(name) < 2:
            return False, "name must be at least 2 characters"

        # Validate grade
        grade = str(data["grade"])
        if grade not in StudentDataValidator.VALID_GRADES:
            return (
                False,
                f"grade must be one of: {', '.join(StudentDataValidator.VALID_GRADES)}",
            )

        # Validate exam_target if provided
        if "exam_target" in data and data["exam_target"]:
            if data["exam_target"] not in StudentDataValidator.VALID_EXAM_TARGETS:
                return (
                    False,
                    f"exam_target must be one of: {', '.join(StudentDataValidator.VALID_EXAM_TARGETS)}",
                )

        # Validate learning_style if provided
        if "learning_style" in data and data["learning_style"]:
            try:
                LearningStyle(data["learning_style"])
            except ValueError:
                valid_styles = [ls.value for ls in LearningStyle]
                return (
                    False,
                    f"learning_style must be one of: {', '.join(valid_styles)}",
                )

        # Validate knowledge_level if provided
        if "knowledge_level" in data and data["knowledge_level"]:
            try:
                KnowledgeLevel(data["knowledge_level"])
            except ValueError:
                valid_levels = [kl.value for kl in KnowledgeLevel]
                return (
                    False,
                    f"knowledge_level must be one of: {', '.join(valid_levels)}",
                )

        # Validate available_time if provided
        if "available_time" in data and data["available_time"] is not None:
            try:
                time_val = int(data["available_time"])
                if time_val < 0 or time_val > 168:  # Max 168 hours per week
                    return (
                        False,
                        "available_time must be between 0 and 168 hours per week",
                    )
            except (ValueError, TypeError):
                return False, "available_time must be an integer"

        # Validate interests if provided
        if "interests" in data and data["interests"]:
            if not isinstance(data["interests"], list):
                return False, "interests must be a list"

        return True, None

    @staticmethod
    def validate_student_id(student_id: str) -> bool:
        """Validate student ID format"""
        if not isinstance(student_id, str):
            return False
        if len(student_id) < 3 or len(student_id) > 50:
            return False
        # Only alphanumeric and underscores
        if not re.match(r"^[a-zA-Z0-9_]+$", student_id):
            return False
        return True


class AssessmentDataValidator:
    """Validator for assessment-related data"""

    @staticmethod
    def validate_assessment_request(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate assessment request data"""
        # Check student_id
        if "student_id" not in data or not data["student_id"]:
            return False, "student_id is required"

        if not StudentDataValidator.validate_student_id(data["student_id"]):
            return False, "Invalid student_id format"

        # Check subject
        if "subject" not in data or not data["subject"]:
            return False, "subject is required"

        # Validate question_count if provided
        if "question_count" in data:
            try:
                count = int(data["question_count"])
                if count < 1 or count > 50:
                    return False, "question_count must be between 1 and 50"
            except (ValueError, TypeError):
                return False, "question_count must be an integer"

        return True, None

    @staticmethod
    def validate_assessment_results(
        results: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate assessment results data"""
        # Check required fields
        if "student_id" not in results:
            return False, "student_id is required in results"

        if "scores" not in results and "topic_scores" not in results:
            return False, "scores or topic_scores required in results"

        # Validate scores
        if "scores" in results:
            if not isinstance(results["scores"], list):
                return False, "scores must be a list"
            for score in results["scores"]:
                if not isinstance(score, (int, float)) or score < 0 or score > 100:
                    return False, "Each score must be between 0 and 100"

        # Validate topic_scores
        if "topic_scores" in results:
            if not isinstance(results["topic_scores"], dict):
                return False, "topic_scores must be a dictionary"
            for topic, score in results["topic_scores"].items():
                if not isinstance(score, (int, float)) or score < 0 or score > 100:
                    return False, f"Score for {topic} must be between 0 and 100"

        return True, None


class ResourceDataValidator:
    """Validator for resource-related data"""

    VALID_PLATFORMS = ["youtube", "khan_academy", "oer", "custom"]
    VALID_RESOURCE_TYPES = ["video", "article", "exercise", "quiz", "interactive"]

    @staticmethod
    def validate_resource_search(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate resource search parameters"""
        # Check topic/query
        if "topic" not in data and "query" not in data:
            return False, "topic or query is required"

        # Validate count if provided
        if "count" in data:
            try:
                count = int(data["count"])
                if count < 1 or count > 100:
                    return False, "count must be between 1 and 100"
            except (ValueError, TypeError):
                return False, "count must be an integer"

        # Validate difficulty if provided
        if "difficulty" in data and data["difficulty"]:
            if isinstance(data["difficulty"], str):
                try:
                    KnowledgeLevel(data["difficulty"])
                except ValueError:
                    valid_levels = [kl.value for kl in KnowledgeLevel]
                    return (
                        False,
                        f"difficulty must be one of: {', '.join(valid_levels)}",
                    )

        # Validate learning_style if provided
        if "learning_style" in data and data["learning_style"]:
            if isinstance(data["learning_style"], str):
                try:
                    LearningStyle(data["learning_style"])
                except ValueError:
                    valid_styles = [ls.value for ls in LearningStyle]
                    return (
                        False,
                        f"learning_style must be one of: {', '.join(valid_styles)}",
                    )

        return True, None

    @staticmethod
    def validate_resource_data(resource: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate resource data structure"""
        # Check required fields
        required = ["resource_id", "title", "type", "platform", "url"]
        for field in required:
            if field not in resource or not resource[field]:
                return False, f"Required field missing: {field}"

        # Validate type
        if resource["type"] not in ResourceDataValidator.VALID_RESOURCE_TYPES:
            return (
                False,
                f"type must be one of: {', '.join(ResourceDataValidator.VALID_RESOURCE_TYPES)}",
            )

        # Validate platform
        if resource["platform"] not in ResourceDataValidator.VALID_PLATFORMS:
            return (
                False,
                f"platform must be one of: {', '.join(ResourceDataValidator.VALID_PLATFORMS)}",
            )

        # Validate URL format
        url = resource["url"]
        if not url.startswith(("http://", "https://")):
            return False, "url must start with http:// or https://"

        # Validate duration if provided
        if "duration" in resource and resource["duration"] is not None:
            try:
                duration = int(resource["duration"])
                if duration < 0:
                    return False, "duration must be positive"
            except (ValueError, TypeError):
                return False, "duration must be an integer (minutes)"

        return True, None


class PathDataValidator:
    """Validator for learning path data"""

    @staticmethod
    def validate_path_generation_request(
        data: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate path generation request"""
        # Check student_id
        if "student_id" not in data or not data["student_id"]:
            return False, "student_id is required"

        if not StudentDataValidator.validate_student_id(data["student_id"]):
            return False, "Invalid student_id format"

        # Check goal
        if "goal" in data and data["goal"]:
            if not isinstance(data["goal"], str) or len(data["goal"]) < 3:
                return False, "goal must be at least 3 characters"

        return True, None

    @staticmethod
    def validate_progress_update(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate progress update data"""
        # Check student_id
        if "student_id" not in data or not data["student_id"]:
            return False, "student_id is required"

        # Check completed_resource_ids
        if "completed_resource_ids" not in data:
            return False, "completed_resource_ids is required"

        if not isinstance(data["completed_resource_ids"], list):
            return False, "completed_resource_ids must be a list"

        # Validate performance_data if provided
        if "performance_data" in data and data["performance_data"]:
            if not isinstance(data["performance_data"], dict):
                return False, "performance_data must be a dictionary"

            # Check avg_score if provided
            if "avg_score" in data["performance_data"]:
                try:
                    score = float(data["performance_data"]["avg_score"])
                    if score < 0 or score > 100:
                        return False, "avg_score must be between 0 and 100"
                except (ValueError, TypeError):
                    return False, "avg_score must be a number"

        return True, None


class ChatDataValidator:
    """Validator for chat/conversation data"""

    @staticmethod
    def validate_chat_message(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate chat message data"""
        # Check session_id
        if "session_id" not in data or not data["session_id"]:
            return False, "session_id is required"

        # Check message
        if "message" not in data or not data["message"]:
            return False, "message is required"

        message = data["message"]
        if not isinstance(message, str):
            return False, "message must be a string"

        if len(message) < 1 or len(message) > 5000:
            return False, "message must be between 1 and 5000 characters"

        return True, None


def validate_and_raise(
    validator_func, data: Dict[str, Any], error_prefix: str = "Validation failed"
):
    """
    Helper function to validate and raise ValidationError if invalid

    Args:
        validator_func: Validation function to call
        data: Data to validate
        error_prefix: Prefix for error message

    Raises:
        ValidationError: If validation fails
    """
    is_valid, error_msg = validator_func(data)
    if not is_valid:
        raise ValidationError(f"{error_prefix}: {error_msg}")
