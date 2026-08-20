# A1 Altın Yol — Uçtan Uca Ölçüm Planı

> **Agentic worker'lar için:** Bu plan `Workflow` aracıyla yürütülür (FAZ 1–3).
> FAZ 0 ve FAZ 4 ana oturumda elle koşar. Adımlar `- [ ]` kutucuk sözdizimi kullanır.

**Hedef:** A1 kabul kriterinin dört ayağının her biri için — kayıt, e-posta
doğrulama, 40 soruluk TYT Matematik sınavı, net + konu kırılımı — canlı stack'ten
**ham çıktıyla** desteklenmiş tek bir yargı üretmek: `ÇALIŞIYOR` · `KIRIK` · `YOK`.

**Mimari:** Ölçüm ve düzeltme ayrılır. Beş bağımsız ölçücü ayakları paralel ölçer;
beş şüpheci her ayağın bulgularını **çürütmeye** çalışır (varsayılan yargı:
ÇÜRÜTÜLDÜ); bir eksiklik eleştirmeni hiç ölçülmemiş hata modlarını arar. Düzeltme
bu planın kapsamı **değil** — ölçüm çıktısı ayrı bir düzeltme planının girdisidir.

**Tasarım:** `docs/superpowers/specs/2026-08-20-a1-altin-yol-e2e-design.md` (`fa1784215`)

**Tech Stack:** FastAPI (canlı `localhost:8000`, container `kiro2-backend`) ·
React/Vite (`localhost:3000`, container `kiro2-frontend`) · PostgreSQL 18.1
(`localhost:5434`, db `kiro2`) · Playwright MCP · `curl` · `psql`

---

## Ölçülmüş taban (bu plan yazılırken canlıdan alındı, 20 Ağu 2026)

```
question_bank                 3.922
mv_safe_for_beta (kapı)       3.560   -> MAT dilimi 353 / 14 konu · KIM 3.207
canlı OpenAPI yol sayısı      1.119
users                             7   (hepsi STUDENT)
backend /health               200     frontend /  200     5 container healthy
```

**Kayıt sözleşmesi** (`POST /api/v1/auth/kayit`, şema `KullaniciOlustur`):
zorunlu `email`, `ad_soyad`, `sifre`, `rol`; `rol` enum'u
`ogrenci|ogretmen|veli|admin|super_admin`; `birth_date` varsayılanı `2000-01-01`;
opsiyonel `telefon`, `veli_email`, `aktif` (varsayılan `true`).

**Giriş sözleşmesi** (`POST /api/v1/auth/giris`, şema `KullaniciGiris`):
zorunlu `email`; parola alanı **iki isimden biri** — `sifre` veya `password`.

**Ölçülmüş ön-bulgu (FAZ 1'in doğrulayacağı):** `backend/api/v1/exams.py`
(`/generate-mock`, `/{id}/answer`, `/{id}/submit`) **canlı OpenAPI'de yok**.
1.119 yolun hiçbiri `/api/v1/exams/*` değil. Canlıda olan motor
`/api/v1/osym-exam/*`: `create`, `beta-practice`, `{id}/start`, `{id}/save-answer`,
`{id}/complete`, `{id}/subject-performance`, `{id}/current-question`, `{id}/navigate`.

---

## Dosya yapısı

| Yol | Sorumluluk | İşlem |
|---|---|---|
| `docs/audits/2026-08-20_a1_altin_yol_olcum.md` | Dört ayağın yargısı + ham kanıt + doğrulanmış engelleyici sıralaması | Oluştur |
| `.a1_e2e_kimlik.json` | FAZ 0 test hesabının kimliği + token (takipsiz, `.gitignore`'da) | Oluştur |
| `docs/superpowers/plans/2026-08-20-a1-altin-yol-duzeltme.md` | FAZ 4 TDD düzeltme planı | FAZ 3 çıktısından sonra yazılır |

Bu plan **hiçbir üretim dosyasını değiştirmez.** Üretim kodu değişikliği düzeltme
planının konusudur.

---

## FAZ 0 — Test hesabı (ana oturum, elle)

Neden elle: L2–L5'in hepsi aynı kimlik doğrulanmış oturuma bağımlı. Hesabı
ajanlara açtırmak beş ajanın beş ayrı özne üzerinde ölçmesine yol açar.

### Task 0: Damgalı test öğrencisi aç ve token al

**Files:**
- Create: `.a1_e2e_kimlik.json` (takipsiz)
- Modify: `.gitignore` (tek satır, `.a1_e2e_kimlik.json`)

- [ ] **Adım 1: `.gitignore`'a kimlik dosyasını ekle**

```bash
cd /c/Users/husey/kiro2
grep -qxF '.a1_e2e_kimlik.json' .gitignore || printf '\n# A1 uctan uca olcum test hesabi (S241)\n.a1_e2e_kimlik.json\n' >> .gitignore
grep -n 'a1_e2e_kimlik' .gitignore
```

Beklenen: `.a1_e2e_kimlik.json` satırı listelenir.

- [ ] **Adım 2: Kayıt öncesi taban sayımı ölç**

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 -t -A \
  -c "SELECT count(*) FROM users;"
```

Beklenen: `7` (bu plan yazılırken ölçülen değer). Farklıysa **not al ve devam et** —
taban kayar, ölçüm bozulmaz.

- [ ] **Adım 3: Yeni öğrenciyi kaydet, HAM gövdeyi yakala**

E-posta `a1e2e+s241@kiro2.test` sabittir (damga: `+s241` ve `.test` TLD'si bu
hesabı gerçek kullanıcılardan ayırır ve temizlemeyi tek sorguya indirir).

```bash
cd /c/Users/husey/kiro2
curl -s -w '\nHTTP_CODE=%{http_code}\n' -X POST http://localhost:8000/api/v1/auth/kayit \
  -H 'Content-Type: application/json' \
  -d '{"email":"a1e2e+s241@kiro2.test","ad_soyad":"A1 E2E Ogrenci","sifre":"A1altinYol!2026","rol":"ogrenci","birth_date":"2005-03-15"}' \
  | tee .a1_kayit_ham.txt
```

Beklenen: bilinmiyor — **ölçülecek olan budur.** HTTP kodu ve gövde birebir
kaydedilir. 409/duplicate dönerse hesap zaten var demektir, Adım 5'e geç.

`birth_date` 2005-03-15 kasıtlı: 2026'da 21 yaş → **reşit**. KVKK veli-onay
dalını (`veli_email` zorunluluğu) tetiklemez; o dal ayrı bir ayağın konusu.

- [ ] **Adım 4: DB tarafında ne oluştuğunu ölç**

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 -t -A -F'|' \
  -c "SELECT id, email, role, is_active, is_verified, organization_id FROM users WHERE email='a1e2e+s241@kiro2.test';"
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 -t -A \
  -c "SELECT count(*) FROM student_profiles sp JOIN users u ON u.id=sp.user_id WHERE u.email='a1e2e+s241@kiro2.test';"
```

Beklenen: bilinmiyor. `is_verified` değeri **L2'nin çekirdek ölçümüdür**.
İkinci sorgu `student_profiles` tablosu yoksa hata verir — o da bir bulgudur, not al.

- [ ] **Adım 5: Giriş yap, token al**

Parola alanının iki adı var; ikisi de denenir çünkü hangisinin bağlayıcı olduğu
şemadan anlaşılmıyor (ikisi de opsiyonel görünüyor).

```bash
cd /c/Users/husey/kiro2
for FIELD in sifre password; do
  echo "=== alan: $FIELD ==="
  curl -s -w '\nHTTP_CODE=%{http_code}\n' -X POST http://localhost:8000/api/v1/auth/giris \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"a1e2e+s241@kiro2.test\",\"$FIELD\":\"A1altinYol!2026\"}"
done | tee .a1_giris_ham.txt
```

Beklenen: en az birinde `200` + içinde `access_token`. İkisi de başarısızsa
**L1/L2 KIRIK** demektir; ham gövdeyi kaydet ve FAZ 1'i token'sız başlat
(ölçücüler "kimliksiz erişim" senaryosunu ölçer).

- [ ] **Adım 6: Kimliği dosyaya yaz**

```bash
cd /c/Users/husey/kiro2
python - <<'PY'
import json, re, pathlib
ham = pathlib.Path(".a1_giris_ham.txt").read_text(encoding="utf-8", errors="replace")
m = re.search(r'"access_token"\s*:\s*"([^"]+)"', ham)
kimlik = {
    "email": "a1e2e+s241@kiro2.test",
    "sifre": "A1altinYol!2026",
    "access_token": m.group(1) if m else None,
    "kaynak": ".a1_giris_ham.txt",
}
pathlib.Path(".a1_e2e_kimlik.json").write_text(
    json.dumps(kimlik, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("token bulundu:", bool(m))
PY
```

Beklenen: `token bulundu: True`. `False` ise Adım 5'in ham çıktısını oku —
token başka bir anahtar adı altında olabilir (`token`, `erisim_belirteci`).

- [ ] **Adım 7: Token'ın gerçekten çalıştığını doğrula (kontrol kolu)**

Token'ın varlığı çalıştığının kanıtı değildir.

```bash
cd /c/Users/husey/kiro2
TOKEN=$(python -c "import json;print(json.load(open('.a1_e2e_kimlik.json'))['access_token'] or '')")
curl -s -o /dev/null -w 'profil (tokenli)   -> %{http_code}\n' \
  -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/profil
curl -s -o /dev/null -w 'profil (tokensiz)  -> %{http_code}\n' \
  http://localhost:8000/api/v1/auth/profil
```

Beklenen: tokenli `200`, tokensiz `401`/`403`. **İkisi de aynı kodu dönerse
ölçüm aleti değil kimlik kapısı bozuktur** — bu başlı başına bir P0 bulgusudur.

---

## FAZ 1–3 — Workflow (5 ölçücü → 5 şüpheci → 1 eksiklik eleştirmeni)

### Task 1: Workflow'u koştur

**Files:**
- Create: `docs/audits/2026-08-20_a1_altin_yol_olcum.md` (workflow dönüşünden sonra ana oturum yazar)

- [ ] **Adım 1: `Workflow` aracını çağır**

`args` olarak FAZ 0'ın token'ı ve test e-postası geçilir. Script `meta.name`:
`a1-altin-yol-olcum`. Faz başlıkları: `Ölçüm`, `Çürütme`, `Eksiklik`.

Beş ölçücü — her biri **salt-okunur**, `Edit`/`Write` yasak, DB'ye yazma yasak:

| Ajan | Ayak | Zorunlu kanıt |
|---|---|---|
| `olc:L1-kayit` | Kayıt kod yolu: `/auth/kayit` hangi dosyada, `is_verified`'ı ne yapıyor, `student_profiles` satırını kim yazıyor | `dosya:satır` + ham HTTP |
| `olc:L2-dogrulama` | `users.is_verified`'ı set eden **her** kod yolu; `/auth/giris` doğrulanmamışı blokluyor mu; `magic-link/send`+`/verify` zinciri; e-posta gönderimi nerede düşüyor | `dosya:satır` + canlı HTTP + container log |
| `olc:L3-sinav` | `/api/v1/exams/*` neden mount değil; `/osym-exam/create` + `beta-practice` **40 TYT MAT** dönüyor mu; sorular kapıdan mı; **`correct_answer` istemciye sızıyor mu** | kesilmemiş ham JSON |
| `olc:L4-puanlama` | `save-answer` + `complete` + `subject-performance`; net formülü (D − Y/4); konu kırılımı doğru konulara mı yazıyor | bilinen cevap seti → beklenen vs dönen |
| `olc:L5-yuzey` | Playwright ile `/exam/start` → `/exam/:id` → `/exam/:id/results`; hangi backend ucu çağrılıyor (network); konsol hatası; sonuç ekranında net + kırılım görünüyor mu | ekran görüntüsü + konsol + network dökümü |

Her ölçücü şu şemayla döner:

```
{ ayak, yargi: "CALISIYOR"|"KIRIK"|"YOK", bulgular: [
    { baslik, siniflandirma: "ENGELLEYICI"|"KUSUR"|"GOZLEM",
      kanit_ham, kok_neden_ankraji, olcum_komutu } ] }
```

Beş şüpheci (`curut:<ayak>`) — her ölçücünün çıktısı **tamamlandığı anda**
pipeline ile kendi şüphecisine akar, bariyer yok. Şüphecinin görevi bulguyu
**doğrulamak değil çürütmektir**; verilen mercek:

> Bu bulgu gerçek bir kusur mu, yoksa ölçenin aletinin arızası mı? Bu oturumda
> aynı hata iki kez oldu: `primary_topic_id LIKE 'MAT%'` **0** döndü (kolon UUID,
> kod `topic_hierarchy.code`'da) ve `information_schema` matview'i görmedi
> (`pg_attribute` gerekiyordu). Ölçüm komutunu **kendin tekrar koş**. Kanıt ham
> çıktı değilse bulguyu **düşür**. Varsayılan yargı: ÇÜRÜTÜLDÜ.

Bir eksiklik eleştirmeni (`eksik:kapsam`) — beş ayağın birleşik çıktısını alır
(bu tek yerde bariyer meşru: soru "ne ölçülmedi", cevabı tüm sonuçları gerektirir):

> Hangi ayak, hata modu veya sözleşme hiç ölçülmedi? Özellikle: eşzamanlılık,
> yetkisiz erişim (başka öğrencinin oturumu — IDOR), boş/eksik cevap, süre aşımı,
> kapı dışı soru sızıntısı, Türkçe karakter bozulması, yeniden gönderim
> (idempotens). Bulduğun her boşluk sonraki turun işidir.

- [ ] **Adım 2: Workflow dönüşünü oku ve denetle**

Workflow bittiğinde dönen nesne ana oturumda **satır satır** okunur.
`curut` aşamasında `refuted: true` işaretlenen bulgular rapora **çürütülmüş**
olarak girer — silinmez (sessiz silme yok).

Beklenen: her ayak için tek bir yargı + en az bir ham kanıt bloğu.

- [ ] **Adım 3: Denetim raporunu yaz**

`docs/audits/2026-08-20_a1_altin_yol_olcum.md` şu bölümlerle:

1. **Methodology** — ölçüm komutları, N, canlı taban sayıları, kesme var mı,
   yeniden üretilebilir mi (audit-methodology.md zorunlu başlığı)
2. **Dört ayağın yargı tablosu** — ayak · yargı · kök neden ankrajı · kanıt satırı
3. **Doğrulanmış engelleyiciler** — ağırdan hafife, her biri `dosya:satır` ankrajlı
4. **Çürütülen iddialar** — hangi bulgu neden düştü (alet arızası mı, fantom mu)
5. **Ölçülmemiş kalanlar** — eksiklik eleştirmeninin listesi

- [ ] **Adım 4: Commit**

Commit mesajı **`-F` ile dosyadan** verilir (`L-s231-ters-tirnak`: bash çift
tırnağı içindeki ters tırnak komut çalıştırır ve mesaj gövdesini sessizce yutar).

```bash
cd /c/Users/husey/kiro2
cat > .commit_msg_tmp <<'EOF'
docs(audit): A1 Altin Yol dort ayagin uctan uca olcumu (S241)

<workflow ciktisindan turetilen ozet: her ayagin yargisi tek satir>
EOF
git add docs/audits/2026-08-20_a1_altin_yol_olcum.md .gitignore
git commit -F .commit_msg_tmp; RC=$?; rm -f .commit_msg_tmp
echo "EXIT=$RC"; git show --stat HEAD
```

Beklenen: `EXIT=0` **ve** `git show --stat HEAD` beklenen dosyaları listeler.
(`L-s232-boru-hattinda-exit-kodu`: exit kodu ayrı değişkene alınır; yeni hash
görmek her şeyin girdiği anlamına gelmez.)

---

## FAZ 4 — Düzeltme (ayrı plan)

FAZ 3 bitince doğrulanmış engelleyici listesi kullanıcıya sunulur, hangisinin
düzeltileceğine **kullanıcı karar verir**, ve o karardan sonra
`docs/superpowers/plans/2026-08-20-a1-altin-yol-duzeltme.md` yazılır.

Bu planın FAZ 4 adımlarını **şimdi yazmak yer tutucu üretmek olurdu** — hangi
ayağın kırık olduğu ölçülmeden düzeltme adımı yazılamaz. Tasarımın merkezî
kararı tam olarak budur.

FAZ 4'ün uyacağı kurallar (şimdiden bağlayıcı):

- Her düzeltme **önce kırmızı test** (`debugging-first.md` + `verification.md` TDD)
- Düzeltme başına **en fazla 3 dosya**
- Düzeltme `backend/api` · `backend/services` · `backend/algorithms` ·
  `frontend/src` altına düşmeli (E3 kullanıcı-görünür çıktı ölçütü)
- `correct_answer` ve `is_active` **hiçbir yolla değişmez**
- Kapı (`.claude/hooks` türetilmiş 24 dosyalık zorlayıcı liste) yeşil kalmalı:
  taban `250 passed / 1 skipped / 1 xfailed / 0 failed`

---

## Temizlik

Test hesabı oturum sonunda **silinmez** — sonraki turların aynı özne üzerinde
ölçmesi için tutulur. Silinmesi gerekirse tek sorgu yeter:

```sql
DELETE FROM users WHERE email = 'a1e2e+s241@kiro2.test';
```

`.a1_kayit_ham.txt` ve `.a1_giris_ham.txt` takipsiz kalır; `.a1_e2e_kimlik.json`
`.gitignore`'a Task 0 Adım 1'de eklenir. **Token commit'lenmez.**

---

## Öz-denetim (bu plan yazıldıktan sonra koşuldu)

**1. Spec kapsaması:** Tasarımın §3'teki beş ayağının beşi de FAZ 1'de bir
ölçücüye eşlendi (L1–L5). §5'teki sert kısıtlar FAZ 1 ajan talimatına ve FAZ 4
kurallarına yazıldı. §6'nın 1. şartı FAZ 1+2'nin çıktısı; 2. şartı FAZ 4'ün
konusu ve kapsam dışı bırakıldığı **açıkça** belirtildi — gizli boşluk yok.

**2. Yer tutucu taraması:** FAZ 4'ün adım kodu yok; bu bir yer tutucu değil,
**ölçüm bağımlılığı** ve gerekçesi yazılı. Task 0 ve Task 1'in her adımı
çalıştırılabilir komut içeriyor. "Beklenen: bilinmiyor" yazan üç adım var
(Adım 3, 4, 5) — bunlar ölçümün kendisi; beklenen değer uydurmak ölçümü
yanlış-doğrulamaya çevirirdi.

**3. Tip tutarlılığı:** Ölçücü dönüş şeması (`ayak`, `yargi`, `bulgular[]`)
şüpheci girdisi ve rapor bölüm 2–4 ile aynı alan adlarını kullanıyor.
`yargi` enum'u üç yerde de `CALISIYOR|KIRIK|YOK`.

**Denetimde düzeltilen:** ilk taslak giriş isteğinde yalnız `sifre` alanını
deniyordu; şema ikisini de opsiyonel gösterdiği için Adım 5 **iki alanı da**
denecek şekilde değiştirildi — tek alan denemek "giriş kırık" yanlış-pozitifi
üretebilirdi.
