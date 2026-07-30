# Oturum devri — 30-31 Tem 2026

Branch: feature/self-evolution-optimization · HEAD `ad1236cad` (push edildi)

## Canlıda ve doğrulandı

- **Ağ açığı KAPALI.** LAN'dan kimliksiz cevap anahtarı çekilebiliyordu
  (`192.168.8.2:9200` → 200 + `correct_answer`). ES+Redis 127.0.0.1'e bağlandı;
  ES 64.270/64.270 doküman ve redis 114/114 anahtar KORUNDU, kesinti yok.
  ES compose'a geri kondu (9 aydır yetimdi), volume `external: true`.
- **ES kapı takası.** alias `turkiye_sinav_platform` → `..._v20260731` (25.127).
  Servis edilen index'te `correct_answer` = **0** (önce 64.270).
  Yedek `..._yedek_20260731` (64.270) duruyor; geri alım tek `_aliases`.
  Gecelik senkron **04:00** beat'te ve ELLE KOŞTURULUP kanıtlandı:
  `{'eklenen': 0, 'silinen': 0, 'kapi': 25127}`.
- **CI YAML** (2 dosya 3,5 aydır ayrıştırılamıyordu), **admin DELETE 500→200/404**,
  **çakışmada 409**, **`/api/v1/me` 401** (önce 404). 3 imaj rebuild + deploy.

## Ölçümler (iddia değil)

- question_bank **187.835** / aktif 110.858 / kapı 25.127. CLAUDE.md'nin
  "77.336 in production" rakamı bir DOSYA SATIR SAYISI (d-dataset jsonl) —
  ama 2026-03-04 ingest'i (77.327 satır) ile provenance zinciri KAPALI.
- Persona: 15 alanın **6'sı 77/77 kullanıcıda null**, 2'si %95.
- Gerçek öğrenci trafiği **0** (117 oturumun hepsi tek test hesabından).

## Kalan — sadece operatör

1. **#441 SMTP** — `.env.mvp`'ye `SMTP_HOST` VE `SMTP_SERVER` (farklı dosyalar
   farklı adı okuyor). 6/6 değişken boş, şifre kurtarma işlevsiz.
2. **#436/#390/#270 GitHub** — harcama limiti, 20 Dependabot PR'ı, `gh` yok.
3. **#445** — 73 STUDENT hesabı triyajı.
4. **Karar:** CI fix master'a gidince merge kapısı 7 ölçülmüş kalemle ilk PR'ı
   bloklar. Feature dalında tetiklenmiyor, acele yok.

## Kalan — kod

- **#458** temizlik (149 çift-kodlanmış dizi + referanssız fix_validators.py)
- **#444 canlı duman testi** (öğretmen ekle/çıkar, gerçek hesapla)
- `soru_bankasi_service.py` lint borcu: E712 otomatik düzeltmesi PostgreSQL'de
  FARKLI SQL üretiyor (ölçüldü) → BİLEREK ertelendi, pyproject'te gerekçeli.

## Bu oturumun dersi

Yeşil test doğruluk kanıtı değil — 6 kez kanıtlandı: `.dockerignore` `scripts/`i
eliyordu (gecelik görev her gece çökerdi, testler host'ta yeşildi), ES analiz
zinciri kaybolmuştu (doküman sayısı tutuyordu), `# nosec` f-string'in içine
düşüp SQL'i bozmuştu, GF6w aylardır çakışma yolunu test ediyordu.
