import socket, select, string, sys, py_compile, os, shelve, sqlite3, subprocess
from ftplib import FTP


def does_compile(filename):
    try:
        py_compile.compile(filename, doraise=True)
        return True
    except py_compile.PyCompileError:
        print("PROGRAM DOES NOT COMPILE!")
        return False


def get_results(task_dir, s):
    parent_dir = os.getcwd()
    path = os.path.join(parent_dir, task_dir)
    os.mkdir(path)
    ftp = FTP("")
    ftp.connect("localhost", 1026)
    ftp.login()
    ftp.cwd(task_dir)
    for file_name in ftp.nlst():
        localfile = open(task_dir + "/" + file_name, "wb")
        ftp.retrbinary("RETR " + file_name, localfile.write, 1024)
    ftp.quit()
    localfile.close()
    with open(task_dir + "/runtime.txt", "r") as file:
        run_time = file.read().replace("\n", "")
    os.remove(task_dir + "/runtime.txt")
    print(
        "\n       FINISHED EXECUTION OF",
        task_dir,
        " IN "
        + run_time
        + "\n        \____ RESULTS CAN BE FOUND IN DIRECTORY /"
        + task_dir,
    )
    s.send(str.encode("FINISH" + task_dir))


def send_file(sub_file, s):
    ftp = FTP("")
    ftp.connect("localhost", 1026)
    ftp.login()
    ftp.cwd("")  # replace with your directory
    executable = None
    data = None
    email = None
    filename = sub_file
    with open(filename, "r") as file:
        for line in file:
            if "executable" in line:
                executable = line.split()[2]
            if "data" in line:
                data = line.split()[2]

    ftp.storbinary("STOR " + filename, open(filename, "rb"))
    ftp.storbinary("STOR " + executable, open(executable, "rb"))
    if data is not None:
        ftp.storbinary("STOR " + data, open(data, "rb"))
    ftp.quit()
    os.remove(sub_file)
    os.remove(executable)
    if data is not None:
        os.remove(data)


def save_id(id):
    conn = sqlite3.connect("db_control.db")
    conn.execute("INSERT INTO UserID VALUES (" + str(id) + ")")
    conn.commit()
    conn.close()


def prompt():
    if enable_cli:
        sys.stdout.write("\nConnected clients - write a")
        sys.stdout.write("\nStatistics of clients - write s")
        sys.stdout.write("\nQueue and running tasks - JOB-status")
        sys.stdout.write("\nTask submission - SUBMIT filename.txt")
        sys.stdout.write("\nTo disable command-line usage - write disable\n")
    else:
        sys.stdout.write("\nTo enable command-line usage - write enable\n")
    sys.stdout.flush()


# main function
if __name__ == "__main__":

    enable_cli = False

    tasks_count = 1
    client_id = None

    if len(sys.argv) < 3:
        print("Usage : python control_client.py hostname port")
        sys.exit()

    host = sys.argv[1]
    port = int(sys.argv[2])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect to remote host
    try:
        s.connect((host, port))
    except:
        print("Unable to connect")
        sys.exit()

    conn = sqlite3.connect("db_control.db")
    cursor = conn.execute("SELECT COUNT(*) FROM UserID")
    for row in cursor:
        if row[0] == 0:
            print("NEW USER CONNECTED")
            s.send(str.encode("CONTROL"))
            break
        else:
            cursor2 = conn.execute("SELECT Id FROM UserID")
            for data in cursor2:
                client_id = data[0]
                print(
                    "\n\n            CONNECTED TO THE SERVER.\n            YOUR ID IS:",
                    str(client_id),
                )
                s.send(str.encode("EXISTING_CONTROL" + str(client_id)))
                prompt()
                break
        break
    conn.close()

    while 1:
        socket_list = [sys.stdin, s]

        # Get the list sockets which are readable
        read_sockets, write_sockets, error_sockets = select.select(
            socket_list, [], [], 1
        )

        for x in range(0, len(read_sockets)):

            with open("fileA.txt", "r+") as file:
                if file.read(1):
                    file.seek(0, 0)
                    input_command = file.read()
                    file.truncate(0)
                    if input_command.startswith("SUBMIT"):
                        is_valid = True
                        if is_valid:
                            send_file(input_command[7:], s)
                            s.send(str.encode(input_command))

                    else:
                        s.send(str.encode(input_command))

            # incoming message from remote server
            if read_sockets[x] == s:
                data = read_sockets[x].recv(4096)
                if not data:
                    print("\nDisconnected from chat server")
                    sys.exit()
                elif data.decode().startswith("a"):
                    with open("fileB.txt", "w") as fileB:
                        fileB.write("addr\n" + data.decode()[3:])
                    if enable_cli:
                        value = data.decode()[5:]
                        if not value.startswith("---"):
                            sys.stdout.write("\n--------------------\n")
                        sys.stdout.write(data.decode()[3:])
                        sys.stdout.write("\n--------------------")
                        prompt()

                elif data.decode().startswith("DONE"):
                    get_results(data.decode()[4:], s)

                elif data.decode().startswith("error"):
                    with open("fileB.txt", "w") as fileB:
                        fileB.write(data.decode())
                        print("error written to file")

                elif data.decode().startswith("s"):
                    with open("fileB.txt", "w") as fileB:
                        fileB.write("stats\n" + data.decode()[3:])
                        fileB.flush()
                    if enable_cli:
                        value = data.decode()
                        sys.stdout.write("\n--------------------")
                        if len(value) == 3:
                            sys.stdout.write("\nNO CLIENTS CONNECTED")
                        else:
                            sys.stdout.write("\n" + data.decode()[3:])
                        if len(value) == 3:
                            sys.stdout.write("\n--------------------")
                        else:
                            sys.stdout.write("--------------------")
                        prompt()

                elif data.decode().startswith("RETURN"):
                    get_results(data.decode()[6:], s)

                elif data.decode().startswith("JOB-status"):
                    with open("fileB.txt", "w") as fileB:
                        fileB.write("jobs\n" + data.decode()[10:])
                    if enable_cli:
                        sys.stdout.write("\n--------------------")
                        sys.stdout.write(data.decode()[10:])
                        sys.stdout.write("\n--------------------")
                        prompt()
                elif data.decode().startswith("RETRIEVE"):
                    print(
                        "\n\n     RESULTS OF FINISHED TASKS ARE BEING RETRIEVED FROM SERVER\n"
                    )
                    s.send(str.encode("RETRIEVE"))
                elif data.decode().startswith("CONTROL_ID"):
                    print(
                        "\n\n            CONNECTED TO THE SERVER.\n            YOUR ID IS:",
                        data.decode()[10:],
                    )
                    client_id = int(data.decode()[10:])
                    save_id(client_id)
                    email_addr = input("Enter your email address:")
                    s.send(str.encode("EMAIL" + email_addr))
                    prompt()
                elif data.decode().startswith("CONFIRM"):
                    digits = 0
                    while data.decode()[13 + digits].isdigit():
                        digits += 1
                    print(
                        "\n       ",
                        data.decode()[13 + digits :],
                        "SENT FOR EXECUTION AS",
                        data.decode()[8 : 13 + digits],
                    )
                else:
                    print(".")

            # user entered a message
            else:
                msg = sys.stdin.readline().replace("\n", "")
                if msg.startswith("SUBMIT"):

                    # CHECK IF EXECUTABLE COMPILES
                    # is_valid = does_compile(msg[7:])
                    is_valid = True
                    if is_valid:
                        send_file(msg[7:], s)
                        s.send(str.encode(msg))

                elif msg.startswith("enable"):
                    enable_cli = True
                    prompt()

                elif msg.startswith("disable"):
                    enable_cli = False
                    prompt()

                elif msg == "s":
                    s.send(str.encode(msg))

                elif msg == "a":
                    s.send(str.encode(msg))

                elif msg.startswith("JOB-status"):
                    s.send(str.encode(msg))

                else:
                    print("\n--------------------------------------")
                    print("Input is incorrect. Please try again.")
                    print("--------------------------------------")
                    prompt()
