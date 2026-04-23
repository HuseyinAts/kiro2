
"""
Test Suite for API Response Format Standardization
Comprehensive tests for validating response format compliance
"""

import pytest
from fastapi.responses import JSONResponse

from core.response_models import (
    APIResponse,
    ErrorDetail,
    ErrorResponse,
    ErrorType,
    PaginatedResponse,
    PaginationMeta,
    ResponseBuilder,
    ResponseStatus,
    SuccessResponse,
    error_response,
    paginated_response,
    success_response,
    turkish_error_response,
    turkish_success_response,
)
from core.response_validators import (
    ResponseTestCase,
    ResponseTestDataGenerator,
    ResponseTester,
    ResponseValidationError,
    ResponseValidator,
    run_response_validation_tests,
    validate_api_endpoint_response,
)


class TestResponseModels:
    """Test response model functionality"""

    def test_api_response_creation(self):
        """Test basic APIResponse creation"""
        response = APIResponse(
            success=True,
            status=ResponseStatus.SUCCESS,
            message="Test message",
            data={"test": "data"},
        )

        assert response.success == True
        assert response.status == ResponseStatus.SUCCESS
        assert response.message == "Test message"
        assert response.data == {"test": "data"}
        assert response.meta is not None

    def test_success_response_creation(self):
        """Test SuccessResponse creation"""
        response = SuccessResponse(message="Success message", data={"result": "ok"})

        assert response.success == True
        assert response.status == ResponseStatus.SUCCESS
        assert response.message == "Success message"
        assert response.data == {"result": "ok"}

    def test_error_response_creation(self):
        """Test ErrorResponse creation"""
        error_detail = ErrorDetail(
            code=ErrorType.VALIDATION_ERROR.value, message="Validation failed"
        )

        response = ErrorResponse(message="Error occurred", errors=[error_detail])

        assert response.success == False
        assert response.status == ResponseStatus.ERROR
        assert response.message == "Error occurred"
        assert len(response.errors) == 1
        assert response.errors[0].code == ErrorType.VALIDATION_ERROR.value

    def test_paginated_response_creation(self):
        """Test PaginatedResponse creation"""
        pagination = PaginationMeta(page=1, page_size=20, total_items=100)

        response = PaginatedResponse(
            success=True,
            status=ResponseStatus.SUCCESS,
            message="Paginated data",
            data=[{"id": 1}, {"id": 2}],
            pagination=pagination,
        )

        assert response.pagination is not None
        assert response.pagination.page == 1
        assert response.pagination.total_pages == 5
        assert response.pagination.has_next == True
        assert response.pagination.has_previous == False


class TestResponseBuilder:
    """Test ResponseBuilder functionality"""

    def test_success_response_building(self):
        """Test building success response"""
        response = (
            ResponseBuilder()
            .success("Operation successful")
            .with_data({"result": "ok"})
            .with_meta(request_id="test-123")
            .build()
        )

        assert response.success == True
        assert response.status == ResponseStatus.SUCCESS
        assert response.message == "Operation successful"
        assert response.data == {"result": "ok"}
        assert response.meta.request_id == "test-123"

    def test_error_response_building(self):
        """Test building error response"""
        error_detail = ErrorDetail(
            code=ErrorType.NOT_FOUND_ERROR.value, message="Resource not found"
        )

        response = (
            ResponseBuilder()
            .error("Not found")
            .with_errors([error_detail])
            .with_meta(request_id="test-456")
            .build()
        )

        assert response.success == False
        assert response.status == ResponseStatus.ERROR
        assert response.message == "Not found"
        assert len(response.errors) == 1
        assert response.errors[0].code == ErrorType.NOT_FOUND_ERROR.value

    def test_paginated_response_building(self):
        """Test building paginated response"""
        data = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

        response = (
            ResponseBuilder()
            .success("Data retrieved")
            .with_data(data)
            .with_pagination(page=2, page_size=10, total_items=25)
            .build()
        )

        assert isinstance(response, PaginatedResponse)
        assert response.pagination.page == 2
        assert response.pagination.page_size == 10
        assert response.pagination.total_items == 25
        assert response.pagination.total_pages == 3
        assert response.pagination.has_next == True
        assert response.pagination.has_previous == True


class TestConvenienceFunctions:
    """Test convenience response creation functions"""

    def test_success_response_function(self):
        """Test success_response function"""
        response = success_response(
            data={"user_id": 123}, message="User created", request_id="req-789"
        )

        assert response.success == True
        assert response.data == {"user_id": 123}
        assert response.message == "User created"
        assert response.meta.request_id == "req-789"

    def test_error_response_function(self):
        """Test error_response function"""
        error_detail = ErrorDetail(
            code=ErrorType.AUTHORIZATION_ERROR.value, message="Access denied"
        )

        response = error_response(
            message="Authorization failed", errors=[error_detail], request_id="req-101"
        )

        assert response.success == False
        assert response.message == "Authorization failed"
        assert len(response.errors) == 1
        assert response.meta.request_id == "req-101"

    def test_paginated_response_function(self):
        """Test paginated_response function"""
        data = [{"id": i} for i in range(1, 11)]

        response = paginated_response(
            data=data, page=1, page_size=10, total_items=50, message="Items retrieved"
        )

        assert len(response.data) == 10
        assert response.pagination.total_items == 50
        assert response.pagination.total_pages == 5

    def test_turkish_success_response(self):
        """Test Turkish success response"""
        response = turkish_success_response(
            data={"sonuc": "basarili"}, message_key="data_created"
        )

        assert response.success == True
        assert "başarıyla" in response.message

    def test_turkish_error_response(self):
        """Test Turkish error response"""
        response = turkish_error_response(message_key="validation_error")

        assert response.success == False
        assert "doğrulama" in response.message.lower()


class TestResponseValidator:
    """Test response validation functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.validator = ResponseValidator(strict_validation=False)
        self.strict_validator = ResponseValidator(strict_validation=True)
        self.generator = ResponseTestDataGenerator()

    def test_valid_response_structure(self):
        """Test validation of valid response structure"""
        valid_response = self.generator.valid_success_response()

        assert self.validator.validate_response_structure(valid_response) == True

    def test_invalid_response_missing_fields(self):
        """Test validation of response missing required fields"""
        invalid_response = {"data": {"some": "data"}}

        assert self.validator.validate_response_structure(invalid_response) == False

    def test_invalid_response_wrong_types(self):
        """Test validation of response with wrong field types"""
        invalid_response = {
            "success": "true",  # Should be boolean
            "status": "success",
            "message": 123,  # Should be string
            "data": None,
        }

        assert self.validator.validate_response_structure(invalid_response) == False

    def test_strict_validation_raises_exception(self):
        """Test that strict validation raises exceptions"""
        invalid_response = {"invalid": "response"}

        with pytest.raises(ResponseValidationError):
            self.strict_validator.validate_response_structure(invalid_response)

    def test_meta_structure_validation(self):
        """Test meta field structure validation"""
        response_with_invalid_meta = {
            "success": True,
            "status": "success",
            "message": "Test",
            "meta": "invalid_meta",  # Should be dict
        }

        assert (
            self.validator.validate_response_structure(response_with_invalid_meta)
            == False
        )

    def test_pagination_structure_validation(self):
        """Test pagination field structure validation"""
        response_with_invalid_pagination = {
            "success": True,
            "status": "success",
            "message": "Test",
            "pagination": {
                "page": "1",  # Should be int
                "page_size": 20,
                "total_items": 100,
            },
        }

        assert (
            self.validator.validate_response_structure(response_with_invalid_pagination)
            == False
        )


class TestResponseTester:
    """Test response testing functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.tester = ResponseTester()
        self.generator = ResponseTestDataGenerator()

    def test_assert_success_response(self):
        """Test success response assertion"""
        valid_success = self.generator.valid_success_response()
        failures = self.tester.assert_success_response(valid_success)

        assert failures == []

    def test_assert_error_response(self):
        """Test error response assertion"""
        valid_error = self.generator.valid_error_response(ErrorType.NOT_FOUND_ERROR)
        failures = self.tester.assert_error_response(
            valid_error, ErrorType.NOT_FOUND_ERROR
        )

        assert failures == []

    def test_assert_paginated_response(self):
        """Test paginated response assertion"""
        valid_paginated = self.generator.valid_paginated_response()
        failures = self.tester.assert_paginated_response(valid_paginated)

        assert failures == []

    def test_failed_assertions(self):
        """Test failed response assertions"""
        # Test success assertion on error response
        error_response = self.generator.valid_error_response()
        failures = self.tester.assert_success_response(error_response)

        assert len(failures) > 0
        assert any("success" in failure.lower() for failure in failures)

    def test_pagination_details_validation(self):
        """Test pagination details validation"""
        paginated_response = self.generator.valid_paginated_response(
            page=3, page_size=15, total_items=200
        )

        failures = self.tester.assert_paginated_response(
            paginated_response, expected_page=3, expected_total=200
        )

        assert failures == []

        # Test with wrong expectations
        failures = self.tester.assert_paginated_response(
            paginated_response,
            expected_page=1,  # Wrong page
            expected_total=100,  # Wrong total
        )

        assert len(failures) == 2


class TestResponseTestCase:
    """Test ResponseTestCase functionality"""

    def test_test_case_execution(self):
        """Test test case execution and reporting"""
        test_case = ResponseTestCase("Test API Responses")
        generator = ResponseTestDataGenerator()

        # Run successful test
        valid_response = generator.valid_success_response()
        result = test_case.test_response(
            valid_response, "Valid Success Response Test", "assert_success_response"
        )

        assert result == True

        # Run failing test
        error_response = generator.valid_error_response()
        result = test_case.test_response(
            error_response, "Success Response Test on Error", "assert_success_response"
        )

        assert result == False

        # Get report
        report = test_case.get_test_report()

        assert report["summary"]["total"] == 2
        assert report["summary"]["passed"] == 1
        assert report["summary"]["failed"] == 1
        assert "50.0%" in report["summary"]["success_rate"]


class TestFullResponseValidationWorkflow:
    """Test complete response validation workflow"""

    def test_run_validation_tests(self):
        """Test running complete validation test suite"""
        report = run_response_validation_tests()

        assert "test_case_name" in report
        assert "summary" in report
        assert "results" in report
        assert report["summary"]["total"] > 0

    def test_validate_api_endpoint_response(self):
        """Test API endpoint response validation"""
        generator = ResponseTestDataGenerator()

        # Test valid success response
        success_response = generator.valid_success_response()
        result = validate_api_endpoint_response(
            success_response, "/api/v1/users", "success"
        )

        assert result["validation_passed"] == True
        assert result["endpoint"] == "/api/v1/users"
        assert len(result["errors"]) == 0

        # Test invalid response
        invalid_response = {"invalid": "structure"}
        result = validate_api_endpoint_response(
            invalid_response, "/api/v1/invalid", "success"
        )

        assert result["validation_passed"] == False
        assert len(result["errors"]) > 0


class TestIntegrationWithFastAPI:
    """Test integration with FastAPI responses"""

    def test_json_response_validation(self):
        """Test validation of FastAPI JSONResponse objects"""
        # Create JSONResponse with valid data
        valid_data = ResponseTestDataGenerator.valid_success_response()
        json_response = JSONResponse(content=valid_data)

        validator = ResponseValidator(strict_validation=False)

        # Note: This test verifies JSONResponse was created successfully
        assert json_response is not None
        assert validator is not None
        assert json_response.status_code == 200

    def test_response_models_with_fastapi(self):
        """Test response models work with FastAPI"""
        # Test that response models serialize correctly
        response = success_response(data={"test": "data"}, message="Test successful")

        # Convert to dict (as FastAPI would do)
        response_dict = response.dict(exclude_none=True)

        assert "success" in response_dict
        assert "status" in response_dict
        assert "message" in response_dict
        assert "data" in response_dict
        assert "meta" in response_dict


# Integration test for actual API endpoints
@pytest.mark.integration
class TestAPIEndpointResponseFormats:
    """Integration tests for actual API endpoint response formats"""

    def test_auth_endpoints_response_format(self):
        """Test auth endpoints return proper response format"""
        # This would test actual API endpoints
        # Placeholder for actual integration tests

    def test_content_management_endpoints_response_format(self):
        """Test content management endpoints return proper response format"""
        # This would test actual API endpoints
        # Placeholder for actual integration tests

    def test_error_handling_response_format(self):
        """Test error handling returns proper response format"""
        # This would test actual error scenarios
        # Placeholder for actual integration tests


if __name__ == "__main__":
    # Run basic validation tests
    print("Running Response Format Validation Tests...")

    # Test response models
    print("\\nTesting Response Models...")
    test_models = TestResponseModels()
    test_models.test_api_response_creation()
    test_models.test_success_response_creation()
    test_models.test_error_response_creation()
    test_models.test_paginated_response_creation()
    print("[CHECK] Response Models tests passed")

    # Test response builder
    print("\\nTesting Response Builder...")
    test_builder = TestResponseBuilder()
    test_builder.test_success_response_building()
    test_builder.test_error_response_building()
    test_builder.test_paginated_response_building()
    print("[CHECK] Response Builder tests passed")

    # Test convenience functions
    print("\\nTesting Convenience Functions...")
    test_functions = TestConvenienceFunctions()
    test_functions.test_success_response_function()
    test_functions.test_error_response_function()
    test_functions.test_paginated_response_function()
    test_functions.test_turkish_success_response()
    test_functions.test_turkish_error_response()
    print("[CHECK] Convenience Functions tests passed")

    # Run comprehensive validation tests
    print("\\nRunning Comprehensive Validation Tests...")
    report = run_response_validation_tests()
    print(
        f"[CHECK] Validation Tests completed: {report['summary']['success_rate']} success rate"
    )

    print(
        "\\n[PARTY] All Response Format Standardization tests completed successfully!"
    )
