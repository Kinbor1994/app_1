import logging
from django.conf import settings
from django.contrib.auth.models import User, Group
from keycloak import KeycloakOpenID, KeycloakAdmin

logger = logging.getLogger(__name__)


class KeycloakService:
    """Service pour gérer l'authentification avec Keycloak"""
    
    def __init__(self):
        self.server_url = settings.KEYCLOAK_SERVER_URL
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET_KEY
        self.redirect_uri = settings.KEYCLOAK_REDIRECT_URI
        
        # Client OpenID pour l'authentification
        self.keycloak_openid = KeycloakOpenID(
            server_url=self.server_url,
            client_id=self.client_id,
            realm_name=self.realm,
            client_secret_key=self.client_secret,
        )
    
    def get_authorization_url(self, state):
        """Génère l'URL pour rediriger l'utilisateur vers Keycloak"""
        auth_url = self.keycloak_openid.auth_url(
            redirect_uri=self.redirect_uri,
            state=state,
            scope="openid profile email"
        )
        return auth_url
    
    def exchange_code_for_token(self, code):
        """Échange le code d'authentification pour un token"""
        try:
            token = self.keycloak_openid.token(
                code=code,
                grant_type='authorization_code',
            )
            return token
        except Exception as e:
            logger.error(f"Erreur lors de l'échange du code: {e}")
            return None
    
    def get_userinfo(self, access_token):
        """Récupère les infos utilisateur depuis Keycloak"""
        try:
            userinfo = self.keycloak_openid.userinfo(access_token)
            return userinfo
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos utilisateur: {e}")
            return None
    
    def create_or_update_user(self, userinfo):
        """Crée ou met à jour un utilisateur Django basé sur les infos Keycloak"""
        try:
            username = userinfo.get('preferred_username')
            email = userinfo.get('email')
            first_name = userinfo.get('given_name', '')
            last_name = userinfo.get('family_name', '')
            
            # Créer ou récupérer l'utilisateur
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            
            # Mettre à jour les infos
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            # Gérer les rôles/groupes depuis Keycloak
            self.sync_user_roles(user, userinfo)
            
            return user
        except Exception as e:
            logger.error(f"Erreur lors de la création/mise à jour de l'utilisateur: {e}")
            return None
    
    def sync_user_roles(self, user, userinfo):
        """Synchronise les rôles Keycloak avec les groupes Django"""
        # Récupérer les rôles depuis le userinfo
        client_roles = userinfo.get('resource_access', {}).get(self.client_id, {}).get('roles', [])
        realm_roles = userinfo.get('realm_access', {}).get('roles', [])
        
        all_roles = list(set(client_roles + realm_roles))
        
        logger.info(f"Rôles trouvés pour {user.username}: {all_roles}")
        
        # Récupérer ou créer les groupes Django correspondants
        for role_name in all_roles:
            group, _ = Group.objects.get_or_create(name=role_name)
            user.groups.add(group)
        
        # Retirer les groupes que l'utilisateur n'a plus
        user_group_names = set(user.groups.values_list('name', flat=True))
        for group_name in user_group_names:
            if group_name not in all_roles:
                group = Group.objects.get(name=group_name)
                user.groups.remove(group)
                logger.info(f"Groupe {group_name} retiré de {user.username}")