import socket, select, os, shutil

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
                print('No clients available')
        else:
                busy_connections.append(socket_to_execute)
                AVAIL_CONNECTIONS.remove(socket_to_execute)
                try:
                        socket_to_execute.send(str.encode(submit_msg))
                except:
                        addr = socket_to_execute.getpeername()
                        socket_to_execute.close()
                        AVAIL_CONNECTIONS.remove(socket_to_execute)
                        busy_connections.remove(socket_to_execute)
                        active_addr.remove(addr)


#Function to broadcast chat messages to all connected clients
def broadcast_data (sock, message):
        #Do not send the message to master socket and the client who has send us the message
        for socket in AVAIL_CONNECTIONS:
                if socket != server_socket and socket != sock :
                        try :
                                socket.send(str.encode(message))
                        except :
                                # broken socket connection may be, chat client pressed ctrl+c for example
                                addr = socket.getpeername()
                                socket.close()
                                AVAIL_CONNECTIONS.remove(socket)
                                active_addr.remove(addr)

def get_statistics(sock):
        for socket in AVAIL_CONNECTIONS:
                if socket != server_socket and socket != sock:
                        try:
                                socket.send(str.encode('s'))
                        except:
                                addr = socket.getpeername()
                                socket.close()
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
                AVAIL_CONNECTIONS.remove(control_sock)
                active_addr.remove(addr)


def clients_status (sock,curr_addr):
        message = "a \n ------\n"+str(len(active_addr)-1)+" active clients with addresses:\n"
        for addr in active_addr:
                if addr != curr_addr:
                        message += str(addr)+'\n'
                        print(addr)
        message += " ------\n"
        try:
                sock.send(str.encode(message))
        except:
                sock.close()
                AVAIL_CONNECTIONS.remove(socket)
                active_addr.remove(curr_addr)


if __name__ == "__main__":

        # List to keep track of socket descriptors
        task_count = 1
        AVAIL_CONNECTIONS = []
        active_addr = []
        busy_connections = []
        statistics = {}
        RECV_BUFFER = 4096 # Advisable to keep it as an exponent of 2
        PORT = 5000
        host_addr = ("0.0.0.0",PORT)
        control_sock = None

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # this has no effect, why ?
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("0.0.0.0", PORT))
        server_socket.listen(10)


        # Add server socket to the list of readable connections
        AVAIL_CONNECTIONS.append(server_socket)

        print("server started on port " + str(PORT))

        while 1:
                # Get the list sockets which are ready to be read through select
                read_sockets,write_sockets,error_sockets = select.select(AVAIL_CONNECTIONS,[],[])

                for sock in read_sockets:
                        #New connection
                        if sock == server_socket:
                                # Handle the case in which there is a new connection recieved through server_socket
                                sockfd, addr = server_socket.accept()
                                AVAIL_CONNECTIONS.append(sockfd)
                                active_addr.append(addr)
                                print("Client (%s, %s) connected" % addr)

                                broadcast_data(sockfd, "[%s:%s] entered room\n" % addr)

                        #Some incoming message from a client
                        else:
                                # Data recieved from client, process it
                                data = sock.recv(RECV_BUFFER)
                                if data:
                                        if data.decode() == 'a':
                                                addr_curr = sock.getpeername()
                                                clients_status(sock, addr_curr)


                                        if data.decode().startswith('SUBMIT'):
                                                print(sock.getpeername())
                                                if len(AVAIL_CONNECTIONS) > 2:
                                                        print('Task ' + str(task_count) + ' sending for execution')
                                                        task_count += 1
                                                        send_to_execute(data.decode()[7:],sock, task_count-1)
                                                else:
                                                        print('no clients available')


                                        elif data.decode().startswith('ret_s'):
                                                send_statistics(data.decode()[5:],sock.getpeername())


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
                                        sock.close()
                                        AVAIL_CONNECTIONS.remove(sock)
                                        active_addr.remove(addr)
                                        continue

        server_socket.close()
