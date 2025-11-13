import aiomysql
from configparser import ConfigParser
from functions.GetPlayFabAPI import PlayFabFetcher
import json
# from functions.GetSteamAPI import SteamFetcher

class gatewayAPI:
    def __init__(self, config_path: str = "configurations/config.ini"):
        self.config_path = config_path
        self.config = ConfigParser()
        self.config.read(config_path)

        self.session_ticket = self.config.get("playfab", "session_ticket")
        self.title_id = self.config.get("playfab", "title_id")
        self.sql_query = self.config.get("sql_query", "get_playfab_ids")
        self.table_name = self.config.get("database", "table")
        self.pool = None
        self.playfab_fetcher = None
        # self.steam_fetcher = None

    async def init_pool(self):
        destination = self.config.get("output", "destination", fallback="database")
        
        # Only initialize pool if using database destination
        if destination == "database":
            self.pool = await aiomysql.create_pool(
                host=self.config.get("database", "host"),
                port=self.config.getint("database", "port"),
                user=self.config.get("database", "user"),
                password=self.config.get("database", "password"),
                db=self.config.get("database", "database"),
                autocommit=True
            )
        else:
            print(f"[📝] Sauvegarde en mode: {destination}")

    async def run(self):
        if not self.pool:
            await self.init_pool()

        self.playfab_fetcher = PlayFabFetcher(
            pool=self.pool,
            session_ticket=self.session_ticket,
            title_id=self.title_id,
            sql_query=self.sql_query,
            config=self.config  # Passer la config ici
        )

        # self.steam_fetcher = SteamFetcher(...)

        print("[📡] Lancement de la collecte PlayFab...")
        playfab_data = await self.playfab_fetcher.collect_all()

        print(f"[🧠] {len(playfab_data)} players collected from PlayFab.")
        await self.insert_into_database(playfab_data)

    async def insert_into_database(self, data: list):
        destination = self.config.get("output", "destination", fallback="database")
        
        if destination == "database":
            await self._insert_into_database_db(data)
        else:
            await self._insert_into_txt_file(data)

    async def _insert_into_database_db(self, data: list):
        """Sauvegarde dans la base de données MariaDB"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                for player in data:
                    try:
                        await cur.execute(
                            f"""
                            INSERT INTO {self.table_name} (
                                playfab_id, id, username, platform,
                                entity_id, created_at, stats_json
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                username = VALUES(username),
                                platform = VALUES(platform),
                                created_at = VALUES(created_at),
                                stats_json = VALUES(stats_json)
                            """,
                            (
                                player["playfab_id"],
                                player["id"],
                                player["username"],
                                player["platform"],
                                player["entity_id"],
                                player["created_at"],
                                json.dumps(player["stats"])
                            )
                        )
                        print(f'[💾] Registered : {player["username"]}')
                    except Exception as e:
                        print(f"[⚠️] Insertion failure: {player.get('playfab_id', '?')} -> {str(e)}")

    async def _insert_into_txt_file(self, data: list):
        """Sauvegarde dans un fichier txt"""
        txt_file_path = self.config.get("output", "txt_file", fallback="configurations/saved_playfabids.txt")
        
        try:
            with open(txt_file_path, "a", encoding="utf-8") as f:
                for player in data:
                    try:
                        player_json = json.dumps(player, ensure_ascii=False)
                        f.write(player_json + "\n")
                        print(f'[💾] Saved to file : {player["username"]}')
                    except Exception as e:
                        print(f"[⚠️] Save failure: {player.get('playfab_id', '?')} -> {str(e)}")
        except Exception as e:
            print(f"[❌] Error writing to file {txt_file_path}: {str(e)}")

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
