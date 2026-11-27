import asyncio
from app.services.cache import RedisCache

async def main():
    cache = RedisCache()
    try:
        if cache.client is None:
            raise SystemExit("Redis disabled or URL invalid")
        if await cache.client.ping():
            print("Redis connected: PONG")
    finally:
        await cache.close()

if __name__ == "__main__":
    asyncio.run(main())
