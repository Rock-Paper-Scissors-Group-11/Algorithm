"""Serve the static HandRPS website locally and open it in a browser."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser

HOST = "127.0.0.1"
PORT = 8000
PROJECT_ROOT = Path(__file__).resolve().parent
URL = f"http://localhost:{PORT}/"


def main() -> None:
    handler = partial(SimpleHTTPRequestHandler, directory=str(PROJECT_ROOT))
    server = ThreadingHTTPServer((HOST, PORT), handler)
    print(f"HandRPS is running at {URL}")
    print("Keep this window open while you play. Press Ctrl+C to stop.")
    webbrowser.open(URL)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nHandRPS server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
