# Beta Pattern Scanner — Counts

**Date:** 2026-05-19

| Category | Count | Reason |
|---|---|---|
| `image_gorsel` | 953 | ✅ APPLY Soru metni 'görsel' kelimesi içeriyor — image olmadan çözülemez |
| `image_kavram_harita` | 52 | ✅ APPLY Tarih/sosyal — kavram haritası referansı |
| `image_deney_duzene` | 113 | ✅ APPLY Fizik/kimya/biyoloji deney düzeneği şekli |
| `image_sekildeki_kap` | 22 | ✅ APPLY Kimya — şekildeki kaplar (deney şekli) |
| `image_cam_boru` | 57 | ✅ APPLY Kimya — cam boru ile bağlı deney |
| `image_numaraland_ozelli` | 23 | ✅ APPLY Numaralandırılmış özellik referansı (numbered list) |
| `image_paralelkenar` | 708 | ✅ APPLY Geometri paralelkenar + segment notation (|AB|, |AKL|) |
| `image_dikucgen` | 1,818 | ✅ APPLY Geometri üçgen + segment notation |
| `image_abcd_segment` | 3,937 | ✅ APPLY ABCD figür + segment notation |
| `broken_ends_III` | 0 | ✅ APPLY Roman numaralı liste yarıda kesik (sonu II/III/IV) |
| `broken_ends_dotdot` | 1 | ✅ APPLY Paragraf '...' ile bitiyor (truncation indicator) |
| `incomplete_roman_options_no_text` | 2,841 | ⏭ SKIP Opsiyonlarda Roman list var ama metinde işaret yok |
| `latex_options_frac` | 6,531 | ⏭ SKIP Opsiyonlarda \frac raw — Frontend MathText wrap eksik (Bug #1 v2) |
| `latex_options_sqrt` | 4,242 | ⏭ SKIP Opsiyonlarda \sqrt raw — Bug #1 v2 |
| `latex_options_alpha_beta` | 1,107 | ⏭ SKIP Opsiyonlarda Greek/math symbol raw — Bug #1 v2 |

**Total auto_judged_high:** 
83,906
