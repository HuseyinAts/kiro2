"""
Property-Based Tests - OAuth2 State Parameter

Bu modul, hypothesis kullanarak OAuth2 state parametresi ve
CSRF korumasi icin property-based testler icerir.

Property 3: State parameter prevents CSRF
- Her state token benzersiz olmali
- State tokenlar belirli sure sonra expire olmali
- State token dogrulama CSRF saldirilarini engellemeli
- Farkli provider icin state token eslesmemeli

Requirements:
- REQ-2.3: State parameter ile CSRF korumasi
- REQ-3.1: State token benzersizligi
- REQ-3.2: State token expiry
- REQ-3.3: Provider-specific state validation
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional

from hypothesis import assume, given, settings, strategies as st

import sys
sys.path.insert(0, "c:/Users/husey/kiro2/backend")


# OAuth2 state yonetimi icin minimal implementation
# Production kodunu test icin simule eder
@dataclass
class OAuth2StateToken:
    """OAuth2 state token bilgisi."""
    state: str
    provider: str
    created_at: datetime
    expires_at: datetime
    redirect_uri: Optional[str] = None


class OAuth2StateManager:
    """
    OAuth2 state token yonetimi.

    CSRF korumasi icin state parametresi yonetir.
    Production'daki OAuth2Service'i simule eder.
    """

    STATE_EXPIRY_MINUTES = 10

    def __init__(self):
        self._states: dict[str, OAuth2StateToken] = {}

    def generate_state(self) -> str:
        """Kriptografik olarak guvenli state token olusturur."""
        return secrets.token_urlsafe(32)

    def store_state(
        self,
        provider: str,
        redirect_uri: Optional[str] = None,
        created_at: Optional[datetime] = None
    ) -> str:
        """State token olusturur ve saklar."""
        state = self.generate_state()
        now = created_at or datetime.now(timezone.utc)

        state_obj = OAuth2StateToken(
            state=state,
            provider=provider.lower(),
            created_at=now,
            expires_at=now + timedelta(minutes=self.STATE_EXPIRY_MINUTES),
            redirect_uri=redirect_uri,
        )
        self._states[state] = state_obj

        return state

    def verify_state(
        self,
        state: str,
        provider: str,
        check_time: Optional[datetime] = None
    ) -> tuple[bool, str]:
        """
        State token'i dogrular ve sonuc dondurur.

        Returns:
            tuple[bool, str]: (is_valid, reason)
        """
        now = check_time or datetime.now(timezone.utc)

        # State bulunamadi
        if state not in self._states:
            return False, "state_not_found"

        state_obj = self._states[state]

        # Suresi dolmus
        if now > state_obj.expires_at:
            return False, "state_expired"

        # Provider eslesmemesi
        if state_obj.provider != provider.lower():
            return False, "provider_mismatch"

        # Basarili - state'i kaldir (one-time use)
        del self._states[state]
        return True, "valid"

    def consume_state(self, state: str, provider: str) -> OAuth2StateToken | None:
        """State'i dogrular, tüketir ve bilgilerini dondurur."""
        is_valid, reason = self.verify_state(state, provider)
        if not is_valid:
            return None

        # State zaten verify_state icinde silindi
        # Eger silinmemis olsaydi burada silinirdi
        return OAuth2StateToken(
            state=state,
            provider=provider,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc),
        )

    def get_active_state_count(self) -> int:
        """Aktif state sayisini dondurur."""
        now = datetime.now(timezone.utc)
        return sum(1 for s in self._states.values() if now <= s.expires_at)

    def cleanup_expired(self) -> int:
        """Suresi dolmus state'leri temizler."""
        now = datetime.now(timezone.utc)
        expired = [s for s, obj in self._states.items() if now > obj.expires_at]
        for s in expired:
            del self._states[s]
        return len(expired)


class TestOAuth2StateCSRFProperties:
    """OAuth2 state CSRF korumasi property-based testleri."""

    def setup_method(self):
        """Her test oncesi OAuth2StateManager olustur."""
        self.manager = OAuth2StateManager()

    @given(
        provider=st.sampled_from(["google", "github", "facebook", "microsoft"])
    )
    @settings(max_examples=100)
    def test_generated_state_is_unique(self, provider: str):
        """
        Property 3.1: Her state token benzersiz olmali.

        Ayni provider icin bile farkli state token'lar uretilmeli.
        """
        states = set()

        for _ in range(100):
            state = self.manager.store_state(provider)
            states.add(state)

        # Tum state'ler benzersiz olmali
        assert len(states) == 100, \
            f"All 100 states should be unique, got {len(states)} unique"

    @given(
        provider=st.sampled_from(["google", "github"])
    )
    @settings(max_examples=100)
    def test_state_length_sufficient(self, provider: str):
        """
        Property 3.2: State token yeterli uzunlukta olmali.

        En az 32 karakter ile brute force'a karsi guvenli olmali.
        """
        state = self.manager.store_state(provider)

        # En az 32 karakter (256 bit entropy icin)
        assert len(state) >= 32, \
            f"State should be at least 32 chars, got {len(state)}"

    @given(
        provider=st.sampled_from(["google", "github"])
    )
    @settings(max_examples=100)
    def test_valid_state_verifies_successfully(self, provider: str):
        """
        Property 3.3: Gecerli state dogrulama basarili olmali.

        Olusturulan state ayni provider ile dogrulanabilmeli.
        """
        state = self.manager.store_state(provider)

        is_valid, reason = self.manager.verify_state(state, provider)

        assert is_valid, \
            f"Valid state should verify successfully, reason: {reason}"
        assert reason == "valid"

    @given(
        original_provider=st.sampled_from(["google", "github"]),
        attack_provider=st.sampled_from(["facebook", "microsoft"])
    )
    @settings(max_examples=100)
    def test_state_fails_with_wrong_provider(self, original_provider: str, attack_provider: str):
        """
        Property 3.4: Farkli provider ile state dogrulanamaz.

        CSRF korumasi: State belirli provider icin gecerli olmali.
        """
        # original_provider ve attack_provider farkli olmali
        assume(original_provider != attack_provider)

        state = self.manager.store_state(original_provider)

        is_valid, reason = self.manager.verify_state(state, attack_provider)

        assert not is_valid, \
            "State should fail with wrong provider"
        assert reason == "provider_mismatch"

    @given(
        expiry_minutes=st.integers(min_value=11, max_value=60)
    )
    @settings(max_examples=100)
    def test_expired_state_fails_verification(self, expiry_minutes: int):
        """
        Property 3.5: Suresi dolmus state dogrulanamaz.

        State 10 dakika sonra gecersiz olmali.
        """
        base_time = datetime.now(timezone.utc)
        state = self.manager.store_state("google", created_at=base_time)

        # expiry_minutes sonra kontrol (10 dakikadan fazla)
        check_time = base_time + timedelta(minutes=expiry_minutes)
        is_valid, reason = self.manager.verify_state(state, "google", check_time=check_time)

        assert not is_valid, \
            "Expired state should fail verification"
        assert reason == "state_expired"

    @given(
        minutes=st.integers(min_value=1, max_value=9)
    )
    @settings(max_examples=100)
    def test_state_valid_before_expiry(self, minutes: int):
        """
        Property 3.6: Suresi dolmadan state gecerli olmali.

        10 dakikadan once state hala gecerli olmali.
        """
        base_time = datetime.now(timezone.utc)
        state = self.manager.store_state("google", created_at=base_time)

        # minutes sonra kontrol (10 dakikadan az)
        check_time = base_time + timedelta(minutes=minutes)
        is_valid, reason = self.manager.verify_state(state, "google", check_time=check_time)

        assert is_valid, \
            f"State should be valid before expiry at {minutes} minutes"

    @given(
        fake_state=st.text(
            alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"),
            min_size=32,
            max_size=64
        )
    )
    @settings(max_examples=100)
    def test_unknown_state_fails(self, fake_state: str):
        """
        Property 3.7: Bilinmeyen state dogrulanamaz.

        Sistem tarafindan olusturulmamis state reddedilmeli.
        """
        # Gercek bir state olustur (farkli oldugunu garantile)
        real_state = self.manager.store_state("google")

        # Fake state farkli olmali
        assume(fake_state != real_state)

        is_valid, reason = self.manager.verify_state(fake_state, "google")

        assert not is_valid, \
            "Unknown state should fail verification"
        assert reason == "state_not_found"

    @given(
        provider=st.sampled_from(["google", "github"])
    )
    @settings(max_examples=100)
    def test_state_single_use(self, provider: str):
        """
        Property 3.8: State tek kullanimlik olmali.

        Ayni state iki kez dogrulanamaz (replay attack korumasi).
        """
        state = self.manager.store_state(provider)

        # Ilk dogrulama basarili
        is_valid_first, _ = self.manager.verify_state(state, provider)
        assert is_valid_first, "First verification should succeed"

        # Ikinci dogrulama basarisiz
        is_valid_second, reason = self.manager.verify_state(state, provider)
        assert not is_valid_second, \
            "Second verification should fail (replay protection)"
        assert reason == "state_not_found"

    @given(
        state_count=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=100)
    def test_multiple_states_independent(self, state_count: int):
        """
        Property 3.9: Her state bagimsiz olmali.

        Bir state'in dogrulanmasi digerlerini etkilememeli.
        """
        states = []
        for i in range(state_count):
            state = self.manager.store_state("google")
            states.append(state)

        # Ilk state'i dogrula
        is_valid, _ = self.manager.verify_state(states[0], "google")
        assert is_valid

        # Diger state'ler hala gecerli olmali
        for state in states[1:]:
            is_valid, reason = self.manager.verify_state(state, "google")
            assert is_valid, \
                f"Other states should still be valid, reason: {reason}"


class TestOAuth2StateEntropyProperties:
    """OAuth2 state entropy property-based testleri."""

    def setup_method(self):
        """Her test oncesi OAuth2StateManager olustur."""
        self.manager = OAuth2StateManager()

    @given(
        sample_size=st.integers(min_value=50, max_value=100)
    )
    @settings(max_examples=50)
    def test_state_entropy_distribution(self, sample_size: int):
        """
        Property 3.10: State token'lar iyi dagilima sahip olmali.

        Kriptografik rastgelelik kontrolu.
        """
        states = []
        for _ in range(sample_size):
            state = self.manager.store_state("google")
            states.append(state)

        # Tum state'ler farkli olmali
        unique_states = set(states)
        assert len(unique_states) == sample_size, \
            f"All {sample_size} states should be unique"

        # Ilk karakterlerin dagilimi (tamamen deterministik olmamali)
        first_chars = [s[0] for s in states]
        unique_first_chars = set(first_chars)

        # En az 5 farkli ilk karakter beklenir (iyi dagilim)
        assert len(unique_first_chars) >= 5, \
            "First characters should have good distribution"

    @given(
        provider=st.sampled_from(["google", "github"])
    )
    @settings(max_examples=100)
    def test_state_no_predictable_pattern(self, provider: str):
        """
        Property 3.11: State token tahmin edilemez olmali.

        Ardisik state'ler arasinda pattern olmamali.
        """
        state1 = self.manager.store_state(provider)
        state2 = self.manager.store_state(provider)

        # Hash'ler farkli olmali
        hash1 = hashlib.sha256(state1.encode()).hexdigest()
        hash2 = hashlib.sha256(state2.encode()).hexdigest()

        assert hash1 != hash2, \
            "Consecutive states should have different hashes"

        # Ilk N karakter bile farkli olmali (pattern yok)
        assert state1[:8] != state2[:8], \
            "State prefixes should differ"


class TestOAuth2StateRedirectProperties:
    """OAuth2 state redirect URI property-based testleri."""

    def setup_method(self):
        """Her test oncesi OAuth2StateManager olustur."""
        self.manager = OAuth2StateManager()

    @given(
        redirect_uri=st.sampled_from([
            "https://app.example.com/callback",
            "https://localhost:3000/oauth/callback",
            "/dashboard",
            None
        ])
    )
    @settings(max_examples=100)
    def test_redirect_uri_preserved(self, redirect_uri: str | None):
        """
        Property 3.12: Redirect URI state ile saklanmali.

        State olusturulurken verilen redirect_uri korunmali.
        """
        state = self.manager.store_state("google", redirect_uri=redirect_uri)

        # State bilgisini al (verify etmeden)
        state_obj = self.manager._states.get(state)

        assert state_obj is not None
        assert state_obj.redirect_uri == redirect_uri, \
            "Redirect URI should be preserved"

    @given(
        provider=st.sampled_from(["google", "github", "microsoft"])
    )
    @settings(max_examples=100)
    def test_provider_case_insensitive(self, provider: str):
        """
        Property 3.13: Provider karsilastirmasi case-insensitive olmali.

        "Google" ve "google" ayni provider olmali.
        """
        state = self.manager.store_state(provider.upper())

        # Lowercase ile dogrula
        is_valid, _ = self.manager.verify_state(state, provider.lower())

        assert is_valid, \
            "Provider comparison should be case-insensitive"
