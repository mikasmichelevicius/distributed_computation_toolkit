import os
from threading import Thread

def server_func():
    os.system('python control_client.py localhost 5002')

def ftp_server():
    os.system('python manage.py runserver 7000')

if __name__ == '__main__':
    Thread(target = server_func).start()
    Thread(target = ftp_server).start()
