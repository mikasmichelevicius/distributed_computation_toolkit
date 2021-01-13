import socket, select, string, sys, py_compile, os, shelve
from ftplib import FTP

def does_compile(filename):
        try:
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
        with open(task_dir+"/runtime.txt", 'r') as file:
                run_time = file.read().replace('\n', '')
        os.remove(task_dir+"/runtime.txt")
        print('\n       FINISHED EXECUTION OF',task_dir," IN "+run_time+"\n        \____ RESULTS CAN BE FOUND IN DIRECTORY /"+task_dir)
        s.send(str.encode("FINISH"+task_dir))


def send_file(sub_file):
        ftp = FTP('')
        ftp.connect('localhost',1026)
        ftp.login()
        ftp.cwd('') #replace with your directory
        #ftp.retrlines('LIST')
        executable = None
        data = None
        filename = sub_file
        with open(filename, 'r') as file:
                print(file)
                for line in file:
                        if 'executable' in line:
                                executable = line.split()[2]
                                print(executable)
                        if 'data' in line:
                                data = line.split()[2]
                                print(data)

        #filename = 'task_example.py' #replace with your file in your home folder
        ftp.storbinary('STOR '+filename, open(filename, 'rb'))
        ftp.storbinary('STOR '+executable, open(executable, 'rb'))
        if data is not None:
                ftp.storbinary('STOR '+data, open(data, 'rb'))
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
        sys.stdout.write('\nStatus of tasks - JOB-status')
        sys.stdout.write('\nTask submission - SUBMIT filename.txt\n')
        sys.stdout.flush()

#main function
if __name__ == "__main__":

        tasks_count = 1
        client_id = None

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

        if os.path.isfile('data.db'):
                d = shelve.open('data.db')
                client_id = d['id']
                print("\n\n            CONNECTED TO THE SERVER.\n            YOUR ID IS:",str(client_id))
                s.send(str.encode("EXISTING_CONTROL"+str(client_id)))
                d.close()
                prompt()
        else:
                s.send(str.encode("CONTROL"))

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
                                        # prompt()
                                elif data.decode().startswith('DONE'):
                                        get_results(data.decode()[4:],s)

                                elif data.decode().startswith('RETURN'):
                                        get_results(data.decode()[6:],s)

                                elif data.decode().startswith('JOB-status'):
                                        sys.stdout.write(data.decode()[10:])
                                elif data.decode().startswith('RETRIEVE'):
                                        print("\n\n     RESULTS OF FINISHED TASKS ARE BEING RETRIEVED FROM SERVER\n")
                                        s.send(str.encode("RETRIEVE"))
                                elif data.decode().startswith('CONTROL_ID'):
                                        print("\n\n            CONNECTED TO THE SERVER.\n            YOUR ID IS:",data.decode()[10:])
                                        client_id = int(data.decode()[10:])
                                        d = shelve.open('data.db')
                                        d['id'] = client_id
                                        d.close()
                                        prompt()
                                elif data.decode().startswith('CONFIRM'):
                                        digits = 0
                                        while data.decode()[13+digits].isdigit():
                                                digits += 1
                                        print("\n       ",data.decode()[13+digits:],"SENT FOR EXECUTION AS",data.decode()[8:13+digits])
                                else :
                                        #print data
                                        sys.stdout.write(data.decode())
                                        # prompt()

                        #user entered a message
                        else :
                                msg = sys.stdin.readline().replace('\n','')
                                if (msg.startswith('SUBMIT')):

                                        # CHECK IF EXECUTABLE COMPILES ================================
                                        # is_valid = does_compile(msg[7:])
                                        is_valid = True
                                        if is_valid:
                                                send_file(msg[7:])
                                                s.send(str.encode(msg))

                                else:
                                        s.send(str.encode(msg))
                                        prompt()
