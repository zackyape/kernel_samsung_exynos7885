import logging

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[logging.StreamHandler()],
    format="%(asctime)s - %(filename)s:%(lineno)-3d - %(levelname)-8s: %(message)s",
)
