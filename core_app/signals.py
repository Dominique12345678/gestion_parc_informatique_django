import random
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from .models import User, Role, Ticket, MaintenanceReport, Device, DeviceHistory
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

@receiver(post_save, sender=Ticket)
def notify_tech_on_new_ticket(sender, instance, created, **kwargs):
    """Notification des techniciens lors de l'ouverture d'un nouveau ticket."""
    if created:
        techs = User.objects.filter(role__name=Role.TECHNICIAN)
        emails = [t.email for t in techs if t.email]
        
        if emails:
            subject = f"⚠️ Nouveau Ticket : {instance.device.name}"
            message = f"Un nouveau problème a été signalé par {instance.reported_by.username}.\n\nDescription : {instance.description}\nPriorité : {instance.get_priority_display()}\n\nConnectez-vous au dashboard pour intervenir."
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, emails)

@receiver(post_save, sender=MaintenanceReport)
def notify_user_on_resolution(sender, instance, created, **kwargs):
    """Notification de l'utilisateur quand son ticket est résolu via un rapport."""
    if created and instance.ticket.is_resolved:
        user = instance.ticket.reported_by
        if user.email:
            subject = f"✅ Problème Résolu : {instance.ticket.device.name}"
            message = f"Bonjour {user.username},\n\nLe technicien {instance.technician.username} a terminé l'intervention sur votre équipement.\n\nAction effectuée : {instance.action_taken}\n\nVotre équipement est de nouveau opérationnel."
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

# --- AUTOMATED DEVICE HISTORY ---

@receiver(pre_save, sender=Device)
def capture_old_device_state(sender, instance, **kwargs):
    """Capture l'état précédent avant sauvegarde pour détecter les changements."""
    if instance.id:
        try:
            old_obj = Device.objects.get(id=instance.id)
            instance._old_status = old_obj.status
            instance._old_assigned = old_obj.assigned_to
        except Device.DoesNotExist:
            instance._old_status = None
            instance._old_assigned = None
    else:
        instance._old_status = None
        instance._old_assigned = None

@receiver(post_save, sender=Device)
def auto_log_device_history(sender, instance, created, **kwargs):
    """Génère automatiquement une entrée dans DeviceHistory lors de changements clés."""
    if created:
        DeviceHistory.objects.create(device=instance, action="Enregistrement initial de l'équipement")
    else:
        # Détection changement de statut
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            DeviceHistory.objects.create(
                device=instance, 
                action=f"Auto: Passage de {old_status} à {instance.status}"
            )
        
        # Détection changement d'affectation
        old_assigned = getattr(instance, '_old_assigned', None)
        if old_assigned != instance.assigned_to:
            name = instance.assigned_to.username if instance.assigned_to else "Personne (Remis en stock)"
            DeviceHistory.objects.create(device=instance, action=f"Auto: Affecté à {name}")

# --- CACHE INVALIDATION ---

@receiver([post_save, post_delete], sender=Device)
@receiver([post_save, post_delete], sender=Ticket)
def clear_dashboard_cache(sender, **kwargs):
    """Vider le cache du dashboard admin quand les données changent."""
    cache.delete('admin_dashboard_stats')