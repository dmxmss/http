#!/usr/bin/python3

import cgi
import requests

form = cgi.FieldStorage()
username = form.getvalue("username")
password = form.getvalue("password")

url = "http://0.0.0.0:8000/register"

response = requests.post(url, data={"username": username, "password": password})
