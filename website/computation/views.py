from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
import socket, select, string, sys, py_compile, os, shelve, sqlite3, time
from django.utils.datastructures import MultiValueDictKeyError
from ftplib import FTP
from subprocess import run

def prompt(request):
    username = request.user.username
    message = "You are connected to the server"
    return render(request, 'computation/home.html', {'username' : username, 'message': message})

def trigger_sock():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = ("0.0.0.0",5002)
    ret = sock.connect_ex(address)
    sock.close()
    return ret

def submit(request):
    if request.method == "POST":
        try:
            executable = request.FILES['executable']
        except MultiValueDictKeyError:
            executable = None
        try:
            dataset = request.FILES['dataset']
        except MultiValueDictKeyError:
            dataset = None

        email = request.POST['email']
        print("email====", email)
        
        if executable is not None:
            fs = FileSystemStorage()
            fs.save(executable.name, executable)
        else:
            print("Executable not uploaded")
        if dataset is not None:
            fsd = FileSystemStorage()
            fsd.save(dataset.name, dataset)
        else:
            print("Dataset not uploaded")


        with open("submit_file.txt", "w") as submit_file:
            submit_file.write("executable = "+executable.name+"\n")
            if dataset is not None:
                submit_file.write("data = "+dataset.name+"\n")

        with open("fileA.txt", "w") as fileA:
            fileA.write("SUBMIT submit_file.txt")
            fileA.flush()
        is_running = trigger_sock()
    context = {}
    return render(request, 'computation/submit.html', context)

def queue(request):
    queue_info = ""
    error_message = "Server is currently closed"
    with open("fileA.txt", "w") as fileA:
        fileA.write("JOB-status")
    is_running = trigger_sock()
    if is_running == 0:
        while True:
            with open("fileB.txt", "r+") as fileB:
                if fileB.read(1):
                    fileB.seek(0,0)
                    queue_info = fileB.readlines()
                    if len(queue_info)>0 and queue_info[0].startswith("jobs"):
                        print("==========", queue_info)
                        fileB.seek(0,0)
                        fileB.truncate(0)
                        break
                    else:
                        error_message = "Please refresh the page for the information."
                        return render(request, 'computation/queue.html', {'error_message':error_message})
    else:
        return render(request, 'computation/queue.html', {'error_message':error_message})
    context = {'queue_info':queue_info}
    return render(request, 'computation/queue.html', context)

def params(request):
    statistics = ""
    with open("fileA.txt", "w") as fileA:
        fileA.write("s")
    is_running = trigger_sock()
    if is_running == 0:
        while True:
            with open("fileB.txt", "r+") as fileB:
                if fileB.read(1):
                    fileB.seek(0,0)
                    statistics = fileB.readlines()
                    if len(statistics)>0 and statistics[0].startswith("stats"):
                        print("==========", statistics)
                        fileB.seek(0,0)
                        fileB.truncate(0)
                        break
                    else:
                        error_message = "Please refresh the page for the information."
                        return render(request, 'computation/params.html', {'error_message':error_message})
    else:
        return render(request, 'computation/params.html', {'error_message':"Server is currently closed"})
    context = {'statistics':statistics}
    return render(request, 'computation/params.html', context)


def clients(request):
    addresses = ""
    with open("fileA.txt", "w") as fileA:
        fileA.write("a")
    is_running = trigger_sock()
    if is_running == 0:
        while True:
            with open("fileB.txt", "r+") as fileB:
                if fileB.read(1):
                    fileB.seek(0,0)
                    addresses = fileB.readlines()
                    if len(addresses) > 0 and addresses[0].startswith("addr"):
                        print("==========", addresses)
                        fileB.seek(0,0)
                        fileB.truncate(0)
                        print("DELETED")
                        break
                    else:
                        error_message = "Please refresh the page for the information."
                        return render(request, 'computation/clients.html', {'error_message':error_message})
    else:
        return render(request, 'computation/clients.html', {'error_message':"Server is currently closed"})
    context = {'addresses':addresses}
    return render(request, 'computation/clients.html', context)

def home(request):
    username = request.user.username
    addresses = ""
    statistics = ""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = ("0.0.0.0",5002)
    is_running = sock.connect_ex(address)
    sock.close()
    if is_running == 0:
        message = "You are connected to the server"
        context = {'username' : username, 'message' : message}
        return render(request, 'computation/home.html', context)
    else:
        print("Server is not running")
        message = "Server is currently closed"
        return render(request, 'computation/home.html', {'username' : username, 'message': message, 'addresses' : addresses, 'statistics' : statistics})
    # print("HOME ENTERED")
    # username = request.user.username
    # addresses = None
    # statistics = None
    # tasks_count = 1
    # client_id = None
    # host = "0.0.0.0"
    # port = 5000
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.settimeout(2)
    # # connect to remote host
    # try :
    #     s.connect((host, port))
    # except :
    #     message = "Server is currently closed."
    #     return render(request, 'computation/home.html', {'username' : username, 'message': message})
    #     print('Unable to connect')
    #     sys.exit()
    #
    # conn = sqlite3.connect('db_control.db')
    # cursor = conn.execute("SELECT COUNT(*) FROM UserID")
    # for row in cursor:
    #     if row[0] == 0:
    #         print("NEW USER CONNECTED")
    #         s.send(str.encode("CONTROL"))
    #         break
    #     else:
    #         cursor2 = conn.execute("SELECT Id FROM UserID")
    #         for data in cursor2:
    #             client_id = data[0]
    #             print("\n\n            CONNECTED TO THE SERVER.\n            YOUR ID IS:",str(client_id))
    #             s.send(str.encode("EXISTING_CONTROL"+str(client_id)))
    #             # prompt(request)
    #             break
    #     break
    # conn.close()
    # s.send(str.encode("a"))
    # while 1:
    #     socket_list = [sys.stdin, s]
    #     read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [], 0)
    #     for x in range(0, len(read_sockets)):
    #         if read_sockets[x] == s:
    #             data = read_sockets[x].recv(4096)
    #             if not data:
    #                 print('\nDisconnected from server')
    #                 sys.exit();
    #             elif (data.decode().startswith('a')):
    #                 addresses = data.decode()[1:]
    #                 s.send(str.encode("s"))
    #             elif (data.decode().startswith('s')):
    #                 statistics = data.decode()[1:]
    #
    #     if addresses is not None and statistics is not None:
    #         s.shutdown(socket.SHUT_WR)
    #         s.close()
    #         break
    #
    # print(addresses)
    # print(statistics)
    # print("Port is open")
    # message = "You are connected to the server."
    # return render(request, 'computation/home.html', {'username' : username, 'message': message, 'addresses' : addresses, 'statistics' : statistics})
    # return HttpResponse("You are logged in.")

def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request,user)
                return HttpResponseRedirect(reverse('computation:home'))
        else:
            return render(request, 'computation/login_user.html', {'message':"Login details are incorrect."})
    return render(request, 'computation/login_user.html', {})

def sign_up(request):
    context = {}
    message = ""
    form = UserCreationForm(request.POST or None)
    if request.method == "POST":
        message = "Details are not valid"
        if form.is_valid():
            user = form.save()
            login(request, user)
            username = request.user.username
            user = User.objects.get(username = username)
            email = request.POST.get('email')
            user.email = email
            user.save()
            return HttpResponseRedirect(reverse('computation:home'))
    else:
        form = UserCreationForm()
        return render(request, 'computation/sign_up.html', {'form': form, 'message' : message})


def index(request):
    return render(request, 'computation/index.html', {'message':"Welcome to the Computation tool. To get started please Log in or Sign up."})
    # return render(request, 'computation/index.html', {'message': "Server is currently closed, please try to connect later."})
