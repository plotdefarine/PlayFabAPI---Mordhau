from functions.gatewayAPI import gatewayAPI
from configparser import ConfigParser
from functions.GetSessionTicket import get_session_ticket
import asyncio
import logging
import logging.handlers
import os


def setup_logging(log_dir: str = "logs", log_file: str = "app.log", log_level: str = "standard"):
    """Configure logging handlers. log_level: standard|medium|maximum"""
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger()

    # Determine levels based on config value
    # standard -> console INFO, file INFO
    # medium   -> console DEBUG, file INFO
    # maximum  -> console DEBUG, file DEBUG
    lvl = log_level.lower()
    if lvl == "medium":
        console_level = logging.DEBUG
        file_level = logging.INFO
    elif lvl == "maximum":
        console_level = logging.DEBUG
        file_level = logging.DEBUG
    else:
        console_level = logging.INFO
        file_level = logging.INFO

    # Root logger level should be the minimum of both so all messages are captured
    root_level = min(console_level, file_level)
    logger.setLevel(root_level)

    # Rotating file handler
    fh = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, log_file), maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(file_level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(console_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


async def run_fetch_process():
    config_path = "configurations/config.ini"
    config = ConfigParser()
    config.read(config_path)

    # Read logging level from config before initializing logging
    log_level = "standard"
    try:
        if config.has_section("logging"):
            log_level = config.get("logging", "log_level", fallback="standard")
    except Exception:
        pass

    setup_logging(log_level=log_level)
    log = logging.getLogger("main")

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
