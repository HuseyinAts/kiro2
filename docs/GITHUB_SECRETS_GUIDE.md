# GitHub Secrets Konfigürasyonu

Bu belge, KIRO2 projesinin CI/CD pipeline'ı için gerekli GitHub Secrets'ları açıklar.

## Gerekli Secrets

### 1. KUBE_CONFIG (Staging)
**Kullanım:** Staging ortamına Kubernetes deployment
**Format:** Base64 encoded kubeconfig

```bash
# Staging kubeconfig'i base64'e çevir:
cat ~/.kube/config-staging | base64 -w0
```

**Repository'ye ekleme:**
- Settings → Secrets and variables → Actions → New repository secret
- Name: `KUBE_CONFIG`
- Value: Base64 encoded kubeconfig içeriği

---

### 2. PROD_KUBE_CONFIG
**Kullanım:** Production ortamına Kubernetes deployment
**Format:** Base64 encoded kubeconfig

```bash
# Production kubeconfig'i base64'e çevir:
cat ~/.kube/config-production | base64 -w0
```

**Güvenlik notu:** Production credentials için restricted access kullanın.

---

### 3. STAGING_TEST_PASSWORD
**Kullanım:** Staging ortamında otomatik test kullanıcısı şifresi
**Format:** Plain text şifre

**Örnek değer:** `staging_test_password_123!`

**Önemli:** Bu gerçek kullanıcı hesabı değil, sadece staging testleri için oluşturulmuş test hesabıdır.

---

### 4. SLACK_WEBHOOK
**Kullanım:** Deployment bildirimlerini Slack'e göndermek
**Format:** Slack webhook URL

**Oluşturma adımları:**
1. https://api.slack.com/apps adresine git
2. "Create New App" → "From scratch"
3. "Incoming Webhooks" etkinleştir
4. "Add New Webhook to Workspace"
5. Kanal seç (örn: #deployments)
6. Webhook URL'ini kopyala

**Örnek format:**
```
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
```

---

## Otomatik Sağlanan Secrets

### GITHUB_TOKEN
Bu secret GitHub tarafından otomatik sağlanır ve workflow içinde kullanılabilir.

**Yetkileri:**
- Container registry erişimi (ghcr.io)
- Code scanning sonuçları yükleme
- Super-linter için repo erişimi

---

## Ekleme Adımları

1. GitHub repository sayfasına git
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** tıkla
4. Secret adını ve değerini gir
5. **Add secret** tıkla

---

## Environment-Specific Secrets

Farklı environment'lar için farklı secrets kullanmak isterseniz:

1. **Settings** → **Environments** → Environment oluştur
2. Environment'a özel secrets ekle

### Örnek Environment Yapısı:
- `development` - Geliştirme ortamı
- `staging` - Test ortamı
- `production` - Canlı ortam (approval required)

---

## Güvenlik Tavsiyeleri

1. **Minimum yetki prensibi:** Secrets sadece gerekli yetkilerle oluşturun
2. **Rotasyon:** Secrets'ları düzenli olarak değiştirin (önerilen: 90 gün)
3. **Audit:** Settings → Security → Secret scanning alerts kontrol edin
4. **Production koruma:** Production environment için "Required reviewers" etkinleştirin

---

## Sorun Giderme

### "Secret not found" hatası
- Secret adının workflow'daki ile birebir aynı olduğundan emin olun (büyük/küçük harf duyarlı)

### "Bad credentials" hatası
- KUBE_CONFIG veya PROD_KUBE_CONFIG için base64 encoding doğru mu kontrol edin
- Kubeconfig'deki cluster ve user bilgileri geçerli mi kontrol edin

### Slack bildirimi gelmiyor
- SLACK_WEBHOOK URL'inin doğru olduğundan emin olun
- Slack uygulamasının aktif olduğunu kontrol edin
