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
        print("[🔄] Aucun session_ticket détecté, connexion à PlayFab (CustomID)...")
        session_ticket = await get_session_ticket()
        config.set("playfab", "session_ticket", session_ticket)
        with open(config_path, "w") as f:
            config.write(f)
        print("[✅] Nouveau session_ticket obtenu et enregistré.")

    gateway = gatewayAPI(config_path=config_path)

    await gateway.run()

    print("\n✅ Processus terminé.")

if __name__ == "__main__":
    asyncio.run(run_fetch_process())