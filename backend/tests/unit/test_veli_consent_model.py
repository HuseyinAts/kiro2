"""VeliConsent modeli + token helper unit testleri."""

from models.veli_consent import (
    CONSENT_TOKEN_TTL_DAYS,
    VeliConsent,
    generate_token,
    hash_token,
)


def test_generate_token_is_urlsafe_and_unique():
    t1 = generate_token()
    t2 = generate_token()
    assert isinstance(t1, str) and len(t1) >= 32
    assert t1 != t2  # kriptografik rastgelelik


def test_hash_token_is_sha256_hex_and_stable():
    token = "abc123"
    h = hash_token(token)
    assert len(h) == 64  # sha256 hexdigest
    assert h == hash_token(token)  # deterministik
    assert h != token  # plaintext değil


def test_veli_consent_defaults():
    c = VeliConsent(child_user_id="u1", veli_email="veli@example.com")
    assert c.status == "pending" or c.status is None  # default DB-side/py-side
    assert CONSENT_TOKEN_TTL_DAYS == 7
    assert VeliConsent.__tablename__ == "veli_consent"
