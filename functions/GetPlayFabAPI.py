import aiohttp
import aiomysql
import asyncio
import json
from datetime import datetime
from pathlib import Path

class PlayFabFetcher:
    def __init__(self, pool, session_ticket: str, title_id: str, sql_query: str, config=None):
        self.pool = pool
        self.session_ticket = session_ticket
        self.title_id = title_id
        self.sql_query = sql_query
        self.parameters = self.load_info_request_parameters("configurations/parameters.json")
        self.memory_buffer = []
        self.config = config  # Ajout de la config
        
    @staticmethod
    def format_iso_to_sql_datetime(iso_str: str) -> str:
        if not iso_str:
            return None
        try:
            dt = datetime.fromisoformat(iso_str.replace("Z", "").split(".")[0])
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None
    @staticmethod
    def format_timestamp(timestamp: int) -> str:
        try:
            return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return str(timestamp)

    @staticmethod
    def load_info_request_parameters(path: str) -> dict:
        if not Path(path).exists():
            raise FileNotFoundError(f"Fichier {path} introuvable.")
        with open(path, "r") as f:
            return json.load(f).get("InfoRequestParameters", {})

    async def fetch_single_player(self, playfab_id: str) -> dict:
        url = f"https://{self.title_id}.playfabapi.com/Client/GetPlayerCombinedInfo"
        headers = {
            "Content-Type": "application/json",
            "X-Authorization": self.session_ticket
        }
        payload = {
            "PlayFabId": playfab_id,
            "InfoRequestParameters": self.parameters
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    data = await response.json()
                    raise Exception(data.get("errorMessage", "Erreur inconnue"))

    async def get_playfab_ids(self):
        # Choix de la source selon la config
        source = "database"
        manual_file = None
        if self.config and self.config.has_section("input"):
            source = self.config.get("input", "source", fallback="database")
            manual_file = self.config.get("input", "manual_file", fallback="configurations/manual_playfabids.txt")
        if source == "manual_file":
            # Charger les IDs depuis le fichier
            if not Path(manual_file).exists():
                raise FileNotFoundError(f"Manual PlayFabIDs file not found: {manual_file}")
            with open(manual_file, "r") as f:
                playfab_ids = [line.strip() for line in f if line.strip()]
            return playfab_ids
        else:
            # Charger depuis la base de données
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(self.sql_query)
                    rows = await cur.fetchall()
                    playfab_ids = [row[0] for row in rows]
            return playfab_ids

    async def collect_all(self) -> list:
        playfab_ids = await self.get_playfab_ids()
        semaphore_value = 10 # Default value if not set in config
        if self.config and self.config.has_section("playfab"):
            try:
                semaphore_value = self.config.getint("playfab", "semaphore_limit", fallback=12)
            except ValueError:
                print("[Warning] Invalid value for semaphore_limit in config.ini. Using default: 12")

        semaphore = asyncio.Semaphore(semaphore_value)

        async def limited_fetch(playfab_id: str):
            async with semaphore:
                try:
                    response = await self.fetch_single_player(playfab_id)
                    info = response.get("data", {}).get("InfoResultPayload", {})

                    readonly_str = info.get("UserReadOnlyData", {}).get("AccountInfo", {}).get("Value", "{}")
                    readonly_data = json.loads(readonly_str)

                    player_stats = info.get("PlayerStatistics", [])
                    stats = {
                        stat["StatisticName"]: stat["Value"] for stat in player_stats
                        if stat["StatisticName"] not in (
                            "CasualRank", "CasualRankTimestamp", "CasualRankSamples", "CasualMatchCount")
                    }

                    for ts_key in ("TeamfightRankTimestamp", "DuelRankTimestamp"):
                        if ts_key in stats:
                            stats[f"{ts_key}_formatted"] = self.format_timestamp(stats[ts_key])

                    entry = {
                        "playfab_id": readonly_data.get("PlayFabId"),
                        "id": readonly_data.get("PlatformAccountId"),
                        "platform": readonly_data.get("Platform"),
                        "username": readonly_data.get("Name"),
                        "entity_id": readonly_data.get("EntityId"),
                        "created_at": self.format_iso_to_sql_datetime(info.get("AccountInfo", {}).get("Created")),
                        "stats": stats
                    }
                    if not entry["playfab_id"]:
                        raise ValueError("PlayFabId is missing in the response.")
                    
                    if not entry.get("id"):
                        raise ValueError("Missing ID for PlayFabID: " + entry.get("playfab_id", "?"))


                    print(f'✅ Player: "{entry["username"]}" | PlayFabID: {entry["playfab_id"]} | ID: {entry["id"]} | Status: OK')
                    return entry

                except Exception as e:
                    print(f'❌ Player: "?" | PlayFabID: {playfab_id} | SteamID: "?" | Status: {str(e)}')
                    return None

        tasks = [limited_fetch(pid) for pid in playfab_ids]
        results = await asyncio.gather(*tasks)

        self.memory_buffer = [r for r in results if r is not None]
        return self.memory_buffer
