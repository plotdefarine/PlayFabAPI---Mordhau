import asyncio
from functions.GetSessionTicket import get_session_ticket

async def main():
    await get_session_ticket()

if __name__ == "__main__":
    asyncio.run(main())
