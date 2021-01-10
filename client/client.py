import socket, select, string, sys, os, shutil, subprocess, time
from ftplib import FTP


def prompt() :
        sys.stdout.write('\n<Client> ')
        sys.stdout.flush()

def results_to_server(task_dir, filename):
        result_files = os.listdir(task_dir)
        result_files.remove(filename)
        print(result_files)

        ftp = FTP('')
        ftp.connect('localhost',1026)
        ftp.login()
        ftp.cwd(task_dir) #replace with your directory
        #ftp.retrlines('LIST')
        for x in range(len(result_files)):
                # filename = task_dir+"/"+result_files[x]
                filename = result_files[x]
                ftp.storbinary('STOR '+filename, open(task_dir+"/"+filename, 'rb'))
        ftp.quit()
        shutil.rmtree(task_dir)

def get_file(filename,task_dir):
        ftp = FTP('')
        ftp.connect('localhost',1026)
        ftp.login()
        parent_dir = os.getcwd()
        path = os.path.join(parent_dir, task_dir)
        os.mkdir(path)
        ftp.cwd(task_dir) #replace with directory in server?

        localfile = open(task_dir+"/"+filename, 'wb')
        ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
        ftp.quit()
        localfile.close()

def execute_task(submit_msg,s,digits):
        task_dir = submit_msg[:4+digits]
        task_no = int(submit_msg[4:4+digits])
        print(task_no,'====================')
        filename = submit_msg[4+digits:]
        get_file(filename, task_dir)

        run_program = "python " + task_dir+"/"+filename + " > " + task_dir+"/stdout.txt"
        start_time = time.time()
        proc = subprocess.Popen(run_program, stderr=subprocess.PIPE, shell=True)
        total_time = time.time() - start_time
        (out, err) = proc.communicate()
        err_file = open(task_dir+"/stderr.txt", "w")
        if proc.returncode == 0:
                status = "Successful"
        else:
                status = "Unsuccessful"
        err_file.write("Program Execution Was " + status+ "!\n")
        if err:
                err_file.write(err.decode())
        err_file.close()
        run_file = open(task_dir+"/runtime.txt", "w")
        run_file.write(str("{:.2f}".format(time.time() - start_time))+" SECONDS")
        run_file.close()
        results_to_server(task_dir, filename)
        print('RESPONDING TO SERVER ABOUT COMPLETION')
        resp_mesg = "DONE"+task_dir
        print(s.send(str.encode(resp_mesg)))


def return_stats(s):

        with open('/proc/meminfo') as file:
                for line in file:
                        if 'MemTotal' in line:
                                total = line.split()[1]
                        if 'MemFree' in line:
                                free = line.split()[1]
                        if 'MemAvailable' in line:
                                available = line.split()[1]
                                break

        with open('/proc/cpuinfo') as file:
                for line in file:
                        if 'siblings' in line:
                                #print(line)
                                siblings = line.split()[2]
                        if 'cpu cores' in line:
                                #print(line)
                                cores = line.split()[3]
                                break

        work_dir = os.getcwd()
        stat = shutil.disk_usage(work_dir)

        stats_details = "ret_s\n ------\nClient "+str(s.getsockname())+" statistics:\nMemory in MB:\nTotal:"+str(int(int(total)/1000))+", Free:"+str(int(int(free)/1000))+", Available:"+str(int(int(available)/1000))+"\n"
        stats_details += "CPU info:\nCore(s):"+cores+", Thread(s):"+str(int(int(siblings)/int(cores)))+", Core(s) with hyper-threading:"+siblings
        stats_details += "\nDisk usage in KB:\n"+str(stat)+"\n ------\n"
        s.send(str.encode(stats_details))

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

        s.send(str.encode("CLIENT"))
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


                                elif (data.decode() == 's'):
                                        return_stats(s)


                                elif data.decode().startswith('TASK'):
                                        digits = 1
                                        while data.decode()[4+digits].isdigit():
                                                digits += 1
                                                print('MULTIPLE DIGITS')

                                        print('EXECUTING', data.decode()[:4+digits])
                                        execute_task(data.decode(),s,digits)


                                else :
                                        #print data
                                        sys.stdout.write(data.decode())
                                        prompt()

                        #user entered a message
                        else :
                                msg = sys.stdin.readline().replace('\n','')
                                s.send(str.encode(msg))
                                prompt()
