# Tasks Document - Auth Enhancement

## Overview

Bu doküman, Auth Enhancement sisteminin implementation task'larını tanımlar. Tüm task'lar FastAPI + pyotp + authlib + python-saml stack'i kullanarak Python 3.13+ ile implement edilecek.

## Tasks

### 1. Setup Project Structure
- [x] 1.1 Create directory structure and dependencies
  - Create `backend/core/` directory (already exists with auth modules)
  - Add pyotp>=2.9.0 to requirements.txt ✓
  - Add authlib>=1.3.0 for OAuth2 ✓
  - Add hypothesis>=6.0 for property testing ✓
  - _Requirements: REQ-1.1_

### 2. Implement Multi-Factor Authentication
- [x] 2.1 Create MFA system
  - [x] 2.1.1 `backend/core/two_factor_auth.py` (EXISTS)
    - Implement TOTP generation using pyotp (RFC 6238) ✓
    - Generate QR code with secret key embedded ✓
    - Verify TOTP with 30-second time window ✓
    - Add Turkish docstrings (Google style) ✓
    - _Requirements: REQ-1.1, REQ-1.2, REQ-1.3_

  - [x] 2.1.2 Implement backup codes (EXISTS in two_factor_auth.py)
    - Generate 10 single-use backup codes ✓
    - Hash backup codes before storage (SHA-256) ✓
    - Implement backup code verification ✓
    - _Requirements: REQ-1.4_
  
  - [x] 2.1.3 Implement MFA recovery
    - Email verification for MFA recovery
    - Temporary recovery token (15 min expiry)
    - _Requirements: REQ-1.5_

  - [x] 2.1.4 Enforce MFA for admin users
    - Check user role before allowing MFA bypass
    - Mandatory MFA for admin accounts
    - _Requirements: REQ-1.6_

- [x]* 2.2 Write property test for TOTP validity
  - Create `backend/tests/property/test_mfa.py` ✓
  - **Property 1: MFA Token Validity** - TOTP valid only within 30s window ✓
  - Test with random timestamps ✓
  - Run 100+ iterations ✓
  - **Validates: Requirements REQ-1.3**

### 3. Implement OAuth2 Integration
- [x] 3.1 Create OAuth2 system
  - [x] 3.1.1 Create `backend/core/oauth2_service.py`
    - Implement authorization code grant flow
    - Support Google OAuth2 API
    - Generate and verify state parameter for CSRF protection
    - Add Turkish docstrings (Google style)
    - _Requirements: REQ-2.1, REQ-2.2, REQ-2.3_

  - [x] 3.1.2 Implement token exchange
    - Exchange authorization code for tokens
    - Store access + refresh tokens
    - Handle token refresh
    - _Requirements: REQ-2.4_

  - [x] 3.1.3 Fetch user info
    - Call provider profile API
    - Extract email, name, profile picture
    - _Requirements: REQ-2.5_

  - [x] 3.1.4 Implement account linking
    - Email-based account merge
    - Link OAuth account to existing user
    - _Requirements: REQ-2.6_

- [x]* 3.2 Write property test for OAuth2 state
  - Create `backend/tests/property/test_oauth2.py` ✓
  - **Property 3: OAuth2 State Parameter** - State prevents CSRF ✓
  - Test with random state values ✓
  - Run 100+ iterations ✓
  - **Validates: Requirements REQ-2.3**

### 4. Implement Single Sign-On (SSO)
- [x] 4.1 Create SSO system
  - [x] 4.1.1 Create `backend/core/sso_saml_service.py` ✓
    - Implement SAML 2.0 protocol ✓
    - Parse IdP XML metadata ✓
    - Verify SAML assertion signatures ✓
    - Add Turkish docstrings (Google style) ✓
    - _Requirements: REQ-3.1, REQ-3.2, REQ-3.3_

  - [x] 4.1.2 Implement attribute mapping ✓
    - Extract email, name, role from SAML assertion ✓
    - Map SAML attributes to user model (ATTRIBUTE_MAP) ✓
    - _Requirements: REQ-3.4_

  - [x] 4.1.3 Implement single logout (SLO) ✓
    - Support SAML single logout (initiate_logout, handle_logout_response) ✓
    - Sync session timeout with IdP ✓
    - _Requirements: REQ-3.5, REQ-3.6_

- [x]* 4.2 Write integration tests for SSO ✓
  - Create `backend/tests/integration/test_sso_saml.py` ✓
  - Test SAML assertion validation ✓
  - Test attribute mapping ✓
  - Test single logout flow ✓
  - _Requirements: REQ-3.1-3.6_

### 5. Implement Biometric Authentication
- [x] 5.1 Create biometric auth system
  - [x] 5.1.1 Create `backend/core/biometric_auth_service.py` ✓
    - Check device capability for biometric (check_device_capability) ✓
    - Integrate platform API (Touch ID, Face ID) ✓
    - Use device-local storage for biometric data ✓
    - Add Turkish docstrings (Google style) ✓
    - _Requirements: REQ-4.1, REQ-4.2, REQ-4.3_

  - [x] 5.1.2 Implement fallback mechanism ✓
    - Provide PIN/password fallback option (fallback_to_password) ✓
    - _Requirements: REQ-4.4_

  - [x] 5.1.3 Implement challenge-response ✓
    - Use challenge-response protocol (generate_challenge, verify_challenge_response) ✓
    - Implement liveness detection (liveness_check_passed flag) ✓
    - _Requirements: REQ-4.5, REQ-4.6_

- [x]* 5.2 Write unit tests for biometric auth ✓
  - Create `backend/tests/unit/auth/test_biometric.py` ✓
  - Test device capability check ✓
  - Test fallback mechanism ✓
  - Test challenge-response protocol ✓
  - _Requirements: REQ-4.1-4.6_

### 6. Implement Passwordless Authentication
- [x] 6.1 Create passwordless auth system
  - [x] 6.1.1 Create `backend/core/passwordless_auth.py` ✓
    - Implement magic link with time-limited token (15 min) ✓
    - Enforce one-time use token ✓
    - Add Turkish docstrings (Google style) ✓
    - _Requirements: REQ-5.1, REQ-5.2_

  - [x] 6.1.2 Implement WebAuthn/FIDO2 ✓
    - Apply FIDO2 standard (WebAuthnService class) ✓
    - Register passkey (generate_registration_options, verify_registration_response) ✓
    - Authenticate with challenge-response (generate_authentication_options, verify_authentication_response) ✓
    - _Requirements: REQ-5.3, REQ-5.4, REQ-5.5_

  - [x] 6.1.3 Implement fallback ✓
    - Provide traditional login option (supports_fallback_to_password) ✓
    - _Requirements: REQ-5.6_

- [x]* 6.2 Write integration tests for passwordless ✓
  - Create `backend/tests/integration/test_passwordless_webauthn.py` ✓
  - Test magic link flow ✓
  - Test WebAuthn registration and authentication ✓
  - Test fallback mechanism ✓
  - _Requirements: REQ-5.1-5.6_

### 7. Implement Session Management
- [x] 7.1 Create session management system (`backend/core/unified_auth_service.py` EXISTS)
  - [x] 7.1.1 Session management in `unified_auth_service.py` (EXISTS)
    - Generate cryptographically secure session ID ✓
    - Implement idle timeout + absolute timeout ✓
    - Session tracking in _sessions dictionary ✓
    - Add Turkish docstrings ✓
    - _Requirements: REQ-6.1, REQ-6.2, REQ-6.3_

  - [x] 7.1.2 Implement session hijacking prevention
    - Bind session to IP + User-Agent ✓
    - Detect suspicious session activity ✓
    - `bind_session_to_context()`, `detect_session_hijacking()` ✓
    - _Requirements: REQ-6.4_

  - [x] 7.1.3 Implement session revocation (EXISTS)
    - Immediate session invalidation (`end_session()`) ✓
    - Log session activity (audit logging) ✓
    - `end_all_user_sessions()` for logout-all ✓
    - _Requirements: REQ-6.5, REQ-6.6_

- [x]* 7.2 Write property test for session timeout
  - Create `backend/tests/property/test_session.py` ✓
  - **Property 2: Session Timeout Enforcement** - Expire after 30 min idle or 24h absolute ✓
  - Test with random activity patterns ✓
  - Run 100+ iterations ✓
  - **Validates: Requirements REQ-6.2**

### 8. Implement Role-Based Access Control
- [x] 8.1 Create RBAC system (`backend/core/rbac_system.py` EXISTS)
  - [x] 8.1.1 `backend/core/rbac_system.py` (EXISTS)
    - Define roles: student, teacher, admin, super_admin, parent, guest ✓
    - Implement granular permissions (read, write, delete, execute, approve, etc.) ✓
    - Support role hierarchy with inheritance ✓
    - Add Turkish docstrings ✓
    - _Requirements: REQ-7.1, REQ-7.2, REQ-7.3_

  - [x] 8.1.2 Implement decorator-based authorization (EXISTS in auth_dependencies.py)
    - Permission checking via RBACManager ✓
    - Check permissions before endpoint execution ✓
    - _Requirements: REQ-7.4_

  - [x] 8.1.3 Implement role management (EXISTS)
    - Immediate effect on role change (cache clearing) ✓
    - Log permission access (audit logging) ✓
    - _Requirements: REQ-7.5, REQ-7.6_

- [x]* 8.2 Write property test for role inheritance
  - Create `backend/tests/property/test_rbac.py` ✓
  - **Property 4: Role Permission Inheritance** - Child roles inherit parent permissions ✓
  - Test with random role hierarchies ✓
  - Run 100+ iterations ✓
  - **Validates: Requirements REQ-7.3**

### 9. Implement Account Security Features
- [x] 9.1 Create account security system
  - [x] 9.1.1 Create `backend/core/account_security.py`
    - Detect suspicious activity (unusual IP, device)
    - Send email alert on suspicious activity
    - Require device verification for new devices
    - Add Turkish docstrings (Google style)
    - _Requirements: REQ-8.1, REQ-8.2_

  - [x] 9.1.2 Implement password change security
    - Invalidate all sessions on password change
    - _Requirements: REQ-8.3_

  - [x] 9.1.3 Implement account recovery
    - Multi-step verification for recovery
    - Show last 10 login attempts
    - Require admin approval for account unlock
    - _Requirements: REQ-8.4, REQ-8.5, REQ-8.6_

- [ ]* 9.2 Write integration tests for account security
  - Create `tests/integration/auth/test_security.py`
  - Test suspicious activity detection
  - Test device verification
  - Test account recovery flow
  - _Requirements: REQ-8.1-8.6_

### 10. Create Auth API Endpoints
- [x] 10.1 Create FastAPI endpoints
  - `backend/api/auth.py` (EXISTS - core auth endpoints) ✓
  - `backend/api/two_factor_auth_api.py` (EXISTS - MFA endpoints) ✓
  - `backend/api/enhanced_auth_api.py` (NEW - OAuth2, Magic Link, Sessions) ✓
  - POST /api/v1/auth/register - User registration ✓
  - POST /api/v1/auth/login - Password login ✓
  - POST /api/v1/auth/logout - Logout ✓
  - POST /api/v1/auth/2fa/enable - Enable MFA ✓
  - POST /api/v1/auth/2fa/verify - Verify TOTP ✓
  - GET /api/v1/auth/oauth2/{provider} - OAuth2 login ✓
  - POST /api/v1/auth/magic-link/send - Send magic link ✓
  - GET /api/v1/auth/sessions - List active sessions ✓
  - DELETE /api/v1/auth/sessions/{id} - Revoke session ✓
  - Add Pydantic request/response models ✓
  - Add Turkish docstrings (Google style) ✓
  - _Requirements: All_

- [ ]* 10.2 Write API integration tests
  - Create `tests/integration/auth/test_api.py`
  - Test all auth endpoints
  - Test authentication flows
  - Test error handling
  - _Requirements: All_

### 11. Checkpoint - Integration Testing
- [ ] 11.1 Run full integration test suite
  - Test complete MFA flow
  - Test OAuth2 login flow
  - Test SSO SAML flow
  - Test session management
  - Test RBAC authorization
  - Verify MFA adoption rate >= 60%
  - Verify OAuth2 success rate >= 95%
  - Verify auth latency < 200ms
  - Ensure all tests pass, ask the user if questions arise.

### 12. Documentation and Deployment
- [ ] 12.1 Update documentation
  - Create `docs/auth/mfa-setup.md`
  - Create `docs/auth/oauth2-integration.md`
  - Create `docs/auth/sso-configuration.md`
  - Create `docs/auth/rbac-guide.md`
  - _Requirements: All_

- [ ] 12.2 Create deployment configuration
  - Update `docker-compose.yml` with auth services
  - Configure OAuth2 client credentials
  - Configure SAML IdP metadata
  - Set environment variables
  - _Requirements: All_

## Success Metrics
1. **MFA Adoption Rate:** >= 60%
2. **OAuth2 Login Success Rate:** >= 95%
3. **Session Hijacking Prevention:** 100%
4. **Account Takeover Prevention:** 100%
5. **Auth Latency:** < 200ms

## Notes
- Tasks marked with `*` are optional test tasks
- All async operations use Python 3.13+ async/await syntax
- Follow AGENTS.md coding standards
- Use pyotp for TOTP implementation
- Use authlib for OAuth2
- Use python3-saml for SAML SSO
- Use webauthn for FIDO2/WebAuthn
