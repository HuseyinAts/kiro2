"""
PDF Rapor Oluşturucu
Gelişmiş sınav raporları için PDF oluşturma utility'si
"""

import logging
import os
from typing import Any

# matplotlib.pyplot imported but not used - removed plt
import matplotlib
from reportlab.lib.colors import HexColor, black, white

# Charts imported but not used - removed PieChart, BarChart
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

matplotlib.use("Agg")  # Non-interactive backend

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """PDF rapor oluşturucu sınıfı"""

    def __init__(self):
        """PDF oluşturucuyu başlat"""
        self.setup_fonts()
        self.setup_styles()
        self.reports_dir = "reports/pdf"
        os.makedirs(self.reports_dir, exist_ok=True)

    def setup_fonts(self):
        """Türkçe karakter desteği için fontları ayarla"""
        try:
            # DejaVu Sans font'u kullan (Türkçe karakter desteği)
            font_path = "fonts/DejaVuSans.ttf"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
                pdfmetrics.registerFont(
                    TTFont("DejaVuSans-Bold", "fonts/DejaVuSans-Bold.ttf")
                )
            else:
                logger.warning(
                    "DejaVu Sans font bulunamadı, varsayılan font kullanılacak"
                )
        except Exception as e:
            logger.error(f"Font yükleme hatası: {e!s}")

    def setup_styles(self):
        """PDF stilleri ayarla"""
        self.styles = getSampleStyleSheet()

        # Başlık stilleri
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=HexColor("#2E86AB"),
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CustomHeading1",
                parent=self.styles["Heading1"],
                fontSize=18,
                spaceAfter=20,
                textColor=HexColor("#2E86AB"),
                borderWidth=1,
                borderColor=HexColor("#2E86AB"),
                borderPadding=5,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CustomHeading2",
                parent=self.styles["Heading2"],
                fontSize=14,
                spaceAfter=15,
                textColor=HexColor("#A23B72"),
            )
        )

        # İçerik stilleri
        self.styles.add(
            ParagraphStyle(
                name="CustomNormal",
                parent=self.styles["Normal"],
                fontSize=11,
                spaceAfter=10,
                alignment=TA_LEFT,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CustomBullet",
                parent=self.styles["Normal"],
                fontSize=10,
                leftIndent=20,
                bulletIndent=10,
                spaceAfter=5,
            )
        )

    async def generate_advanced_exam_report(
        self, rapor_data: dict[str, Any], filename: str
    ) -> str:
        """
        Gelişmiş sınav raporu PDF'i oluştur

        Args:
            rapor_data: Rapor verileri
            filename: PDF dosya adı

        Returns:
            str: Oluşturulan PDF dosya yolu
        """
        try:
            file_path = os.path.join(self.reports_dir, filename)

            # PDF dokümanı oluştur
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # İçerik listesi
            story = []

            # Başlık sayfası
            story.extend(self._create_title_page(rapor_data))
            story.append(PageBreak())

            # Özet bölümü
            story.extend(self._create_summary_section(rapor_data))
            story.append(PageBreak())

            # IRT Morfoloji analizi
            if rapor_data.get("irt_morfoloji_analizi"):
                story.extend(
                    self._create_irt_analysis_section(
                        rapor_data["irt_morfoloji_analizi"]
                    )
                )
                story.append(PageBreak())

            # ZPD analizi
            if rapor_data.get("zpd_analizi"):
                story.extend(
                    self._create_zpd_analysis_section(rapor_data["zpd_analizi"])
                )
                story.append(PageBreak())

            # Hibrit öğrenme stili analizi
            if rapor_data.get("hibrit_ogrenme_stili_analizi"):
                story.extend(
                    self._create_learning_style_section(
                        rapor_data["hibrit_ogrenme_stili_analizi"]
                    )
                )
                story.append(PageBreak())

            # ÖSYM/ETS karşılaştırması
            if rapor_data.get("osym_ets_karsilastirmasi"):
                story.extend(
                    self._create_comparison_section(
                        rapor_data["osym_ets_karsilastirmasi"]
                    )
                )
                story.append(PageBreak())

            # Kişiselleştirilmiş öneriler
            if rapor_data.get("kisisellestirilmis_oneriler"):
                story.extend(
                    self._create_recommendations_section(
                        rapor_data["kisisellestirilmis_oneriler"]
                    )
                )

            # PDF'i oluştur
            doc.build(story)

            logger.info(f"PDF rapor oluşturuldu: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"PDF oluşturma hatası: {e!s}")
            raise

    def _create_title_page(self, rapor_data: dict[str, Any]) -> list:
        """Başlık sayfası oluştur"""
        story = []

        # Ana başlık
        story.append(
            Paragraph("Gelişmiş Sınav Analiz Raporu", self.styles["CustomTitle"])
        )
        story.append(Spacer(1, 0.5 * inch))

        # Sınav bilgileri
        temel_sonuc = rapor_data.get("temel_sonuc", {})
        sinav_tipi = temel_sonuc.get("sinav_tipi", "Bilinmiyor")

        story.append(
            Paragraph(f"Sınav Tipi: {sinav_tipi}", self.styles["CustomHeading2"])
        )
        story.append(
            Paragraph(
                f"Rapor Tarihi: {rapor_data.get('rapor_tarihi', 'Bilinmiyor')}",
                self.styles["CustomNormal"],
            )
        )
        story.append(
            Paragraph(
                f"Öğrenci ID: {rapor_data.get('ogrenci_id', 'Bilinmiyor')}",
                self.styles["CustomNormal"],
            )
        )

        story.append(Spacer(1, 1 * inch))

        # Rapor özeti kutusu
        ozet_data = [
            ["Ham Puan", f"{temel_sonuc.get('ham_puan', 0):.1f}"],
            ["Net Sayısı", f"{temel_sonuc.get('net_sayisi', 0):.2f}"],
            ["Doğru", str(temel_sonuc.get("dogru_sayisi", 0))],
            ["Yanlış", str(temel_sonuc.get("yanlis_sayisi", 0))],
            ["Boş", str(temel_sonuc.get("bos_sayisi", 0))],
        ]

        ozet_table = Table(ozet_data, colWidths=[2 * inch, 2 * inch])
        ozet_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2E86AB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), HexColor("#F0F8FF")),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                ]
            )
        )

        story.append(ozet_table)
        story.append(Spacer(1, 1 * inch))

        # Uyarı notu
        story.append(
            Paragraph(
                "Bu rapor, gelişmiş AI algoritmaları kullanılarak oluşturulmuş kapsamlı bir analiz içermektedir. "
                "IRT parametreleri, Türkçe morfoloji analizi, ZPD hesaplamaları ve hibrit öğrenme stili değerlendirmeleri "
                "ile kişiselleştirilmiş öğrenme önerileri sunmaktadır.",
                self.styles["CustomNormal"],
            )
        )

        return story

    def _create_summary_section(self, rapor_data: dict[str, Any]) -> list:
        """Özet bölümü oluştur"""
        story = []

        story.append(
            Paragraph("[CHART] Sınav Sonuçları Özeti", self.styles["CustomHeading1"])
        )

        temel_sonuc = rapor_data.get("temel_sonuc", {})

        # Temel istatistikler tablosu
        istatistik_data = [
            ["Metrik", "Değer", "Açıklama"],
            [
                "Ham Puan",
                f"{temel_sonuc.get('ham_puan', 0):.1f}",
                "100 üzerinden başarı puanı",
            ],
            [
                "Net Sayısı",
                f"{temel_sonuc.get('net_sayisi', 0):.2f}",
                "Doğru - (Yanlış/4)",
            ],
            [
                "Başarı Oranı",
                f"{(temel_sonuc.get('ham_puan', 0)):.1f}%",
                "Genel başarı yüzdesi",
            ],
            [
                "Toplam Soru",
                str(temel_sonuc.get("toplam_soru", 0)),
                "Çözülen toplam soru sayısı",
            ],
        ]

        istatistik_table = Table(
            istatistik_data, colWidths=[2 * inch, 1.5 * inch, 2.5 * inch]
        )
        istatistik_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2E86AB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), HexColor("#F8F9FA")),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        story.append(istatistik_table)
        story.append(Spacer(1, 0.3 * inch))

        # Konu performansları
        story.append(
            Paragraph("[BOOKS] Konu Bazlı Performans", self.styles["CustomHeading2"])
        )

        konu_performanslari = temel_sonuc.get("konu_performanslari", [])
        if konu_performanslari:
            konu_data = [["Konu", "Doğru", "Yanlış", "Boş", "Başarı %"]]

            for kp in konu_performanslari:
                konu_data.append(
                    [
                        kp.get("konu", ""),
                        str(kp.get("dogru_sayisi", 0)),
                        str(kp.get("yanlis_sayisi", 0)),
                        str(kp.get("bos_sayisi", 0)),
                        f"{kp.get('basari_yuzdesi', 0):.1f}%",
                    ]
                )

            konu_table = Table(
                konu_data,
                colWidths=[2 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 1 * inch],
            )
            konu_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#A23B72")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), white),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#FFF0F5")),
                        ("GRID", (0, 0), (-1, -1), 1, black),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ]
                )
            )

            story.append(konu_table)

        story.append(Spacer(1, 0.3 * inch))

        # Güçlü ve zayıf alanlar
        guclu_konular = temel_sonuc.get("guclu_konular", [])
        zayif_konular = temel_sonuc.get("zayif_konular", [])

        if guclu_konular:
            story.append(Paragraph("💪 Güçlü Alanlar", self.styles["CustomHeading2"]))
            for konu in guclu_konular:
                story.append(Paragraph(f"• {konu}", self.styles["CustomBullet"]))

        if zayif_konular:
            story.append(
                Paragraph(
                    "[TRENDING_UP] Geliştirilmesi Gereken Alanlar",
                    self.styles["CustomHeading2"],
                )
            )
            for konu in zayif_konular:
                story.append(Paragraph(f"• {konu}", self.styles["CustomBullet"]))

        return story

    def _create_irt_analysis_section(self, irt_analizi: dict[str, Any]) -> list:
        """IRT analizi bölümü oluştur"""
        story = []

        story.append(
            Paragraph(
                "[MICROSCOPE] IRT + Morfoloji Analizi", self.styles["CustomHeading1"]
            )
        )

        # Genel istatistikler
        genel_stats = irt_analizi.get("genel_istatistikler", {})

        story.append(
            Paragraph("[CHART] IRT Parametreleri", self.styles["CustomHeading2"])
        )

        irt_data = [
            ["Parametre", "Değer", "Açıklama"],
            [
                "Ortalama Zorluk",
                f"{genel_stats.get('ortalama_zorluk', 0):.3f}",
                "Soru zorluk seviyesi (-4 ile +4 arası)",
            ],
            [
                "Ortalama Ayırt Edicilik",
                f"{genel_stats.get('ortalama_ayirt_edicilik', 0):.3f}",
                "Soruların ayırt etme gücü",
            ],
            [
                "Morfoloji Faktörü",
                f"{genel_stats.get('ortalama_morfoloji_faktoru', 0):.3f}",
                "Türkçe morfolojik karmaşıklık",
            ],
        ]

        irt_table = Table(irt_data, colWidths=[2 * inch, 1.5 * inch, 2.5 * inch])
        irt_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#FF6B6B")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), HexColor("#FFF5F5")),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        story.append(irt_table)
        story.append(Spacer(1, 0.3 * inch))

        # Morfoloji farkındalığı
        morfoloji_fark = irt_analizi.get("morfoloji_farkindaliği", {})

        story.append(
            Paragraph("🔤 Morfoloji Farkındalığı Analizi", self.styles["CustomHeading2"])
        )

        story.append(
            Paragraph(
                f"Genel Seviye: {morfoloji_fark.get('genel_seviye', 'Bilinmiyor').title()}",
                self.styles["CustomNormal"],
            )
        )

        guclu_alanlar = morfoloji_fark.get("guclu_alanlar", [])
        if guclu_alanlar:
            story.append(Paragraph("Güçlü Alanlar:", self.styles["CustomNormal"]))
            for alan in guclu_alanlar:
                story.append(Paragraph(f"• {alan}", self.styles["CustomBullet"]))

        gelisim_alanlari = morfoloji_fark.get("gelisim_alanlari", [])
        if gelisim_alanlari:
            story.append(Paragraph("Gelişim Alanları:", self.styles["CustomNormal"]))
            for alan in gelisim_alanlari:
                story.append(Paragraph(f"• {alan}", self.styles["CustomBullet"]))

        # IRT performans profili
        irt_profil = irt_analizi.get("irt_performans_profili", {})

        story.append(
            Paragraph(
                "[TRENDING_UP] IRT Performans Profili", self.styles["CustomHeading2"]
            )
        )

        profil_data = [
            ["Metrik", "Değer"],
            ["Yetenek Tahmini (θ)", f"{irt_profil.get('yetenek_tahmini', 0):.2f}"],
            ["Standart Hata", f"{irt_profil.get('standart_hata', 0):.2f}"],
            [
                "Güven Aralığı",
                f"{irt_profil.get('guven_araligi', [0, 0])[0]:.2f} - {irt_profil.get('guven_araligi', [0, 0])[1]:.2f}",
            ],
        ]

        profil_table = Table(profil_data, colWidths=[3 * inch, 2 * inch])
        profil_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#4ECDC4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), HexColor("#F0FFFF")),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        story.append(profil_table)

        return story

    def _create_zpd_analysis_section(self, zpd_analizi: dict[str, Any]) -> list:
        """ZPD analizi bölümü oluştur"""
        story = []

        story.append(
            Paragraph("[TARGET] ZPD + Maarif Analizi", self.styles["CustomHeading1"])
        )

        # Genel ZPD profili
        genel_profil = zpd_analizi.get("genel_zpd_profili", {})

        story.append(
            Paragraph("[CHART] Genel ZPD Profili", self.styles["CustomHeading2"])
        )

        zpd_data = [
            ["Metrik", "Değer", "Açıklama"],
            [
                "Mevcut Seviye",
                f"{genel_profil.get('ortalama_mevcut_seviye', 0):.2f}",
                "Öğrencinin şu anki yetenek seviyesi",
            ],
            [
                "Optimal Zorluk",
                f"{genel_profil.get('ortalama_optimal_zorluk', 0):.2f}",
                "Önerilen zorluk seviyesi",
            ],
            [
                "Kültürel Uyum",
                genel_profil.get("kulturel_uyum_seviyesi", "Bilinmiyor"),
                "Türk kültürü faktörleri uyumu",
            ],
            [
                "Maarif Uyumu",
                genel_profil.get("maarif_degerleri_uyumu", "Bilinmiyor"),
                "MEB değerleri uyumu",
            ],
        ]

        zpd_table = Table(zpd_data, colWidths=[2 * inch, 1.5 * inch, 2.5 * inch])
        zpd_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#45B7D1")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), HexColor("#F0F8FF")),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        story.append(zpd_table)
        story.append(Spacer(1, 0.3 * inch))

        # Kültürel faktörler
        kulturel_faktorler = zpd_analizi.get("kulturel_faktorler", {})

        story.append(
            Paragraph("🏛️ Türk Kültürü Faktörleri", self.styles["CustomHeading2"])
        )

        for faktor, deger in kulturel_faktorler.items():
            faktor_adi = faktor.replace("_", " ").title()
            story.append(
                Paragraph(f"• {faktor_adi}: {deger:.1%}", self.styles["CustomBullet"])
            )

        story.append(Spacer(1, 0.2 * inch))

        # MEB Maarif değerleri
        maarif_profili = zpd_analizi.get("maarif_degerleri_profili", {})

        story.append(
            Paragraph("🇹🇷 MEB Maarif Değerleri Uyumu", self.styles["CustomHeading2"])
        )

        for deger, uyum in maarif_profili.items():
            deger_adi = deger.replace("_", " ").title()
            story.append(
                Paragraph(f"• {deger_adi}: {uyum:.1%}", self.styles["CustomBullet"])
            )

        return story

    def _create_learning_style_section(
        self, ogrenme_stili_analizi: dict[str, Any]
    ) -> list:
        """Hibrit öğrenme stili bölümü oluştur"""
        story = []

        story.append(
            Paragraph(
                "[BRAIN] Hibrit Öğrenme Stili Analizi", self.styles["CustomHeading1"]
            )
        )

        # Hibrit profil özeti
        hibrit_ozet = ogrenme_stili_analizi.get("hibrit_profil_ozeti", {})

        story.append(
            Paragraph(
                "[CLIPBOARD] Öğrenme Stili Profili", self.styles["CustomHeading2"]
            )
        )

        story.append(
            Paragraph(
                f"Hibrit Kod: {hibrit_ozet.get('hibrit_kod', 'Bilinmiyor')}",
                self.styles["CustomNormal"],
            )
        )
        story.append(
            Paragraph(
                f"Dominant VARK Stili: {hibrit_ozet.get('dominant_vark_stili', 'Bilinmiyor').title()}",
                self.styles["CustomNormal"],
            )
        )
        story.append(
            Paragraph(
                f"Güven Seviyesi: {hibrit_ozet.get('guven_seviyesi', 0):.1%}",
                self.styles["CustomNormal"],
            )
        )

        story.append(Spacer(1, 0.2 * inch))

        # VARK profili
        vark_profili = ogrenme_stili_analizi.get("vark_profili", {})

        story.append(
            Paragraph("👁️ VARK Öğrenme Tercihleri", self.styles["CustomHeading2"])
        )

        vark_data = [["Stil", "Skor", "Açıklama"]]
        vark_aciklamalar = {
            "visual": "Görsel materyaller, diyagramlar, grafikler",
            "auditory": "Sesli anlatım, tartışma, müzik",
            "reading": "Metin okuma, yazma, notlar",
            "kinesthetic": "Uygulamalı çalışma, hareket, dokunma",
        }

        for stil, skor in vark_profili.items():
            vark_data.append(
                [stil.title(), f"{skor:.1%}", vark_aciklamalar.get(stil, "")]
            )

        vark_table = Table(vark_data, colWidths=[1.5 * inch, 1 * inch, 3.5 * inch])
        vark_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#96CEB4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), HexColor("#F0FFF0")),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        story.append(vark_table)
        story.append(Spacer(1, 0.3 * inch))

        # Performans uyumu
        performans_uyumu = ogrenme_stili_analizi.get("performans_uyumu", [])

        story.append(
            Paragraph(
                "[CHART] Konu Bazlı Öğrenme Stili Uyumu", self.styles["CustomHeading2"]
            )
        )

        if performans_uyumu:
            uyum_data = [["Konu", "Başarı %", "Stil Uyumu %", "Önerilen Yöntem"]]

            for uyum in performans_uyumu:
                uyum_data.append(
                    [
                        uyum.get("konu", ""),
                        f"{uyum.get('basari_yuzdesi', 0):.1f}%",
                        f"{uyum.get('ogrenme_stili_uyumu', 0):.1f}%",
                        uyum.get("onerilen_yontem", "").replace("_", " ").title(),
                    ]
                )

            uyum_table = Table(
                uyum_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 2 * inch]
            )
            uyum_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#FFEAA7")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), black),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#FFFEF7")),
                        ("GRID", (0, 0), (-1, -1), 1, black),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ]
                )
            )

            story.append(uyum_table)

        return story

    def _create_comparison_section(self, karsilastirma: dict[str, Any]) -> list:
        """ÖSYM/ETS karşılaştırma bölümü oluştur"""
        story = []

        story.append(
            Paragraph(
                "⚖️ ÖSYM/ETS Standartları Karşılaştırması",
                self.styles["CustomHeading1"],
            )
        )

        # Sonuç değerlendirmesi
        sonuc = karsilastirma.get("sonuc_degerlendirmesi", "Bilinmiyor")
        story.append(
            Paragraph(f"Genel Değerlendirme: {sonuc}", self.styles["CustomHeading2"])
        )

        # ÖSYM karşılaştırması
        osym_karsilastirma = karsilastirma.get("osym_karsilastirma", {})

        story.append(
            Paragraph(
                "🇹🇷 ÖSYM Standartları ile Karşılaştırma", self.styles["CustomHeading2"]
            )
        )

        osym_data = [
            ["Parametre", "Durum", "Skor"],
            [
                "Ayırt Edicilik",
                osym_karsilastirma.get("ayirt_edicilik_durumu", {}).get("durum", ""),
                f"{osym_karsilastirma.get('ayirt_edicilik_durumu', {}).get('skor', 0):.0f}",
            ],
            [
                "Zorluk Seviyesi",
                osym_karsilastirma.get("zorluk_durumu", {}).get("durum", ""),
                f"{osym_karsilastirma.get('zorluk_durumu', {}).get('skor', 0):.0f}",
            ],
            [
                "Şans Faktörü",
                osym_karsilastirma.get("sans_faktoru_durumu", {}).get("durum", ""),
                f"{osym_karsilastirma.get('sans_faktoru_durumu', {}).get('skor', 0):.0f}",
            ],
            ["Genel Uyum", "", f"{osym_karsilastirma.get('genel_uyum_skoru', 0):.0f}"],
        ]

        osym_table = Table(osym_data, colWidths=[2 * inch, 2 * inch, 1 * inch])
        osym_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E74C3C")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), HexColor("#FADBD8")),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        story.append(osym_table)
        story.append(Spacer(1, 0.3 * inch))

        # ETS karşılaştırması
        ets_karsilastirma = karsilastirma.get("ets_karsilastirma", {})

        story.append(
            Paragraph(
                "🌍 ETS Standartları ile Karşılaştırma", self.styles["CustomHeading2"]
            )
        )

        ets_data = [
            ["Parametre", "Durum", "Skor"],
            [
                "Ayırt Edicilik",
                ets_karsilastirma.get("ayirt_edicilik_durumu", {}).get("durum", ""),
                f"{ets_karsilastirma.get('ayirt_edicilik_durumu', {}).get('skor', 0):.0f}",
            ],
            [
                "Zorluk Seviyesi",
                ets_karsilastirma.get("zorluk_durumu", {}).get("durum", ""),
                f"{ets_karsilastirma.get('zorluk_durumu', {}).get('skor', 0):.0f}",
            ],
            [
                "Şans Faktörü",
                ets_karsilastirma.get("sans_faktoru_durumu", {}).get("durum", ""),
                f"{ets_karsilastirma.get('sans_faktoru_durumu', {}).get('skor', 0):.0f}",
            ],
            ["Genel Uyum", "", f"{ets_karsilastirma.get('genel_uyum_skoru', 0):.0f}"],
        ]

        ets_table = Table(ets_data, colWidths=[2 * inch, 2 * inch, 1 * inch])
        ets_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#3498DB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), HexColor("#D6EAF8")),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        story.append(ets_table)
        story.append(Spacer(1, 0.3 * inch))

        # Morfoloji avantajı
        morfoloji_avantaji = karsilastirma.get("morfoloji_avantaji", {})

        story.append(
            Paragraph("🔤 Türkçe Morfoloji Avantajı", self.styles["CustomHeading2"])
        )

        story.append(
            Paragraph(
                morfoloji_avantaji.get("osym_ets_uzerindeki_avantaj", ""),
                self.styles["CustomNormal"],
            )
        )

        ek_boyutlar = morfoloji_avantaji.get("ek_bilgi_boyutlari", [])
        if ek_boyutlar:
            story.append(Paragraph("Ek Analiz Boyutları:", self.styles["CustomNormal"]))
            for boyut in ek_boyutlar:
                story.append(Paragraph(f"• {boyut}", self.styles["CustomBullet"]))

        return story

    def _create_recommendations_section(self, oneriler: list[dict[str, Any]]) -> list:
        """Kişiselleştirilmiş öneriler bölümü oluştur"""
        story = []

        story.append(
            Paragraph(
                "[BULB] Kişiselleştirilmiş Öneriler", self.styles["CustomHeading1"]
            )
        )

        # Öncelik grupları
        yuksek_oncelik = [o for o in oneriler if o.get("oncelik") == "yuksek"]
        orta_oncelik = [o for o in oneriler if o.get("oncelik") == "orta"]
        dusuk_oncelik = [o for o in oneriler if o.get("oncelik") == "dusuk"]

        if yuksek_oncelik:
            story.append(
                Paragraph("🔴 Yüksek Öncelikli Öneriler", self.styles["CustomHeading2"])
            )
            for oneri in yuksek_oncelik:
                story.append(
                    Paragraph(
                        f"• {oneri.get('konu', '')}: {oneri.get('aciklama', '')}",
                        self.styles["CustomBullet"],
                    )
                )
                story.append(
                    Paragraph(
                        f"  Tahmini Süre: {oneri.get('tahmini_sure', 'Belirtilmemiş')}",
                        self.styles["CustomBullet"],
                    )
                )

        if orta_oncelik:
            story.append(
                Paragraph("🟡 Orta Öncelikli Öneriler", self.styles["CustomHeading2"])
            )
            for oneri in orta_oncelik:
                story.append(
                    Paragraph(
                        f"• {oneri.get('konu', '')}: {oneri.get('aciklama', '')}",
                        self.styles["CustomBullet"],
                    )
                )
                story.append(
                    Paragraph(
                        f"  Tahmini Süre: {oneri.get('tahmini_sure', 'Belirtilmemiş')}",
                        self.styles["CustomBullet"],
                    )
                )

        if dusuk_oncelik:
            story.append(
                Paragraph("🟢 Düşük Öncelikli Öneriler", self.styles["CustomHeading2"])
            )
            for oneri in dusuk_oncelik:
                story.append(
                    Paragraph(
                        f"• {oneri.get('konu', '')}: {oneri.get('aciklama', '')}",
                        self.styles["CustomBullet"],
                    )
                )
                story.append(
                    Paragraph(
                        f"  Tahmini Süre: {oneri.get('tahmini_sure', 'Belirtilmemiş')}",
                        self.styles["CustomBullet"],
                    )
                )

        # Genel öneriler
        story.append(Spacer(1, 0.3 * inch))
        story.append(
            Paragraph("[BOOKS] Genel Çalışma Önerileri", self.styles["CustomHeading2"])
        )

        genel_oneriler = [
            "Düzenli çalışma programı oluşturun ve takip edin",
            "Zayıf konularınıza daha fazla zaman ayırın",
            "Öğrenme stilinize uygun materyaller kullanın",
            "Grup çalışması ve bireysel çalışmayı dengeleyin",
            "Türkçe morfoloji farkındalığınızı geliştirin",
            "Düzenli deneme sınavları çözerek ilerlemenizi takip edin",
        ]

        for oneri in genel_oneriler:
            story.append(Paragraph(f"• {oneri}", self.styles["CustomBullet"]))

        return story
