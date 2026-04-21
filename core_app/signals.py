import random
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Role
from allauth.account.models import EmailAddress

@receiver(post_save, sender=User)
def auto_verify_admin_email(sender, instance, created, **kwargs):
    """Bypass email verification and OTP for admins and superusers."""
    if instance.is_admin() or instance.is_superuser:
        if instance.email:
            email_obj, created_email = EmailAddress.objects.get_or_create(
                user=instance,
                email=instance.email,
                defaults={'verified': True, 'primary': True}
            )
            if not email_obj.verified:
                email_obj.verified = True
                email_obj.save()


@receiver(post_save, sender=User)
def send_otp_on_signup(sender, instance, created, **kwargs):
    if created and not instance.is_verified:
        # 1. Assigner le rôle Utilisateur par défaut
        if not instance.role and not instance.is_superuser:
            user_role, _ = Role.objects.get_or_create(name=Role.USER)
            instance.role = user_role

        # 2. Générer un code à 6 chiffres
        otp = f"{random.randint(100000, 999999)}"
        instance.auth_code = otp
        instance.save()

        # 2. Préparer l'email
        subject = "Vérification de votre compte G-Parc"
        message = f"Bienvenue {instance.username} !\n\nVotre code de vérification est : {otp}\n\nL'équipe G-Parc."
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [instance.email]

        # 3. Envoyer le mail (utilisera la console en mode dev)
        send_mail(subject, message, email_from, recipient_list)