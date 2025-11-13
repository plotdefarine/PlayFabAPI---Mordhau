from functions.gatewayAPI import gatewayAPI
from configparser import ConfigParser
from functions.GetSessionTicket import get_session_ticket
import asyncio
import logging
import logging.handlers
import os


def setup_logging(log_dir: str = "logs", log_file: str = "app.log"):
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Rotating file handler
    fh = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, log_file), maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


async def run_fetch_process():
    setup_logging()
    log = logging.getLogger("main")

    config_path = "configurations/config.ini"
    config = ConfigParser()
    config.read(config_path)

    session_ticket = config.get("playfab", "session_ticket")

    if not session_ticket.strip():
        log.info("No session_ticket detected, connection to PlayFab (CustomID)...")
        session_ticket = await get_session_ticket()
        config.set("playfab", "session_ticket", session_ticket)
        with open(config_path, "w") as f:
            config.write(f)
        log.info("New session_ticket obtained and saved.")

    gateway = gatewayAPI(config_path=config_path)

    try:
        await gateway.run()
        log.info("Process completed successfully.")
    except Exception:
        log.exception("Unhandled exception during run_fetch_process")


if __name__ == "__main__":
    asyncio.run(run_fetch_process())
