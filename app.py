import os
from base64 import b64encode, b64decode
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

        elif self.path == "/login/index":
            if "token" not in self.cookies.keys():
                self.load_error(401, "Authorization is needed")
                return

            username = self.get_username_from_token()

            self.load_page("src/success.html", data=username) 
            

    def do_POST(self):
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
            status, data = self.verified_login_data()
            if status == False:
                error = data
                self.load_error(401, error)
                return

            username, password = data

            token = b64encode(f"{username}:{password}".encode()).decode()

            self.send_response(302)
            self.send_header("Location", "/login/index")
            self.send_header("Set-Cookie", f"token={token}")
            self.end_headers()


    def get_username_from_token(self):
        token = self.cookies["token"].value.lstrip("token=")
        return b64decode(token.encode()).decode().split(":")[0]
    

    def make_redirect(self, address, headers={}):
        self.send_response(303)
        self.send_header("Location", address)
        for header, value in headers.items():
            self.send_header(header, value)
        self.end_headers()

    
    def load_error(self, code, message, headers={}):
        error = f"Error: {message}."
        file = self.insert_to_page("src/error.html", error)

        self.load_http(code, file, headers)


    def load_page(self, page, data="", headers={}):
        file = self.insert_to_page(page, data)
        self.load_http(200, file, headers)


    def load_http(self, code, file, headers):
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        for header, value in headers.items():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(file.encode("utf-8"))


    def insert_to_page(self, page, data):
        with open(page) as f:
            file = f.read().replace("{{}}", data)

        return file

    def verified_login_data(self):
        status, data = self.userdata_is_present()
        if status == False:
            error = data
            return False, error

        username, password = data

        cursor.execute(f"SELECT * FROM users WHERE UserName = '{username}' AND UserPassword = '{password}'")

        if cursor.fetchone() is None:
            return False, "Invalid username or password"
        return True, (username, password)

    def verified_signup_data(self):
        status, data = userdata_is_present()

        if status == False:
            error = data
            return False, error

        username, password = data
        
        if not self.unique_username(username):
            return False, f"Invalid username: {username} already exists"

        return True, (username, password)


    def userdata_is_present(self):
        if ("username" not in self.form_data.keys()) or ("password" not in self.form_data.keys()):
            error = "bad arguments: invalid username or password"
            return False, error

        username = self.form_data["username"]
        password = self.form_data["password"]

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
