from functions.gatewayAPI import gatewayAPI
from configparser import ConfigParser
from functions.GetSessionTicket import get_session_ticket
import asyncio

async def run_fetch_process():
    config_path = "configurations/config.ini"
    config = ConfigParser()
    config.read(config_path)

    session_ticket = config.get("playfab", "session_ticket")

    if not session_ticket.strip():
        print("[🔄] No session_ticket detected, connection to PlayFab (CustomID)...")
        session_ticket = await get_session_ticket()
        config.set("playfab", "session_ticket", session_ticket)
        with open(config_path, "w") as f:
            config.write(f)
        print("[✅] New session_ticket obtained and saved.")

    gateway = gatewayAPI(config_path=config_path)

    await gateway.run()

    print("\n✅ Process completed.")

if __name__ == "__main__":
    asyncio.run(run_fetch_process())
