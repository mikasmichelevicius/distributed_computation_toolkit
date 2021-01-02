import socket, select, os, shutil, time, shelve

def job_status(sock):
        print('Listing running and queued tasks')
        message = "JOB-status\nACTIVE:\n"
        if len(running_tasks) == 0:
                message += "    NO TASKS ARE RUNNING RIGHT NOW.\n"
        else:
                for key in running_tasks:
                        start_time = execution_time[running_tasks[key]]
                        run_time = "{:.2f}".format(time.time() - start_time)
                        message += "    "+str(running_tasks[key])+" IS RUNNING ON HOST " + str(key) + ".\n        EXECUTION TIME: "+str(run_time)+" SECONDS.\n"

        message += "\nQUEUE:\n"
        if len(queued_tasks) == 0:
                message += "    NO TASKS ARE QUEUED RIGHT NOW.\n"
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

def send_results(task_dir, execution_sock):
        if control_sock:
                running_tasks.pop(execution_sock.getpeername())
                execution_time.pop(task_dir)
                busy_connections.remove(execution_sock)
                AVAIL_CONNECTIONS.append(execution_sock)
                control_sock.send(str.encode("DONE"+task_dir))
        else:
                running_tasks.pop(execution_sock.getpeername())
                start_time = execution_time[task_dir]
                execution_time[task_dir] = time.time() - start_time
                busy_connections.remove(execution_sock)
                AVAIL_CONNECTIONS.append(execution_sock)
                tasks_to_return.append(task_dir)
        execute_queued()

def send_waiting(task_dir):
        control_sock.send(str.encode("RETURN"+task_dir))

def get_waiting_results():
        if len(tasks_to_return) > 0:
                task_dir = tasks_to_return[0]
                send_waiting(task_dir)
                tasks_to_return.remove(task_dir)
        else:
                print("All results returned")

def send_to_execute_queued(directory):
        files = os.listdir(directory)
        submit_msg = ""
        for file in files:
                if file.endswith('.py'):
                        submit_msg = directory+file
                        break;
        if not submit_msg:
                return
        socket_to_execute = None
        for socket in AVAIL_CONNECTIONS:
                if socket != server_socket and socket != control_sock:
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
        print(path)
        os.mkdir(path)

        shutil.move(filename, directory)

        submit_msg = directory + filename

        socket_to_execute = None
        for socket in AVAIL_CONNECTIONS:
                if socket != server_socket and socket != sock:
                        socket_to_execute = socket
                        break

        if socket_to_execute is None:
                queued_tasks.append(directory)
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

def get_statistics(sock):
        for socket in CONNECTIONS:
                if socket != server_socket and socket != sock:
                        try:
                                socket.send(str.encode('s'))
                        except:
                                addr = socket.getpeername()
                                socket.close()
                                CONNECTIONS.remove(socket)
                                AVAIL_CONNECTIONS.remove(socket)
                                active_addr.remove(addr)

def send_statistics(message,addr_curr):
        if addr_curr not in statistics and addr_curr != control_sock.getpeername():
                statistics[addr_curr] = message
        try:
                control_sock.send(str.encode(message))
        except:
                addr = control_sock.getpeername()
                control_sock.close()
                CONNECTIONS.remove(control_sock)
                AVAIL_CONNECTIONS.remove(control_sock)
                active_addr.remove(addr)

def clients_status (sock,curr_addr):
        if (len(AVAIL_CONNECTIONS) < 2) and (len(busy_connections) == 0):
                try:
                        sock.send(str.encode("a \n____________________\nNO CLIENTS CONNECTED"))
                except:
                        sock.close()
                        CONNECTIONS.remove(socket)
                        AVAIL_CONNECTIONS.remove(socket)
                        active_addr.remove(curr_addr)
                return

        message = "a \nAVAILABLE CLIENTS:\n"
        if len(AVAIL_CONNECTIONS) > 1:
                for socket in AVAIL_CONNECTIONS:
                        if socket != control_sock:
                                message += "    CLIENT WIHT ADDRESS: "+str(socket.getpeername())+"\n"
        else:
                message += "    NO AVAILABLE CLIENTS RIGHT NOW\n"

        message += "\nBUSY CLIENTS:\n"
        if len(busy_connections) > 0:
                for socket in busy_connections:
                        message += "    CLIENT WITH ADDRESS: "+str(socket.getpeername())+"\n"
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

if __name__ == "__main__":

        if os.path.isfile('data.db'):
                d = shelve.open('data.db')
                control_count = d['id_count']
                d.close()
        else:
                d = shelve.open('data.db')
                d['id_count'] = 0
                control_count = 0
                d.close()
        # List to keep track of socket descriptors
        task_count = 1
        # control_count = 1
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
        PORT = 5000
        host_addr = ("0.0.0.0",PORT)
        control_sock = None
        control_clients = {}

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
                read_sockets,write_sockets,error_sockets = select.select(CONNECTIONS,[],[])

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
                                data = sock.recv(RECV_BUFFER)
                                addr = sock.getpeername()
                                if data:
                                        if data.decode() == 'a':
                                                addr_curr = sock.getpeername()
                                                clients_status(sock, addr_curr)


                                        if data.decode().startswith('SUBMIT'):
                                                print(sock.getpeername())
                                                if control_sock is None:
                                                        control_sock = sock

                                                print('Task ' + str(task_count) + ' sending for execution')
                                                task_count += 1
                                                send_to_execute(data.decode()[7:],sock, task_count-1)
                                                ret_msg = "CONFIRM_TASK"+str(task_count-1)+data.decode()[7:]
                                                sock.send(str.encode(ret_msg))

                                        elif data.decode().startswith('JOB-status'):
                                                job_status(sock)

                                        elif data.decode().startswith('DONE'):
                                                send_results(data.decode()[4:],sock)

                                        elif data.decode().startswith('FINISH'):
                                                finish_task(data.decode()[6:])


                                        elif data.decode().startswith('ret_s'):
                                                send_statistics(data.decode()[5:],sock.getpeername())

                                        elif data.decode().startswith('RETRIEVE'):
                                                get_waiting_results()

                                        elif data.decode().startswith('CONTROL'):
                                                # CONTROL SOCK CONNECTS, ADD TO THE LIST OF THESE SOCKS
                                                control_sock = sock
                                                if sock in control_clients.keys():
                                                        print('CONTROL CLIENT',control_clients[sock],'HAS CONNECTED')
                                                else:
                                                        control_clients[sock] = control_count
                                                        control_count += 1
                                                        d = shelve.open('data.db')
                                                        d['id_count'] = control_count
                                                        d.close()

                                                return_id(sock, control_count)
                                                if len(tasks_to_return) > 0:
                                                        sock.send(str.encode("RETRIEVE"))

                                        elif data.decode().startswith('CLIENT'):
                                                execute_queued()

                                        elif data.decode().startswith('EXISTING_CONTROL'):
                                                control_clients[sock] = int(data.decode()[16:])
                                                print("CONTROL CLIENT ID IS:",control_clients[sock])

                                        elif data.decode() == 's':
                                                print(len(statistics), len(active_addr))
                                                if len(statistics) == len(active_addr)-1:
                                                        message = ""
                                                        for x in statistics:
                                                                message += statistics[x]
                                                        print('Retrieving stored info')
                                                        send_statistics(message,sock.getpeername())
                                                else:
                                                        control_sock = sock
                                                        get_statistics(sock)


                                        else:
                                                broadcast_data(sock, "\r" + '<' + str(sock.getpeername()) + '> ' + data.decode())

                                else:
                                        broadcast_data(sock, "Client (%s, %s) is offline" % addr)
                                        print("Client (%s, %s) is offline" % addr)
                                        if (sock == control_sock):
                                                control_sock = None
                                        sock.close()
                                        CONNECTIONS.remove(sock)
                                        AVAIL_CONNECTIONS.remove(sock)
                                        print(active_addr)
                                        active_addr.remove(addr)
                                        continue

        server_socket.close()
