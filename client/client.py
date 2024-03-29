import socket, select, string, sys, os, shutil, subprocess, time, io
from ftplib import FTP
import tensorflow as tf


def results_to_server(task_dir, filename, data):
    result_files = os.listdir(task_dir)
    result_files.remove(filename)
    if data in result_files:
        result_files.remove(data)
    print(result_files)

    ftp = FTP("")
    ftp.connect("localhost", 1026)
    ftp.login()
    ftp.cwd(task_dir)  # replace with your directory
    for x in range(len(result_files)):
        filename = result_files[x]
        ftp.storbinary("STOR " + filename, open(task_dir + "/" + filename, "rb"))
    ftp.quit()
    shutil.rmtree(task_dir)


def get_file(filename, task_dir):
    ftp = FTP("")
    ftp.connect("localhost", 1026)
    ftp.login()
    parent_dir = os.getcwd()
    path = os.path.join(parent_dir, task_dir)
    os.mkdir(path)
    ftp.cwd(task_dir)  # replace with directory in server?

    localfile = open(task_dir + "/" + filename, "wb")
    ftp.retrbinary("RETR " + filename, localfile.write, 1024)
    localfile.close()

    executable = None
    data = None

    current = os.getcwd()
    os.chdir(os.path.join(current, task_dir))

    with open(filename) as file:
        for line in file:
            if "executable" in line:
                executable = line.split()[2]
            if "data" in line:
                data = line.split()[2]
    os.chdir(current)
    localfile = open(task_dir + "/" + executable, "wb")
    ftp.retrbinary("RETR " + executable, localfile.write, 1024)
    localfile.close()

    if data is not None:
        localfile = open(task_dir + "/" + data, "wb")
        ftp.retrbinary("RETR " + data, localfile.write, 1024)
        localfile.close()

    ftp.quit()


def execute_task(submit_msg, s, digits):
    task_dir = submit_msg[: 4 + digits]
    task_no = int(submit_msg[4 : 4 + digits])
    submit_file = submit_msg[4 + digits :]
    get_file(submit_file, task_dir)

    current = os.getcwd()
    os.chdir(os.path.join(os.getcwd(), task_dir))
    data = None
    with open(submit_file) as file:
        for line in file:
            if "executable" in line:
                filename = line.split()[2]
            if "data" in line:
                data = line.split()[2]

    run_program = "python " + filename + " > stdout.txt"
    start_time = time.time()
    proc = subprocess.Popen(run_program, stderr=subprocess.PIPE, shell=True)
    total_time = time.time() - start_time
    (out, err) = proc.communicate()
    err_file = open("stderr.txt", "w")
    if proc.returncode == 0:
        status = "Successful"
    else:
        status = "Unsuccessful"
    err_file.write("Program Execution Was " + status + "!\n")
    if err:
        err_file.write(err.decode())
    err_file.close()
    run_file = open("runtime.txt", "w")
    run_file.write(str("{:.2f}".format(time.time() - start_time)) + " SECONDS")
    run_file.close()
    os.chdir(current)
    results_to_server(task_dir, filename, data)
    print("RESPONDING TO SERVER ABOUT COMPLETION")
    resp_mesg = "DONE" + task_dir + submit_file
    print(s.send(str.encode(resp_mesg)))


def return_stats():
    with open("/proc/meminfo") as file:
        for line in file:
            if "MemTotal" in line:
                total = line.split()[1]
            if "MemFree" in line:
                free = line.split()[1]
            if "MemAvailable" in line:
                available = line.split()[1]
                break

    with open("/proc/cpuinfo") as file:
        for line in file:
            if "siblings" in line:
                siblings = line.split()[2]
            if "cpu cores" in line:
                cores = line.split()[3]
                break

    work_dir = os.getcwd()

    stat = ""
    gpus = tf.config.list_physical_devices("GPU")
    if len(gpus) > 0:
        stat += "CUDA compatible GPU: Yes"
    else:
        stat += "CUDA compatible GPU: No"

    stats_details = "RAM available:" + str(int(int(available) / (1024 * 1024))) + "\n"
    stats_details += (
        "Number of CPU cores:"
        + cores
        + ", Thread(s):"
        + str(int(int(siblings) / int(cores)))
    )
    stats_details += "\n" + str(stat) + "\n"
    return stats_details


# main function
if __name__ == "__main__":
    os.environ["TF_XLA_FLAGS"] = "--tf_xla_enable_xla_devices"

    if len(sys.argv) < 3:
        print("Usage : python client.py localhost port")
        sys.exit()

    host = sys.argv[1]
    port = int(sys.argv[2])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)

    # connect to remote host
    try:
        s.connect((host, port))
    except:
        print("Unable to connect")
        sys.exit()

    stats = return_stats()
    s.send(str.encode("CLIENT" + stats))
    print("Connected to the server")

    while 1:
        socket_list = [s]

        # Get the list sockets which are readable
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

        for x in range(0, len(read_sockets)):
            # incoming message from remote server
            if read_sockets[x] == s:
                data = read_sockets[x].recv(4096)
                if not data:
                    print("\nDisconnected from chat server")
                    sys.exit()

                elif data.decode() == "s":
                    return_stats(s)

                elif data.decode().startswith("TASK"):
                    digits = 1
                    while data.decode()[4 + digits].isdigit():
                        digits += 1
                    print("\n\n------------------------------")
                    print("EXECUTING", data.decode()[: 4 + digits])
                    execute_task(data.decode(), s, digits)
