"""PeopleVault application entry point; HTTP details live in backend.server."""
from backend.server import *  # Re-exported temporarily for existing policy tests.


if __name__ == "__main__":
    if not FRONTEND_DIR.exists():
        raise SystemExit("React build is missing. Run: cd frontend && npm run build")
    server = ThreadingHTTPServer(("127.0.0.1", 8001), HRHandler)
    print("Secure HR RAG demo: http://127.0.0.1:8001")
    server.serve_forever()
