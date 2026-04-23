"""
API Schemas Package
Shared Pydantic models for API contracts
"""

from .batch import (
    BatchErrorDetail,
    BatchOperation,
    BatchRequest,
    BatchResponse,
    HTTPMethod,
    OperationResult,
)
from .error_responses import (
    AUTH_RESPONSES,
    CREATE_RESPONSES,
    CRUD_RESPONSES,
    LIST_RESPONSES,
    STANDARD_ERROR_RESPONSES,
    # Response Wrappers
    APIResponse,
    ConflictResponse,
    # Error Models
    ErrorResponse,
    ForbiddenResponse,
    InternalServerErrorResponse,
    NotFoundResponse,
    PaginatedResponse,
    PaginationMeta,
    RateLimitResponse,
    UnauthorizedResponse,
    ValidationErrorResponse,
    create_error_response,
    create_paginated_response,
    # Helper Functions
    create_success_response,
)
from .irt_schemas import (
    DifficultyLevel,
    IRTAnalysisResponse,
    IRTBatchUpdateRequest,
    IRTCalibrationRequest,
    IRTModelType,
    IRTParameters,
    IRTParametersBase,
    IRTParametersUpdateRequest,
    QuestionIRTData,
    ZPDOptimalRange,
    ZPDRecommendation,
)
from .learning_path_schemas import (
    LearningPathCreateRequest,
    ResourceSearchRequest,
    StudentProfileData,
)
from .sparse_fieldset import (
    SparseFieldsetMixin,
    SparseFieldsetResponse,
    create_sparse_response,
    parse_fields_param,
)

__all__ = [
    # Learning Path Schemas
    "LearningPathCreateRequest",
    "StudentProfileData",
    "ResourceSearchRequest",
    # IRT Schemas
    "IRTModelType",
    "DifficultyLevel",
    "IRTParametersBase",
    "IRTParameters",
    "QuestionIRTData",
    "IRTParametersUpdateRequest",
    "IRTBatchUpdateRequest",
    "IRTCalibrationRequest",
    "IRTAnalysisResponse",
    "ZPDOptimalRange",
    "ZPDRecommendation",
    # Sparse Fieldset Support
    "SparseFieldsetMixin",
    "SparseFieldsetResponse",
    "create_sparse_response",
    "parse_fields_param",
    # Batch API Schemas
    "BatchErrorDetail",
    "BatchOperation",
    "BatchRequest",
    "BatchResponse",
    "HTTPMethod",
    "OperationResult",
    # Response Wrappers
    "APIResponse",
    "PaginatedResponse",
    "PaginationMeta",
    "create_success_response",
    "create_error_response",
    "create_paginated_response",
    # Error Response Schemas
    "ErrorResponse",
    "ValidationErrorResponse",
    "UnauthorizedResponse",
    "ForbiddenResponse",
    "NotFoundResponse",
    "ConflictResponse",
    "RateLimitResponse",
    "InternalServerErrorResponse",
    "STANDARD_ERROR_RESPONSES",
    "AUTH_RESPONSES",
    "CRUD_RESPONSES",
    "CREATE_RESPONSES",
    "LIST_RESPONSES",
]
