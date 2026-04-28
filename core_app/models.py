import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from .validators import validate_file_size, validate_image_extension

# ==========================================
# 1. SYSTÈME D'AUTHENTIFICATION ET RÔLES
# ==========================================

class Role(models.Model):
    """Table de référence pour les accès : ADMIN, HEAD_TECHNICIAN, TECHNICIAN, USER"""
    ADMIN = 'ADMIN'
    HEAD_TECHNICIAN = 'HEAD_TECHNICIAN'
    TECHNICIAN = 'TECHNICIAN'
    USER = 'USER'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrateur'),
        (HEAD_TECHNICIAN, 'Technicien Principal'),
        (TECHNICIAN, 'Technicien IT'),
        (USER, 'Utilisateur Simple'),
    ]
    
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()

class User(AbstractUser):
    """Modèle utilisateur personnalisé avec vérification par mail"""
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_verified = models.BooleanField(default=False)
    auth_code = models.CharField(max_length=6, blank=True)

    def is_admin(self):
        return self.role and self.role.name == Role.ADMIN

    def is_head_technician(self):
        return self.role and self.role.name == Role.HEAD_TECHNICIAN

    def is_technician(self):
        return self.role and (self.role.name == Role.TECHNICIAN or self.role.name == Role.HEAD_TECHNICIAN)

    def is_simple_user(self):
        return self.role and self.role.name == Role.USER

# ==========================================
# 2. GESTION DU PARC (INVENTAIRE)
# ==========================================

class Category(models.Model):
    name = models.CharField(max_length=100)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.name

class Device(models.Model):
    """Équipement informatique avec génération automatique de QR Code"""
    STATUS_CHOICES = [
        ('AVAILABLE', 'Disponible'),
        ('ASSIGNED', 'Assigné'),
        ('MAINTENANCE', 'En maintenance / Panne'),
        ('BROKEN', 'Hors service'),
    ]

    name = models.CharField("Nom de l'appareil", max_length=200)
    serial_number = models.CharField("N° de série", max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='devices/', null=True, blank=True, validators=[validate_file_size, validate_image_extension])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    
    # Matériel attribué à un collaborateur
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='my_devices'
    )
    
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, editable=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Générer le QR code si le numéro de série est présent et le QR n'existe pas
        if not self.qr_code:
            qr_content = f"SN:{self.serial_number} | Device:{self.name}"
            qr_img = qrcode.make(qr_content)
            canvas = BytesIO()
            qr_img.save(canvas, format='PNG')
            self.qr_code.save(f"qr_{self.serial_number}.png", File(canvas), save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.serial_number}"

class DeviceHistory(models.Model):
    """Historique des actions sur un équipement"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='history')
    action = models.CharField("Action", max_length=255)
    performer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.device.name} - {self.action} le {self.timestamp.strftime('%d/%m/%Y')}"

# ==========================================
# 3. MAINTENANCE ET SIGNALEMENTS (TICKETS)
# ==========================================

class Ticket(models.Model):
    """Signalement de panne ou problème"""
    PRIORITY_CHOICES = [('LOW', 'Basse'), ('MEDIUM', 'Moyenne'), ('HIGH', 'Haute')]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='tickets')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_tickets')
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tickets',
        limit_choices_to={'role__name__in': ['TECHNICIAN', 'HEAD_TECHNICIAN']}
    )
    description = models.TextField("Description du problème")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    is_resolved = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.device.name}"

class MaintenanceReport(models.Model):
    """Rapport technique rempli par le Technicien IT"""
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='report')
    technician = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'role__name__in': ['TECHNICIAN', 'HEAD_TECHNICIAN']}
    )
    action_taken = models.TextField("Actions effectuées")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_deleted = models.BooleanField(default=False)
    repair_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rapport #{self.id} pour {self.ticket.device.name}"

class TicketChat(models.Model):
    """Chat en temps réel entre le Technicien Principal et le Technicien assigné sur un ticket"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='chats')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField("Message")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message de {self.sender.username} - Ticket #{self.ticket.id}"