"""
Response Validation and Testing Utilities
Tools for validating API response format compliance and testing
"""

import json
from datetime import datetime
from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from .response_models import APIResponse, ErrorType, ResponseStatus


class ResponseValidationError(Exception):
    """Exception raised when response validation fails"""

    def __init__(self, message: str, validation_errors: list[str] | None = None):
        self.message = message
        self.validation_errors = validation_errors or []
        super().__init__(self.message)


class ResponseValidator:
    """
    Utility class for validating API responses against standardized format
    """

    def __init__(self, strict_validation: bool = True):
        """
        Initialize response validator

        Args:
            strict_validation: If True, validation is strict and raises exceptions.
                             If False, returns validation results without raising.
        """
        self.strict_validation = strict_validation

    def validate_response_structure(
        self,
        response_data: dict[str, Any],
        expected_type: type[APIResponse] = APIResponse,
    ) -> bool:
        """
        Validate that response data conforms to APIResponse structure

        Args:
            response_data: Response data dictionary to validate
            expected_type: Expected response model type

        Returns:
            bool: True if valid, raises exception or returns False if invalid
        """
        errors = []

        # Check required fields
        required_fields = ["success", "status", "message"]
        for field in required_fields:
            if field not in response_data:
                errors.append(f"Missing required field: {field}")

        # Validate field types and values
        if "success" in response_data:
            if not isinstance(response_data["success"], bool):
                errors.append("Field 'success' must be boolean")

        if "status" in response_data:
            valid_statuses = [status.value for status in ResponseStatus]
            if response_data["status"] not in valid_statuses:
                errors.append(f"Invalid status. Must be one of: {valid_statuses}")

        if "message" in response_data:
            if not isinstance(response_data["message"], str):
                errors.append("Field 'message' must be string")

        # Validate meta field structure if present
        if "meta" in response_data:
            meta_errors = self._validate_meta_structure(response_data["meta"])
            errors.extend(meta_errors)

        # Validate pagination field structure if present
        if "pagination" in response_data:
            pagination_errors = self._validate_pagination_structure(
                response_data["pagination"]
            )
            errors.extend(pagination_errors)

        # Validate errors field structure if present
        if "errors" in response_data and response_data["errors"] is not None:
            errors_field_errors = self._validate_errors_field(response_data["errors"])
            errors.extend(errors_field_errors)

        if errors:
            if self.strict_validation:
                raise ResponseValidationError("Response validation failed", errors)
            return False

        return True

    def validate_json_response(
        self,
        json_response: JSONResponse,
        expected_type: type[APIResponse] = APIResponse,
    ) -> bool:
        """
        Validate JSONResponse object against expected format

        Args:
            json_response: FastAPI JSONResponse object to validate
            expected_type: Expected response model type

        Returns:
            bool: True if valid
        """
        try:
            # Extract content from JSONResponse
            content = (
                json_response.body.decode() if hasattr(json_response, "body") else None
            )
            if not content:
                # Get content from response
                if hasattr(json_response, "body_iterator"):
                    content = b""
                    for chunk in json_response.body_iterator:
                        content += chunk
                    content = content.decode()

            if content:
                response_data = json.loads(content)
                return self.validate_response_structure(response_data, expected_type)
            if self.strict_validation:
                raise ResponseValidationError("Empty response body")
            return False

        except json.JSONDecodeError as e:
            if self.strict_validation:
                raise ResponseValidationError(f"Invalid JSON format: {e!s}")
            return False

    def validate_pydantic_model(
        self, response_data: dict[str, Any], model_class: type[BaseModel]
    ) -> bool:
        """
        Validate response data against Pydantic model

        Args:
            response_data: Response data to validate
            model_class: Pydantic model class to validate against

        Returns:
            bool: True if valid
        """
        try:
            model_class.parse_obj(response_data)
            return True
        except ValidationError as e:
            if self.strict_validation:
                raise ResponseValidationError(f"Pydantic validation failed: {e!s}")
            return False

    def _validate_meta_structure(self, meta_data: Any) -> list[str]:
        """Validate meta field structure"""
        errors = []

        if not isinstance(meta_data, dict):
            errors.append("Field 'meta' must be an object")
            return errors

        # Check for expected meta fields
        if "timestamp" in meta_data:
            timestamp = meta_data["timestamp"]
            if isinstance(timestamp, str):
                try:
                    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    errors.append("Field 'meta.timestamp' must be valid ISO format")

        if "processing_time_ms" in meta_data:
            if not isinstance(meta_data["processing_time_ms"], (int, float)):
                errors.append("Field 'meta.processing_time_ms' must be numeric")

        if "api_version" in meta_data:
            if not isinstance(meta_data["api_version"], str):
                errors.append("Field 'meta.api_version' must be string")

        return errors

    def _validate_pagination_structure(self, pagination_data: Any) -> list[str]:
        """Validate pagination field structure"""
        errors = []

        if not isinstance(pagination_data, dict):
            errors.append("Field 'pagination' must be an object")
            return errors

        # Check required pagination fields
        required_fields = [
            "page",
            "page_size",
            "total_items",
            "total_pages",
            "has_next",
            "has_previous",
        ]
        for field in required_fields:
            if field not in pagination_data:
                errors.append(f"Missing pagination field: {field}")

        # Validate field types
        if "page" in pagination_data and not isinstance(pagination_data["page"], int):
            errors.append("Field 'pagination.page' must be integer")

        if "page_size" in pagination_data and not isinstance(
            pagination_data["page_size"], int
        ):
            errors.append("Field 'pagination.page_size' must be integer")

        if "total_items" in pagination_data and not isinstance(
            pagination_data["total_items"], int
        ):
            errors.append("Field 'pagination.total_items' must be integer")

        if "has_next" in pagination_data and not isinstance(
            pagination_data["has_next"], bool
        ):
            errors.append("Field 'pagination.has_next' must be boolean")

        if "has_previous" in pagination_data and not isinstance(
            pagination_data["has_previous"], bool
        ):
            errors.append("Field 'pagination.has_previous' must be boolean")

        return errors

    def _validate_errors_field(self, errors_data: Any) -> list[str]:
        """Validate errors field structure"""
        errors = []

        if not isinstance(errors_data, list):
            errors.append("Field 'errors' must be an array")
            return errors

        for i, error_item in enumerate(errors_data):
            if not isinstance(error_item, dict):
                errors.append(f"Error item {i} must be an object")
                continue

            if "code" not in error_item:
                errors.append(f"Error item {i} missing required field 'code'")

            if "message" not in error_item:
                errors.append(f"Error item {i} missing required field 'message'")

            if "code" in error_item and not isinstance(error_item["code"], str):
                errors.append(f"Error item {i} field 'code' must be string")

            if "message" in error_item and not isinstance(error_item["message"], str):
                errors.append(f"Error item {i} field 'message' must be string")

        return errors


class ResponseTester:
    """
    Testing utilities for API response validation
    """

    def __init__(self):
        self.validator = ResponseValidator(strict_validation=False)

    def assert_response_format(
        self,
        response_data: dict[str, Any],
        expected_success: bool = True,
        expected_status: ResponseStatus | None = None,
        has_data: bool = True,
        has_errors: bool = False,
        has_pagination: bool = False,
    ) -> list[str]:
        """
        Assert response format with detailed validation

        Args:
            response_data: Response data to test
            expected_success: Expected success value
            expected_status: Expected status value
            has_data: Whether response should have data
            has_errors: Whether response should have errors
            has_pagination: Whether response should have pagination

        Returns:
            List[str]: List of assertion failures (empty if all pass)
        """
        failures = []

        # Basic structure validation
        if not self.validator.validate_response_structure(response_data):
            failures.append("Response structure validation failed")

        # Success field validation
        if response_data.get("success") != expected_success:
            failures.append(
                f"Expected success={expected_success}, got {response_data.get('success')}"
            )

        # Status field validation
        if expected_status and response_data.get("status") != expected_status.value:
            failures.append(
                f"Expected status={expected_status.value}, got {response_data.get('status')}"
            )

        # Data field validation
        if has_data and "data" not in response_data:
            failures.append("Response should have 'data' field")
        elif (
            not has_data
            and "data" in response_data
            and response_data["data"] is not None
        ):
            failures.append("Response should not have 'data' field")

        # Errors field validation
        if has_errors and (
            "errors" not in response_data or not response_data["errors"]
        ):
            failures.append("Response should have 'errors' field with errors")
        elif not has_errors and response_data.get("errors"):
            failures.append("Response should not have errors")

        # Pagination field validation
        if has_pagination and "pagination" not in response_data:
            failures.append("Response should have 'pagination' field")
        elif not has_pagination and "pagination" in response_data:
            failures.append("Response should not have 'pagination' field")

        return failures

    def assert_success_response(
        self, response_data: dict[str, Any], expected_data_type: type | None = None
    ) -> list[str]:
        """Assert response is a valid success response"""
        failures = self.assert_response_format(
            response_data,
            expected_success=True,
            expected_status=ResponseStatus.SUCCESS,
            has_data=True,
            has_errors=False,
        )

        # Validate data type if specified
        if expected_data_type and "data" in response_data:
            data = response_data["data"]
            if not isinstance(data, expected_data_type):
                failures.append(
                    f"Expected data type {expected_data_type.__name__}, got {type(data).__name__}"
                )

        return failures

    def assert_error_response(
        self,
        response_data: dict[str, Any],
        expected_error_type: ErrorType | None = None,
    ) -> list[str]:
        """Assert response is a valid error response"""
        failures = self.assert_response_format(
            response_data,
            expected_success=False,
            expected_status=ResponseStatus.ERROR,
            has_data=False,
            has_errors=True,
        )

        # Validate error type if specified
        if (
            expected_error_type
            and "errors" in response_data
            and response_data["errors"]
        ):
            error_codes = [error.get("code") for error in response_data["errors"]]
            if expected_error_type.value not in error_codes:
                failures.append(
                    f"Expected error type {expected_error_type.value} not found in errors"
                )

        return failures

    def assert_paginated_response(
        self,
        response_data: dict[str, Any],
        expected_page: int | None = None,
        expected_total: int | None = None,
    ) -> list[str]:
        """Assert response is a valid paginated response"""
        failures = self.assert_response_format(
            response_data, expected_success=True, has_data=True, has_pagination=True
        )

        # Validate pagination details if specified
        if "pagination" in response_data:
            pagination = response_data["pagination"]

            if expected_page and pagination.get("page") != expected_page:
                failures.append(
                    f"Expected page {expected_page}, got {pagination.get('page')}"
                )

            if expected_total and pagination.get("total_items") != expected_total:
                failures.append(
                    f"Expected total_items {expected_total}, got {pagination.get('total_items')}"
                )

        return failures


class ResponseTestCase:
    """
    Test case helper for response format testing
    """

    def __init__(self, name: str):
        self.name = name
        self.tester = ResponseTester()
        self.test_results = []

    def test_response(
        self,
        response_data: dict[str, Any],
        test_name: str,
        assertion_method: str,
        **kwargs,
    ) -> bool:
        """
        Run a test case on response data

        Args:
            response_data: Response data to test
            test_name: Name of the test
            assertion_method: Method name to call on ResponseTester
            **kwargs: Additional arguments for assertion method

        Returns:
            bool: True if test passes
        """
        try:
            method = getattr(self.tester, assertion_method)
            failures = method(response_data, **kwargs)

            if failures:
                self.test_results.append(
                    {"test_name": test_name, "status": "FAIL", "failures": failures}
                )
                return False
            self.test_results.append({"test_name": test_name, "status": "PASS"})
            return True

        except Exception as e:
            self.test_results.append(
                {"test_name": test_name, "status": "ERROR", "error": str(e)}
            )
            return False

    def get_test_report(self) -> dict[str, Any]:
        """Get comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])

        return {
            "test_case_name": self.name,
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
                if total_tests > 0
                else "0%",
            },
            "results": self.test_results,
        }


# Pre-built test data generators
class ResponseTestDataGenerator:
    """Generate test response data for validation testing"""

    @staticmethod
    def valid_success_response(data: Any = None) -> dict[str, Any]:
        """Generate valid success response"""
        return {
            "success": True,
            "status": "success",
            "message": "İşlem başarıyla tamamlandı",
            "data": data or {"example": "data"},
            "errors": None,
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "request_id": "test-request-123",
                "api_version": "v1",
                "processing_time_ms": 150.5,
            },
        }

    @staticmethod
    def valid_error_response(
        error_type: ErrorType = ErrorType.INTERNAL_SERVER_ERROR,
    ) -> dict[str, Any]:
        """Generate valid error response"""
        return {
            "success": False,
            "status": "error",
            "message": "Bir hata oluştu",
            "data": None,
            "errors": [
                {
                    "code": error_type.value,
                    "message": "Test error message",
                    "field": None,
                    "details": None,
                }
            ],
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "request_id": "test-request-456",
                "api_version": "v1",
            },
        }

    @staticmethod
    def valid_paginated_response(
        data: list[Any] = None,
        page: int = 1,
        page_size: int = 20,
        total_items: int = 100,
    ) -> dict[str, Any]:
        """Generate valid paginated response"""
        total_pages = (total_items + page_size - 1) // page_size

        return {
            "success": True,
            "status": "success",
            "message": "Veriler başarıyla getirildi",
            "data": data or [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
            "errors": None,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "request_id": "test-request-789",
                "api_version": "v1",
            },
        }

    @staticmethod
    def invalid_response_missing_fields() -> dict[str, Any]:
        """Generate invalid response missing required fields"""
        return {"data": {"some": "data"}}

    @staticmethod
    def invalid_response_wrong_types() -> dict[str, Any]:
        """Generate invalid response with wrong field types"""
        return {
            "success": "true",  # Should be boolean
            "status": 200,  # Should be string
            "message": {"not": "string"},  # Should be string
            "data": "data",
        }


# Usage example functions
def run_response_validation_tests():
    """Run comprehensive response validation tests"""
    test_case = ResponseTestCase("Response Format Validation")
    generator = ResponseTestDataGenerator()

    # Test valid success response
    valid_success = generator.valid_success_response()
    test_case.test_response(
        valid_success, "Valid Success Response", "assert_success_response"
    )

    # Test valid error response
    valid_error = generator.valid_error_response()
    test_case.test_response(
        valid_error, "Valid Error Response", "assert_error_response"
    )

    # Test valid paginated response
    valid_paginated = generator.valid_paginated_response()
    test_case.test_response(
        valid_paginated, "Valid Paginated Response", "assert_paginated_response"
    )

    # Test invalid responses
    invalid_missing = generator.invalid_response_missing_fields()
    test_case.test_response(
        invalid_missing, "Invalid Response - Missing Fields", "assert_response_format"
    )

    invalid_types = generator.invalid_response_wrong_types()
    test_case.test_response(
        invalid_types, "Invalid Response - Wrong Types", "assert_response_format"
    )

    return test_case.get_test_report()


def validate_api_endpoint_response(
    response_data: dict[str, Any], endpoint_name: str, expected_format: str = "success"
) -> dict[str, Any]:
    """
    Validate individual API endpoint response

    Args:
        response_data: Response data to validate
        endpoint_name: Name of the API endpoint
        expected_format: Expected response format (success, error, paginated)

    Returns:
        Dict containing validation results
    """
    validator = ResponseValidator(strict_validation=False)
    tester = ResponseTester()

    results = {
        "endpoint": endpoint_name,
        "expected_format": expected_format,
        "validation_passed": False,
        "errors": [],
    }

    try:
        # Basic structure validation
        if not validator.validate_response_structure(response_data):
            results["errors"].append("Basic response structure validation failed")

        # Format-specific validation
        if expected_format == "success":
            failures = tester.assert_success_response(response_data)
            results["errors"].extend(failures)
        elif expected_format == "error":
            failures = tester.assert_error_response(response_data)
            results["errors"].extend(failures)
        elif expected_format == "paginated":
            failures = tester.assert_paginated_response(response_data)
            results["errors"].extend(failures)

        results["validation_passed"] = len(results["errors"]) == 0

    except Exception as e:
        results["errors"].append(f"Validation exception: {e!s}")

    return results
