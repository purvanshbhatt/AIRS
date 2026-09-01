import http.server
import socketserver
import os
import sys

PORT = 5173
DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist-staging")

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        full_path = self.translate_path(self.path)
        if not os.path.exists(full_path) and "." not in self.path.split("/")[-1]:
            self.path = "/index.html"
        return super().do_GET()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), SPAHandler) as httpd:
        print(f"Serving SPA {DIRECTORY} at http://127.0.0.1:{PORT}")
        httpd.serve_forever()
