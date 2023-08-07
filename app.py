import json
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

class WebRequestHandler(BaseHTTPRequestHandler):
    def get_response(self):
        return json.dumps({
            "response": "hello world",
            })

    def do_GET(self):
        self.send_response(200)    
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(self.get_response().encode("utf-8"))

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
    server.serve_forever()
