from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

def home(request):
    """Page d'accueil : affiche login ou dashboard selon auth"""
    if request.user.is_authenticated:
        return redirect('home:dashboard')
    
    context = {
        'title': 'Accueil',
    }
    return render(request, 'home/home.html', context)


@login_required(login_url='auth_login')
def dashboard(request):
    """Dashboard de l'utilisateur connecté"""
    user = request.user
    
    # Récupérer les rôles/groupes de l'utilisateur
    groups = user.groups.all()
    
    context = {
        'title': 'Dashboard',
        'user': user,
        'groups': groups,
    }
    return render(request, 'home/dashboard.html', context)


@login_required(login_url='auth_login')
def profile(request):
    """Page de profil de l'utilisateur"""
    user = request.user
    
    # Récupérer les infos de l'utilisateur
    context = {
        'title': 'Profil',
        'user': user,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'groups': user.groups.all(),
    }
    return render(request, 'home/profile.html', context)