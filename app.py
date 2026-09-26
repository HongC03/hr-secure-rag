"""PeopleVault application entry point; HTTP details live in backend.server."""
import os

from backend.server import *  # Re-exported temporarily for existing policy tests.


if __name__ == "__main__":
    configure_server_logging()
    if os.environ.get("API_ONLY") != "1" and not FRONTEND_DIR.exists():
        raise SystemExit("React build is missing. Run: cd frontend && npm run build")
    host = os.environ.get("APP_HOST", "127.0.0.1")
    server = LoggingHTTPServer((host, 8001), HRHandler)
    LOGGER.info("server_started address=http://%s:8001", host)
    server.serve_forever()
