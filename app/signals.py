from django.dispatch import receiver
from allauth.socialaccount.signals import pre_social_login
from allauth.account.signals import user_logged_in
from django.contrib.auth import login
from django.shortcuts import redirect

@receiver(pre_social_login)
def social_login_auto_connect(sender, request, sociallogin, **kwargs):
    """
    Conecta automaticamente contas sociais a usuários existentes
    """
    if sociallogin.is_existing:
        return
    
    email = sociallogin.account.extra_data.get('email')
    if email:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            existing_user = User.objects.get(email=email)
            # Conecta a conta social e faz login
            sociallogin.connect(request, existing_user)
            from allauth.account.utils import perform_login
            perform_login(request, existing_user, email_verification='none')
        except User.DoesNotExist:
            # Novo usuário, prossegue normalmente
            pass