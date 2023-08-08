import os
import json
import mysql.connector
from urllib.parse import urlparse, parse_qsl
from functools import cached_property

from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

db = mysql.connector.connect(
        host="localhost",
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD")
)

cursor = db.cursor()
cursor.execute("USE users")
cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    UserId               INT UNSIGNED NOT NULL AUTO_INCREMENT,
    UserName             VARCHAR(255) NOT NULL UNIQUE,
    UserPassword         VARCHAR(255) NOT NULL,

    PRIMARY KEY (UserId)
);""")

class WebRequestHandler(BaseHTTPRequestHandler):

    @cached_property
    def post_data(self):
        content_length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(content_length)

    @cached_property
    def form_data(self):
        return dict(parse_qsl(self.post_data.decode("utf-8")))

    def do_POST(self):
        if ("username" not in self.form_data.keys()) or ("password" not in self.form_data.keys()):
            self.send_error(400, "bad arguments", "there is no username or password")

        username = self.form_data["username"]
        password = self.form_data["password"]

        cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")

        if cursor.fetchone() is not None:
            self.send_error(400, "username already exists")

        cursor.execute(f"INSERT INTO users(UserName, UserPassword) VALUES ('{username}', '{password}');")
        db.commit()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "success",
            "data": username
        }).encode("utf-8"))
    
    def send_error(self, code, message, explain=""):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "error",
            "data": message,
            "explain": explain
        }).encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
    server.serve_forever()
