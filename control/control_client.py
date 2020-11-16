import socket, select, string, sys, py_compile, os
from ftplib import FTP

def does_compile(filename):
        try:
                print(filename)
                py_compile.compile(filename, doraise=True)
                return True
        except py_compile.PyCompileError:
                print("PROGRAM DOES NOT COMPILE!")
                return False

def get_results(task_dir,s):
        parent_dir = os.getcwd()
        path = os.path.join(parent_dir, task_dir)
        os.mkdir(path)
        ftp = FTP('')
        ftp.connect('localhost',1026)
        ftp.login()
        ftp.cwd(task_dir)
        for file_name in ftp.nlst():
                localfile = open(task_dir+"/"+file_name, 'wb')
                ftp.retrbinary('RETR ' + file_name, localfile.write, 1024)
        ftp.quit()
        localfile.close()
        print('FINISHED EXECUTION OF',data.decode()[4:])
        s.send(str.encode("FINISH"+task_dir))


def send_file(sub_file):
        print('====',sub_file)
        ftp = FTP('')
        ftp.connect('localhost',1026)
        ftp.login()
        ftp.cwd('') #replace with your directory
        #ftp.retrlines('LIST')
        filename = sub_file
        #filename = 'task_example.py' #replace with your file in your home folder
        ftp.storbinary('STOR '+filename, open(filename, 'rb'))
        ftp.quit()

def get_file():
        ftp = FTP('')
        ftp.connect('localhost',1026)
        ftp.login()
        ftp.cwd('') #replace with your directory
        #ftp.retrlines('LIST')
        filename = 'kazkas.txt' #replace with your file in the directory ('directory_name')
        localfile = open(filename, 'wb')
        ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
        ftp.quit()
        localfile.close()

def prompt() :
        sys.stdout.write('\nClients addresses - write a')
        sys.stdout.write('\nStatistics of clients - write s')
        sys.stdout.write('\nTask submission - SUBMIT filename.txt\n')
        sys.stdout.flush()

#main function
if __name__ == "__main__":

        if(len(sys.argv) < 3) :
                print('Usage : python telnet.py hostname port')
                sys.exit()

        host = sys.argv[1]
        port = int(sys.argv[2])

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)

        # connect to remote host
        try :
                s.connect((host, port))
        except :
                print('Unable to connect')
                sys.exit()

        print('Connected to remote host. Start sending messages')
        prompt()

        while 1:
                socket_list = [sys.stdin, s]

                # Get the list sockets which are readable
                read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])

                for x in range(0,len(read_sockets)):
                        #incoming message from remote server
                        if read_sockets[x] == s:
                                data = read_sockets[x].recv(4096)
                                if not data :
                                        #print('won\'t disconnect')
                                        print('\nDisconnected from chat server')
                                        sys.exit()
                                elif (data.decode().startswith('a')):
                                        sys.stdout.write(data.decode()[1:])
                                        prompt()
                                elif data.decode().startswith('DONE'):
                                        get_results(data.decode()[4:],s)
                                else :
                                        #print data
                                        sys.stdout.write(data.decode())
                                        prompt()

                        #user entered a message
                        else :
                                msg = sys.stdin.readline().replace('\n','')
                                if (msg.startswith('SUBMIT')):
                                        #get_file()
                                        is_valid = does_compile(msg[7:])
                                        if is_valid:
                                                send_file(msg[7:])
                                                s.send(str.encode(msg))

                                else:
                                        s.send(str.encode(msg))
                                #prompt()
