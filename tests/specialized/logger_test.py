import logging

logHandler = logging.FileHandler("log.txt", mode="w", encoding="utf-8")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
logHandler.setFormatter(formatter)
logging.basicConfig(level=logging.DEBUG, handlers=[logHandler])
logger = logging.getLogger(__name__)
logger.info("Test log entry")
