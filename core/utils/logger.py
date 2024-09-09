import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s.%(msecs)03d] [%(levelname).3s] [%(name)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_log(name: str) -> logging.Logger:
    return logging.getLogger(name)
