"""Test gamification endpoint via HTTP to see the actual error"""
import httpx
import asyncio
import traceback


async def test():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://localhost:8001/api/v1/gamification/badges",
                params={"user_id": "test-user"},
                timeout=10.0,
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            if response.status_code != 200:
                print("ERROR: Non-200 status code")
            else:
                print("SUCCESS!")
        except Exception as e:
            print(f"Exception: {type(e).__name__}: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
