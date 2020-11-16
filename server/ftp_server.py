import os
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import socket
import socketserver


authorizer = DummyAuthorizer()
work_dir = os.getcwd();
authorizer.add_user("user", "12345", work_dir, perm="elradfmw")
authorizer.add_anonymous(work_dir, perm="elradfmw")

handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer(("127.0.0.1", 1026), handler)
server.serve_forever()
