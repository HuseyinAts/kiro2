"""
AI Agents API - Türkiye Üniversite Sınavları Hazırlık Platformu
Basit agents listesi ve mock data
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_current_user
from models.database import User

logger = logging.getLogger(__name__)

# Router setup - remove prefix to avoid middleware blocking
router = APIRouter(tags=["Agents"])


@router.get("/agents/test")
async def test_agents(current_user: User = Depends(get_current_user)):
    """Simple test endpoint"""
    return {"test": "ok", "count": 8}


@router.get("/agents")
async def get_agents(current_user: User = Depends(get_current_user)):
    """Available AI agents listesi döndür (mock data)"""
    try:
        # Ultra simplified mock data for testing
        agents = [
            {
                "id": "matematik_uzman",
                "name": "Matematik Uzman",
                "description": "TYT ve AYT matematik sorularında uzman AI asistan",
                "type": "subject_expert",
                "available": True,
                "specialties": ["matematik", "geometri"],
                "model": "gpt-4",
            }
        ]

        logger.info(f"Returning {len(agents)} agents")
        return agents

    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(
            status_code=500, detail="Agent listesi alınırken hata oluştu"
        )
