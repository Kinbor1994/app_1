from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.views.decorators.http import require_POST

def home_view(request):
    return render(request, 'home/home.html')

@login_required
def profile_view(request):
    return render(request, 'home/profile.html')

@require_POST
def logout_view(request):
    logout(request)
    return redirect('logged_out')

def logged_out_view(request):
    return render(request, 'home/logged_out.html')
