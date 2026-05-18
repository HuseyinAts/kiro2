# Beta Pattern Scanner — Counts

**Date:** 2026-05-19

| Category | Count | Reason |
|---|---|---|
| `image_sekil_numbered` | 0 | ✅ APPLY 'Şekil 1', 'şekil 2' — numbered figure ref |
| `image_sekildeki` | 0 | ✅ APPLY 'Şekildeki/şekildeki' — image ref (NOT 'bu şekilde') |
| `image_yukari_sek` | 0 | ✅ APPLY 'Yukarı(da/daki) ...şek' — image ref |
| `image_asagi_sek` | 0 | ✅ APPLY 'Aşağı(da/daki) ...şek' — image ref |
| `image_verilen_sek` | 0 | ✅ APPLY 'Verilen ...şek' — image ref |
| `image_sekilde_goster` | 0 | ✅ APPLY 'Şekilde gösterilmiş/bağlanmış/verilmiş/çizilmiş' |
| `image_gorsel` | 0 | ✅ APPLY Soru metni 'Görsel/görsel' kelimesi (image-bound) |
| `image_kavram_harita` | 0 | ✅ APPLY Tarih/sosyal — kavram haritası referansı |
| `image_deney_duzene` | 0 | ✅ APPLY Fizik/kimya/biyoloji deney düzeneği şekli |
| `image_yukarida` | 0 | ✅ APPLY 'Yukarıda...şekil/grafik/tablo' image-bound referansı |
| `image_asagida` | 0 | ✅ APPLY 'Aşağıda...şekil/grafik/tablo' image-bound referansı |
| `image_grafikte` | 0 | ✅ APPLY 'Grafikte/grafikte' referansı |
| `image_tabloda` | 0 | ✅ APPLY 'Tabloda/tabloda' referansı |
| `image_semada` | 0 | ✅ APPLY 'Şemada/şemada' referansı |
| `image_haritada` | 0 | ✅ APPLY 'Haritada/haritada' referansı |
| `image_sekildeki_kap` | 0 | ✅ APPLY Kimya — şekildeki kaplar |
| `image_cam_boru` | 0 | ✅ APPLY Kimya — cam boru deney |
| `image_numaraland_ozelli` | 0 | ✅ APPLY Numaralandırılmış özellik referansı |
| `image_paralelkenar` | 0 | ✅ APPLY Geometri paralelkenar + segment notation |
| `image_dikucgen` | 0 | ✅ APPLY Geometri üçgen + segment notation |
| `image_abcd_segment` | 0 | ✅ APPLY ABCD figür + segment notation |
| `image_verilenler` | 0 | ✅ APPLY 'Verilen graf/tablo/şema' referansı |
| `context_bu_opening` | 90 | ✅ APPLY 'Bu X...' opening — dangling context reference |
| `context_yukaridaki_acik` | 110 | ✅ APPLY 'Yukarıdaki/Yukarıda verilen...' opening (preceding context) |
| `context_asagidaki_acik` | 91 | ✅ APPLY 'Aşağıdaki/Aşağıda verilen...' opening (following context) |
| `broken_ends_III` | 0 | ✅ APPLY Roman numaralı liste yarıda kesik (sonu II/III/IV) |
| `broken_ends_dotdot` | 0 | ✅ APPLY Paragraf '...' ile bitiyor (truncation indicator) |
| `incomplete_roman_options_no_text` | 1,673 | ⏭ SKIP Opsiyonlarda Roman list var ama metinde işaret yok |
| `latex_options_frac` | 4,018 | ⏭ SKIP Opsiyonlarda \frac raw — Frontend MathText wrap eksik (Bug #1 v2) |
| `latex_options_sqrt` | 1,906 | ⏭ SKIP Opsiyonlarda \sqrt raw — Bug #1 v2 |
| `latex_options_alpha_beta` | 598 | ⏭ SKIP Opsiyonlarda Greek/math symbol raw — Bug #1 v2 |

**Total auto_judged_high:** 
54,967
