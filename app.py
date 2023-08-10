import os
import json
import mysql.connector
from urllib.parse import urlparse, parse_qsl
from functools import cached_property

from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie

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


    @cached_property
    def cookies(self):
        return SimpleCookie(self.headers.get("Cookie"))


    def do_GET(self):
        if self.path == "/":
            self.load_page("src/index.html")

        elif self.path == "/register":
            self.load_page("src/register.html")

        elif self.path == "/login":
            self.load_page("src/login.html")

        elif self.path.startswith("/login/"):
            self.load_page("src/success.html")


    def do_POST(self):
        print(self.path)
        if self.path == "/register":
            status, data = self.verified_signup_data()

            if status == False:
                error = data
                self.load_error(400, error)
                return

            username, password = data

            self.create_user(username, password)

            self.make_redirect("/register")
        elif self.path == "/login":
            username = self.form_data["username"]
            password = self.form_data["password"]

            cursor.execute(f"SELECT * FROM users WHERE UserName = '{username}' AND UserPassword = '{password}'")

            if cursor.fetchone() is None:
                self.load_error(401, "Invalid username or password")
            else:
                self.make_redirect(f"/login/{username}")


    def make_redirect(self, address):
        self.send_response(303)
        self.send_header("Location", address)
        self.end_headers()

    
    def load_error(self, code, message):
        error = f"Error: {message}."
        file = self.insert_to_page("src/error.html", error)

        self.load_http(code, file)


    def load_page(self, page, data=""):
        file = self.insert_to_page(page, data)
        self.load_http(200, file)


    def load_http(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(data.encode("utf-8"))


    def insert_to_page(self, page, data):
        with open(page) as f:
            file = f.read().replace("{{}}", data)

        return file


    def verified_signup_data(self):
        if ("username" not in self.form_data.keys()) or ("password" not in self.form_data.keys()):
            error = "bad arguments: invalid username or password"
            return False, error

        username = self.form_data["username"]
        password = self.form_data["password"]
        
        if not self.unique_username(username):
            return False, f"Invalid username: {username} already exists"

        return True, (username, password)


    def unique_username(self, username):
        cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")

        if cursor.fetchone() is not None:
            return False
        return True


    def create_user(self, username, password):
        cursor.execute(f"INSERT INTO users(UserName, UserPassword) VALUES ('{username}', '{password}');")
        db.commit()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
    server.serve_forever()
