"""Direct test of gamification endpoint to see the actual error"""
import sys
import asyncio
from api.gamification_api import get_all_badges


async def test():
    try:
        result = await get_all_badges(user_id="test-user", category=None)
        print("SUCCESS:", result)
    except Exception as e:
        print("ERROR:", type(e).__name__, str(e))
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
