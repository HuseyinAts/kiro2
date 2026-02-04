# Writer + Reviewer Pattern

> "Bir agent kod yazıyor, digeri review ediyor - daha fazla sorun yakalaniyor."

## Konsept

```
┌─────────────────┐        ┌─────────────────┐
│ Writer Agent    │        │ Reviewer Agent  │
│   (python-pro)  │        │ (code-reviewer) │
└────────┬────────┘        └────────┬────────┘
         │                          │
         │  1. Kod yaz              │
         ├─────────────────────────>│
         │                          │ 2. Review et
         │<─────────────────────────┤
         │  3. Feedback             │
         │                          │
         │  4. Duzelt               │
         ├─────────────────────────>│
         │                          │ 5. Onayla
         │<─────────────────────────┤
         │                          │
         ▼                          ▼
    ┌─────────────────────────────────┐
    │        Final Kod                │
    │   (verification-agent)          │
    └─────────────────────────────────┘
```

## Adim Adim Uygulama

### Adim 1: Writer Kod Olusturur
```
@python-pro: JWT authentication endpoint implement et

POST /api/v1/auth/login
- email/password validation
- JWT token generation
- Refresh token logic
```

### Adim 2: Reviewer Inceler
```
@code-reviewer: Auth endpoint'i incele:
- Guvenlik aciklari
- Type safety
- Error handling
- KIRO2 conventions
```

### Adim 3: Feedback Uygulanir
```
@python-pro: Reviewer feedback'ini uygula:
1. Rate limiting ekle (5/dakika)
2. Password hashing guclendir (bcrypt cost 12)
3. Error message'lari genellestir (info leak onle)
```

### Adim 4: Final Dogrulama
```
@verification-agent: Full verification calistir
```

## KIRO2 Agent Eslestirme

| Writer | Reviewer | Kullanim |
|--------|----------|----------|
| python-pro | code-reviewer | Backend API |
| kiro2-frontend-specialist | code-reviewer | React components |
| turkish-nlp-specialist | code-reviewer | NLP modules |

## Review Checklist

### Guvenlik
- [ ] SQL injection korunmasi
- [ ] XSS korunmasi
- [ ] Hardcoded secrets yok
- [ ] Rate limiting var
- [ ] Input validation var

### Performans
- [ ] N+1 query yok
- [ ] Gereksiz re-render yok
- [ ] Memory leak riski yok
- [ ] Async/await dogru kullanilmis

### KIRO2 Spesifik
- [ ] IRT parametreleri valid [-4,4], [0.2,4], [0,0.35]
- [ ] Turkce karakter handling dogru
- [ ] authStore.ts kullanilmis (useAuth.ts degil)
- [ ] DB port 5434 kullanilmis

### Kod Kalitesi
- [ ] Type hints tam
- [ ] Docstring var
- [ ] DRY prensibi
- [ ] SOLID prensipleri

## Ornek Session

```markdown
## Writer Session

User: "Kullanici profil endpoint'i olustur"

@python-pro:
```python
@router.get("/users/{user_id}/profile")
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserProfileResponse:
    # Implementation...
```

## Reviewer Session

@code-reviewer:
🔴 KRITIK:
- user_id int yerine UUID olmali (tahmin edilemez)
- current_user kontrolu eksik (yetki)

🟡 UYARI:
- Cache eklenebilir (sik erişilen endpoint)

🟢 ONERI:
- Response model icin Pydantic kullan

## Writer Duzeltme

@python-pro: Feedback'e gore duzelt:
```python
@router.get("/users/{user_id}/profile")
async def get_user_profile(
    user_id: UUID,  # int -> UUID
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserProfileResponse:
    # Yetki kontrolu
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(403, "Unauthorized")
    # ...
```
```

## Avantajlar

1. **Hata yakalama**: Iki goz, bir gozden iyi
2. **Bilgi paylasimi**: Reviewer yeni pattern'ler onerir
3. **Kalite artisi**: %40-60 daha az bug
4. **Ogrenme**: Junior writer, senior reviewer'dan ogrenir

## Ne Zaman Kullanilmali

- Kritik modul degisiklikleri (auth, payment, data)
- Yeni feature implementasyonu
- Major refactoring
- Security-sensitive kod
- Performance-critical kod

## Ne Zaman KULLANILMAMALI

- Basit typo/comment fix
- Config degisiklikleri
- Tek satirlik duzeltmeler
- Acil hotfix (sonra review)
