import logging


def init_logging() -> None:
    logging.basicConfig(
        # Note: If needed "debug", more complex logging setup must be done.
        #   Because some libraries may be too verbose in debug mode.
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
