from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
import socket, select, string, sys, py_compile, os, shelve, sqlite3
from ftplib import FTP

def prompt(request):
    username = request.user.username
    message = "You are connected to the server"
    return render(request, 'computation/home.html', {'username' : username, 'message': message})


def home(request):
    print("HOME ENTERED")
    username = request.user.username
    addresses = None
    statistics = None
    tasks_count = 1
    client_id = None
    host = "0.0.0.0"
    port = 5000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    # connect to remote host
    try :
        s.connect((host, port))
    except :
        message = "Server is currently closed."
        return render(request, 'computation/home.html', {'username' : username, 'message': message})
        print('Unable to connect')
        sys.exit()

    conn = sqlite3.connect('db_control.db')
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
                print("\n\n            CONNECTED TO THE SERVER.\n            YOUR ID IS:",str(client_id))
                s.send(str.encode("EXISTING_CONTROL"+str(client_id)))
                # prompt(request)
                break
        break
    conn.close()
    s.send(str.encode("a"))
    while 1:
        socket_list = [sys.stdin, s]
        read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [], 0)
        for x in range(0, len(read_sockets)):
            if read_sockets[x] == s:
                data = read_sockets[x].recv(4096)
                if not data:
                    print('\nDisconnected from server')
                    sys.exit();
                elif (data.decode().startswith('a')):
                    addresses = data.decode()[1:]
                    s.send(str.encode("s"))
                elif (data.decode().startswith('s')):
                    statistics = data.decode()[1:]

        if addresses is not None and statistics is not None:
            s.shutdown(socket.SHUT_WR)
            s.close()
            break

    print(addresses)
    print(statistics)
    print("Port is open")
    message = "You are connected to the server."
    return render(request, 'computation/home.html', {'username' : username, 'message': message, 'addresses' : addresses, 'statistics' : statistics})
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
