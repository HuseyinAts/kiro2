# Implementation Plan: YKS Soru Kalite Doğrulama Sistemi

## Overview

Bu implementation plan, verification feedback loops prensibine dayalı YKS soru kalite doğrulama sistemini adım adım oluşturur. Sistem 4 validator, 1 orchestrator ve reporting mekanizması içerir.

## Tasks

- [ ] 1. Setup project structure and base classes
  - Create validators/ directory structure
  - Define BaseValidator abstract class with ValidationResult model
  - Setup Pydantic models for Question and ValidationReport
  - Configure async support with asyncio
  - _Requirements: 1.1, 5.1_

- [ ]* 1.1 Write property test for ValidationResult model
  - **Property 1: Score Bounds** - Score must be 0-100
  - **Validates: Requirements 6.5**

- [ ] 2. Implement ÖSYM Format Validator
  - [ ] 2.1 Create OSYMFormatValidator class
    - Implement required fields check (question_text, options, correct_answer, difficulty)
    - Implement options count validation (exactly 4)
    - Implement option label validation (A, B, C, D)
    - Implement correct answer validation
    - Implement difficulty level validation
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 2.2 Write property test for ÖSYM validator
    - **Property 4: Format Validation Completeness**
    - **Validates: Requirements 1.1-1.5**

  - [ ] 2.3 Implement error message generation
    - Generate specific error messages for each validation failure
    - Generate fix suggestions
    - _Requirements: 1.6, 7.1, 7.2_

- [ ] 3. Implement Müfredat Checker
  - [ ] 3.1 Create MufredatChecker class
    - Integrate with MEB API client
    - Implement kazanım fetching logic
    - Implement semantic similarity calculation using embeddings
    - Calculate compliance score (0-100)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.2 Implement multi-kazanım detection
    - Handle questions covering multiple kazanımlar
    - List all relevant kazanımlar
    - _Requirements: 2.5, 2.6_

  - [ ]* 3.3 Write unit tests for müfredat checker
    - Test kazanım matching with mock MEB API
    - Test similarity score calculation
    - _Requirements: 2.1-2.6_

- [ ] 4. Implement Turkish Language Validator
  - [ ] 4.1 Create TurkishValidator class with Zemberek
    - Setup Zemberek TurkishMorphology
    - Implement spell checking
    - Implement sentence complexity analysis
    - Implement Turkish character validation
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 4.2 Implement error categorization
    - Categorize errors (yazım, sözdizimi, anlam)
    - Generate correction suggestions
    - _Requirements: 3.6, 7.1_

  - [ ]* 4.3 Write unit tests for Turkish validator
    - Test spell checking with known misspellings
    - Test sentence complexity detection
    - _Requirements: 3.1-3.6_

- [ ] 5. Implement Math Validator
  - [ ] 5.1 Create MathValidator class with SymPy
    - Setup SymPy expression parser
    - Implement mathematical expression extraction
    - Implement expression validation
    - Implement correct answer verification
    - Implement distractor validation
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ] 5.2 Implement unit handling
    - Check unit consistency across problem
    - Validate unit conversions
    - _Requirements: 4.5_

  - [ ]* 5.3 Write property test for math validator
    - Generate random math expressions
    - Verify SymPy can parse and validate
    - _Requirements: 4.1-4.6_

- [ ] 6. Checkpoint - Ensure all validators pass unit tests
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement Quality Score Calculator
  - [ ] 7.1 Create QualityScorer class
    - Implement weighted average calculation
    - Apply weights: ÖSYM (30%), Müfredat (30%), Turkish (20%), Math (20%)
    - Normalize final score to 0-100 range
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 7.2 Write property test for score calculation
    - **Property 2: Weighted Average Correctness**
    - **Validates: Requirements 6.1-6.5**

  - [ ] 7.3 Implement approval logic
    - Check if score >= 70
    - Check if errors list is empty
    - Mark question as approved/rejected
    - _Requirements: 6.6_

  - [ ]* 7.4 Write property test for approval threshold
    - **Property 3: Approval Threshold**
    - **Validates: Requirements 6.6**

- [ ] 8. Implement Validation Orchestrator
  - [ ] 8.1 Create ValidationOrchestrator class
    - Initialize all validators with weights
    - Implement parallel validation execution using asyncio.gather
    - Aggregate validation results
    - Calculate final score
    - _Requirements: 5.2, 5.3, 5.4, 5.5_

  - [ ] 8.2 Implement error aggregation
    - Collect all errors from validators
    - Collect all warnings from validators
    - Collect all suggestions from validators
    - Prioritize errors by severity
    - _Requirements: 7.4, 7.5_

  - [ ]* 8.3 Write integration test for orchestrator
    - Test full validation pipeline with sample questions
    - Verify all validators are called
    - Verify final score calculation
    - _Requirements: 5.1-5.6_

- [ ] 9. Implement Error Reporter
  - [ ] 9.1 Create ErrorReporter class
    - Implement error categorization (format, müfredat, dil, matematik)
    - Implement error location tracking
    - Generate Turkish error messages
    - _Requirements: 7.1, 7.2, 7.5_

  - [ ] 9.2 Create SuggestionGenerator class
    - Generate concrete fix examples
    - Provide step-by-step correction guidance
    - _Requirements: 7.3_

  - [ ]* 9.3 Write unit tests for error reporting
    - Test error message generation
    - Test suggestion generation
    - _Requirements: 7.1-7.6_

- [ ] 10. Implement PostToolUse Hook
  - [ ] 10.1 Create PostToolUseHook class
    - Implement hook trigger mechanism
    - Call ValidationOrchestrator on question generation
    - Handle validation results
    - _Requirements: 5.1, 5.2_

  - [ ] 10.2 Implement result persistence
    - Save validation results to PostgreSQL
    - Save validation results to JSON log file
    - _Requirements: 5.6, 7.6_

  - [ ]* 10.3 Write integration test for hook
    - Test hook trigger on question generation
    - Verify validation is executed
    - Verify results are persisted
    - _Requirements: 5.1-5.6_

- [ ] 11. Implement Performance Optimization
  - [ ] 11.1 Add Redis caching
    - Cache validation results for identical questions
    - Cache MEB kazanım data
    - Set appropriate TTL values
    - _Requirements: 8.4_

  - [ ] 11.2 Implement parallel processing
    - Enable concurrent validation of multiple questions
    - Limit concurrent workers to 10
    - _Requirements: 8.2_

  - [ ]* 11.3 Write property test for performance
    - **Property 6: Performance Bound**
    - Validate 100 random questions
    - Verify each takes < 5 seconds
    - **Validates: Requirements 8.1**

- [ ] 12. Implement Monitoring and Alerting
  - [ ] 12.1 Add performance logging
    - Log validation duration for each question
    - Log average response time
    - _Requirements: 8.5_

  - [ ] 12.2 Add alerting mechanism
    - Alert when system slows down (> 5s avg)
    - Alert when error rate increases
    - Send notifications to admin
    - _Requirements: 8.6_

  - [ ]* 12.3 Write integration tests for monitoring
    - Test performance logging
    - Test alert triggering
    - _Requirements: 8.5, 8.6_

- [ ] 13. Create API Endpoints
  - [ ] 13.1 Create FastAPI endpoints
    - POST /api/v1/validate-question - Validate single question
    - POST /api/v1/validate-batch - Validate multiple questions
    - GET /api/v1/validation-report/{question_id} - Get validation report
    - _Requirements: All_

  - [ ]* 13.2 Write API integration tests
    - Test all endpoints with various inputs
    - Test error handling
    - Test response format
    - _Requirements: All_

- [ ] 14. Final Checkpoint - Integration Testing
  - Run full end-to-end test with real questions
  - Verify all validators work together
  - Verify performance meets < 5s requirement
  - Verify approval rate >= 80%
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Documentation and Deployment
  - [ ] 15.1 Write API documentation
    - Document all endpoints with OpenAPI
    - Provide example requests/responses
    - Document error codes

  - [ ] 15.2 Create deployment configuration
    - Setup Docker container
    - Configure environment variables
    - Setup database migrations

## Notes

- Tasks marked with `*` are optional test tasks
- Each validator should be independently testable
- Use async/await throughout for performance
- Cache frequently accessed data (MEB kazanımlar)
- Property tests should run with minimum 100 iterations
- Integration tests should use test database
- Performance tests should measure actual execution time
