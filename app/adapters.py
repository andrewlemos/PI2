from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Se o email já existe → conecta
        Se não existe → cria automaticamente
        """
        if sociallogin.is_existing:
            return

        # Tenta conectar por email
        try:
            user = User.objects.get(email=sociallogin.user.email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            # Cria usuário automaticamente
            sociallogin.user.username = sociallogin.user.email
            sociallogin.save(request)