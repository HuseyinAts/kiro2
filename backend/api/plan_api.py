"""
Faz 4 Plan API — GET /api/v1/plan/week
Returns the weekly plan for the Haftalık Plan Page.
"""

from fastapi import APIRouter, Depends
from core.dependencies import AuthenticatedUser, get_current_user

router = APIRouter(prefix="/api/v1/plan", tags=["Plan"])

@router.get("/week")
async def get_plan_week(current_user: AuthenticatedUser = Depends(get_current_user)):
    # This returns a mock structure as expected by the frontend Phase 4 contract.
    # In a real implementation, this would build blocks based on the user's active study plan.
    return {
        "gunler": [
            {
                "gun": "Pzt",
                "tarih": "29 Haz",
                "bugun": True,
                "bloklar": [
                    {
                        "tur": "calisma",
                        "ders": "mat",
                        "baslik": "Türev",
                        "meta": "12 soru · ~30 dk",
                        "dk": 30,
                        "hedefRota": "/soru-cozme"
                    },
                    {
                        "tur": "tekrar",
                        "ders": "mat",
                        "baslik": "Limit ve Süreklilik tekrarı",
                        "meta": "4 kart · ~16 dk",
                        "dk": 16,
                        "hedefRota": "/tekrar"
                    }
                ]
            },
            {
                "gun": "Sal",
                "tarih": "30 Haz",
                "bugun": False,
                "bloklar": [
                    {
                        "tur": "calisma",
                        "ders": "kim",
                        "baslik": "Gazlar",
                        "meta": "12 soru · ~30 dk",
                        "dk": 30,
                        "hedefRota": "/soru-cozme"
                    }
                ]
            },
            {
                "gun": "Çar",
                "tarih": "1 Tem",
                "bugun": False,
                "bloklar": [
                    {
                        "tur": "calisma",
                        "ders": "fiz",
                        "baslik": "Elektrik",
                        "meta": "12 soru · ~30 dk",
                        "dk": 30,
                        "hedefRota": "/soru-cozme"
                    }
                ]
            },
            {
                "gun": "Per",
                "tarih": "2 Tem",
                "bugun": False,
                "bloklar": [
                    {
                        "tur": "calisma",
                        "ders": "kim",
                        "baslik": "Kimyasal Tepkimeler",
                        "meta": "12 soru · ~30 dk",
                        "dk": 30,
                        "hedefRota": "/soru-cozme"
                    }
                ]
            },
            {
                "gun": "Cum",
                "tarih": "3 Tem",
                "bugun": False,
                "bloklar": [
                    {
                        "tur": "calisma",
                        "ders": "mat",
                        "baslik": "Limit ve Süreklilik",
                        "meta": "12 soru · ~30 dk",
                        "dk": 30,
                        "hedefRota": "/soru-cozme"
                    }
                ]
            },
            {
                "gun": "Cmt",
                "tarih": "4 Tem",
                "bugun": False,
                "bloklar": [
                    {
                        "tur": "deneme",
                        "baslik": "Harmanlanmış Deneme",
                        "meta": "TYT + AYT · ~135 dk",
                        "dk": 135,
                        "hedefRota": "/deneme"
                    }
                ]
            },
            {
                "gun": "Paz",
                "tarih": "5 Tem",
                "bugun": False,
                "bloklar": [
                    {
                        "tur": "analiz",
                        "baslik": "Deneme analizi",
                        "meta": "net + zayıf konu · ~25 dk",
                        "dk": 25,
                        "hedefRota": "/sinav-sonuc"
                    },
                    {
                        "tur": "mola",
                        "baslik": "Nefes molası",
                        "meta": "sakinleş · ~10 dk",
                        "dk": 10,
                        "hedefRota": "/mola"
                    }
                ]
            }
        ],
        "aralik": "29 Haz – 5 Tem",
        "gunlukHedefDk": 120
    }
