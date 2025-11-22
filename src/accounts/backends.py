from mozilla_django_oidc.auth import OIDCAuthenticationBackend
import unicodedata

class KeycloakBackend(OIDCAuthenticationBackend):

    def verify_claims(self, claims):
        """
        Vérifie que les informations critiques sont présentes
        """
        verified = super(KeycloakBackend, self).verify_claims(claims)
        # On s'assure que Keycloak envoie bien le nom d'utilisateur
        msg = "Le champ 'preferred_username' est manquant dans Keycloak."
        if not claims.get('preferred_username'):
            print(msg) # Pour le debug
            return False
        return verified

    def filter_users_by_claims(self, claims):
        """
        Cette méthode sert à retrouver un utilisateur existant lors de la connexion.
        On cherche par le username 'borel' au lieu de l'email ou du hash.
        """
        username = claims.get('preferred_username')
        if not username:
            return self.UserModel.objects.none()
        
        # On cherche dans la base de données Django si 'borel' existe déjà
        return self.UserModel.objects.filter(username=username)

    def create_user(self, claims):
        """
        Création de l'utilisateur avec le BON username.
        """
        # On récupère les valeurs brutes
        email = claims.get('email')
        username = claims.get('preferred_username')

        # On crée l'utilisateur manuellement avec le username 'borel'
        user = self.UserModel.objects.create_user(username, email=email)
        
        # On remplit le reste des infos (prénom, nom...)
        self.update_user_claims(user, claims)
        
        return user

    def update_user_claims(self, user, claims):
        """
        Mise à jour des infos ET des permissions basées sur les rôles Keycloak
        """
        # 1. Mise à jour des infos de base
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.email = claims.get('email', '')

        # 2. Récupération des rôles depuis Keycloak
        # On regarde dans 'realm_access' -> 'roles'
        realm_access = claims.get('realm_access', {})
        roles = realm_access.get('roles', [])
        print(roles)
        # Astuce debug : décommente pour voir tes rôles actuels
        # print(f"Rôles reçus pour {user.username}: {roles}")

        # 3. Gestion du statut Admin / Staff
        # Si l'utilisateur a le rôle 'admin_django' dans Keycloak, il devient Superuser
        if 'admin' in roles:
            user.is_staff = True
            user.is_superuser = True
        
        # Si l'utilisateur a le rôle 'editeur' dans Keycloak, il accède à l'admin mais n'est pas superuser
        elif 'moderator' in roles:
            user.is_staff = True
            user.is_superuser = False
        
        # Sinon, on s'assure de retirer les droits s'il les a perdus dans Keycloak
        else:
            user.is_staff = False
            user.is_superuser = False

        # 4. (Optionnel) Gestion des Groupes Django
        # Si l'utilisateur a le rôle 'comptable', on l'ajoute au groupe 'Compta' de Django
        # if 'comptable' in roles:
        #     # On récupère ou crée le groupe Django
        #     group, created = Group.objects.get_or_create(name='Compta')
        #     user.groups.add(group)
        # else:
        #     # S'il n'a plus le rôle, on le retire du groupe (optionnel, selon ta logique)
        #     try:
        #         group = Group.objects.get(name='Compta')
        #         user.groups.remove(group)
        #     except Group.DoesNotExist:
        #         pass

        user.save()

        return user