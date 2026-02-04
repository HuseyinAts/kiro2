"""
Fast unit tests for security middleware
Tests: Module imports and basic enum/class existence
Coverage target: +5-10% for core.security_middleware
"""
import pytest


class TestSecurityMiddlewareImports:
    """Test security middleware module imports"""

    def test_module_imports_successfully(self):
        """Test security middleware module can be imported"""
        from core import security_middleware

        assert security_middleware is not None

    def test_authentication_type_import(self):
        """Test AuthenticationType import"""
        from core.enhanced_authentication import AuthenticationType

        assert AuthenticationType is not None

    def test_token_type_import(self):
        """Test TokenType import"""
        from core.enhanced_authentication import TokenType

        assert TokenType is not None

    def test_rbac_action_import(self):
        """Test RBAC Action import"""
        from core.rbac_system import Action

        assert Action is not None

    def test_rbac_resource_type_import(self):
        """Test RBAC ResourceType import"""
        from core.rbac_system import ResourceType

        assert ResourceType is not None

    def test_error_severity_import(self):
        """Test ErrorSeverity import"""
        from core.exceptions import ErrorSeverity

        assert ErrorSeverity is not None
