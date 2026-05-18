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
| `context_bu_opening` | 0 | ✅ APPLY 'Bu X...' opening — dangling context reference |
| `context_yukaridaki_acik` | 0 | ✅ APPLY 'Yukarıdaki/Yukarıda verilen...' opening (preceding context) |
| `context_asagidaki_acik` | 0 | ✅ APPLY 'Aşağıdaki/Aşağıda verilen...' opening (following context) |
| `v4_asagida_verilmis` | 0 | ✅ APPLY Aşağıda(ki) ...gösterilmiştir/verilmiştir — image-bound |
| `v4_yukarida_gorulm` | 0 | ✅ APPLY Yukarıda(ki) ...görülmektedir/gösterilmiştir — image-bound |
| `v4_duzgun_polygon` | 0 | ✅ APPLY ABCDE düzgün beşgen — geometri figür |
| `v4_function_graph` | 0 | ✅ APPLY Fonksiyonun grafiği referansı |
| `v4_coord_duzlem` | 0 | ✅ APPLY Dik koordinat düzleminde figür ref |
| `v4_dangling_yukaridaki_x` | 0 | ✅ APPLY Yukarıdaki X — dangling reference |
| `v4_dangling_bu_x` | 0 | ✅ APPLY 'Buna göre, bu X' — context dangling |
| `v4_kare_bolmeler` | 0 | ✅ APPLY Eşit kare bölmelere ayrılmış — grid figure |
| `v4_bulmaca` | 0 | ✅ APPLY Bulmaca tarzı — figür gerekir |
| `v4_atomic_diagram` | 0 | ✅ APPLY Atomic structure diagram (Lewis) |
| `v4_kose_sayi` | 0 | ✅ APPLY Köşelere sayı yazılı geometri figür |
| `v4_uzunluk_birim` | 0 | ✅ APPLY Birim uzunluklar verilmiş — figür |
| `v4_eksen_grafigi` | 0 | ✅ APPLY Eksen referansı — grafik figür |
| `v4_sigacin_levha` | 0 | ✅ APPLY Sığaç levhaları figür (fizik) |
| `v4_isin_yolu` | 0 | ✅ APPLY Işık ışını yolu — optik figür |
| `v4_atom_xY_dizilim` | 0 | ✅ APPLY X, Y atomları + dizilim/elektron — atomic diagram |
| `v4_grafik_veril` | 0 | ✅ APPLY Grafiği verilmiştir/gösterilmiştir |
| `v4_parabol_dogru` | 0 | ✅ APPLY Parabol/parabolü verilmiş — grafik |
| `v5_asagidaki_gibi_action` | 0 | ✅ APPLY Aşağıdaki gibi dizilmiş/kurulmuş/katlama — figür |
| `v5_yukaridaki_gibi_action` | 0 | ✅ APPLY Yukarıdaki gibi — figür |
| `v5_sayi_dogrusu` | 0 | ✅ APPLY Sayı doğrusu — figür gerekir |
| `v5_periyodik_cetvel` | 0 | ✅ APPLY Periyodik cetvelde yerleri verilen — figür |
| `v5_devre_fizik` | 0 | ✅ APPLY Devre + lamba/üreteç/direnç — devre figürü |
| `v5_kac_numara_gosterilmis` | 0 | ✅ APPLY Kaç numara ile gösterilmiştir — figür |
| `v5_yay_atom_cisim` | 0 | ✅ APPLY K ve L yayları/cisimleri/elektroskopları — figür ref |
| `v5_aci_geometri` | 0 | ✅ APPLY m(âçı) notation — geometri figür |
| `v5_ornuntu_dizi` | 0 | ✅ APPLY Örüntü/desen oluşturma — figür |
| `v5_I_II_nolu` | 0 | ✅ APPLY I. nolu / II. kapta — numbered figure |
| `v5_kuvvet_uygulanan` | 0 | ✅ APPLY Kuvvetler uygulanan + yörünge/hız — fizik figür |
| `v5_zipline_ip_iki_direk` | 0 | ✅ APPLY İki direk / zipline — figür |
| `v5_iki_daire_cember` | 0 | ✅ APPLY İki daire/çember + yarıçap/merkez — figür |
| `v5_serbest_uc` | 0 | ✅ APPLY Serbest uç + yay/ip — fizik figür |
| `v5_x_y_z_atom` | 0 | ✅ APPLY X/Y/Z atom + periyot/grup/dizilim — atomic diagram |
| `v5_K_L_M_lamba_devre` | 0 | ✅ APPLY K, L, M lambaları/üreteçleri — devre figür |
| `v5_kapta_bulunan` | 0 | ✅ APPLY I. kapta / II. nolu kap — numbered containers (figür) |
| `v5_dort_renkli_havuc` | 0 | ✅ APPLY Sebze/meyve + I/II. kap — figür |
| `v5_kent_kentine_giderken` | 0 | ✅ APPLY A kentinden B kentine — harita figür |
| `v5_bilgisayar_ekran` | 0 | ✅ APPLY Bilgisayar ekranı görüntüsü — figür |
| `v5_hucre_zarı_fosfolipit` | 0 | ✅ APPLY Hücre zarı + numara ile gösterilm — diyagram |
| `v6_sekil_dash` | 0 | ✅ APPLY Şekil-I/Şekil-1 dash notation — image-bound |
| `v6_dusey_kesit` | 0 | ✅ APPLY Düşey kesiti verilen — figür |
| `v6_gunes_sistemi` | 0 | ✅ APPLY Güneş Sistemi görsel referans |
| `v6_yukaridaki_kaplar` | 0 | ✅ APPLY Yukarıdaki kaplar/sıvılar — figür |
| `v6_n_nolu_kut` | 0 | ✅ APPLY I/II nolu kutu/kap/şişe — numbered figure |
| `v6_egik_duzlem_K` | 0 | ✅ APPLY Eğik düzlem — fizik figür |
| `v6_KL_LM_MN_segment` | 0 | ✅ APPLY KL/LM segments + nokta — figür |
| `v6_abcde_dots` | 0 | ✅ APPLY ABCDE... n kenarlı — polygon figür |
| `v6_O_merkez` | 0 | ✅ APPLY O merkezli daire/çember — figür |
| `v6_sayi_duzenegi` | 0 | ✅ APPLY Sayı düzeneği — figür |
| `v6_sekilde_belirtil` | 0 | ✅ APPLY Şekilde belirtilen yön/işaret — figür |
| `v6_birim_kareler` | 0 | ✅ APPLY Birim karelerden oluşan — grid figure |
| `v6_kepler_kepler_yasalari` | 0 | ✅ APPLY Astronomi/fizik nesne + figür ref |
| `v6_kapsam_sapma_grafigi` | 0 | ✅ APPLY Yörünge/grafik ref — figür |
| `v6_evre_ait_yukaridaki` | 0 | ✅ APPLY Evreler/aşamalar yukarıdaki — figür |
| `v6_akim_devre` | 0 | ✅ APPLY Devre akım/gerilim — devre figür |
| `v6_kuvvet_F1_F2` | 0 | ✅ APPLY F_1, F_2 kuvvetleri — figür |
| `v6_ucgen_geometri_acidol` | 0 | ✅ APPLY Üçgen geometri + açı — figür |
| `v6_omurga_skolyoz_rontgen` | 0 | ✅ APPLY Tıbbi görüntü ref |
| `v6_yatay_dusey_eksen` | 0 | ✅ APPLY Yatay/düşey düzlem fizik — figür |
| `v7_sekil_dash_loose` | 315 | ✅ APPLY Şekil - I/II (dash with optional spaces) |
| `v7_x_es_karelerden` | 6 | ✅ APPLY N eş kareden oluşan — grid figure |
| `v7_sekilde_fonk` | 0 | ✅ APPLY Şekilde f(x) — graphed function |
| `v7_yukaridaki_kalem_dizi` | 31 | ✅ APPLY Yukarıdaki kalem/kutu/şekil — figür |
| `v7_durumdaki_kab` | 5 | ✅ APPLY 1./2. durumdaki kap/kutu — figür |
| `v7_numaralandirilmis_kut` | 0 | ✅ APPLY Numaralandırılmış kutular/kaplar — figür |
| `v7_iki_tekerlek_bisiklet` | 15 | ✅ APPLY İki tekerlekli bisiklet — figür |
| `v7_telefon_tablet_ekran` | 17 | ✅ APPLY Tablet/telefon ekranı — figür |
| `v7_isik_kaynagi_levha` | 11 | ✅ APPLY K ve L levhaları/aynaları — figür |
| `v7_renkli_boncuk_cubuk` | 40 | ✅ APPLY Renkli boncuk/çubuk/disk — figür |
| `v7_dort_eskenar` | 134 | ✅ APPLY ABC eşkenar üçgen — figür |
| `v7_piramit_koni_silindir` | 554 | ✅ APPLY Piramit/koni/silindir + göster — figür |
| `v7_uygulamalar_satira` | 25 | ✅ APPLY Tablet uygulamaları sırasız — figür |
| `v7_asagidaki_duzenek` | 53 | ✅ APPLY Aşağıdaki düzenek/deney/şişe — figür |
| `v7_asagidaki_cubuklar` | 50 | ✅ APPLY Aşağıdaki çubuklar/tepkimeler — figür |
| `v7_ucgen_acisal_aci` | 705 | ✅ APPLY ABC üçgen/dörtgen + noktası/köşesi — figür |
| `v7_dik_koord_sistem_figur` | 68 | ✅ APPLY Dik koordinat sistemi + figür ref |
| `v7_K_L_M_N_noktalar` | 0 | ✅ APPLY K, L, M, N noktaları — figür ref |
| `v7_yatay_yol_F_kuvvet` | 34 | ✅ APPLY Yatay yol + kuvvet — fizik figür |
| `v7_F1_F2_F3` | 0 | ✅ APPLY F_1, F_2, F_3 kuvvetler — figür |
| `v7_strob_periyodik_dalga` | 164 | ✅ APPLY Stroboskop / dalga — fizik figür |
| `v7_kesit_verilen_eks` | 20 | ✅ APPLY Kesit verilen/gösterilen — figür |
| `v7_aci_widehat_nolu` | 332 | ✅ APPLY m(âçı) — geometri figür |
| `broken_ends_III` | 0 | ✅ APPLY Roman numaralı liste yarıda kesik (sonu II/III/IV) |
| `broken_ends_dotdot` | 0 | ✅ APPLY Paragraf '...' ile bitiyor (truncation indicator) |
| `incomplete_roman_options_no_text` | 1,089 | ⏭ SKIP Opsiyonlarda Roman list var ama metinde işaret yok |
| `latex_options_frac` | 2,452 | ⏭ SKIP Opsiyonlarda \frac raw — Frontend MathText wrap eksik (Bug #1 v2) |
| `latex_options_sqrt` | 1,014 | ⏭ SKIP Opsiyonlarda \sqrt raw — Bug #1 v2 |
| `latex_options_alpha_beta` | 363 | ⏭ SKIP Opsiyonlarda Greek/math symbol raw — Bug #1 v2 |

**Total auto_judged_high:** 
36,725
