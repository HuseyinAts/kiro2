---
inclusion: always
---

---
inclusion: always
---

# Teknofest 2025 Eğitim Eylemci Platformu - Development Guidelines

## Communication & Language
- Always communicate in Turkish when interacting with users
- Use proper Turkish educational terminology: LGS (Liselere Geçiş Sınavı), YKS (Yükseköğretim Kurumları Sınavı), MEB (Milli Eğitim Bakanlığı)
- Maintain student-focused, encouraging, and supportive tone

## Code Standards
- **Python**: Use Black formatter, mandatory type hints, Turkish docstrings
- **TypeScript**: ESLint + Prettier configuration, strict mode enabled
- **Error Handling**: Comprehensive try-catch blocks with Turkish error messages
- **Async Patterns**: Use async/await for all I/O operations
- **Import Order**: Standard library → Third-party → Local modules

## Architecture Patterns
- **Agent Structure**: Place agents in `agents/` directory (LearningPathAgent, StudyAgent, ExamAgent)
- **Service Layer**: Core services in `core/` (llm_service, rag_service, monitoring_service)
- **Integration Layer**: External service integrations in `integrations/` (youtube_service, wikipedia_service)
- **Modular Design**: Separate module and test file for each feature
- **Dependency Injection**: Inject service dependencies via constructors

## Performance Guidelines
- Use `@lru_cache` decorator for function memoization
- Implement connection pooling with aiohttp ClientSession
- Apply rate limiting on API endpoints
- Implement lazy loading for large datasets
- Use context managers for resource management

## Testing Requirements
- Target minimum 80% test coverage
- Use pytest framework with pytest-asyncio for async tests
- Mock external services using `mock_responses.py`
- Follow `test_*.py` naming convention
- Define common test data in fixtures

## Security & Configuration
- Store sensitive data in `.env` files (`.env.production` for production)
- Use Pydantic models for input validation
- Configure appropriate CORS policies for frontend
- Implement secure API key management for external services

## Educational Content Standards
- Ensure compliance with Turkish National Education (MEB) curriculum
- Focus on LGS (8th grade) and YKS (12th grade) exam preparation
- Personalize content based on student level and learning style
- Combine multi-modal resources: YouTube videos, Wikipedia articles, interactive content
- Implement difficulty progression: Easy → Medium → Hard

## API Design
- Follow RESTful design with `/api/v1/` versioning
- Use consistent JSON response format: `{"success": bool, "data": any, "message": str}`
- Return meaningful HTTP status codes
- Provide Turkish error messages for user-friendly responses
- Implement pagination for large datasets

## Core Modules
- **LearningStyleDetector**: Detect student learning preferences
- **UnifiedResourceRanker**: Rank resources by relevance and quality
- **AssessmentSystem**: Track student evaluation and progress
- **PersonalizedLearningPath**: Generate customized learning paths