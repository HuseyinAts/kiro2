import random
from typing import Any, ClassVar


class MotivationGenerator:
    """
    Phase 10: Growth Mindset Tabanlı Motivasyon Jeneratörü
    Öğrencinin son performans verilerine göre pedagojik, psikolojik esnekliği
    destekleyen ve toksik olmayan (şefkatli, veriye dayalı) bildirimler üretir.
    """

    SUCCESS_TEMPLATES: ClassVar[list[str]] = [
        "Son {days} günde {subject} dersinde %{improvement} ilerleme kaydettin. Aynı tempoyu küçük adımlarla sürdürebilirsin.",
        "{subject} konusundaki son çaban sonuç verdi. Hatalarından öğrenme stratejin işe yarıyor.",
        "Hedefine doğru attığın bu adım, doğru çalışma yöntemini bulduğunu gösteriyor. Harika bir ivme!",
    ]

    DROP_TEMPLATES: ClassVar[list[str]] = [
        "Son denemede beklediğin sonucu alamamış olabilirsin, ancak hataların sana eksiklerini gösteren en iyi rehberdir. Bugün küçük bir tekrarla başlayalım.",
        "{subject} netlerindeki dalgalanma çok normal. Öğrenme süreci her zaman düz bir çizgi değildir; zayıf noktalarını tespit edip güçlendirme fırsatın var.",
        "Sonucun seni tanımlamaz, sadece şu anki stratejini yansıtır. Farklı bir yöntemle {subject} konusuna yaklaşmayı deneyebiliriz.",
    ]

    STREAK_TEMPLATES: ClassVar[list[str]] = [
        "{streak} gündür aralıksız çalışıyorsun, istikrarın zekadan daha güçlü olduğunu kanıtlıyorsun.",
        "Düzenli eforun ({streak} gün) sana kalıcı bir altyapı inşa ediyor. Küçük adımların büyük sonuçlar doğuracak.",
        "Bugün de masaya oturdun. Bu {streak}. günün. Sürece duyduğun bu saygı en büyük başarın.",
    ]

    NEUTRAL_TEMPLATES: ClassVar[list[str]] = [
        "Her yeni soru, beynindeki yeni bir nöral bağdır. Bugünü verimli geçirmeye odaklan.",
        "Öğrenmek bir maratondur. Bugün kendine yapacağın en küçük yatırım bile çok değerli.",
        "Sonuçlara değil, sürece odaklan. Bugün dünden bir bilgi daha fazla biliyorsan, kazanmışsındır.",
    ]

    @classmethod
    def generate_daily_message(cls, metrics: dict[str, Any]) -> str:
        """
        metrics:
            - streak (int): Öğrencinin kaç gündür aralıksız girdiği
            - recent_improvement (float): Son net artışı (yüzde veya puan bazında)
            - focus_subject (str): Öğrencinin son çalıştığı ders
            - has_dropped (bool): Netlerinde son zamanda belirgin bir düşüş var mı?
        """
        streak = metrics.get("streak", 0)
        recent_improvement = metrics.get("recent_improvement", 0.0)
        has_dropped = metrics.get("has_dropped", False)
        subject = metrics.get("focus_subject", "çalışmalarında")
        days = metrics.get("days", 3)

        # 1. Öncelik: Düşüş yaşayan öğrenciyi "toparlamak" (Compassion)
        if has_dropped:
            msg = random.choice(cls.DROP_TEMPLATES)  # nosec B311  # sablon secimi, kripto degil
            return msg.format(subject=subject)

        # 2. Öncelik: Belirgin bir artış varsa (Positive Reinforcement)
        if recent_improvement > 5.0:
            msg = random.choice(cls.SUCCESS_TEMPLATES)  # nosec B311  # sablon secimi, kripto degil
            return msg.format(
                subject=subject, improvement=int(recent_improvement), days=days
            )

        # 3. Öncelik: Sadece çok istikrarlıysa (Consistency)
        if streak >= 3:
            msg = random.choice(cls.STREAK_TEMPLATES)  # nosec B311  # sablon secimi, kripto degil
            return msg.format(streak=streak)

        # 4. Fallback (Neutral)
        return random.choice(cls.NEUTRAL_TEMPLATES)  # nosec B311  # sablon secimi, kripto degil
