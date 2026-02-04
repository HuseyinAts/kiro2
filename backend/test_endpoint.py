"""Minimal test endpoint to isolate the issue"""
from fastapi import FastAPI, APIRouter
import uvicorn

app = FastAPI()
router = APIRouter(prefix="/api/test", tags=["Test"])


@router.get("/simple")
async def test_simple():
    """Simple test - just return dict"""
    return {"message": "Simple test works"}


@router.get("/badges")
async def test_badges():
    """Test exact same return structure as gamification badges"""
    return {
        "success": True,
        "data": {
            "badges": [
                {
                    "badge_id": "test_1",
                    "name": "Kararlı Öğrenci",
                    "description": "Test description",
                    "category": "study",
                    "rarity": "common",
                    "icon": "badge_fire",
                    "earned": False,
                    "earned_at": None,
                }
            ],
            "total_count": 1,
            "earned_count": 0,
        },
        "message": "Rozetler başarıyla getirildi",
    }


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
