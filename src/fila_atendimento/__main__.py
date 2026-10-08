import logging

from waitress import serve

from .app import create_app
from .config import Config


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    config = Config.carregar()
    serve(create_app(config), host="0.0.0.0", port=config.porta, threads=8)


if __name__ == "__main__":
    main()
