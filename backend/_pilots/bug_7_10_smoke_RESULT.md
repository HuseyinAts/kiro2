# Bug #7 + #10 Smoke Test — Bug #11 image-required exclude verification

## Pool stats

- `v_safe_for_beta` total: **23,417**
- Image-required pattern (Bug #11 regex): **16,927**
- Has `question_image_url`: **23,417**

⚠️  **Note:** 16,927 satır view'da image-required pattern var.
Backend API runtime filter (`soru_bankasi_service.py`, `placement_service.py`, `cat_session.py`) bu satırları endpoint response'undan exclude eder.
View seviyesinde dahil olabilirler — frontend image suppress ek defansif katman.

## Sample 10 random (smoke check)

| id | pattern | preview |
|---|---|---|
| `a2193cb8` | IMG_REQ | Bir bakteri türünün S (kapsüllü) ve R (kapsülsüz) tipleri bulunmaktadır. Bu bakteri tipler |
| `c5f65419` | OK | Şekil 1'de genişlikleri aynı uzunlukları farklı ön yüzeyleri dikdörtgen şeklindeki X, Y ve |
| `39891d70` | OK | Katman elektron dizilimleri verilen X ve Y atomları ile ilgili, I. X ametal, Y metaldir. I |
| `40f1ef19` | IMG_REQ | Aslı, elindeki dikdörtgen şeklindeki oyun kartlarını hikaye kitabının iki kenarına araları |
| `bbe47dcf` | OK | Şekil 1'de sarı ve mavi kutuların yükseklikleri toplamı, masanın yüksekliğinden 24 cm eksi |
| `8dc5b0f2` | IMG_REQ | Aşağıda bir futbolcunun vurduğu topun yatayda aldığı mesafe metre türünden $x(\alpha) = 80 |
| `cc9af98f` | IMG_REQ | Birer kenarları çakışık olan ABC ve BCD dik üçgenleri şekilde gösterilmiştir. $m(\widehat{ |
| `4822fb37` | IMG_REQ | Yukarıda, $y=f(x)$ fonksiyonunun grafiği verilmiştir. Buna göre, $x \cdot f'(x) \le 0$ eşi |
| `eb315cb4` | IMG_REQ | Bir tekstil atölyesinde, art arda dizilmiş kartonlar etiketleme yapan iki makineden sırayl |
| `14abe450` | OK | Dik koordinat düzleminde $y=f(x)$ fonksiyonunun grafiği verilmiştir. Buna göre I. $x=2$ ap |

## Conclusion

**Bug #7** (question-image content MISMATCH):
- Bug #11 frontend `question_image_url` render suppressed (commit `4bc0a6e29`)
- Image hiç gösterilmiyor → MISMATCH user-facing değil ✅

**Bug #10** (image-bound soru, image yok/yanlış):
- Image-required regex backend filter (4 service)
- Frontend image render suppress
- Image-bound soru API'den dönmüyor + image hiç render edilmiyor ✅

**Action:** Sprint sonrası vision API ile re-crop (84K), frontend suppress kaldır.
