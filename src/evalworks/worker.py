import logging

from evalworks.config import validate_production_settings
from evalworks.jobs import worker_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


if __name__ == "__main__":
    validate_production_settings()
    worker_loop()
