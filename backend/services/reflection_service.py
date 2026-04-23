"""
Claude Diary Plugin - Reflection Service

Guided reflection ve depth measurement servisi (REQ-3).
Yansitma sorulari, derinlik olcumu ve ogrenim cikartma.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.diary import (
    ReflectionCreate,
    ReflectionPromptsResponse,
)
from models.diary import Reflection, ReflectionDepth


class ReflectionService:
    """
    Reflection servisi (REQ-3)

    Guided reflection:
    - Guided questions (REQ-3.1)
    - "What went well?" analysis (REQ-3.2)
    - "What could improve?" identification (REQ-3.3)
    - "What did I learn?" extraction (REQ-3.4)
    - "What will I do differently?" planning (REQ-3.5)
    - Depth measurement (REQ-3.6)
    """

    # Reflection prompts (Turkce)
    PROMPTS = {
        "what_went_well": [
            "Bugün iyi giden şeyler nelerdi?",
            "Hangi görevlerde başarılı oldunuz?",
            "Gurur duyduğunuz bir an var mıydı?",
            "Bugün size enerji veren ne oldu?",
        ],
        "what_could_improve": [
            "Daha iyi yapabilecek olsaydınız ne değiştirirdiniz?",
            "Hangi konularda zorlandınız?",
            "Gelecek sefer nelere dikkat etmelisiniz?",
            "Hangi engeller sizi yavaşlattı?",
        ],
        "what_did_i_learn": [
            "Bugün ne öğrendiniz?",
            "Yeni keşfettiğiniz bir şey var mı?",
            "Hangi becerilerinizi geliştirdiniz?",
            "Şaşırtıcı bir içgörü edindiniz mi?",
        ],
        "what_will_i_do_differently": [
            "Yarın farklı ne yapacaksınız?",
            "Bugünün derslerini nasıl uygulayacaksınız?",
            "Hangi alışkanlığı değiştirmek istiyorsunuz?",
            "Bir sonraki adımınız ne olacak?",
        ],
    }

    # Depth indicators (deep thinking keywords)
    DEEP_INDICATORS = [
        "farkettim", "farketmek", "anladim", "anladım", "dusundum", "düşündüm",
        "nedeni", "sebebi", "cunku", "çünkü", "aslinda", "aslında",
        "onemli", "önemli", "gelecekte", "iliskili", "ilişkili",
        "stratejik", "planlama", "uzun vadede", "perspektif",
        "varsayim", "varsayım", "hipotez", "analiz", "sentez",
        "deger", "değer", "anlam", "amac", "amaç", "motivasyon",
        "kendimi", "ic goru", "içgörü", "farkindalik", "farkındalık",
    ]

    # Surface indicators (shallow response keywords)
    SURFACE_INDICATORS = [
        "iyi", "kotu", "kötü", "normal", "tamam", "ok", "evet", "hayir", "hayır",
        "yaptim", "yaptım", "ettim", "tamamladim", "tamamladım", "bitti",
    ]

    def __init__(self, db: AsyncSession):
        """
        Initialize ReflectionService.

        Args:
            db: AsyncSession - SQLAlchemy async session
        """
        self.db = db

    # =========================================================================
    # REQ-3.1: Guided Questions
    # =========================================================================

    def get_prompts(
        self,
        context: dict[str, Any] | None = None,
        category: str | None = None,
    ) -> ReflectionPromptsResponse:
        """
        Guided reflection sorularini getir (REQ-3.1).

        Args:
            context: Optional[Dict] - Baglam bilgisi (orn. gunluk ozet)
            category: Optional[str] - Soru kategorisi

        Returns:
            ReflectionPromptsResponse - Sorular ve ipuclari
        """
        prompts: list[str] = []
        context_hints: dict[str, str] = {}

        # Kategori belirtilmisse
        if category and category in self.PROMPTS:
            prompts = self.PROMPTS[category]
        else:
            # Tum kategorilerden birer soru
            prompts = [
                self.PROMPTS["what_went_well"][0],
                self.PROMPTS["what_could_improve"][0],
                self.PROMPTS["what_did_i_learn"][0],
                self.PROMPTS["what_will_i_do_differently"][0],
            ]

        # Context'e gore ipuclari
        if context:
            if context.get("success_count", 0) > 0:
                context_hints["success"] = (
                    f"Bugün {context['success_count']} görev başarıyla tamamlandı."
                )
            if context.get("challenges"):
                context_hints["challenges"] = (
                    f"Karşılaşılan zorluklar: {', '.join(context['challenges'][:2])}"
                )
            if context.get("learnings"):
                context_hints["learnings"] = (
                    f"Kaydedilen öğrenimler: {len(context['learnings'])} adet"
                )

        return ReflectionPromptsResponse(
            prompts=prompts,
            context_hints=context_hints if context_hints else None
        )

    def get_all_prompts(self) -> dict[str, list[str]]:
        """
        Tum reflection sorularini getir.

        Returns:
            Dict[str, List[str]] - Kategorize edilmis sorular
        """
        return self.PROMPTS.copy()

    # =========================================================================
    # REQ-3.6: Depth Measurement
    # =========================================================================

    def measure_depth(
        self,
        responses: ReflectionCreate,
    ) -> tuple[ReflectionDepth, float]:
        """
        Reflection derinligini olc (REQ-3.6).

        Surface vs deep thinking ratio.

        Args:
            responses: ReflectionCreate - Yansitma yanitlari

        Returns:
            Tuple[ReflectionDepth, float] - Derinlik seviyesi ve skor
        """
        all_text = " ".join([
            responses.what_went_well or "",
            responses.what_could_improve or "",
            responses.what_did_i_learn or "",
            responses.what_will_i_do_differently or "",
            responses.additional_notes or "",
        ]).lower()

        if not all_text.strip():
            return ReflectionDepth.SURFACE, 0.0

        # Kelime sayisi
        word_count = len(all_text.split())

        # Deep indicator sayisi
        deep_count = sum(1 for ind in self.DEEP_INDICATORS if ind in all_text)

        # Surface indicator sayisi
        surface_count = sum(1 for ind in self.SURFACE_INDICATORS if ind in all_text)

        # Cumle uzunlugu (ortalama)
        sentences = [s.strip() for s in all_text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

        # Depth score hesaplama (0-1)
        depth_score = 0.0

        # Kelime sayisi etkisi (max 0.3)
        if word_count >= 100:
            depth_score += 0.3
        elif word_count >= 50:
            depth_score += 0.2
        elif word_count >= 20:
            depth_score += 0.1

        # Deep indicator etkisi (max 0.4)
        depth_score += min(deep_count * 0.05, 0.4)

        # Surface indicator negatif etkisi (max -0.2)
        depth_score -= min(surface_count * 0.02, 0.2)

        # Cumle uzunlugu etkisi (max 0.3)
        if avg_sentence_length >= 15:
            depth_score += 0.3
        elif avg_sentence_length >= 10:
            depth_score += 0.2
        elif avg_sentence_length >= 6:
            depth_score += 0.1

        # 0-1 arasina normalize et
        depth_score = max(0.0, min(1.0, depth_score))

        # Depth seviyesi belirle
        if depth_score >= 0.7:
            depth = ReflectionDepth.DEEP
        elif depth_score >= 0.4:
            depth = ReflectionDepth.MODERATE
        else:
            depth = ReflectionDepth.SURFACE

        return depth, round(depth_score, 3)

    # =========================================================================
    # REQ-3.4: Learning Extraction
    # =========================================================================

    def extract_learnings(self, responses: ReflectionCreate) -> list[str]:
        """
        Yanitlardan ogrenimleri cikar (REQ-3.4).

        Args:
            responses: ReflectionCreate - Yansitma yanitlari

        Returns:
            List[str] - Cikarilan ogrenimler
        """
        learnings: list[str] = []

        # "What did I learn?" yaniti
        if responses.what_did_i_learn:
            # Cumlelere bol
            sentences = [
                s.strip()
                for s in responses.what_did_i_learn.replace("!", ".").replace("?", ".").split(".")
                if s.strip() and len(s.strip()) > 10
            ]
            learnings.extend(sentences[:3])

        # Diger yanitlardan ogrenim cikar
        learning_keywords = ["ogrendim", "öğrendim", "farkettim", "farketim", "anladim", "anladım", "kesfettim", "keşfettim"]

        for text in [responses.what_went_well, responses.what_could_improve, responses.additional_notes]:
            if text:
                text_lower = text.lower()
                for keyword in learning_keywords:
                    if keyword in text_lower:
                        # Keyword iceren cumleyi bul
                        sentences = text.split(".")
                        for sent in sentences:
                            if keyword in sent.lower() and len(sent.strip()) > 10:
                                learnings.append(sent.strip())
                                break

        # Benzersiz ve maksimum 5
        unique_learnings = []
        for learning in learnings:
            if learning not in unique_learnings:
                unique_learnings.append(learning)

        return unique_learnings[:5]

    # =========================================================================
    # REQ-3.5: Action Items Extraction
    # =========================================================================

    def extract_action_items(self, responses: ReflectionCreate) -> list[str]:
        """
        Yanitlardan aksiyon ogelerini cikar (REQ-3.5).

        Args:
            responses: ReflectionCreate - Yansitma yanitlari

        Returns:
            List[str] - Aksiyon ogeleri
        """
        action_items: list[str] = []

        # "What will I do differently?" yaniti
        if responses.what_will_i_do_differently:
            sentences = [
                s.strip()
                for s in responses.what_will_i_do_differently.replace("!", ".").replace("?", ".").split(".")
                if s.strip() and len(s.strip()) > 10
            ]
            action_items.extend(sentences[:3])

        # Aksiyon anahtar kelimeleri
        action_keywords = [
            "yapacagim", "yapacağım", "edecegim", "edeceğim",
            "deneyecegim", "deneyeceğim", "baslayacagim", "başlayacağım",
            "odaklanacagim", "odaklanacağım", "calisacagim", "çalışacağım",
        ]

        for text in [responses.what_could_improve, responses.additional_notes]:
            if text:
                text_lower = text.lower()
                for keyword in action_keywords:
                    if keyword in text_lower:
                        sentences = text.split(".")
                        for sent in sentences:
                            if keyword in sent.lower() and len(sent.strip()) > 10:
                                action_items.append(sent.strip())
                                break

        # Benzersiz ve maksimum 5
        unique_items = []
        for item in action_items:
            if item not in unique_items:
                unique_items.append(item)

        return unique_items[:5]

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def create_reflection(
        self,
        user_id: UUID,
        data: ReflectionCreate,
    ) -> Reflection:
        """
        Yeni reflection olustur.

        Args:
            user_id: UUID - Kullanici ID
            data: ReflectionCreate - Reflection verileri

        Returns:
            Reflection - Olusturulan reflection
        """
        # Depth olc
        depth, depth_score = self.measure_depth(data)

        # Ogrenimleri cikar
        learnings = self.extract_learnings(data)

        # Aksiyonlari cikar
        action_items = self.extract_action_items(data)

        reflection = Reflection(
            user_id=user_id,
            diary_entry_id=data.diary_entry_id,
            what_went_well=data.what_went_well,
            what_could_improve=data.what_could_improve,
            what_did_i_learn=data.what_did_i_learn,
            what_will_i_do_differently=data.what_will_i_do_differently,
            additional_notes=data.additional_notes,
            depth=depth,
            depth_score=depth_score,
            extracted_learnings=learnings,
            action_items=action_items,
        )

        self.db.add(reflection)
        await self.db.commit()
        await self.db.refresh(reflection)

        return reflection

    async def get_reflections(
        self,
        user_id: UUID,
        diary_entry_id: UUID | None = None,
        depth: ReflectionDepth | None = None,
        limit: int = 20,
    ) -> list[Reflection]:
        """
        Reflection'lari getir.

        Args:
            user_id: UUID - Kullanici ID
            diary_entry_id: Optional[UUID] - Diary entry ID filtresi
            depth: Optional[ReflectionDepth] - Depth filtresi
            limit: int - Maksimum kayit sayisi

        Returns:
            List[Reflection] - Reflection listesi
        """
        conditions = [Reflection.user_id == user_id]

        if diary_entry_id:
            conditions.append(Reflection.diary_entry_id == diary_entry_id)

        if depth:
            conditions.append(Reflection.depth == depth)

        query = (
            select(Reflection)
            .where(and_(*conditions))
            .order_by(desc(Reflection.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_reflection_by_id(
        self,
        reflection_id: UUID,
        user_id: UUID,
    ) -> Reflection | None:
        """
        ID ile reflection getir.

        Args:
            reflection_id: UUID - Reflection ID
            user_id: UUID - Kullanici ID

        Returns:
            Optional[Reflection] - Reflection veya None
        """
        query = select(Reflection).where(
            and_(
                Reflection.id == reflection_id,
                Reflection.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_reflection(
        self,
        reflection_id: UUID,
        user_id: UUID,
        data: ReflectionCreate,
    ) -> Reflection | None:
        """
        Reflection guncelle.

        Args:
            reflection_id: UUID - Reflection ID
            user_id: UUID - Kullanici ID
            data: ReflectionCreate - Yeni veriler

        Returns:
            Optional[Reflection] - Guncellenmis reflection veya None
        """
        reflection = await self.get_reflection_by_id(reflection_id, user_id)
        if not reflection:
            return None

        # Alanlari guncelle
        reflection.what_went_well = data.what_went_well
        reflection.what_could_improve = data.what_could_improve
        reflection.what_did_i_learn = data.what_did_i_learn
        reflection.what_will_i_do_differently = data.what_will_i_do_differently
        reflection.additional_notes = data.additional_notes

        # Depth yeniden hesapla
        depth, depth_score = self.measure_depth(data)
        reflection.depth = depth
        reflection.depth_score = depth_score

        # Ogrenimleri yeniden cikar
        reflection.extracted_learnings = self.extract_learnings(data)
        reflection.action_items = self.extract_action_items(data)

        await self.db.commit()
        await self.db.refresh(reflection)

        return reflection

    async def delete_reflection(
        self,
        reflection_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Reflection sil.

        Args:
            reflection_id: UUID - Reflection ID
            user_id: UUID - Kullanici ID

        Returns:
            bool - Basari durumu
        """
        reflection = await self.get_reflection_by_id(reflection_id, user_id)
        if not reflection:
            return False

        await self.db.delete(reflection)
        await self.db.commit()
        return True

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_depth_statistics(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Depth istatistiklerini getir.

        Args:
            user_id: UUID - Kullanici ID
            days: int - Gun sayisi

        Returns:
            Dict - Depth istatistikleri
        """
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)

        query = select(Reflection).where(
            and_(
                Reflection.user_id == user_id,
                Reflection.created_at >= start_date
            )
        )

        result = await self.db.execute(query)
        reflections = list(result.scalars().all())

        if not reflections:
            return {
                "total_reflections": 0,
                "surface_count": 0,
                "moderate_count": 0,
                "deep_count": 0,
                "average_depth_score": 0.0,
                "depth_trend": "stable",
            }

        surface_count = sum(1 for r in reflections if r.depth == ReflectionDepth.SURFACE)
        moderate_count = sum(1 for r in reflections if r.depth == ReflectionDepth.MODERATE)
        deep_count = sum(1 for r in reflections if r.depth == ReflectionDepth.DEEP)

        avg_score = sum(r.depth_score for r in reflections) / len(reflections)

        # Trend analizi (son 7 gun vs onceki 7 gun)
        recent_reflections = [r for r in reflections if r.created_at >= datetime.now() - timedelta(days=7)]
        older_reflections = [r for r in reflections if r.created_at < datetime.now() - timedelta(days=7)]

        trend = "stable"
        if recent_reflections and older_reflections:
            recent_avg = sum(r.depth_score for r in recent_reflections) / len(recent_reflections)
            older_avg = sum(r.depth_score for r in older_reflections) / len(older_reflections)

            if recent_avg > older_avg + 0.1:
                trend = "improving"
            elif recent_avg < older_avg - 0.1:
                trend = "declining"

        return {
            "total_reflections": len(reflections),
            "surface_count": surface_count,
            "moderate_count": moderate_count,
            "deep_count": deep_count,
            "surface_percentage": round(surface_count / len(reflections) * 100, 1),
            "moderate_percentage": round(moderate_count / len(reflections) * 100, 1),
            "deep_percentage": round(deep_count / len(reflections) * 100, 1),
            "average_depth_score": round(avg_score, 3),
            "depth_trend": trend,
        }
