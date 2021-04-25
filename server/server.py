import socket, select, os, shutil, time, shelve, sqlite3, smtplib, ssl
from itertools import count, filterfalse


def enqueue(directory, id):
        print(directory, "OF USER WITH ID", id, "IS ADDED TO QUEUE")
        if not queued_tasks:
                queued_tasks.append(directory)
                return

        queued_tasks.append(directory)
        update_queue()

def update_queue():
        conn = sqlite3.connect('db_server.db')
        cursor = conn.execute('SELECT UserId, ExecTime FROM Users')
        for row in cursor:
                user_exec_time[row[0]] = row[1]
        conn.close()


        print("===================BEFORE UPDATING===================")
        print(queued_tasks)
        print("=====================================================")
        priority = len(queued_tasks)-1
        id = task_user_map[queued_tasks[len(queued_tasks)-1]]
        for i in range(len(queued_tasks)-2, -1, -1):
                temp_id = task_user_map[queued_tasks[i]]
                if temp_id == id:
                        priority = i
                elif user_exec_time[temp_id] <= user_exec_time[id]:
                        priority = i
                        id = temp_id
        if priority != 0:
                # queued_tasks[0], queued_tasks[priority] = queued_tasks[priority], queued_tasks[0]
                queued_tasks.insert(0,queued_tasks.pop(priority))

        print("===================AFTER UPDATING====================")
        print(queued_tasks)
        print("=====================================================")

def update_exec_times(task_dir, time):
        user_id = task_user_map[task_dir]
        conn = sqlite3.connect('db_server.db')
        conn.execute("UPDATE Users SET ExecTime = ExecTime +"+str(time)+" WHERE UserId ="+str(user_id))
        conn.commit()
        conn.close()
        if len(queued_tasks) > 1:
                update_queue()


def remove_datafile(submit_file, task_dir):
        current = os.getcwd()
        os.chdir(os.path.join(current, task_dir))
        data = None
        executable = None
        with open(submit_file) as file:
                for line in file:
                        if 'executable' in line:
                                executable = line.split()[2]
                        if 'data' in line:
                                data = line.split()[2]
        if data is not None:
                os.remove(data)
        os.remove(executable)

        os.chdir(current)

def job_status(sock):
        print('Listing running and queued tasks')
        message = "JOB-status\nACTIVE:\n"
        if len(running_tasks) == 0:
                message += "    NO TASKS ARE RUNNING RIGHT NOW.\n"
        else:
                for key in running_tasks:
                        start_time = execution_time[running_tasks[key]]
                        run_time = "{:.2f}".format(time.time() - start_time)
                        message += "    "+str(running_tasks[key])+" IS RUNNING ON CLIENT #" + str(addr_to_number[key]) + ".        EXECUTION TIME: "+str(run_time)+" SECONDS.\n"

        message += "QUEUE:\n"
        if len(queued_tasks) == 0:
                message += "    NO TASKS ARE QUEUED RIGHT NOW."
        else:
                for task in queued_tasks:
                        message += "    "+str(task)+" IS WAITING IN THE QUEUE.\n"
        try:
                sock.send(str.encode(message))
        except:
                addr = socket_to_execute.getpeername()
                socket_to_execute.close()
                CONNECTIONS.remove(socket_to_execute)
                active_addr.remove(addr)

def finish_task(task_dir):
        shutil.rmtree(task_dir)
        if (len(tasks_to_return) > 0):
                get_waiting_results()

def execute_queued():
        for x in queued_tasks:
                task_no = x[4:]
                send_to_execute_queued(x)

def send_results(task_dir, submit_file, execution_sock):
        remove_datafile(submit_file, task_dir)
        user_id = task_user_map[task_dir]
        user_return = control_clients[user_id]

        exec_time = (time.time() - execution_time[task_dir])/60
        update_exec_times(task_dir, exec_time)

        if user_return in CONNECTIONS:
                send_email(user_id, task_dir, exec_time)
                running_tasks.pop(execution_sock.getpeername())
                busy_connections.remove(execution_sock)
                AVAIL_CONNECTIONS.append(execution_sock)
                execution_time.pop(task_dir)
                del task_user_map[task_dir]
                user_return.send(str.encode("DONE"+task_dir))
        else:
                send_email(user_id, task_dir, exec_time)
                running_tasks.pop(execution_sock.getpeername())
                start_time = execution_time[task_dir]
                execution_time[task_dir] = time.time() - start_time
                busy_connections.remove(execution_sock)
                AVAIL_CONNECTIONS.append(execution_sock)
                tasks_to_return.append(task_dir)
        execute_queued()

def send_waiting(task_dir):
        user_id = task_user_map[task_dir]
        user_return = control_clients[user_id]
        user_return.send(str.encode("RETURN"+task_dir))

def get_waiting_results():
        if len(tasks_to_return) > 0:
                for task_dir in tasks_to_return:
                        if control_clients[task_user_map[task_dir]] in CONNECTIONS:
                                send_waiting(task_dir)
                                tasks_to_return.remove(task_dir)
        else:
                print("All results returned")

def send_to_execute_queued(directory):
        files = os.listdir(directory)
        submit_msg = ""
        for file in files:
                if file.endswith('.txt'):
                        submit_msg = directory+file
                        break;
        if not submit_msg:
                return
        socket_to_execute = None
        for socket in AVAIL_CONNECTIONS:
                if socket != server_socket:
                        socket_to_execute = socket
                        break
        if socket_to_execute is None:
                print('No clients available, still in queue.')
        else:
                running_tasks[socket_to_execute.getpeername()] = directory
                busy_connections.append(socket_to_execute)
                AVAIL_CONNECTIONS.remove(socket_to_execute)
                queued_tasks.remove(directory)
                try:
                        execution_time[directory] = time.time()
                        socket_to_execute.send(str.encode(submit_msg))
                except:
                        execution_time.pop(directory)
                        addr = socket_to_execute.getpeername()
                        socket_to_execute.close()
                        CONNECTIONS.remove(socket_to_execute)
                        busy_connections.remove(socket_to_execute)
                        active_addr.remove(addr)

def send_to_execute (filename, sock, task_no):
        directory = "TASK"+str(task_no)
        parent_dir = os.getcwd()
        path = os.path.join(parent_dir, directory)
        os.mkdir(path)

        for id, user in control_clients.items():
                if user == sock:
                        task_user_map[directory] = id
                        break

        executable = None
        data = None
        email = None
        selected_client = None
        with open(filename) as file:
                for line in file:
                        if 'executable' in line:
                                executable = line.split()[2]
                        if 'data' in line:
                                data = line.split()[2]
                        if 'email' in line:
                                email = line.split()[2]
                        if 'client' in line:
                                selected_client = line.split()[2]
                                if selected_client == "default":
                                        selected_client = None
        if email is not None:
                update_id = None
                for id, user in control_clients.items():
                        if user == sock:
                                update_id = id
                                break
                update_email(update_id, email)

        shutil.move(filename, directory)
        shutil.move(executable, directory)
        if data is not None:
                shutil.move(data, directory)

        submit_msg = directory + filename

        socket_to_execute = None
        if selected_client is not None:
                for socket in AVAIL_CONNECTIONS:
                        if client_no[socket] == int(selected_client):
                                socket_to_execute = socket
        else:
                for socket in AVAIL_CONNECTIONS:
                        if socket != server_socket:
                                socket_to_execute = socket
                                break

        if socket_to_execute is None:
                # ENQUEUE METHOD?
                enqueue(directory, task_user_map[directory])
                # queued_tasks.append(directory)
                print('No clients available, added to queue')

        else:
                # ADD TO RUNNING QUEUE
                running_tasks[socket_to_execute.getpeername()] = directory
                busy_connections.append(socket_to_execute)
                AVAIL_CONNECTIONS.remove(socket_to_execute)
                try:
                        execution_time[directory] = time.time()
                        socket_to_execute.send(str.encode(submit_msg))
                except:
                        execution_time.pop(directory)
                        addr = socket_to_execute.getpeername()
                        socket_to_execute.close()
                        CONNECTIONS.remove(socket_to_execute)
                        busy_connections.remove(socket_to_execute)
                        active_addr.remove(addr)

#Function to broadcast chat messages to all connected clients
def broadcast_data (sock, message):
        #Do not send the message to master socket and the client who has send us the message
        for socket in CONNECTIONS:
                if socket != server_socket and socket != sock :
                        try :
                                socket.send(str.encode(message))
                        except :
                                # broken socket connection may be, chat client pressed ctrl+c for example
                                addr = socket.getpeername()
                                socket.close()
                                CONNECTIONS.remove(socket)
                                AVAIL_CONNECTIONS.remove(socket)
                                active_addr.remove(addr)


def clients_status (sock,curr_addr):
        if (len(AVAIL_CONNECTIONS) < 1) and (len(busy_connections) == 0):
                try:
                        print("try to send empty addresses")
                        sock.send(str.encode("a \n--------------------\nNO CLIENTS CONNECTED"))
                except:
                        sock.close()
                        CONNECTIONS.remove(socket)
                        AVAIL_CONNECTIONS.remove(socket)
                        active_addr.remove(curr_addr)
                return

        message = "a \nAVAILABLE CLIENTS:\n"
        if len(AVAIL_CONNECTIONS) > 0:
                for socket in AVAIL_CONNECTIONS:
                        if socket != control_sock:
                                message += "CLIENT #"+str(client_no[socket])+"\n"
                                # message += "    CLIENT WIHT ADDRESS: "+str(socket.getpeername())+"\n"
        else:
                message += "    NO AVAILABLE CLIENTS RIGHT NOW\n"

        message += "BUSY CLIENTS:\n"
        if len(busy_connections) > 0:
                for socket in busy_connections:
                        message += "CLIENT #" + str(client_no[socket])+"\n"
                        # message += "    CLIENT WITH ADDRESS: "+str(socket.getpeername())+"\n"
        else:
                message += "    NO WORKING CLIENTS RIGHT NOW"
        try:
                sock.send(str.encode(message))
        except:
                sock.close()
                CONNECTIONS.remove(socket)
                AVAIL_CONNECTIONS.remove(socket)
                active_addr.remove(curr_addr)

def return_id (sock, id_no):
        sock.send(str.encode("CONTROL_ID"+str(id_no)))

def get_task_no():
        conn = sqlite3.connect('db_server.db')
        cursor = conn.execute("SELECT TasksCount FROM Tasks")
        for row in cursor:
                ret = row[0]
                conn.close()
                return ret

def get_control_no():
        conn = sqlite3.connect('db_server.db')
        cursor = conn.execute("SELECT UsersCount FROM Ucount")
        for row in cursor:
                ret = row[0]
                conn.close()
                return ret

def update_task_no():
        conn = sqlite3.connect('db_server.db')
        conn.execute("UPDATE Tasks SET TasksCount = TasksCount + 1")
        conn.commit()
        conn.close()

def update_control_no():
        conn = sqlite3.connect('db_server.db')
        conn.execute("UPDATE Ucount SET UsersCount = UsersCount + 1")
        conn.commit()
        conn.close()

def new_user(id):
        conn = sqlite3.connect('db_server.db')
        conn.execute("INSERT INTO Users VALUES ("+str(id)+", 0, '')")
        conn.commit()
        conn.close()

def update_email(id, email):
        conn = sqlite3.connect('db_server.db')
        conn.execute("UPDATE Users SET Mail = '"+email+"' WHERE UserId = " + str(id))
        conn.commit()
        conn.close()

def send_email(user_id, task_dir, exec_time):
        conn = sqlite3.connect('db_server.db')
        cursor = conn.execute("SELECT Mail FROM Users WHERE UserId = " + str(user_id))
        for row in cursor:
                email = row[0]
                break
        conn.close()
        port = 465 # FOR SSL
        password = "mik@sdev1"
        # Create a secure SSL context
        context = ssl.create_default_context()
        message = """\
        Subject:Compute Results Notification


        Your submitted job """+ task_dir+ """ was executed after """ +str(round(exec_time,2))+""" minutes.

        Go check your results. """
        sender_email = "mikas.devtest@gmail.com"
        receiver_email = email

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                server.login(sender_email, password)
                # TO DO: send email
                server.sendmail(sender_email, receiver_email, message)
        print('email sent')


if __name__ == "__main__":

        control_count = get_control_no()
        task_count = get_task_no()
        CONNECTIONS = []
        AVAIL_CONNECTIONS = []
        active_addr = []
        busy_connections = []
        running_tasks = {}
        queued_tasks = []
        execution_time = {}
        tasks_to_return = []
        statistics = {}
        RECV_BUFFER = 4096 # Advisable to keep it as an exponent of 2
        PORT = 5002
        host_addr = ("0.0.0.0",PORT)
        control_sock = None
        control_clients = {}
        task_user_map = {}
        user_exec_time = {}
        client_no = {}
        addr_to_number = {}


        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("0.0.0.0", PORT))
        server_socket.listen(10)


        # Add server socket to the list of readable connections
        CONNECTIONS.append(server_socket)
        #AVAIL_CONNECTIONS.append(server_socket)

        print("server started on port " + str(PORT))

        while 1:
                # Get the list sockets which are ready to be read through select
                read_sockets,write_sockets,error_sockets = select.select(CONNECTIONS,[],[], 1)

                for sock in read_sockets:
                        #New connection
                        if sock == server_socket:
                                # Handle the case in which there is a new connection recieved through server_socket
                                sockfd, addr = server_socket.accept()
                                CONNECTIONS.append(sockfd)
                                AVAIL_CONNECTIONS.append(sockfd)
                                active_addr.append(addr)
                                print("Client (%s, %s) connected" % addr)


                        #Some incoming message from a client
                        else:
                                # Data recieved from client, process it
                                try:
                                        data = sock.recv(RECV_BUFFER)
                                        addr = sock.getpeername()
                                except:
                                        print("Cannot recieve data")
                                        sock.send(str.encode("error"))
                                if data:
                                        if data.decode() == 'a':
                                                print("getting a command")
                                                addr_curr = sock.getpeername()
                                                clients_status(sock, addr_curr)


                                        if data.decode().startswith('SUBMIT'):
                                                print(sock.getpeername())
                                                if control_sock is None:
                                                        control_sock = sock

                                                print('Task ' + str(task_count) + ' sending for execution')
                                                update_task_no()
                                                task_count += 1
                                                send_to_execute(data.decode()[7:],sock, task_count-1)
                                                ret_msg = "CONFIRM_TASK"+str(task_count-1)+data.decode()[7:]
                                                sock.send(str.encode(ret_msg))

                                        elif data.decode().startswith('JOB-status'):
                                                job_status(sock)

                                        elif data.decode().startswith('DONE'):
                                                digits = 1
                                                while data.decode()[8+digits].isdigit():
                                                        digits += 1

                                                send_results(data.decode()[4:8+digits],data.decode()[8+digits:],sock)

                                        elif data.decode().startswith('FINISH'):
                                                finish_task(data.decode()[6:])


                                        elif data.decode().startswith('RETRIEVE'):
                                                get_waiting_results()

                                        elif data.decode().startswith('EMAIL'):
                                                update_id = None
                                                for id, user in control_clients.items():
                                                        if user == sock:
                                                                update_id = id
                                                                break
                                                update_email(update_id, data.decode()[5:])
                                                print('email')

                                        elif data.decode().startswith('CONTROL'):
                                                # CONTROL SOCK CONNECTS, ADD TO THE LIST OF THESE SOCKS
                                                control_sock = sock
                                                if sock in control_clients.values():
                                                        print('CONTROL CLIENT',control_clients[sock],'HAS CONNECTED')
                                                else:
                                                        control_clients[control_count] = sock
                                                        control_count += 1
                                                        update_control_no()

                                                new_user(control_count-1)

                                                if sock in AVAIL_CONNECTIONS:
                                                        AVAIL_CONNECTIONS.remove(sock)

                                                return_id(sock, control_count-1)
                                                if len(tasks_to_return) > 0:
                                                        sock.send(str.encode("RETRIEVE"))

                                        elif data.decode().startswith('CLIENT'):
                                                print("CLIENT CONNECTED, ITS STATS:\n")
                                                if len(client_no) == 0:
                                                        client_no[sock] = 1
                                                else:
                                                        client_no[sock] = next(filterfalse(set(client_no.values()).__contains__, count(1)))
                                                statistics[sock] = "Client #"+str(client_no[sock])+":\n"+data.decode()[6:]
                                                addr_to_number[sock.getpeername()] = client_no[sock]
                                                print(statistics[sock])
                                                execute_queued()

                                        elif data.decode().startswith('EXISTING_CONTROL'):
                                                control_clients[int(data.decode()[16:])] = sock
                                                if sock in AVAIL_CONNECTIONS:
                                                        AVAIL_CONNECTIONS.remove(sock)
                                                print("CONTROL CLIENT ID IS:",int(data.decode()[16:]))
                                                if len(tasks_to_return) > 0:
                                                        sock.send(str.encode("RETRIEVE"))

                                        elif data.decode() == 's':
                                                return_string = '\n'.join(statistics.values())
                                                try:
                                                        print("try to send s")
                                                        sock.send(str.encode("s \n"+return_string))
                                                except:
                                                        print("unsuccessful")
                                                        sock.close()
                                                        CONNECTIONS.remove(socket)
                                                        AVAIL_CONNECTIONS.remove(socket)
                                                        active_addr.remove(curr_addr)


                                        else:
                                                broadcast_data(sock, "\r" + '<' + str(sock.getpeername()) + '> ' + data.decode())

                                else:
                                        broadcast_data(sock, "Client (%s, %s) is offline" % addr)
                                        print("Client (%s, %s) is offline" % addr)
                                        if (sock == control_sock):
                                                control_sock = None
                                        sock.close()
                                        CONNECTIONS.remove(sock)
                                        if sock in AVAIL_CONNECTIONS:
                                                AVAIL_CONNECTIONS.remove(sock)
                                        statistics.pop(sock, None)
                                        client_no.pop(sock,None)
                                        print(active_addr)
                                        active_addr.remove(addr)
                                        continue
        server_socket.close()
