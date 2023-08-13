from ssl import PROTOCOL_TLS_SERVER, SSLContext
from http.server import HTTPServer
from app import WebRequestHandler

ssl_context = SSLContext(PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain("cert.pem", "private.key")
server = HTTPServer(("0.0.0.0", 4443), WebRequestHandler)
server.socket = ssl_context.wrap_socket(server.socket, server_side=True)
server.serve_forever()

