# Schemathesis API Contract Testing

## Overview

This directory contains automated API contract tests using Schemathesis. These tests validate that the API implementation matches its OpenAPI specification.

## What is Contract Testing?

Contract testing ensures that:
- API responses match their OpenAPI schema definitions
- All endpoints are properly documented
- Response formats are consistent
- No 500 errors occur on valid requests
- Required fields are present in responses

## Test Structure

### `test_schemathesis_api.py`

Contains two test classes:

1. **TestAPIContracts**: Tests specific endpoint contracts
   - `/openapi.json`: Schema availability and validity
   - `/health`: Health check endpoint compliance
   - `/`: Root endpoint structure
   - `/docs` and `/redoc`: Documentation accessibility

2. **TestSchemaValidation**: Tests OpenAPI schema structure
   - Required top-level fields (openapi, info, paths)
   - Critical endpoints presence
   - Endpoint definitions completeness
   - Components section (if present)
   - Public GET endpoints behavior

## Running Tests

### Run all contract tests:
```bash
pytest tests/contract/ -v -m contract
```

### Run specific test class:
```bash
pytest tests/contract/test_schemathesis_api.py::TestAPIContracts -v
```

### Run specific test:
```bash
pytest tests/contract/test_schemathesis_api.py::TestAPIContracts::test_health_endpoint_conforms_to_schema -v
```

## Dependencies

- **schemathesis==3.36.3**: Property-based testing for OpenAPI schemas
- **httpx**: HTTP client with ASGI support
- **pytest**: Test framework
- **pytest-asyncio**: Async test support

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

## Test Coverage

Current tests cover:

### ✅ Covered
- OpenAPI schema availability and validation
- Health endpoint contract
- Root endpoint contract
- Documentation endpoints (/docs, /redoc)
- Schema structure validation
- Critical endpoints presence
- Public GET endpoints

### ⚠️ Not Covered (by design)
- POST/PUT/DELETE endpoints (require authentication)
- Authenticated endpoints (would need test credentials)
- Property-based fuzzing (OpenAPI 3.1.0 compatibility limitation)

## Known Limitations

### OpenAPI 3.1.0 Compatibility

Schemathesis 3.36.3 has limited support for OpenAPI 3.1.0 (FastAPI's default).
For full property-based testing with `@schema.parametrize()`, you would need:
- Downgrade to OpenAPI 3.0.3 in FastAPI, OR
- Wait for Schemathesis to fully support OpenAPI 3.1.0

Current implementation uses a simplified approach:
- Manual endpoint testing instead of automatic generation
- Schema validation instead of property-based testing
- Still catches schema violations and 500 errors

### Health Endpoint Behavior

The `/health` endpoint may return:
- **200 OK**: All services healthy (normal operation)
- **503 Service Unavailable**: One or more services down (test environment)

Both are valid responses and tests accept either status code.

## Test Standards

### NEVER Use Reward Hacking
```python
# ❌ WRONG - Fake assertion
assert True

# ✅ RIGHT - Real validation
assert "status" in data, "Missing status field"
```

### Always Use Descriptive Assertions
```python
# ❌ WRONG - Unclear
assert response.status_code == 200

# ✅ RIGHT - Clear message
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
```

### Check Actual Response Content
```python
# ❌ WRONG - Not checking content
response = await client.get("/health")

# ✅ RIGHT - Validate response
response = await client.get("/health")
data = response.json()
assert "status" in data, "Missing required field"
```

## Adding New Tests

To add a new contract test:

1. Identify the endpoint and expected behavior
2. Add test method to appropriate class
3. Use descriptive docstring
4. Validate response structure and content
5. Add `@pytest.mark.contract` decorator
6. Run tests to verify

Example:
```python
@pytest.mark.contract
async def test_new_endpoint_contract(self, client: AsyncClient) -> None:
    \"\"\"
    Validate /new-endpoint response matches schema.

    Expected:
    - 200 status
    - JSON response
    - Required fields present
    \"\"\"
    response = await client.get("/new-endpoint")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "required_field" in data, "Missing required_field"
```

## Continuous Integration

These tests run as part of CI/CD pipeline:
- On every pull request
- Before deployment
- As part of the test suite

Failed contract tests block deployment to ensure API consistency.

## Future Improvements

- [ ] Full property-based testing when OpenAPI 3.1.0 is supported
- [ ] Add POST/PUT/DELETE endpoint tests with test credentials
- [ ] Add response time assertions
- [ ] Add rate limiting tests
- [ ] Add pagination contract tests
- [ ] Add error response format validation

## References

- [Schemathesis Documentation](https://schemathesis.readthedocs.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [FastAPI OpenAPI Support](https://fastapi.tiangolo.com/advanced/extending-openapi/)
- [Contract Testing Best Practices](https://pactflow.io/blog/what-is-contract-testing/)

## Support

For issues or questions:
1. Check test output for specific failures
2. Verify OpenAPI schema is valid at `/openapi.json`
3. Run individual tests for detailed errors
4. Check logs for service health issues

---
*Last updated: 2026-02-02*
*Schemathesis version: 3.36.3*
