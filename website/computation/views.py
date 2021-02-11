from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
import socket

def home(request):
    username = request.user.username
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("0.0.0.0", 5000))
    if result == 0:
       print("Port is open")
       message = "You are connected to the server."
       return render(request, 'computation/home.html', {'username' : username, 'message': message})
    else:
        message = "Server is currently closed."
        return render(request, 'computation/home.html', {'username' : username, 'message': message})
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
