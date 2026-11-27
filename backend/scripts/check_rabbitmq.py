import asyncio
from app.messaging.broker import connect, topology

async def main():
    async with await connect() as connection:
        async with await connection.channel() as channel:
            await topology(channel)
            print("RabbitMQ connected; topology declared.")

if __name__ == "__main__":
    asyncio.run(main())
