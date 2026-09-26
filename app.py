"""PeopleVault application entry point; HTTP details live in backend.server."""
import os

from backend.server import *  # Re-exported temporarily for existing policy tests.


if __name__ == "__main__":
    if os.environ.get("API_ONLY") != "1" and not FRONTEND_DIR.exists():
        raise SystemExit("React build is missing. Run: cd frontend && npm run build")
    host = os.environ.get("APP_HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, 8001), HRHandler)
    print(f"Secure HR RAG demo: http://{host}:8001")
    server.serve_forever()
