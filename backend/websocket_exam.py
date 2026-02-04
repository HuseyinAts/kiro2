"""
Sınav WebSocket Endpoint'leri
Gerçek zamanlı sınav durumu güncellemeleri
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set

from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

from services.sinav_motoru_service import sinav_motoru_servisi
from services.user_service import kullanici_servisi

logger = logging.getLogger(__name__)

# WebSocket router
websocket_router = APIRouter()


# Aktif WebSocket bağlantıları
class ConnectionManager:
    def __init__(self):
        # sinav_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> sinav_id
        self.connection_to_exam: Dict[WebSocket, str] = {}
        # sinav_id -> asyncio.Task (timer task)
        self.timer_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, sinav_id: str, kullanici_id: str):
        """WebSocket bağlantısını kabul et ve kaydet"""
        await websocket.accept()

        # Sınav oturumu kontrolü
        oturum = await sinav_motoru_servisi.oturum_getir(sinav_id)
        if not oturum:
            await websocket.close(code=4004, reason="Sınav oturumu bulunamadı")
            return False

        if oturum.ogrenci_id != kullanici_id:
            await websocket.close(code=4003, reason="Bu sınava erişim yetkiniz yok")
            return False

        # Bağlantıyı kaydet
        if sinav_id not in self.active_connections:
            self.active_connections[sinav_id] = set()

        self.active_connections[sinav_id].add(websocket)
        self.connection_to_exam[websocket] = sinav_id

        # Timer task'ını başlat
        if sinav_id not in self.timer_tasks:
            self.timer_tasks[sinav_id] = asyncio.create_task(
                self.exam_timer_task(sinav_id)
            )

        logger.info(
            f"WebSocket bağlantısı kuruldu: sinav_id={sinav_id}, kullanici_id={kullanici_id}"
        )

        # Bağlantı onayı gönder
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "message": "WebSocket bağlantısı kuruldu",
            },
            websocket,
        )

        return True

    async def disconnect(self, websocket: WebSocket):
        """WebSocket bağlantısını kapat"""
        sinav_id = self.connection_to_exam.get(websocket)

        if sinav_id and sinav_id in self.active_connections:
            self.active_connections[sinav_id].discard(websocket)

            # Eğer bu sınavda başka bağlantı yoksa timer'ı durdur
            if not self.active_connections[sinav_id]:
                del self.active_connections[sinav_id]

                if sinav_id in self.timer_tasks:
                    self.timer_tasks[sinav_id].cancel()
                    del self.timer_tasks[sinav_id]

        if websocket in self.connection_to_exam:
            del self.connection_to_exam[websocket]

        logger.info(f"WebSocket bağlantısı kapatıldı: sinav_id={sinav_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Belirli bir WebSocket'e mesaj gönder"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"WebSocket mesaj gönderme hatası: {e}")

    async def broadcast_to_exam(self, message: dict, sinav_id: str):
        """Belirli bir sınavdaki tüm bağlantılara mesaj gönder"""
        if sinav_id not in self.active_connections:
            return

        disconnected = []
        for websocket in self.active_connections[sinav_id].copy():
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"WebSocket broadcast hatası: {e}")
                disconnected.append(websocket)

        # Bağlantısı kopan WebSocket'leri temizle
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def exam_timer_task(self, sinav_id: str):
        """Sınav timer task'ı - Her saniye kalan süreyi güncelle"""
        try:
            while True:
                # Sınav oturumunu kontrol et
                oturum = await sinav_motoru_servisi.oturum_getir(sinav_id)
                if not oturum or oturum.durum != "DEVAM_EDIYOR":
                    break

                # Kalan süreyi hesapla
                kalan_sure = await sinav_motoru_servisi.kalan_sure_getir(sinav_id)

                if kalan_sure <= 0:
                    # Süre bitti - Sınavı otomatik tamamla
                    await sinav_motoru_servisi.sinav_tamamla(
                        sinav_id, manuel_tamamlama=False
                    )

                    await self.broadcast_to_exam(
                        {
                            "type": "auto_submit",
                            "message": "Süre doldu, sınav otomatik olarak tamamlandı",
                        },
                        sinav_id,
                    )
                    break

                # Süre güncellemesi gönder
                await self.broadcast_to_exam(
                    {"type": "time_update", "remaining_time": kalan_sure}, sinav_id
                )

                # 5 dakika kaldığında uyarı gönder
                if kalan_sure == 300:  # 5 dakika = 300 saniye
                    await self.broadcast_to_exam(
                        {
                            "type": "time_warning",
                            "message": "Sınav sürenizin 5 dakikası kaldı!",
                        },
                        sinav_id,
                    )

                # 1 dakika kaldığında uyarı gönder
                elif kalan_sure == 60:  # 1 dakika = 60 saniye
                    await self.broadcast_to_exam(
                        {
                            "type": "time_warning",
                            "message": "Sınav sürenizin 1 dakikası kaldı!",
                        },
                        sinav_id,
                    )

                await asyncio.sleep(1)  # 1 saniye bekle

        except asyncio.CancelledError:
            logger.info(f"Timer task iptal edildi: sinav_id={sinav_id}")
        except Exception as e:
            logger.error(f"Timer task hatası: sinav_id={sinav_id}, error={e}")


# Connection manager instance
manager = ConnectionManager()


async def get_current_user_from_token(token: str):
    """Token'dan kullanıcı bilgilerini al"""
    try:
        kullanici = await kullanici_servisi.token_dogrula(token)
        if not kullanici:
            raise HTTPException(status_code=401, detail="Geçersiz token")
        return kullanici
    except Exception:
        raise HTTPException(status_code=401, detail="Token doğrulama hatası")


@websocket_router.websocket("/ws/sinav/{sinav_id}")
async def websocket_exam_endpoint(websocket: WebSocket, sinav_id: str):
    """
    Sınav WebSocket endpoint'i
    URL: ws://localhost:8000/ws/sinav/{sinav_id}?token={jwt_token}
    """
    try:
        # Query parameter'dan token al
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Token gerekli")
            return

        # Token'ı doğrula
        try:
            kullanici = await get_current_user_from_token(token)
        except HTTPException:
            await websocket.close(code=4001, reason="Geçersiz token")
            return

        # Bağlantıyı kur
        connected = await manager.connect(websocket, sinav_id, kullanici.kullanici_id)
        if not connected:
            return

        # Mesaj dinleme döngüsü
        try:
            while True:
                # Client'tan mesaj bekle (ping/pong için)
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)

                    # Ping mesajına pong ile yanıt ver
                    if message.get("type") == "ping":
                        await manager.send_personal_message(
                            {"type": "pong", "timestamp": datetime.now().isoformat()},
                            websocket,
                        )

                    # Diğer mesaj tipleri için işlem yapılabilir

                except json.JSONDecodeError:
                    logger.warning(f"Geçersiz JSON mesajı: {data}")

        except WebSocketDisconnect:
            logger.info(f"WebSocket bağlantısı kesildi: sinav_id={sinav_id}")

    except Exception as e:
        logger.error(f"WebSocket endpoint hatası: {e}")

    finally:
        await manager.disconnect(websocket)


# Sınav durumu değişikliklerini broadcast etmek için yardımcı fonksiyonlar
async def broadcast_exam_status_change(
    sinav_id: str, new_status: str, message: str = None
):
    """Sınav durumu değişikliğini broadcast et"""
    await manager.broadcast_to_exam(
        {
            "type": "status_change",
            "new_status": new_status,
            "message": message or f"Sınav durumu değişti: {new_status}",
            "timestamp": datetime.now().isoformat(),
        },
        sinav_id,
    )


async def broadcast_question_change(
    sinav_id: str, question_index: int, total_questions: int
):
    """Soru değişikliğini broadcast et"""
    await manager.broadcast_to_exam(
        {
            "type": "question_change",
            "current_question": question_index + 1,
            "total_questions": total_questions,
            "timestamp": datetime.now().isoformat(),
        },
        sinav_id,
    )


async def broadcast_answer_saved(sinav_id: str, question_id: str, answer: str):
    """Cevap kaydedildiğini broadcast et"""
    await manager.broadcast_to_exam(
        {
            "type": "answer_saved",
            "question_id": question_id,
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
        },
        sinav_id,
    )


# Export manager for use in other modules
__all__ = [
    "websocket_router",
    "manager",
    "broadcast_exam_status_change",
    "broadcast_question_change",
    "broadcast_answer_saved",
]
