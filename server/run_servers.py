import os
from threading import Thread

def server_func():
    os.system('python server.py')

def ftp_server():
    os.system('python ftp_server.py')

if __name__ == '__main__':
    Thread(target = server_func).start()
    Thread(target = ftp_server).start()
