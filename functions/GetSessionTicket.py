import aiohttp
import json
from configparser import ConfigParser

async def get_session_ticket() -> str:
    config_path = "configurations/config.ini"
    config = ConfigParser()
    config.read(config_path)

    title_id = config.get("playfab", "title_id")
    custom_id = config.get("playfab", "custom_id")

    url = f"https://{title_id}.playfabapi.com/Client/LoginWithCustomID"
    payload = {
        "CustomId": custom_id,
        "TitleId": title_id,
        "CreateAccount": True
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"[📡] Request to PlayFab with CustomID = {custom_id}, TitleID = {title_id}...")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            raw = await response.text()
            try:
                data = json.loads(raw)
            except Exception:
                print(f"❌ Unable to decode JSON response: {raw}")
                raise

            print(f"[🔍] HTTP status: {response.status}")
            print(f"[📨] Gross response: {data}")

            if response.status == 200 and "data" in data:
                session_ticket = data["data"]["SessionTicket"]

                config.set("playfab", "session_ticket", session_ticket)
                with open(config_path, "w") as configfile:
                    config.write(configfile)

                print("[✔] SessionTicket (CustomID) registered in config.ini.")
                return session_ticket

            else:
                error = data.get("errorMessage", "Unknown error")
                print(f"❌ Erreur PlayFab: {error}")
                raise Exception(f"PlayFab error: {error}")
