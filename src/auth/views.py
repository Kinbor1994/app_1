import logging
import secrets
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .keycloak_service import KeycloakService

logger = logging.getLogger(__name__)
keycloak_service = KeycloakService()


@require_http_methods(["GET"])
def login_view(request):
    """
    Démarre le flux d'authentification OpenID Connect.
    Redirige l'utilisateur vers Keycloak.
    """
    # Générer un state pour éviter les attaques CSRF
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state
    
    # Récupérer l'URL d'authentification Keycloak
    auth_url = keycloak_service.get_authorization_url(state)
    
    logger.info(f"Redirection vers Keycloak: {auth_url}")
    return redirect(auth_url)


@require_http_methods(["GET"])
def callback_view(request):
    """
    Callback après authentification Keycloak.
    Keycloak redirige ici avec le code d'authentification.
    """
    # Récupérer le code et le state
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    # Vérifier le state pour la sécurité CSRF
    session_state = request.session.get('oauth_state')
    if not state or state != session_state:
        logger.error("State mismatch ou manquant")
        return render(request, 'auth/error.html', {
            'error': 'Erreur de sécurité: state invalide'
        })
    
    if error:
        logger.error(f"Erreur Keycloak: {error}")
        return render(request, 'auth/error.html', {
            'error': f'Erreur d\'authentification: {error}'
        })
    
    if not code:
        logger.error("Code d'authentification manquant")
        return render(request, 'auth/error.html', {
            'error': 'Code d\'authentification manquant'
        })
    
    # Échanger le code pour un token
    token_response = keycloak_service.exchange_code_for_token(code)
    if not token_response:
        logger.error("Impossible d'obtenir le token")
        return render(request, 'auth/error.html', {
            'error': 'Erreur lors de l\'authentification'
        })
    
    # Récupérer le access token
    access_token = token_response.get('access_token')
    if not access_token:
        logger.error("Access token manquant dans la réponse")
        return render(request, 'auth/error.html', {
            'error': 'Erreur: token manquant'
        })
    
    # Récupérer les infos utilisateur
    userinfo = keycloak_service.get_userinfo(access_token)
    if not userinfo:
        logger.error("Impossible de récupérer les infos utilisateur")
        return render(request, 'auth/error.html', {
            'error': 'Erreur lors de la récupération des données utilisateur'
        })
    
    # Créer ou mettre à jour l'utilisateur Django
    user = keycloak_service.create_or_update_user(userinfo)
    if not user:
        logger.error("Impossible de créer/mettre à jour l'utilisateur")
        return render(request, 'auth/error.html', {
            'error': 'Erreur lors de la création de l\'utilisateur'
        })
    
    # Connecter l'utilisateur (sans backend, car l'utilisateur existe)
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    
    # Stocker le token dans la session pour les appels API futurs
    request.session['access_token'] = access_token
    request.session['refresh_token'] = token_response.get('refresh_token')
    
    logger.info(f"Utilisateur {user.username} connecté avec succès")
    
    # Nettoyer le state
    del request.session['oauth_state']
    
    # Rediriger vers le dashboard
    return redirect('home:dashboard')


@require_http_methods(["GET"])
def logout_view(request):
    """
    Déconnecte l'utilisateur de Django et de Keycloak.
    """
    # Récupérer le refresh token
    refresh_token = request.session.get('refresh_token')
    
    # Déconnecter de Django
    logout(request)
    
    # Optionnel : déconnecter de Keycloak aussi
    # (Cela nécessiterait un appel à Keycloak logout endpoint)
    
    logger.info("Utilisateur déconnecté")
    
    # Rediriger vers l'accueil
    return redirect('home:home')