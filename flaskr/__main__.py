import os
from . import create_app


def main() -> None:
    app = create_app()

    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_RUN_PORT", "6000"))
    debug = os.environ.get("FLASK_DEBUG", "0") in ("1", "true", "True")

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()