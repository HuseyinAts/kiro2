"""
SSO/SAML Integration Tests - KIRO2 Auth Enhancement

Task 4.2 gereksinimlerini karsilar.
"""

import pytest

from core.sso_saml_service import (
    SAMLService,
    SPConfig,
    SAMLError,
)


@pytest.fixture
def sp_config() -> SPConfig:
    """Test SP konfigurasyonu."""
    return SPConfig(
        entity_id="https://kiro2.test/saml/metadata",
        acs_url="https://kiro2.test/api/v1/auth/saml/acs",
        slo_url="https://kiro2.test/api/v1/auth/saml/slo",
        metadata_url="https://kiro2.test/api/v1/auth/saml/metadata",
    )


@pytest.fixture
def saml_service(sp_config: SPConfig) -> SAMLService:
    """Test SAML servisi."""
    return SAMLService(sp_config)


@pytest.fixture
def sample_idp_metadata() -> str:
    """Ornek IdP metadata XML."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                     xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
                     entityID="https://idp.test.com/saml">
    <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:KeyDescriptor use="signing">
            <ds:KeyInfo>
                <ds:X509Data>
                    <ds:X509Certificate>MIICpDCCAYwCCQDU+pQ4P2HmHjANBgkqhkiG9w0BAQsFADAUMRIwEAYDVQQDDAl0ZXN0LmNvbTAe
Fw0yMzAxMDEwMDAwMDBaFw0yNDAxMDEwMDAwMDBaMBQxEjAQBgNVBAMMCXRlc3QuY29tMIIBIjAN
BgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy0AHBYMn0riz1e
DnQBv0kUQFhFQhXB0P+I3nMsjvRNzPXzOJfB0L2P0LwZ2KLXQJB0OWJfax3tKLF9e1Ao6TqHqD3g
3k9z9q0fP4vN5h5PE6B5BqPpRH1Y4LCrFQAa5F+oOIJj5BFKYOr5vx5OO4N9L5xDBi0C7xb5xNkh
rZvPLxPQ9UrUyQxZgOYY0P5F5H5v5M5x0Z5o5T5y5p5e5R5a5N5d0O5m5C5o5D5e0AAA</ds:X509Certificate>
                </ds:X509Data>
            </ds:KeyInfo>
        </md:KeyDescriptor>
        <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
        <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                Location="https://idp.test.com/saml/sso"/>
        <md:SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                Location="https://idp.test.com/saml/slo"/>
    </md:IDPSSODescriptor>
</md:EntityDescriptor>"""


class TestIdPMetadataParsing:
    """IdP metadata parse testleri (REQ-3.2)."""

    @pytest.mark.asyncio
    async def test_parse_valid_idp_metadata(
        self,
        saml_service: SAMLService,
        sample_idp_metadata: str,
    ) -> None:
        """Gecerli IdP metadata basariyla parse edilmeli."""
        result = await saml_service.configure_idp(sample_idp_metadata)

        assert result.success is True
        assert result.data is not None

        idp_config = result.data
        assert idp_config.entity_id == "https://idp.test.com/saml"
        assert idp_config.sso_url == "https://idp.test.com/saml/sso"
        assert idp_config.slo_url == "https://idp.test.com/saml/slo"
        assert idp_config.certificate is not None
        assert "BEGIN CERTIFICATE" in idp_config.certificate

    @pytest.mark.asyncio
    async def test_parse_invalid_xml_returns_error(
        self,
        saml_service: SAMLService,
    ) -> None:
        """Gecersiz XML hata dondurmeli."""
        result = await saml_service.configure_idp("<invalid>xml")

        assert result.success is False
        assert result.error == SAMLError.INVALID_METADATA

    @pytest.mark.asyncio
    async def test_parse_missing_entity_id_returns_error(
        self,
        saml_service: SAMLService,
    ) -> None:
        """Entity ID eksikse hata dondurmeli."""
        invalid_metadata = """<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
    <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    </md:IDPSSODescriptor>
</md:EntityDescriptor>"""

        result = await saml_service.configure_idp(invalid_metadata)

        assert result.success is False
        assert result.error == SAMLError.INVALID_METADATA


class TestAuthnRequestGeneration:
    """AuthnRequest olusturma testleri (REQ-3.1)."""

    @pytest.mark.asyncio
    async def test_create_authn_request_requires_idp_config(
        self,
        saml_service: SAMLService,
    ) -> None:
        """IdP konfigurasyonu olmadan hata dondurmeli."""
        result = await saml_service.create_authn_request()

        assert result.success is False
        assert result.error == SAMLError.IDP_NOT_CONFIGURED

    @pytest.mark.asyncio
    async def test_create_authn_request_with_idp_config(
        self,
        saml_service: SAMLService,
        sample_idp_metadata: str,
    ) -> None:
        """IdP konfigurasyonu ile AuthnRequest basariyla olusturulmali."""
        await saml_service.configure_idp(sample_idp_metadata)
        result = await saml_service.create_authn_request(relay_state="/dashboard")

        assert result.success is True
        assert result.data is not None

        request = result.data
        assert request.id.startswith("_kiro2_")
        assert request.destination == "https://idp.test.com/saml/sso"
        assert request.relay_state == "/dashboard"
        assert "SAMLRequest=" in request.redirect_url

    @pytest.mark.asyncio
    async def test_authn_request_generates_unique_ids(
        self,
        saml_service: SAMLService,
        sample_idp_metadata: str,
    ) -> None:
        """Her AuthnRequest benzersiz ID'ye sahip olmali."""
        await saml_service.configure_idp(sample_idp_metadata)

        result1 = await saml_service.create_authn_request()
        result2 = await saml_service.create_authn_request()

        assert result1.data.id != result2.data.id


class TestSPMetadataGeneration:
    """SP metadata olusturma testleri."""

    @pytest.mark.asyncio
    async def test_generate_sp_metadata(
        self,
        saml_service: SAMLService,
    ) -> None:
        """SP metadata XML olusturulmali."""
        metadata = await saml_service.generate_sp_metadata()

        assert "EntityDescriptor" in metadata
        assert saml_service.sp_config.entity_id in metadata
        assert saml_service.sp_config.acs_url in metadata
        assert "KIRO2" in metadata


class TestSingleLogout:
    """Single Logout (SLO) testleri (REQ-3.5)."""

    @pytest.mark.asyncio
    async def test_initiate_logout_requires_idp(
        self,
        saml_service: SAMLService,
    ) -> None:
        """IdP olmadan logout baslatilamamali."""
        result = await saml_service.initiate_logout(
            session_index="session_123",
            name_id="user@test.com",
        )

        assert result.success is False
        assert result.error == SAMLError.IDP_NOT_CONFIGURED

    @pytest.mark.asyncio
    async def test_initiate_logout_with_idp(
        self,
        saml_service: SAMLService,
        sample_idp_metadata: str,
    ) -> None:
        """IdP ile logout basariyla baslatilmali."""
        await saml_service.configure_idp(sample_idp_metadata)

        result = await saml_service.initiate_logout(
            session_index="session_123",
            name_id="user@test.com",
        )

        assert result.success is True
        assert result.data is not None
        assert result.data.destination == "https://idp.test.com/saml/slo"


class TestAttributeMapping:
    """Attribute mapping testleri (REQ-3.4)."""

    def test_attribute_map_contains_email_variants(self) -> None:
        """Email attribute varyantlari tanimli olmali."""
        from core.sso_saml_service import ATTRIBUTE_MAP

        email_mappings = [k for k, v in ATTRIBUTE_MAP.items() if v == "email"]
        assert len(email_mappings) >= 3  # En az 3 farkli email attribute

    def test_attribute_map_contains_name_variants(self) -> None:
        """Name attribute varyantlari tanimli olmali."""
        from core.sso_saml_service import ATTRIBUTE_MAP

        name_mappings = [k for k, v in ATTRIBUTE_MAP.items() if v in ["name", "first_name", "last_name"]]
        assert len(name_mappings) >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
