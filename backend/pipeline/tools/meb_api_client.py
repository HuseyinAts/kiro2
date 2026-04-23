"""
MEB API Client
Milli Eğitim Bakanlığı müfredat ve kazanım API istemcisi

YKS Ders ve Kazanım Yapısı:
- TYT: Türkçe, Matematik, Sosyal, Fen
- AYT: Alan dersleri
"""

from typing import Any

from pydantic import BaseModel


class Kazanim(BaseModel):
    """MEB kazanım modeli"""
    kazanim_id: str
    kazanim_kodu: str
    kazanim_text: str
    ders: str
    sinif: int
    unite: str
    konu: str
    alt_konu: str | None = None
    bloom_seviyesi: str
    sure_dk: int = 45


class Konu(BaseModel):
    """MEB konu modeli"""
    konu_id: str
    konu_adi: str
    ders: str
    sinif: int
    unite: str
    kazanimlar: list[str] = []


class MEBApiClient:
    """
    MEB Müfredat API İstemcisi

    YKS müfredatı ve kazanım bilgilerine erişim sağlar.
    Mock data ile çalışır - gerçek MEB API entegrasyonu eklenebilir.
    """

    # YKS Dersleri
    TYT_DERSLER = ["türkçe", "matematik", "sosyal", "fen"]
    AYT_SAY_DERSLER = ["matematik", "fizik", "kimya", "biyoloji"]
    AYT_EA_DERSLER = ["matematik", "edebiyat", "tarih", "coğrafya"]
    AYT_SOZ_DERSLER = ["edebiyat", "tarih", "coğrafya", "felsefe"]

    # Bloom Taxonomy Seviyeleri
    BLOOM_LEVELS = [
        "hatırlama",
        "anlama",
        "uygulama",
        "analiz",
        "sentez",
        "değerlendirme"
    ]

    # Örnek kazanımlar (Mock data)
    SAMPLE_KAZANIMLAR = {
        "matematik": [
            {
                "kazanim_id": "M.10.1.1.1",
                "kazanim_kodu": "M.10.1.1.1",
                "kazanim_text": "İkinci dereceden bir bilinmeyenli denklemleri çözer",
                "ders": "matematik",
                "sinif": 10,
                "unite": "Polinomlar",
                "konu": "İkinci Dereceden Denklemler",
                "bloom_seviyesi": "uygulama",
                "sure_dk": 45
            },
            {
                "kazanim_id": "M.10.2.1.1",
                "kazanim_kodu": "M.10.2.1.1",
                "kazanim_text": "Parabol grafiğini çizer ve özelliklerini belirler",
                "ders": "matematik",
                "sinif": 10,
                "unite": "Fonksiyonlar",
                "konu": "Parabol",
                "bloom_seviyesi": "analiz",
                "sure_dk": 60
            },
            {
                "kazanim_id": "M.11.3.1.1",
                "kazanim_kodu": "M.11.3.1.1",
                "kazanim_text": "Trigonometrik fonksiyonları tanımlar ve grafiklerini çizer",
                "ders": "matematik",
                "sinif": 11,
                "unite": "Trigonometri",
                "konu": "Trigonometrik Fonksiyonlar",
                "bloom_seviyesi": "uygulama",
                "sure_dk": 90
            }
        ],
        "fizik": [
            {
                "kazanim_id": "F.10.1.1.1",
                "kazanim_kodu": "F.10.1.1.1",
                "kazanim_text": "Newton'un hareket yasalarını açıklar",
                "ders": "fizik",
                "sinif": 10,
                "unite": "Kuvvet ve Hareket",
                "konu": "Newton Yasaları",
                "bloom_seviyesi": "anlama",
                "sure_dk": 45
            },
            {
                "kazanim_id": "F.11.2.1.1",
                "kazanim_kodu": "F.11.2.1.1",
                "kazanim_text": "Elektrik alan ve potansiyel kavramlarını açıklar",
                "ders": "fizik",
                "sinif": 11,
                "unite": "Elektrik",
                "konu": "Elektrik Alan",
                "bloom_seviyesi": "analiz",
                "sure_dk": 60
            }
        ],
        "türkçe": [
            {
                "kazanim_id": "T.9.1.1.1",
                "kazanim_kodu": "T.9.1.1.1",
                "kazanim_text": "Metinde geçen kelime ve kelime gruplarının anlamlarını belirler",
                "ders": "türkçe",
                "sinif": 9,
                "unite": "Okuma",
                "konu": "Sözcük Bilgisi",
                "bloom_seviyesi": "anlama",
                "sure_dk": 30
            }
        ]
    }

    def __init__(self, api_base_url: str | None = None, api_key: str | None = None):
        """
        MEB API Client başlat

        Args:
            api_base_url: API base URL (mock için None)
            api_key: API anahtarı (mock için None)
        """
        self.api_base_url = api_base_url
        self.api_key = api_key
        self._cache: dict[str, Any] = {}

    async def get_kazanim(self, kazanim_id: str) -> Kazanim | None:
        """
        Kazanım ID'ye göre kazanım bilgisi getir

        Args:
            kazanim_id: Kazanım ID (örn: M.10.1.1.1)

        Returns:
            Optional[Kazanim]: Kazanım bilgisi
        """
        # Cache kontrolü
        cache_key = f"kazanim:{kazanim_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Mock data'dan ara
        for ders, kazanimlar in self.SAMPLE_KAZANIMLAR.items():
            for k in kazanimlar:
                if k["kazanim_id"] == kazanim_id:
                    kazanim = Kazanim(**k)
                    self._cache[cache_key] = kazanim
                    return kazanim

        return None

    async def get_kazanimlar_by_konu(
        self,
        ders: str,
        konu: str,
        sinif: int | None = None
    ) -> list[Kazanim]:
        """
        Konu ve derse göre kazanımları getir

        Args:
            ders: Ders adı
            konu: Konu adı
            sinif: Sınıf seviyesi (opsiyonel)

        Returns:
            List[Kazanim]: Kazanım listesi
        """
        results = []
        ders_lower = ders.lower()

        if ders_lower in self.SAMPLE_KAZANIMLAR:
            for k in self.SAMPLE_KAZANIMLAR[ders_lower]:
                if konu.lower() in k["konu"].lower():
                    if sinif is None or k["sinif"] == sinif:
                        results.append(Kazanim(**k))

        return results

    async def get_konular_by_ders(self, ders: str, sinif: int | None = None) -> list[Konu]:
        """
        Derse göre konuları getir

        Args:
            ders: Ders adı
            sinif: Sınıf seviyesi (opsiyonel)

        Returns:
            List[Konu]: Konu listesi
        """
        konular = []
        ders_lower = ders.lower()
        konu_set = set()

        if ders_lower in self.SAMPLE_KAZANIMLAR:
            for k in self.SAMPLE_KAZANIMLAR[ders_lower]:
                if sinif is None or k["sinif"] == sinif:
                    konu_key = f"{k['ders']}:{k['konu']}:{k['sinif']}"
                    if konu_key not in konu_set:
                        konu_set.add(konu_key)
                        konular.append(Konu(
                            konu_id=f"{k['ders']}_{k['konu'].replace(' ', '_')}",
                            konu_adi=k["konu"],
                            ders=k["ders"],
                            sinif=k["sinif"],
                            unite=k["unite"],
                            kazanimlar=[k["kazanim_id"]]
                        ))

        return konular

    async def analyze_kazanim_bloom_level(self, kazanim_text: str) -> str:
        """
        Kazanım metninden Bloom taxonomy seviyesini analiz et

        Args:
            kazanim_text: Kazanım metni

        Returns:
            str: Bloom seviyesi
        """
        kazanim_lower = kazanim_text.lower()

        # Anahtar kelimeler
        bloom_keywords = {
            "hatırlama": ["tanımlar", "listeler", "adlandırır", "tanır", "hatırlar"],
            "anlama": ["açıklar", "özetler", "yorumlar", "karşılaştırır", "sınıflandırır"],
            "uygulama": ["çözer", "uygular", "hesaplar", "gösterir", "kullanır"],
            "analiz": ["analiz eder", "inceler", "ayırır", "ilişkilendirir", "çizer"],
            "sentez": ["tasarlar", "oluşturur", "planlar", "üretir", "geliştirir"],
            "değerlendirme": ["değerlendirir", "eleştirir", "savunur", "yargılar", "karar verir"]
        }

        for level, keywords in bloom_keywords.items():
            for keyword in keywords:
                if keyword in kazanim_lower:
                    return level

        # Varsayılan
        return "anlama"

    async def get_related_kazanimlar(self, kazanim_id: str, limit: int = 5) -> list[Kazanim]:
        """
        İlişkili kazanımları getir

        Args:
            kazanim_id: Kaynak kazanım ID
            limit: Maksimum sonuç sayısı

        Returns:
            List[Kazanim]: İlişkili kazanımlar
        """
        source = await self.get_kazanim(kazanim_id)
        if not source:
            return []

        results = []
        for ders, kazanimlar in self.SAMPLE_KAZANIMLAR.items():
            for k in kazanimlar:
                if k["kazanim_id"] != kazanim_id:
                    # Aynı ders ve benzer konu
                    if k["ders"] == source.ders and k["unite"] == source.unite:
                        results.append(Kazanim(**k))

        return results[:limit]

    def get_bloom_level_weight(self, bloom_level: str) -> float:
        """
        Bloom seviyesi ağırlığını döndür

        Args:
            bloom_level: Bloom seviyesi

        Returns:
            float: Ağırlık (0-1)
        """
        weights = {
            "hatırlama": 0.10,
            "anlama": 0.15,
            "uygulama": 0.25,
            "analiz": 0.25,
            "sentez": 0.15,
            "değerlendirme": 0.10
        }
        return weights.get(bloom_level.lower(), 0.15)

    def suggest_difficulty_for_bloom(self, bloom_level: str) -> str:
        """
        Bloom seviyesine göre zorluk öner

        Args:
            bloom_level: Bloom seviyesi

        Returns:
            str: Önerilen zorluk
        """
        difficulty_map = {
            "hatırlama": "kolay",
            "anlama": "kolay",
            "uygulama": "orta",
            "analiz": "orta",
            "sentez": "zor",
            "değerlendirme": "zor"
        }
        return difficulty_map.get(bloom_level.lower(), "orta")
