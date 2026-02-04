"""
Soru bankası yönetimi API endpoint'leri
Gerçek soru verileri ve IRT kalibrasyonu yönetimi
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core.dependencies import get_current_user
from data.question_bank_data import QuestionBankData
from services.irt_calibration_service import IRTCalibrationService
from services.soru_bankasi_service import SoruBankasiServisi

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/question-bank", tags=["Question Bank Management"])


# Pydantic modelleri
class QuestionCreateRequest(BaseModel):
    """Soru oluşturma isteği"""

    soru_metni: str = Field(..., description="Soru metni")
    secenekler: List[str] = Field(
        ..., min_items=4, max_items=5, description="Soru seçenekleri"
    )
    dogru_cevap: str = Field(..., description="Doğru cevap (A, B, C, D, E)")
    konu: str = Field(..., description="Soru konusu")
    alt_konu: Optional[str] = Field(None, description="Alt konu")
    zorluk_seviyesi: str = Field(..., description="Zorluk seviyesi (kolay, orta, zor)")
    sinav_tipi: str = Field(..., description="Sınav türü (TYT, AYT, YDT)")
    cozum_aciklamasi: Optional[str] = Field(None, description="Çözüm açıklaması")


class QuestionUpdateRequest(BaseModel):
    """Soru güncelleme isteği"""

    soru_metni: Optional[str] = None
    secenekler: Optional[List[str]] = None
    dogru_cevap: Optional[str] = None
    konu: Optional[str] = None
    alt_konu: Optional[str] = None
    zorluk_seviyesi: Optional[str] = None
    cozum_aciklamasi: Optional[str] = None


class IRTCalibrationRequest(BaseModel):
    """IRT kalibrasyon isteği"""

    question_ids: List[str] = Field(..., description="Kalibre edilecek soru ID'leri")
    include_morphology: bool = Field(
        True, description="Morfoloji analizi dahil edilsin mi"
    )
    batch_size: int = Field(50, description="Batch boyutu")


class BulkImportRequest(BaseModel):
    """Toplu soru import isteği"""

    exam_type: str = Field(..., description="Sınav türü (TYT, AYT, YDT)")
    overwrite_existing: bool = Field(False, description="Mevcut soruları üzerine yaz")


class QuestionResponse(BaseModel):
    """Soru yanıt modeli"""

    id: str
    question_text: str
    options: List[str]
    correct_answer: str
    subject: str
    topic: str
    difficulty: str
    exam_type: str
    irt_parameters: Optional[Dict[str, float]] = None
    morphology_complexity: Optional[float] = None
    readability_score: Optional[float] = None
    created_at: datetime
    is_active: bool


# Dependency'ler
async def get_soru_bankasi_service() -> SoruBankasiServisi:
    """Soru bankası servisi dependency"""
    return SoruBankasiServisi()


async def get_irt_service() -> IRTCalibrationService:
    """IRT kalibrasyon servisi dependency"""
    return IRTCalibrationService()


async def get_question_data() -> QuestionBankData:
    """Soru veri servisi dependency"""
    return QuestionBankData()


# API Endpoint'leri
@router.get("/statistics", response_model=Dict[str, Any])
async def get_question_bank_statistics(
    soru_service: SoruBankasiServisi = Depends(get_soru_bankasi_service),
):
    """
    Soru bankası istatistiklerini getir

    Returns:
        Dict: Detaylı soru bankası istatistikleri
    """
    try:
        stats = await soru_service.istatistikler_getir()

        # Ek istatistikler
        question_data = QuestionBankData()
        data_stats = question_data.get_statistics()

        combined_stats = {
            **stats,
            "veri_kaynaği_istatistikleri": data_stats,
            "son_guncelleme": datetime.now().isoformat(),
        }

        return combined_stats

    except Exception as e:
        logger.error(f"İstatistik getirme hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"İstatistik getirme hatası: {str(e)}"
        )


@router.get("/questions", response_model=List[QuestionResponse])
async def list_questions(
    exam_type: Optional[str] = Query(None, description="Sınav türü filtresi"),
    subject: Optional[str] = Query(None, description="Konu filtresi"),
    difficulty: Optional[str] = Query(None, description="Zorluk filtresi"),
    limit: int = Query(100, ge=1, le=500, description="Maksimum soru sayısı"),
    offset: int = Query(0, ge=0, description="Başlangıç offset'i"),
    soru_service: SoruBankasiServisi = Depends(get_soru_bankasi_service),
):
    """
    Filtrelere göre soru listesi getir

    Args:
        exam_type: Sınav türü (TYT, AYT, YDT)
        subject: Konu filtresi
        difficulty: Zorluk filtresi (kolay, orta, zor)
        limit: Maksimum soru sayısı
        offset: Başlangıç offset'i

    Returns:
        List[QuestionResponse]: Filtrelenmiş soru listesi
    """
    try:
        questions = await soru_service.sorular_listele(
            sinav_tipi=exam_type,
            konu=subject,
            zorluk_seviyesi=difficulty,
            limit=limit,
            offset=offset,
        )

        # Response formatına dönüştür
        response_questions = []
        for question in questions:
            response_questions.append(
                QuestionResponse(
                    id=str(question.id),
                    question_text=question.question_text,
                    options=[
                        f"A) {question.option_a}",
                        f"B) {question.option_b}",
                        f"C) {question.option_c}",
                        f"D) {question.option_d}",
                        f"E) {question.option_e}" if question.option_e else None,
                    ],
                    correct_answer=question.correct_answer,
                    subject=question.subject_area.value,
                    topic=question.topic,
                    difficulty=question.difficulty.value,
                    exam_type=question.exam_type.value,
                    irt_parameters={
                        "difficulty": question.irt_difficulty,
                        "discrimination": question.irt_discrimination,
                        "guessing": question.irt_guessing,
                    }
                    if question.irt_difficulty is not None
                    else None,
                    morphology_complexity=question.morphology_complexity,
                    readability_score=question.readability_score,
                    created_at=question.created_at,
                    is_active=question.is_active,
                )
            )

        return response_questions

    except Exception as e:
        logger.error(f"Soru listeleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Soru listeleme hatası: {str(e)}")


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: str,
    soru_service: SoruBankasiServisi = Depends(get_soru_bankasi_service),
):
    """
    Belirli bir soruyu getir

    Args:
        question_id: Soru ID'si

    Returns:
        QuestionResponse: Soru detayları
    """
    try:
        question = await soru_service.soru_getir(question_id)

        if not question:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")

        return QuestionResponse(
            id=str(question.id),
            question_text=question.question_text,
            options=[
                f"A) {question.option_a}",
                f"B) {question.option_b}",
                f"C) {question.option_c}",
                f"D) {question.option_d}",
                f"E) {question.option_e}" if question.option_e else None,
            ],
            correct_answer=question.correct_answer,
            subject=question.subject_area.value,
            topic=question.topic,
            difficulty=question.difficulty.value,
            exam_type=question.exam_type.value,
            irt_parameters={
                "difficulty": question.irt_difficulty,
                "discrimination": question.irt_discrimination,
                "guessing": question.irt_guessing,
            }
            if question.irt_difficulty is not None
            else None,
            morphology_complexity=question.morphology_complexity,
            readability_score=question.readability_score,
            created_at=question.created_at,
            is_active=question.is_active,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Soru getirme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Soru getirme hatası: {str(e)}")


@router.post("/questions", response_model=QuestionResponse)
async def create_question(
    request: QuestionCreateRequest,
    soru_service: SoruBankasiServisi = Depends(get_soru_bankasi_service),
    current_user=Depends(get_current_user),
):
    """
    Yeni soru oluştur

    Args:
        request: Soru oluşturma isteği

    Returns:
        QuestionResponse: Oluşturulan soru
    """
    try:
        # Request'i dict'e dönüştür
        soru_data = request.dict()
        soru_data["created_by"] = current_user.get("user_id", "unknown")

        # Soru oluştur
        question = await soru_service.soru_ekle(soru_data)

        return QuestionResponse(
            id=str(question.id),
            question_text=question.question_text,
            options=[
                f"A) {question.option_a}",
                f"B) {question.option_b}",
                f"C) {question.option_c}",
                f"D) {question.option_d}",
                f"E) {question.option_e}" if question.option_e else None,
            ],
            correct_answer=question.correct_answer,
            subject=question.subject_area.value,
            topic=question.topic,
            difficulty=question.difficulty.value,
            exam_type=question.exam_type.value,
            irt_parameters={
                "difficulty": question.irt_difficulty,
                "discrimination": question.irt_discrimination,
                "guessing": question.irt_guessing,
            }
            if question.irt_difficulty is not None
            else None,
            morphology_complexity=question.morphology_complexity,
            readability_score=question.readability_score,
            created_at=question.created_at,
            is_active=question.is_active,
        )

    except Exception as e:
        logger.error(f"Soru oluşturma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Soru oluşturma hatası: {str(e)}")


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str,
    request: QuestionUpdateRequest,
    soru_service: SoruBankasiServisi = Depends(get_soru_bankasi_service),
    current_user=Depends(get_current_user),
):
    """
    Soru güncelle

    Args:
        question_id: Soru ID'si
        request: Güncelleme isteği

    Returns:
        QuestionResponse: Güncellenmiş soru
    """
    try:
        # Sadece None olmayan alanları güncelle
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        update_data["updated_by"] = current_user.get("user_id", "unknown")

        question = await soru_service.soru_guncelle(question_id, update_data)

        if not question:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")

        return QuestionResponse(
            id=str(question.id),
            question_text=question.question_text,
            options=[
                f"A) {question.option_a}",
                f"B) {question.option_b}",
                f"C) {question.option_c}",
                f"D) {question.option_d}",
                f"E) {question.option_e}" if question.option_e else None,
            ],
            correct_answer=question.correct_answer,
            subject=question.subject_area.value,
            topic=question.topic,
            difficulty=question.difficulty.value,
            exam_type=question.exam_type.value,
            irt_parameters={
                "difficulty": question.irt_difficulty,
                "discrimination": question.irt_discrimination,
                "guessing": question.irt_guessing,
            }
            if question.irt_difficulty is not None
            else None,
            morphology_complexity=question.morphology_complexity,
            readability_score=question.readability_score,
            created_at=question.created_at,
            is_active=question.is_active,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Soru güncelleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Soru güncelleme hatası: {str(e)}")


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: str,
    soru_service: SoruBankasiServisi = Depends(get_soru_bankasi_service),
    current_user=Depends(get_current_user),
):
    """
    Soru sil (soft delete)

    Args:
        question_id: Soru ID'si

    Returns:
        Dict: Silme sonucu
    """
    try:
        success = await soru_service.soru_sil(question_id)

        if not success:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")

        return {"message": "Soru başarıyla silindi", "question_id": question_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Soru silme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Soru silme hatası: {str(e)}")


@router.post("/calibrate-irt")
async def calibrate_irt_parameters(
    request: IRTCalibrationRequest,
    background_tasks: BackgroundTasks,
    irt_service: IRTCalibrationService = Depends(get_irt_service),
    soru_service: SoruBankasiServisi = Depends(get_soru_bankasi_service),
    current_user=Depends(get_current_user),
):
    """
    IRT parametrelerini kalibre et

    Args:
        request: Kalibrasyon isteği

    Returns:
        Dict: Kalibrasyon sonucu
    """
    try:
        # Soruları getir
        questions_data = []
        for question_id in request.question_ids:
            question = await soru_service.soru_getir(question_id)
            if question:
                question_dict = {
                    "soru_metni": question.question_text,
                    "secenekler": [
                        f"A) {question.option_a}",
                        f"B) {question.option_b}",
                        f"C) {question.option_c}",
                        f"D) {question.option_d}",
                        f"E) {question.option_e}" if question.option_e else None,
                    ],
                    "konu": question.subject_area.value,
                    "zorluk_seviyesi": question.difficulty.value,
                }
                questions_data.append((question_id, question_dict))

        if not questions_data:
            raise HTTPException(status_code=400, detail="Geçerli soru bulunamadı")

        # Background task olarak kalibrasyon başlat
        background_tasks.add_task(
            _perform_background_calibration,
            questions_data,
            request.batch_size,
            irt_service,
            soru_service,
        )

        return {
            "message": "IRT kalibrasyon işlemi başlatıldı",
            "question_count": len(questions_data),
            "status": "processing",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IRT kalibrasyon hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"IRT kalibrasyon hatası: {str(e)}")


@router.post("/bulk-import")
async def bulk_import_questions(
    request: BulkImportRequest,
    background_tasks: BackgroundTasks,
    question_data: QuestionBankData = Depends(get_question_data),
    current_user=Depends(get_current_user),
):
    """
    Toplu soru import işlemi

    Args:
        request: Import isteği

    Returns:
        Dict: Import sonucu
    """
    try:
        # Soru verilerini al
        questions = question_data.get_questions_by_exam_type(request.exam_type)

        if not questions:
            raise HTTPException(
                status_code=400, detail=f"{request.exam_type} için soru bulunamadı"
            )

        # Background task olarak import başlat
        background_tasks.add_task(
            _perform_background_import,
            questions,
            request.exam_type,
            request.overwrite_existing,
        )

        return {
            "message": f"{request.exam_type} soruları import işlemi başlatıldı",
            "question_count": len(questions),
            "exam_type": request.exam_type,
            "status": "processing",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Toplu import hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Toplu import hatası: {str(e)}")


@router.get("/subjects", response_model=List[str])
async def get_available_subjects(
    exam_type: Optional[str] = Query(None, description="Sınav türü filtresi"),
    soru_service: SoruBankasiServisi = Depends(get_soru_bankasi_service),
):
    """
    Mevcut konuları listele

    Args:
        exam_type: Sınav türü filtresi

    Returns:
        List[str]: Konu listesi
    """
    try:
        subjects = await soru_service.konu_listesi_getir(exam_type)
        return subjects

    except Exception as e:
        logger.error(f"Konu listesi getirme hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Konu listesi getirme hatası: {str(e)}"
        )


@router.get("/random-questions")
async def get_random_questions(
    exam_type: str = Query(..., description="Sınav türü (TYT, AYT, YDT)"),
    question_count: int = Query(10, ge=1, le=100, description="Soru sayısı"),
    subject_distribution: Optional[str] = Query(
        None, description="Konu dağılımı (JSON string)"
    ),
    soru_service: SoruBankasiServisi = Depends(get_soru_bankasi_service),
):
    """
    Rastgele soru seçimi

    Args:
        exam_type: Sınav türü
        question_count: Soru sayısı
        subject_distribution: Konu dağılımı (opsiyonel)

    Returns:
        List[QuestionResponse]: Seçilen sorular
    """
    try:
        # Konu dağılımını parse et
        konu_dagilimi = None
        if subject_distribution:
            import json

            konu_dagilimi = json.loads(subject_distribution)

        # Rastgele sorular seç
        questions = await soru_service.rastgele_sorular_sec(
            sinav_tipi=exam_type,
            soru_sayisi=question_count,
            konu_dagilimi=konu_dagilimi,
        )

        # Response formatına dönüştür
        response_questions = []
        for question in questions:
            response_questions.append(
                QuestionResponse(
                    id=str(question.id),
                    question_text=question.question_text,
                    options=[
                        f"A) {question.option_a}",
                        f"B) {question.option_b}",
                        f"C) {question.option_c}",
                        f"D) {question.option_d}",
                        f"E) {question.option_e}" if question.option_e else None,
                    ],
                    correct_answer=question.correct_answer,
                    subject=question.subject_area.value,
                    topic=question.topic,
                    difficulty=question.difficulty.value,
                    exam_type=question.exam_type.value,
                    irt_parameters={
                        "difficulty": question.irt_difficulty,
                        "discrimination": question.irt_discrimination,
                        "guessing": question.irt_guessing,
                    }
                    if question.irt_difficulty is not None
                    else None,
                    morphology_complexity=question.morphology_complexity,
                    readability_score=question.readability_score,
                    created_at=question.created_at,
                    is_active=question.is_active,
                )
            )

        return response_questions

    except Exception as e:
        logger.error(f"Rastgele soru seçimi hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Rastgele soru seçimi hatası: {str(e)}"
        )


# Background task fonksiyonları
async def _perform_background_calibration(
    questions_data: List[tuple],
    batch_size: int,
    irt_service: IRTCalibrationService,
    soru_service: SoruBankasiServisi,
):
    """Background IRT kalibrasyon işlemi"""
    try:
        logger.info(
            f"Background IRT kalibrasyon başlatıldı - {len(questions_data)} soru"
        )

        # Kalibrasyon yap
        questions_only = [q[1] for q in questions_data]
        calibrated_params = await irt_service.batch_calibrate_questions(
            questions_only, batch_size
        )

        # Sonuçları database'e kaydet
        for (question_id, _), params in zip(questions_data, calibrated_params):
            update_data = {
                "irt_difficulty": params.difficulty,
                "irt_discrimination": params.discrimination,
                "irt_guessing": params.guessing,
                "morphology_complexity": params.morphology_complexity,
                "readability_score": params.readability_score,
            }
            await soru_service.soru_guncelle(question_id, update_data)

        logger.info(
            f"Background IRT kalibrasyon tamamlandı - {len(calibrated_params)} soru"
        )

    except Exception as e:
        logger.error(f"Background kalibrasyon hatası: {str(e)}")


async def _perform_background_import(
    questions: List[Dict[str, Any]], exam_type: str, overwrite_existing: bool
):
    """Background import işlemi"""
    try:
        logger.info(
            f"Background import başlatıldı - {exam_type}: {len(questions)} soru"
        )

        from scripts.populate_question_bank import QuestionBankPopulator

        populator = QuestionBankPopulator()

        # Import işlemi
        results = await populator.populate_specific_exam_type(exam_type)

        logger.info(
            f"Background import tamamlandı - Başarılı: {results.get('successful_insertions', 0)}"
        )

    except Exception as e:
        logger.error(f"Background import hatası: {str(e)}")
