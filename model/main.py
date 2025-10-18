import logging
import os

from model.model import create_app


def main() -> None:
    """Entrypoint used by the Docker image to serve the Flask app."""
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

    port = int(os.getenv("PORT", "3000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"

    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
