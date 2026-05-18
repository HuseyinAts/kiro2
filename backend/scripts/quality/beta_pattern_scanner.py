#!/usr/bin/env python3
"""
Beta01 flag pattern systematic DB scanner (Faz 7.3 retrospective + cleanup).

Beta01 18 flag'inde 5 pattern kategorisi tespit edildi (15 gerçek bildirim):
  1. image_bound (9): "görsel eksik" — image olmadan çözülemez
  2. wrong_answer (1): math doğrulanır yanlış
  3. incomplete_text (2): paragraf yarıda, numaralı işaret eksik
  4. broken_text (2): paragraf cut-off
  5. latex_render_bug (1): opsiyonlarda raw \frac

Bu script tüm `auto_judged_high` pool'unda BENZER pattern'leri tarar
ve confirmed olanları toplu reject eder.

PATTERN'LER (beta01 flag'lerinden türetildi):

  IMAGE_BOUND (Bug #11 v2 regex genişletmesi):
    - 'görsel' (genel)
    - 'kavram harita'
    - 'deney düzene'
    - 'şekildeki kap'
    - 'cam boru.*bağlı'
    - 'numaraland.* özelli'
    - 'paralelkenar' + numeric ref (|AK|, |AB|, ABCD)

  BROKEN_TEXT (sonu yarıda Roman):
    - 'III\\s*$' / 'III\\.\\s*$' (Roman III sonra hiçbir şey)
    - 'III\\s*[a-z]' (Roman + lowercase devam — broken)

  INCOMPLETE_TEXT (numaralı işaret eksik metin):
    - Numaralı liste opsiyonlar (A: I, B: II, ...) ama metinde I/II/III/IV/V yok

  LATEX_OPTIONS_RAW (Bug #1 v2):
    - option_a/b/c/d/e içinde \frac, \\sqrt, \\pi, \\sum, \\int, \alpha vb.
    - Frontend MathText wrap eksik (Bug #1 sadece question_text fix etti)

USAGE:
  python backend/scripts/quality/beta_pattern_scanner.py --scan
  python backend/scripts/quality/beta_pattern_scanner.py --sample CATEGORY
  python backend/scripts/quality/beta_pattern_scanner.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
AUDIT_DATE = datetime.now().strftime("%Y-%m-%d")

# Pattern definitions: (category, predicate, reason)
# Predicate: SQL fragment to be ANDed with auto_judged_high filter
PATTERNS = [
    # IMAGE_BOUND — v3 char class first letter (PostgreSQL C locale fix)
    # NOTE: 'şekil' tek başına FP riski yüksek (bu şekilde, küp şeklinde idiomatic).
    # Stricter sub-patterns kullan:
    (
        "image_sekil_numbered",
        "question_text ~ '[şŞ]ekil\\s*[0-9]'",
        "'Şekil 1', 'şekil 2' — numbered figure ref",
    ),
    (
        "image_sekildeki",
        "question_text ~ '[şŞ]ekildeki'",
        "'Şekildeki/şekildeki' — image ref (NOT 'bu şekilde')",
    ),
    (
        "image_yukari_sek",
        "question_text ~ '[yY]ukarı.{0,15}\\s[şŞ]ek'",
        "'Yukarı(da/daki) ...şek' — image ref",
    ),
    (
        "image_asagi_sek",
        "question_text ~ '[aA]şağı.{0,15}\\s[şŞ]ek'",
        "'Aşağı(da/daki) ...şek' — image ref",
    ),
    (
        "image_verilen_sek",
        "question_text ~ '[vV]erilen.{0,15}\\s[şŞ]ek'",
        "'Verilen ...şek' — image ref",
    ),
    (
        "image_sekilde_goster",
        "question_text ~ '[şŞ]ekilde\\s+(gösteril|bağlan|veril|çizil)'",
        "'Şekilde gösterilmiş/bağlanmış/verilmiş/çizilmiş'",
    ),
    (
        "image_gorsel",
        "question_text ~ '[gG]örsel'",
        "Soru metni 'Görsel/görsel' kelimesi (image-bound)",
    ),
    (
        "image_kavram_harita",
        "question_text ~ '[kK]avram harita'",
        "Tarih/sosyal — kavram haritası referansı",
    ),
    (
        "image_deney_duzene",
        "question_text ~ '[dD]eney düzene'",
        "Fizik/kimya/biyoloji deney düzeneği şekli",
    ),
    (
        "image_yukarida",
        "question_text ~ '[yY]ukarıda(ki|n)?\\s+(şekil|grafik|tablo|şema|görsel|verilen)'",
        "'Yukarıda...şekil/grafik/tablo' image-bound referansı",
    ),
    (
        "image_asagida",
        "question_text ~ '[aA]şağıda(ki|n)?\\s+(şekil|grafik|tablo|şema|görsel|verilen)'",
        "'Aşağıda...şekil/grafik/tablo' image-bound referansı",
    ),
    (
        "image_grafikte",
        "question_text ~ '[gG]rafikte'",
        "'Grafikte/grafikte' referansı",
    ),
    (
        "image_tabloda",
        "question_text ~ '[tT]abloda'",
        "'Tabloda/tabloda' referansı",
    ),
    (
        "image_semada",
        "question_text ~ '[şŞ]emada'",
        "'Şemada/şemada' referansı",
    ),
    (
        "image_haritada",
        "question_text ~ '[hH]aritada'",
        "'Haritada/haritada' referansı",
    ),
    (
        "image_sekildeki_kap",
        "question_text ~ '[şŞ]ekildeki kap'",
        "Kimya — şekildeki kaplar",
    ),
    (
        "image_cam_boru",
        "question_text ~ '[cC]am boru'",
        "Kimya — cam boru deney",
    ),
    (
        "image_numaraland_ozelli",
        "question_text ~ 'numaraland.* özelli'",
        "Numaralandırılmış özellik referansı",
    ),
    (
        "image_paralelkenar",
        "question_text ~ '[pP]aralelkenar' AND question_text ~ '\\|[A-Z]{1,3}\\|'",
        "Geometri paralelkenar + segment notation",
    ),
    (
        "image_dikucgen",
        "question_text ~ '([dD]ik üçgen|[eE]şkenar üçgen|[iI]kizkenar üçgen)' AND question_text ~ '\\|[A-Z]{1,3}\\|'",
        "Geometri üçgen + segment notation",
    ),
    (
        "image_abcd_segment",
        "question_text ~ 'ABCD' AND question_text ~ '\\|[A-Z]{1,3}\\|'",
        "ABCD figür + segment notation",
    ),
    (
        "image_verilenler",
        "question_text ~ '[vV]erilen(\\s+graf|\\s+tablo|\\s+şema)' OR question_text ~ '[vV]erilenler'",
        "'Verilen graf/tablo/şema' referansı",
    ),
    # CONTEXT_DEPENDENT — başlangıçta dangling reference
    # "Bu X..." opening — önceki bağlam yok ama "Bu X" diye referans yapıyor
    (
        "context_bu_opening",
        "question_text ~ '^Bu (fabrika|tablo|grafik|şek|olay|metin|durum|deney|kümeden|sayıdan|cebirsel|işlem|haritada|şemada|denklem|fonksiyon|paragraf|metinden|tablodan|grafikten|şekilden|şekildeki|tablodaki|grafikteki|verilen)'",
        "'Bu X...' opening — dangling context reference",
    ),
    (
        "context_yukaridaki_acik",
        "question_text ~ '^[YA]ukarıda(ki)? (ver|bul|söy|göst|açık|durum)'",
        "'Yukarıdaki/Yukarıda verilen...' opening (preceding context)",
    ),
    (
        "context_asagidaki_acik",
        "question_text ~ '^[AŞ]şağıda(ki)? (ver|bul|söy|göst|açık|durum)'",
        "'Aşağıdaki/Aşağıda verilen...' opening (following context)",
    ),
    # === V4 PATTERNS — 30-sample audit (19 May 2026, post-v3) ===
    (
        "v4_asagida_verilmis",
        "question_text ~ '[aA]şağıda(ki)?[^.]{0,80}(göster|veril|bilinmek|açıklan)'",
        "Aşağıda(ki) ...gösterilmiştir/verilmiştir — image-bound",
    ),
    (
        "v4_yukarida_gorulm",
        "question_text ~ '[yY]ukarıda(ki)?[^.]{0,80}(görül|göster|veril|açıklan)'",
        "Yukarıda(ki) ...görülmektedir/gösterilmiştir — image-bound",
    ),
    (
        "v4_duzgun_polygon",
        "question_text ~ '[A-Z]{4,7}\\s+düzgün\\s+(beşgen|altıgen|yedigen|sekizgen|dokuzgen|on\\s*iki\\s*gen|on\\s*ikigen)'",
        "ABCDE düzgün beşgen — geometri figür",
    ),
    (
        "v4_function_graph",
        "question_text ~ '[fF]onksiyonu(nun)?\\s+grafi[ğg]i'",
        "Fonksiyonun grafiği referansı",
    ),
    (
        "v4_coord_duzlem",
        "question_text ~ '[dD]ik koordinat düzlemi'",
        "Dik koordinat düzleminde figür ref",
    ),
    (
        "v4_dangling_yukaridaki_x",
        "question_text ~ '[yY]ukarıdaki (bileşik|element|grafik|reaksiyon|denklem|tablo|verilen|veril|şek|şekil|şema|harita|atom|molek|reaks|deney)'",
        "Yukarıdaki X — dangling reference",
    ),
    (
        "v4_dangling_bu_x",
        "question_text ~ 'Buna göre, bu (element|bileşik|atom|molek|sayı|grafik|tablo|şek|durum|deney|reaks|fonksiyon|polinom|paralelkenar|üçgen|dikdörtgen|kare)'",
        "'Buna göre, bu X' — context dangling",
    ),
    (
        "v4_kare_bolmeler",
        "question_text ~ '[eE]şit\\s+kare\\s+bölme'",
        "Eşit kare bölmelere ayrılmış — grid figure",
    ),
    (
        "v4_bulmaca",
        "question_text ~ '[bB]ulmaca'",
        "Bulmaca tarzı — figür gerekir",
    ),
    (
        "v4_atomic_diagram",
        "question_text ~ '[kK]atman elektron\\s+dizili'",
        "Atomic structure diagram (Lewis)",
    ),
    (
        "v4_kose_sayi",
        "question_text ~ 'köşelerin[de]+\\s+sayı(lar)?\\s+yazılı'",
        "Köşelere sayı yazılı geometri figür",
    ),
    (
        "v4_uzunluk_birim",
        "question_text ~ 'uzunluk(lar)?ı\\s+birim cinsinden\\s+(veril|göster|bilinm)'",
        "Birim uzunluklar verilmiş — figür",
    ),
    (
        "v4_eksen_grafigi",
        "question_text ~ '(yatay|düşey)\\s+eksen' OR question_text ~ '(x-ekseni|y-ekseni)'",
        "Eksen referansı — grafik figür",
    ),
    (
        "v4_sigacin_levha",
        "question_text ~ '[sS]ığacın\\s+levha'",
        "Sığaç levhaları figür (fizik)",
    ),
    (
        "v4_isin_yolu",
        "question_text ~ '(ışık|ışın)\\s+ışın(ları)?ının\\s+(izlediği|yol)'",
        "Işık ışını yolu — optik figür",
    ),
    (
        "v4_atom_xY_dizilim",
        "question_text ~ '[A-Z],?\\s+[A-Z]\\s+(atomları|elementleri)' AND question_text ~ '(dizilim|elektron|periyot|grup)'",
        "X, Y atomları + dizilim/elektron — atomic diagram",
    ),
    (
        "v4_grafik_veril",
        "question_text ~ '[gG]rafi[ğg]i\\s+(veril|göster|bilinm)'",
        "Grafiği verilmiştir/gösterilmiştir",
    ),
    (
        "v4_parabol_dogru",
        "question_text ~ '[pP]arabol(ü|ünün|ün)?\\s+(verilm|göster|grafik)'",
        "Parabol/parabolü verilmiş — grafik",
    ),
    # === V5 — second iteration audit (post-v4) ===
    (
        "v5_asagidaki_gibi_action",
        "question_text ~ '[aA]şağıdaki gibi\\s+(diz|göster|kurul|yerleştir|katlama|biçimde|şek|veril)'",
        "Aşağıdaki gibi dizilmiş/kurulmuş/katlama — figür",
    ),
    (
        "v5_yukaridaki_gibi_action",
        "question_text ~ '[yY]ukarıdaki gibi\\s+(diz|göster|kurul|yerleştir|katlama|biçimde|şek)'",
        "Yukarıdaki gibi — figür",
    ),
    (
        "v5_sayi_dogrusu",
        "question_text ~ '[sS]ayı\\s+doğru(sun|sunda|sunun|su\\b)'",
        "Sayı doğrusu — figür gerekir",
    ),
    (
        "v5_periyodik_cetvel",
        "question_text ~ '[pP]eriyodik\\s+(cetvel|tablo)' OR question_text ~ '[cC]etvelde\\s+yerleri'",
        "Periyodik cetvelde yerleri verilen — figür",
    ),
    (
        "v5_devre_fizik",
        "question_text ~ '(devre|devresi)' AND question_text ~ '(lamba|üreteç|direnç|anahtar|pil)'",
        "Devre + lamba/üreteç/direnç — devre figürü",
    ),
    (
        "v5_kac_numara_gosterilmis",
        "question_text ~ 'kaç\\s+numara(\\s+ile)?\\s+(gösteril|veril)'",
        "Kaç numara ile gösterilmiştir — figür",
    ),
    (
        "v5_yay_atom_cisim",
        "question_text ~ '\\b[A-Z]\\s+ve\\s+[A-Z]\\s+(yayları|elektroskopları|cisimleri|kapları|merceğ|merceği|mercekleri|lamba|noktası|noktasında)\\b'",
        "K ve L yayları/cisimleri/elektroskopları — figür ref",
    ),
    (
        "v5_aci_geometri",
        "question_text ~ 'm\\(\\\\widehat\\{' OR question_text ~ '\\\\widehat'",
        "m(âçı) notation — geometri figür",
    ),
    (
        "v5_ornuntu_dizi",
        "question_text ~ '(örüntü|desen)\\s+(oluştur|yap|gibi|kuruluş)'",
        "Örüntü/desen oluşturma — figür",
    ),
    (
        "v5_I_II_nolu",
        "question_text ~ '(I\\.|II\\.|III\\.|IV\\.)\\s+(nolu|kapta|fırın|bölge|kapt|durum|alan)'",
        "I. nolu / II. kapta — numbered figure",
    ),
    (
        "v5_kuvvet_uygulanan",
        "question_text ~ '[kK]uvvet(ler)?\\s+uygulan(arak)?' AND question_text ~ '(yörünge|hız|hareket|sabit)'",
        "Kuvvetler uygulanan + yörünge/hız — fizik figür",
    ),
    (
        "v5_zipline_ip_iki_direk",
        "question_text ~ '[iı]ki\\s+direk\\s+arası' OR question_text ~ '[zZ]ipline'",
        "İki direk / zipline — figür",
    ),
    (
        "v5_iki_daire_cember",
        "question_text ~ '[iı]ki\\s+(daire|çember|cember)' AND question_text ~ '(yarıçap|merkez)'",
        "İki daire/çember + yarıçap/merkez — figür",
    ),
    (
        "v5_serbest_uc",
        "question_text ~ '[sS]erbest\\s+(olan\\s+)?uç' AND question_text ~ '(yay|ip|halat)'",
        "Serbest uç + yay/ip — fizik figür",
    ),
    (
        "v5_x_y_z_atom",
        "question_text ~ '\\b[XYZ]\\s+(atomu|elementi|atomları|elementleri|maddesi|katsı|gazı)' AND question_text ~ '(periyot|grup|elektron|dizilim|katman)'",
        "X/Y/Z atom + periyot/grup/dizilim — atomic diagram",
    ),
    (
        "v5_K_L_M_lamba_devre",
        "question_text ~ '\\b[KLM]\\s+ve\\s+[KLM]\\b' AND question_text ~ '(devre|lamba|üreteç|akım|gerilim|şiddet)'",
        "K, L, M lambaları/üreteçleri — devre figür",
    ),
    (
        "v5_kapta_bulunan",
        "question_text ~ '\\b[III]+\\.\\s+kapta' OR question_text ~ '\\b(I|II|III|IV)\\s*nolu\\s+(kap|kapta)' OR question_text ~ '(I|II)\\.?\\s+kabın'",
        "I. kapta / II. nolu kap — numbered containers (figür)",
    ),
    (
        "v5_dort_renkli_havuc",
        "question_text ~ '(havuç|marul|beyaz turp|mor lahana|sebze|meyve)' AND question_text ~ '(I\\.|II\\.|III\\.)\\s+kap'",
        "Sebze/meyve + I/II. kap — figür",
    ),
    (
        "v5_kent_kentine_giderken",
        "question_text ~ '[A-Z]\\s+kent(ind|ine|inden)'",
        "A kentinden B kentine — harita figür",
    ),
    (
        "v5_bilgisayar_ekran",
        "question_text ~ '[bB]ilgisayar(ın)?\\s+ekran' AND question_text ~ '(görüntü|yazılm|veril|göster)'",
        "Bilgisayar ekranı görüntüsü — figür",
    ),
    (
        "v5_hucre_zarı_fosfolipit",
        "question_text ~ '(hücre zarı|fosfolipit|membran|fosfolipid)' AND question_text ~ '(numara|gösterilmiş|işaretlenmiş)'",
        "Hücre zarı + numara ile gösterilm — diyagram",
    ),
    # === V6 — third iteration audit (post-v5) ===
    (
        "v6_sekil_dash",
        "question_text ~ '[şŞ]ekil-(I|II|III|IV|V|1|2|3|4|5)'",
        "Şekil-I/Şekil-1 dash notation — image-bound",
    ),
    (
        "v6_dusey_kesit",
        "question_text ~ '[dD]üşey\\s+kesit(i|inde)?\\s+(veril|göster|bulun)'",
        "Düşey kesiti verilen — figür",
    ),
    (
        "v6_gunes_sistemi",
        "question_text ~ '[gG]üneş\\s+[sS]istem' AND question_text ~ '(görülmekte|göster|veril|bulunan|şekil)'",
        "Güneş Sistemi görsel referans",
    ),
    (
        "v6_yukaridaki_kaplar",
        "question_text ~ '[yY]ukarıdaki\\s+(kaplar|sıvılar|denekler|şişeler|tüpler|tabloda|deneylere|gruplar)'",
        "Yukarıdaki kaplar/sıvılar — figür",
    ),
    (
        "v6_n_nolu_kut",
        "question_text ~ '(I|II|III|IV|V|1|2|3|4|5)[\\s]+nolu\\s+(kut|kap|şişe|tüp|deney|işlem|bahçe|fırın|levha)'",
        "I/II nolu kutu/kap/şişe — numbered figure",
    ),
    (
        "v6_egik_duzlem_K",
        "question_text ~ '(eğik düzlem|eğik düzlemde|eğik düzlemden|eğik düzlemin)'",
        "Eğik düzlem — fizik figür",
    ),
    (
        "v6_KL_LM_MN_segment",
        "question_text ~ '\\bK(L|M|N)\\b' AND question_text ~ '(nokta|noktası|noktasında|noktasından)'",
        "KL/LM segments + nokta — figür",
    ),
    (
        "v6_abcde_dots",
        "question_text ~ '[A-Z]{3,5}\\.{2,}\\s+n\\s+kenar|[A-Z]{3,5}\\.{2,}\\s+düzgün'",
        "ABCDE... n kenarlı — polygon figür",
    ),
    (
        "v6_O_merkez",
        "question_text ~ '\\bO\\s+merkez(li|i|inde)' AND question_text ~ '(daire|çember|cember|yarıçap)'",
        "O merkezli daire/çember — figür",
    ),
    (
        "v6_sayi_duzenegi",
        "question_text ~ '[sS]ayı\\s+düzeneğ'",
        "Sayı düzeneği — figür",
    ),
    (
        "v6_sekilde_belirtil",
        "question_text ~ '[şŞ]ekilde\\s+(belirtil|işaretlen|verilen)'",
        "Şekilde belirtilen yön/işaret — figür",
    ),
    (
        "v6_birim_kareler",
        "question_text ~ '[bB]irim\\s+kare(ler)?(den)?\\s+(oluş|olan|şek|içeren)'",
        "Birim karelerden oluşan — grid figure",
    ),
    (
        "v6_kepler_kepler_yasalari",
        "question_text ~ '(Kepler|gezegen|yörünge|cisim|kütle merkez|moment).*(şek|göster|veril|kut|bulunmakta)'",
        "Astronomi/fizik nesne + figür ref",
    ),
    (
        "v6_kapsam_sapma_grafigi",
        "question_text ~ '(yörünge|salınım|titreşim|sapma|esneme|sıkış|grafik|grafiği|histogram|pasta|sütun)' AND question_text ~ '(şek|göster|veril|kut|grafiği|grafik)'",
        "Yörünge/grafik ref — figür",
    ),
    (
        "v6_evre_ait_yukaridaki",
        "question_text ~ '(evre|aşama|süreç|safha)' AND question_text ~ '[yY]ukarıdaki'",
        "Evreler/aşamalar yukarıdaki — figür",
    ),
    (
        "v6_akim_devre",
        "question_text ~ '(akım\\s+geçen|akım\\s+akan|gerilim\\s+uygulanan|paralel\\s+bağlı|seri\\s+bağlı|kondansatör|sığa|EMK|elektromotor)'",
        "Devre akım/gerilim — devre figür",
    ),
    (
        "v6_kuvvet_F1_F2",
        "question_text ~ 'F_?1.*F_?2'",
        "F_1, F_2 kuvvetleri — figür",
    ),
    (
        "v6_ucgen_geometri_acidol",
        "question_text ~ '(m\\(â|m\\([A-ZÂ]|^[A-Z]{3,5}\\s+üçgen)' OR question_text ~ 'açıortay'",
        "Üçgen geometri + açı — figür",
    ),
    (
        "v6_omurga_skolyoz_rontgen",
        "question_text ~ '(röntgen|skolyoz|omurga|EKG|MR|tomografi|ultrason)'",
        "Tıbbi görüntü ref",
    ),
    (
        "v6_yatay_dusey_eksen",
        "question_text ~ '(yatay\\s+düzlem|düşey\\s+düzlem|yatay\\s+eksen|düşey\\s+eksen)' AND question_text ~ '(hareket|kuvvet|yörüng|hız|cisim)'",
        "Yatay/düşey düzlem fizik — figür",
    ),
    # === V7 — fourth iteration audit (post-v6, 48% temiz) ===
    (
        "v7_sekil_dash_loose",
        "question_text ~ '[şŞ]ekil\\s*[-–]\\s*(I|II|III|IV|V|VI|1|2|3|4|5|6)'",
        "Şekil - I/II (dash with optional spaces)",
    ),
    (
        "v7_x_es_karelerden",
        "question_text ~ '\\d+\\s+eş\\s+kare(ler)?(den)?\\s+(oluş|olan|şek|içeren)'",
        "N eş kareden oluşan — grid figure",
    ),
    (
        "v7_sekilde_fonk",
        "question_text ~ '[şŞ]ekilde\\s+(f|g|h|y)\\([xyz]\\)'",
        "Şekilde f(x) — graphed function",
    ),
    (
        "v7_yukaridaki_kalem_dizi",
        "question_text ~ '[yY]ukarıdaki\\s+(kalem|kutu|şek|durum|kart|dosya|tabela|sırad)'",
        "Yukarıdaki kalem/kutu/şekil — figür",
    ),
    (
        "v7_durumdaki_kab",
        "question_text ~ '\\d+\\.\\s+durumda(ki)?\\s+(kab|kut|şek|şişe|fır)'",
        "1./2. durumdaki kap/kutu — figür",
    ),
    (
        "v7_numaralandirilmis_kut",
        "question_text ~ '(numaralandırılm|sırala)\\w*\\s+(kut|kap|şişe|tüp|şek|nesne)'",
        "Numaralandırılmış kutular/kaplar — figür",
    ),
    (
        "v7_iki_tekerlek_bisiklet",
        "question_text ~ '(iki|2)\\s+teker(lek)?(li|leği)' OR question_text ~ 'bisiklet.*(göster|veril|şek)'",
        "İki tekerlekli bisiklet — figür",
    ),
    (
        "v7_telefon_tablet_ekran",
        "question_text ~ '(tablet|telefon|akıllı saat|tableti(nin)?|telefonu(nun)?)\\s+ekran'",
        "Tablet/telefon ekranı — figür",
    ),
    (
        "v7_isik_kaynagi_levha",
        "question_text ~ '([kK] ve [L]|[L] ve [M])\\s+(levha|aynalar|merkez|pencere)'",
        "K ve L levhaları/aynaları — figür",
    ),
    (
        "v7_renkli_boncuk_cubuk",
        "question_text ~ '(sarı|mavi|kırmızı|yeşil|mor|turuncu)\\s+(boncuk|çubuk|halka|kutu|disk|bilye)'",
        "Renkli boncuk/çubuk/disk — figür",
    ),
    (
        "v7_dort_eskenar",
        "question_text ~ '[A-Z]{3,5}\\s+(eşkenar|dik|ikizkenar)\\s+üçgen'",
        "ABC eşkenar üçgen — figür",
    ),
    (
        "v7_piramit_koni_silindir",
        "question_text ~ '(kare dik piramit|piramit\\s+biçim|piramit\\s+şek|koni|silindir|prizma|küre|küp)' AND question_text ~ '(göster|veril|şek)'",
        "Piramit/koni/silindir + göster — figür",
    ),
    (
        "v7_uygulamalar_satira",
        "question_text ~ '(uygulamaları|uygulama\\s+sayı|simge|ikon)' AND question_text ~ '(sıra|satır|sıradaki|aşağıdaki gibi)'",
        "Tablet uygulamaları sırasız — figür",
    ),
    (
        "v7_asagidaki_duzenek",
        "question_text ~ '[aA]şağıdaki\\s+(düzenek|deney|şek|şişe|kapt|şartlar)'",
        "Aşağıdaki düzenek/deney/şişe — figür",
    ),
    (
        "v7_asagidaki_cubuklar",
        "question_text ~ '[aA]şağıdaki\\s+(çubuklar|tepkimeler|kart|denklem|denkleminin)'",
        "Aşağıdaki çubuklar/tepkimeler — figür",
    ),
    (
        "v7_ucgen_acisal_aci",
        "question_text ~ '[A-Z]{3,4}\\s+(üçgen|dörtgen|beşgen|altıgen|kare|dikdörtgen|paralel|yamuk)' AND question_text ~ '(noktası|merkez|köş|kenar|açı)'",
        "ABC üçgen/dörtgen + noktası/köşesi — figür",
    ),
    (
        "v7_dik_koord_sistem_figur",
        "question_text ~ '[dD]ik\\s+koordinat\\s+sistem' AND question_text ~ '(verilen|göster|çizil|kare|daire|nokta|grafik)'",
        "Dik koordinat sistemi + figür ref",
    ),
    (
        "v7_K_L_M_N_noktalar",
        "question_text ~ '\\b[KLMN]\\b\\s+nokta' AND question_text ~ '\\b[KLMN]\\b\\s+nokta'",
        "K, L, M, N noktaları — figür ref",
    ),
    (
        "v7_yatay_yol_F_kuvvet",
        "question_text ~ 'yatay(\\s+ve\\s+sürtünmeli)?\\s+(yol|düzlem|zemin)' AND question_text ~ '(kuvvet|F\\s|sürtünme|hız|cisim)'",
        "Yatay yol + kuvvet — fizik figür",
    ),
    (
        "v7_F1_F2_F3",
        "question_text ~ 'F_1.*F_2' OR question_text ~ 'F_?1.*F_?2.*F_?3' OR question_text ~ '\\$F_1\\$'",
        "F_1, F_2, F_3 kuvvetler — figür",
    ),
    (
        "v7_strob_periyodik_dalga",
        "question_text ~ '(stroboskop|stroboskobun|dalga\\s+boyu|dalganın\\s+tep|dalga\\s+kayna)'",
        "Stroboskop / dalga — fizik figür",
    ),
    (
        "v7_kesit_verilen_eks",
        "question_text ~ '(kesit|kesiti)\\s+(veril|göster|şek)'",
        "Kesit verilen/gösterilen — figür",
    ),
    (
        "v7_aci_widehat_nolu_dummy",
        "question_text ~ '(m\\(\\\\widehat|m\\(â|açıortay|^ACI|açı.*derece)' OR question_text ~ '(BAC|ABC|ACD|BCD|ABE|ACE|BCE)\\s*(=|açı|derece)'",
        "DUMMY duplicate skip — replaced by above v7_aci_widehat_nolu",
    ),
    # === V8 — fifth iteration audit (post-v7) ===
    (
        "v8_sekil_no_dash",
        "question_text ~ '[şŞ]ekil\\s+(I|II|III|IV|V|VI|VII)' OR question_text ~ '[şŞ]ekil\\s+[1-6][^0-9]'",
        "Şekil I/II/III without dash",
    ),
    (
        "v8_birimkare_bolunmus",
        "question_text ~ 'birimkare(ler)?e?\\s+bölünmüş'",
        "Birimkarelere bölünmüş — grid figure",
    ),
    (
        "v8_renkli_nesne",
        "question_text ~ '(sarı|mavi|kırmızı|yeşil|turuncu|mor|pembe|gri|siyah|beyaz)\\s+(küp|silindir|prizma|levha|disk|tüp|çubuk|cisim|nokta|alan|bölge|halka|nesne|top|şerit|çizgi|kutu)'",
        "Renkli nesne (küp/levha/silindir) — figür",
    ),
    (
        "v8_atmalari_yay",
        "question_text ~ '\\b[A-Z]\\s+ve\\s+[A-Z]\\s+atma' OR question_text ~ 'yaydaki\\s+[A-Z]'",
        "K ve L atmaları yayda — fizik figür",
    ),
    (
        "v8_yukaridaki_general",
        "question_text ~ '[yY]ukarıdaki\\s+(görüntü|tablo|sıra|durum|çember|otobüs|borular|sıralama|nesneler|cisimler|kareler|koltuk|atma|atmaları|cisim|cisimleri|şişe|tüp|levha)'",
        "Yukarıdaki görüntü/tablo/çember — figür ref",
    ),
    (
        "v8_n_cubukta",
        "question_text ~ '(I|II|III|IV|V|1|2|3|4)\\.\\s+çubukta'",
        "I. çubukta / II. çubukta — figür",
    ),
    (
        "v8_asagidaki_kosullar",
        "question_text ~ '[aA]şağıdaki\\s+koşullara\\s+göre'",
        "Aşağıdaki koşullara göre — figür (oturma planı vb.)",
    ),
    (
        "v8_ust_yan_yan_konulan",
        "question_text ~ '(üst üste|yan yana)\\s+konulan\\s+(küp|kart|kut|silindir|kâğ|şişe|levha|cisim)'",
        "Üst üste konulan küp/kart — figür",
    ),
    (
        "v8_numaralandirilmis_koltuk_sira",
        "question_text ~ '(numaraland|sırala)\\w*\\s+(koltuk|sıra|kart|kut|nesne|cisim|şişe|tepkime|element|deney)'",
        "Numaralandırılmış koltuk/sıra — figür",
    ),
    (
        "v8_yatay_sukrosel_arac",
        "question_text ~ '(serçe|güvercin|martı|karga|kuş|tavşan|cisim)\\s+.*(sabit\\s+sürat|yatay|düşey)'",
        "Kuş/hayvan cisim hareket — fizik figür",
    ),
    (
        "v8_iki_atma_K_L",
        "question_text ~ '(yan\\s+yana|paralel|art\\s+arda)\\s+(yaylar|kartonlar|dosyalar|atma|cisimler|kâğıtlar)'",
        "Paralel yaylar/kartonlar/cisimler — figür",
    ),
    (
        "v8_sicak_soguk_borular",
        "question_text ~ '(sıcak\\s+su|soğuk\\s+su)\\s+boru' OR question_text ~ '(musluk|vana|açıkta|kapalı)\\s+(çıkış|akış|akan)'",
        "Sıcak/soğuk su borusu — figür",
    ),
    (
        "v8_aynı_doğrultuda",
        "question_text ~ '(aynı\\s+doğrultu(d|n)|paralel\\s+ola|yan\\s+yana\\s+koy)'",
        "Aynı doğrultuda — figür",
    ),
    (
        "v8_orta_nokta_segm",
        "question_text ~ '(orta noktası|orta-noktası|orta nokta)\\s+(olan|olmak\\s+üzere)' AND question_text ~ '(duvar|kenar|kenarın|segmenti|nokta|açı)'",
        "Orta nokta + duvar/kenar — figür",
    ),
    (
        "broken_ends_III",
        "question_text ~ ' III\\s*$' OR question_text ~ ' II\\s*$' OR question_text ~ ' IV\\s*$'",
        "Roman numaralı liste yarıda kesik (sonu II/III/IV)",
    ),
    (
        "broken_ends_dotdot",
        "question_text ~ '\\.\\s*\\.\\.\\.\\s*$'",
        "Paragraf '...' ile bitiyor (truncation indicator)",
    ),
    # INCOMPLETE_TEXT — options reference I/II/III but no Roman in text
    # NOTE: complex predicate, false positive risk → skip aggressive apply
    (
        "incomplete_roman_options_no_text",
        (
            "(option_a ~* '(yalnız|I, II|I ve|II ve|III ve)' "
            "OR option_b ~* '(yalnız|I, II|I ve|II ve|III ve)') "
            "AND question_text !~ 'I\\.\\s' AND question_text !~ 'II\\.\\s'"
        ),
        "Opsiyonlarda Roman list var ama metinde işaret yok",
    ),
    # LATEX_OPTIONS_RAW — Bug #1 v2 (options için MathText wrap eksik)
    (
        "latex_options_frac",
        (
            "(option_a ~ '\\\\frac' OR option_b ~ '\\\\frac' OR option_c ~ '\\\\frac' "
            "OR option_d ~ '\\\\frac' OR option_e ~ '\\\\frac')"
        ),
        "Opsiyonlarda \\frac raw — Frontend MathText wrap eksik (Bug #1 v2)",
    ),
    (
        "latex_options_sqrt",
        (
            "(option_a ~ '\\\\sqrt' OR option_b ~ '\\\\sqrt' OR option_c ~ '\\\\sqrt' "
            "OR option_d ~ '\\\\sqrt' OR option_e ~ '\\\\sqrt')"
        ),
        "Opsiyonlarda \\sqrt raw — Bug #1 v2",
    ),
    (
        "latex_options_alpha_beta",
        (
            "(option_a ~ '\\\\(alpha|beta|gamma|delta|theta|pi|sum|int)' "
            "OR option_b ~ '\\\\(alpha|beta|gamma|delta|theta|pi|sum|int)' "
            "OR option_c ~ '\\\\(alpha|beta|gamma|delta|theta|pi|sum|int)' "
            "OR option_d ~ '\\\\(alpha|beta|gamma|delta|theta|pi|sum|int)' "
            "OR option_e ~ '\\\\(alpha|beta|gamma|delta|theta|pi|sum|int)')"
        ),
        "Opsiyonlarda Greek/math symbol raw — Bug #1 v2",
    ),
]

# Reject sınırı: which categories to apply (HIGH confidence)
APPLY_CATEGORIES = {
    "image_sekil_numbered",
    "image_sekildeki",
    "image_yukari_sek",
    "image_asagi_sek",
    "image_verilen_sek",
    "image_sekilde_goster",
    "image_gorsel",
    "image_kavram_harita",
    "image_deney_duzene",
    "image_yukarida",
    "image_asagida",
    "image_grafikte",
    "image_tabloda",
    "image_semada",
    "image_haritada",
    "image_sekildeki_kap",
    "image_cam_boru",
    "image_numaraland_ozelli",
    "image_paralelkenar",
    "image_dikucgen",
    "image_abcd_segment",
    "image_verilenler",
    "context_bu_opening",
    "context_yukaridaki_acik",
    "context_asagidaki_acik",
    "v4_asagida_verilmis",
    "v4_yukarida_gorulm",
    "v4_duzgun_polygon",
    "v4_function_graph",
    "v4_coord_duzlem",
    "v4_dangling_yukaridaki_x",
    "v4_dangling_bu_x",
    "v4_kare_bolmeler",
    "v4_bulmaca",
    "v4_atomic_diagram",
    "v4_kose_sayi",
    "v4_uzunluk_birim",
    "v4_eksen_grafigi",
    "v4_sigacin_levha",
    "v4_isin_yolu",
    "v4_atom_xY_dizilim",
    "v4_grafik_veril",
    "v4_parabol_dogru",
    "v5_asagidaki_gibi_action",
    "v5_yukaridaki_gibi_action",
    "v5_sayi_dogrusu",
    "v5_periyodik_cetvel",
    "v5_devre_fizik",
    "v5_kac_numara_gosterilmis",
    "v5_yay_atom_cisim",
    "v5_aci_geometri",
    "v5_ornuntu_dizi",
    "v5_I_II_nolu",
    "v5_kuvvet_uygulanan",
    "v5_zipline_ip_iki_direk",
    "v5_iki_daire_cember",
    "v5_serbest_uc",
    "v5_x_y_z_atom",
    "v5_K_L_M_lamba_devre",
    "v5_kapta_bulunan",
    "v5_dort_renkli_havuc",
    "v5_kent_kentine_giderken",
    "v5_bilgisayar_ekran",
    "v5_hucre_zarı_fosfolipit",
    "v6_sekil_dash",
    "v6_dusey_kesit",
    "v6_gunes_sistemi",
    "v6_yukaridaki_kaplar",
    "v6_n_nolu_kut",
    "v6_egik_duzlem_K",
    "v6_KL_LM_MN_segment",
    "v6_abcde_dots",
    "v6_O_merkez",
    "v6_sayi_duzenegi",
    "v6_sekilde_belirtil",
    "v6_birim_kareler",
    "v6_kepler_kepler_yasalari",
    "v6_kapsam_sapma_grafigi",
    "v6_evre_ait_yukaridaki",
    "v6_akim_devre",
    "v6_kuvvet_F1_F2",
    "v6_ucgen_geometri_acidol",
    "v6_omurga_skolyoz_rontgen",
    "v6_yatay_dusey_eksen",
    "v7_sekil_dash_loose",
    "v7_x_es_karelerden",
    "v7_sekilde_fonk",
    "v7_yukaridaki_kalem_dizi",
    "v7_durumdaki_kab",
    "v7_numaralandirilmis_kut",
    "v7_iki_tekerlek_bisiklet",
    "v7_telefon_tablet_ekran",
    "v7_isik_kaynagi_levha",
    "v7_renkli_boncuk_cubuk",
    "v7_dort_eskenar",
    "v7_piramit_koni_silindir",
    "v7_uygulamalar_satira",
    "v7_asagidaki_duzenek",
    "v7_asagidaki_cubuklar",
    "v7_ucgen_acisal_aci",
    "v7_dik_koord_sistem_figur",
    "v7_K_L_M_N_noktalar",
    "v7_yatay_yol_F_kuvvet",
    "v7_F1_F2_F3",
    "v7_strob_periyodik_dalga",
    "v7_kesit_verilen_eks",
    "v7_aci_widehat_nolu",
    "v8_sekil_no_dash",
    "v8_birimkare_bolunmus",
    "v8_renkli_nesne",
    "v8_atmalari_yay",
    "v8_yukaridaki_general",
    "v8_n_cubukta",
    "v8_asagidaki_kosullar",
    "v8_ust_yan_yan_konulan",
    "v8_numaralandirilmis_koltuk_sira",
    "v8_yatay_sukrosel_arac",
    "v8_iki_atma_K_L",
    "v8_sicak_soguk_borular",
    "v8_aynı_doğrultuda",
    "v8_orta_nokta_segm",
    "broken_ends_III",
    "broken_ends_dotdot",
    # incomplete_roman_options_no_text → MEDIUM risk, skip
    # LATEX patterns → frontend fix, soru içeriği OK, REJECT ETME
}


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def scan(eng) -> dict[str, int]:
    """Count auto_judged_high questions matching each pattern."""
    from sqlalchemy import text

    counts = {}
    for cat, pred, _ in PATTERNS:
        sql = (
            f"SELECT COUNT(*) FROM question_bank "
            f"WHERE is_active=true AND quality_review_status='auto_judged_high' "
            f"AND ({pred})"
        )
        with eng.connect() as c:
            counts[cat] = c.execute(text(sql)).scalar() or 0
    return counts


def sample(eng, category: str, n: int = 10) -> list:
    """Return N random samples from category for false-positive check."""
    from sqlalchemy import text

    pred = next((p for c, p, _ in PATTERNS if c == category), None)
    if not pred:
        return []

    sql = (
        f"SELECT id::text, source_book, "
        f"  LEFT(question_text, 250) AS qt, "
        f"  LEFT(option_a, 80) AS a, LEFT(option_b, 80) AS b, "
        f"  LEFT(option_c, 80) AS c, LEFT(option_d, 80) AS d, "
        f"  LEFT(option_e, 80) AS e "
        f"FROM question_bank "
        f"WHERE is_active=true AND quality_review_status='auto_judged_high' "
        f"AND ({pred}) "
        f"ORDER BY md5(id::text) LIMIT {n}"
    )
    with eng.connect() as c:
        return c.execute(text(sql)).fetchall()


def apply_reject(eng, dry_run: bool = True) -> dict:
    """Reject all APPLY_CATEGORIES patterns."""
    from sqlalchemy import text

    audit_obj = {"date": AUDIT_DATE, "source": "beta_pattern_scanner_v1"}
    audit_json = json.dumps(audit_obj)
    counts = {}

    for cat, pred, _ in PATTERNS:
        if cat not in APPLY_CATEGORIES:
            continue

        if dry_run:
            sql = (
                f"SELECT COUNT(*) FROM question_bank "
                f"WHERE is_active=true AND quality_review_status='auto_judged_high' "
                f"AND ({pred})"
            )
            with eng.connect() as c:
                counts[cat] = c.execute(text(sql)).scalar() or 0
        else:
            meta = json.dumps({"category": cat})
            sql = f"""
                UPDATE question_bank
                SET quality_review_status = 'rejected',
                    pipeline_metadata = jsonb_set(
                        COALESCE(CAST(pipeline_metadata AS jsonb), '{{}}'::jsonb),
                        '{{beta_pattern_scan_v1}}',
                        CAST(:audit AS jsonb) || CAST(:meta AS jsonb),
                        TRUE
                    )::json,
                    updated_at = NOW()
                WHERE is_active=true
                  AND quality_review_status='auto_judged_high'
                  AND ({pred})
            """
            with eng.begin() as c:
                result = c.execute(text(sql), {"audit": audit_json, "meta": meta})
                counts[cat] = result.rowcount

    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true", help="Count patterns")
    ap.add_argument("--sample", type=str, help="Sample N rows for given category")
    ap.add_argument("--n", type=int, default=10, help="Sample size")
    ap.add_argument("--dry-run", action="store_true", help="Apply dry-run count")
    ap.add_argument("--apply", action="store_true", help="Apply reject")
    args = ap.parse_args()

    if not (args.scan or args.sample or args.dry_run or args.apply):
        print("[error] --scan|--sample|--dry-run|--apply gerekli")
        return 2

    eng = get_engine()
    today = datetime.now().strftime("%Y%m%d")

    if args.scan:
        counts = scan(eng)
        out = PILOTS_DIR / f"{today}_beta_pattern_scan_RESULT.md"
        lines = [
            "# Beta Pattern Scanner — Counts",
            f"\n**Date:** {AUDIT_DATE}\n",
            "| Category | Count | Reason |\n|---|---|---|",
        ]
        for cat, _, reason in PATTERNS:
            n = counts.get(cat, 0)
            marker = "✅ APPLY" if cat in APPLY_CATEGORIES else "⏭ SKIP"
            lines.append(f"| `{cat}` | {n:,} | {marker} {reason} |")
        lines.append("\n**Total auto_judged_high:** ")
        from sqlalchemy import text

        with eng.connect() as c:
            total = c.execute(
                text(
                    "SELECT COUNT(*) FROM question_bank "
                    "WHERE is_active=true AND quality_review_status='auto_judged_high'"
                )
            ).scalar()
        lines.append(f"{total:,}")
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n[scan] {total:,} total auto_judged_high")
        for cat, n in counts.items():
            marker = "✅" if cat in APPLY_CATEGORIES else "⏭"
            print(f"  {marker} {cat}: {n:,}")
        print(f"\n[result] {out}")

    elif args.sample:
        rows = sample(eng, args.sample, args.n)
        out = PILOTS_DIR / f"{today}_sample_{args.sample}.md"
        lines = [f"# Sample {args.sample} (N={len(rows)})\n"]
        for row in rows:
            lines.append(f"\n## `{row.id[:8]}` — {row.source_book}\n")
            qt = (row.qt or "").replace("\n", " ")
            lines.append(f"**Text:** {qt}")
            lines.append(f"- A: {row.a}")
            lines.append(f"- B: {row.b}")
            lines.append(f"- C: {row.c}")
            lines.append(f"- D: {row.d}")
            lines.append(f"- E: {row.e}")
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[sample] {args.sample}: {len(rows)} satır → {out}")

    elif args.dry_run or args.apply:
        counts = apply_reject(eng, dry_run=args.dry_run)
        total = sum(counts.values())
        mode = "dry-run" if args.dry_run else "apply"
        out = PILOTS_DIR / f"{today}_beta_pattern_{mode}_RESULT.md"

        lines = [
            f"# Beta Pattern Scanner — {mode.upper()} RESULT",
            f"\n**Date:** {AUDIT_DATE}\n",
            "## Per Category\n",
            "| Category | Count |\n|---|---|",
        ]
        for cat, n in counts.items():
            lines.append(f"| `{cat}` | {n:,} |")
        lines.append(f"| **TOTAL** | **{total:,}** |\n")

        from sqlalchemy import text

        with eng.connect() as c:
            post = c.execute(
                text(
                    "SELECT quality_review_status, COUNT(*) FROM question_bank "
                    "WHERE is_active=true GROUP BY 1 ORDER BY 2 DESC"
                )
            ).fetchall()
            view = c.execute(text("SELECT COUNT(*) FROM v_safe_for_beta")).scalar()
        lines.append("## Post State\n")
        lines.append("| Status | Count |\n|---|---|")
        for s, n in post:
            lines.append(f"| {s} | {n:,} |")
        lines.append(f"\n**v_safe_for_beta:** {view:,}")

        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n[{mode}] TOTAL: {total:,}")
        for cat, n in counts.items():
            print(f"  {cat}: {n:,}")
        print(f"\n[v_safe_for_beta] {view:,}")
        print(f"[result] {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
