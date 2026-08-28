# DISABLED_ROUTERS Envanteri — 7 Ağustos 2026 (S205)

## Neden bu envanter var

`backend/routers/loader.py` çalışma ağacında (commit'siz) **110 router'ı**
`DISABLED_ROUTERS`'a almış, gerekçe olarak *"Phase 2+ Over-engineering cleanup
(Reduces 1000+ unnecessary operations)"* yazılmış. HEAD'de `DISABLED_ROUTERS`
**boştur** — yani bu, sürüm kontrolüne hiç girmemiş bir değişiklik.

S204 denetiminin "frontend'in 236 çalışma-zamanı yolundan **167'si 404**" ve
"KVKK 23 ucu `DISABLED_ROUTERS`'ta (kod hazır, 1.764 satır)" bulgularının
kaynağı budur.

## Ölçüm

Her kapalı modül için `APIRouter(prefix=...)` çıkarıldı, ardından o prefix
`frontend/src/**/*.ts*` içinde arandı.

| Sonuç | Sayı |
|---|---|
| Toplam kapalı router | **110** |
| Frontend'in çağırdığı | **110** |
| Hiç çağrılmayan | **0** |
| Dosyası bulunamayan | **0** |

**"Over-engineering / kullanılmıyor" gerekçesi verilerle desteklenmiyor.**
Kapatılan router'ların hiçbiri referanssız değil.

### En çok çağrılan 12'si

| Router | Prefix | Frontend çağrısı |
|---|---|---|
| `api.study_rooms` / `api.study_rooms_stub` | `/api/v1/study-rooms` | 101 |
| `api.parent` | `/api/v1/parent` | 55 |
| `api.youtube_routes` | `/api/v1/youtube` | 53 |
| `api.adhd_support_api` | `/api/v1/adhd-support` | 45 |
| `api.diary_api` | `/api/v1/diary` | 40 |
| `api.duel_api` | `/api/v1/duel` | 40 |
| `api.manipulatives_api` | `/api/v1/manipulatives` | 33 |
| `api.student_dashboard` | `/api/v1/student-dashboard` | 31 |
| `api.eba_routes` | `/api/v1/eba` | 27 |
| `api.performance` | `/api/v1/performance` | 23 |
| `api.gamification_api` | `/api/v1/gamification` | 20 |
| `api.curator` | `/api/v1/curator` | 16 |

### Yasal / ticari açıdan kritik olanlar

| Router | Prefix | Çağrı | Not |
|---|---|---|---|
| `api.kvkk_consent_api` | `/api/v1/kvkk/consent` | 9 | KVKK açık rıza |
| `api.kvkk_privacy_api` | `/api/v1/kvkk/privacy` | 6 | KVKK Md.11 hakları |
| `api.kvkk_notice_api` | `/api/v1/kvkk/notice` | 3 | KVKK Md.10 aydınlatma |
| `api.org_billing_api` | `/api/v1/org/billing` | 3 | Faturalama |
| `api.audit_api` / `api.audit_logs_api` | `/api/v1/audit`, `/admin/audit-logs` | 6 / 4 | Denetim izi |
| `api.ferpa_coppa_compliance_api` | `/api/v1/compliance` | 6 | Çocuk verisi uyumu |

B2C öğrenci aboneliği hedefinde KVKK uçlarının kapalı olması **yasal risk**;
faturalama ucunun kapalı olması **ürünün satılamaması** demek.

### P5 bağımlılığı

`api.enhanced_chat` (`/api/v1/enhanced-chat`, 12 çağrı) de kapalı. Cursor
planı P5, Sokratik guardrail'i tam bu router'a bağlamayı öngörüyordu —
yani guardrail bağlansa bile kapalı bir yüzeye bağlanmış olacaktı.

## Ölçümün sınırı

Prefix dizesi frontend kaynağında sayıldı. Bu bir **vekil ölçüm**:

- Çağıran kodun kendisi ölü olabilir (mount edilmemiş sayfa, ölü bileşen).
- `/api/v1/batch` gibi kısa prefix'ler yorum satırında veya alt-dize olarak geçebilir.

Dolayısıyla "frontend çağırıyor" ≠ "özellik gerekli". Ama **ters yön kanıtlandı**:
110'un hiçbiri referanssız değil, yani "kullanılmıyor" gerekçesi ayakta durmuyor.

Bir sonraki adım için doğru ölçüm: her prefix'in çağrıldığı dosyanın **mount
edilmiş bir rotadan erişilebilir olup olmadığı** (App.tsx rota grafiği üzerinden).

## Ham veri

`docs/audits/_disabled_routers_inventory.json` — 110 kaydın tamamı
(kullanılan / ölü / dosyasız ayrımıyla).
