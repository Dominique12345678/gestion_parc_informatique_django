from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db import models
import random
from django.core.mail import send_mail
from django.conf import settings

from .models import User, Role, Device, Ticket, MaintenanceReport, Category, DeviceHistory
from .forms import DeviceForm, TicketForm, MaintenanceReportForm, UserRoleForm, CategoryForm, DeviceAssignmentForm, ProfileForm
from .decorators import admin_required, technician_required, verified_required

# ==========================================
# 1. AUTHENTIFICATION & REDIRECTIONS BASE
# ==========================================
def home(request):
    """Affiche la page d'accueil moderne"""
    return render(request, 'pages/home.html')

@login_required
def verify_otp(request):
    """Vérification du code OTP"""
    if request.user.is_verified:
        return redirect('dashboard')

    if request.method == "POST":
        otp_saisi = request.POST.get('otp_code')
        if request.user.auth_code == otp_saisi:
            user = request.user
            user.is_verified = True
            user.auth_code = ""
            user.save()
            messages.success(request, "Compte vérifié avec succès !")
            return redirect('dashboard')
        else:
            messages.error(request, "Code incorrect.")

    return render(request, 'account/verify_otp.html')

@login_required
def resend_otp(request):
    """Renvoie un nouveau code OTP à l'utilisateur"""
    if request.user.is_verified:
        return redirect('dashboard')
    
    # Générer un nouveau code
    otp = f"{random.randint(100000, 999999)}"
    request.user.auth_code = otp
    request.user.save()

    # Envoyer le mail
    subject = "Nouveau code de vérification G-Parc"
    message = f"Bonjour {request.user.username},\n\nVotre nouveau code de vérification est : {otp}\n\nL'équipe G-Parc."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [request.user.email])

    messages.success(request, "Un nouveau code vient d'être envoyé à votre adresse email.")
    return redirect('verify_otp')

def logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('home')

@login_required
def dashboard(request):
    """Redirection basée sur le rôle"""
    # L'administrateur et le superuser contournent la vérification OTP
    if not request.user.is_verified and not (request.user.is_admin() or request.user.is_superuser):
        return redirect('verify_otp')
    
    if request.user.is_admin() or request.user.is_superuser:
        return redirect('admin_dashboard')
    elif request.user.is_technician():
        return redirect('tech_dashboard')
    else:
        return redirect('user_dashboard')

@login_required
def profile_view(request):
    """Page Mon Compte"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Informations sauvegardées avec succès.")
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    
    # Selectionner le bon layout parent en fonction du rôle
    if request.user.is_admin() or request.user.is_superuser:
        base_template = "admin_base.html"
        block_name = "admin_content"
    else:
        base_template = "base.html"
        block_name = "content"

    return render(request, 'account/profile.html', {
        'form': form, 
        'base_template': base_template,
        'block_name': block_name
    })

# ==========================================
# 2. VUES ADMINISTRATEUR
# ==========================================
@admin_required
def admin_dashboard(request):
    """Tableau de bord de l'administrateur"""
    categories = Category.objects.annotate(
        device_count=Count('device', filter=models.Q(device__is_deleted=False))
    )
    context = {
        'total_users': User.objects.count(),
        'total_devices': Device.objects.filter(is_deleted=False).count(),
        'broken_devices': Device.objects.filter(status='BROKEN', is_deleted=False).count(),
        'pending_tickets': Ticket.objects.filter(is_resolved=False).count(),
        'recent_tickets': Ticket.objects.all().order_by('-created_at')[:5],
        'recent_devices': Device.objects.filter(is_deleted=False).order_by('-created_at')[:5],
        'categories_stats': categories,
    }
    return render(request, 'pages/admin/dashboard_admin.html', context)

@admin_required
def admin_manage_users(request):
    """Gestion des utilisateurs et rôles"""
    users = User.objects.all().order_by('-date_joined')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_role_id = request.POST.get('role_id')
        user_obj = get_object_or_404(User, id=user_id)
        if new_role_id:
            role = get_object_or_404(Role, id=new_role_id)
            user_obj.role = role
        else:
            user_obj.role = None
        user_obj.save()
        messages.success(request, f"Le rôle de {user_obj.username} a été mis à jour.")
        return redirect('admin_manage_users')

    roles = Role.objects.all()
    context = {'users': users, 'roles': roles}
    return render(request, 'pages/admin/manage_users.html', context)

@admin_required
def admin_manage_devices(request):
    """Liste des équipements"""
    devices = Device.objects.filter(is_deleted=False).order_by('-created_at')
    context = {'devices': devices}
    return render(request, 'pages/admin/manage_devices.html', context)

@admin_required
def admin_device_form(request, pk=None):
    """Création ou modification d'un équipement"""
    device = get_object_or_404(Device, pk=pk, is_deleted=False) if pk else None
    
    if request.method == 'POST':
        form = DeviceForm(request.POST, request.FILES, instance=device)
        if form.is_valid():
            created_device = form.save()
            action = "Modifié" if pk else "Créé"
            DeviceHistory.objects.create(device=created_device, action=f"Équipement {action} par admin", performer=request.user)
            
            messages.success(request, f"Équipement {action.lower()} avec succès.")
            if not pk:
                return redirect('admin_device_success', pk=created_device.id)
            return redirect('admin_manage_devices')
    else:
        form = DeviceForm(instance=device)
    
    return render(request, 'pages/admin/device_form.html', {'form': form, 'device': device})

@admin_required
def admin_device_success(request, pk):
    """Page isolée affichant le QR Code juste après la création."""
    device = get_object_or_404(Device, pk=pk, is_deleted=False)
    return render(request, 'pages/admin/admin_device_success.html', {'device': device})

@admin_required
def admin_assign_device(request, pk):
    """Assignation d'un équipement à un utilisateur / tech."""
    device = get_object_or_404(Device, pk=pk, is_deleted=False)
    if request.method == 'POST':
        form = DeviceAssignmentForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            assign_str = f"Assigné à {device.assigned_to.username}" if device.assigned_to else "Désaffecté"
            DeviceHistory.objects.create(device=device, action=f"Affectation: {assign_str}. Statut: {device.get_status_display()}", performer=request.user)
            messages.success(request, "Assignation mise à jour.")
            return redirect('admin_manage_devices')
    else:
        form = DeviceAssignmentForm(instance=device)
    return render(request, 'pages/admin/admin_assign_device.html', {'form': form, 'device': device})

@admin_required
def admin_device_history(request, pk):
    """Affiche l'historique d'un équipement"""
    device = get_object_or_404(Device, pk=pk)
    return render(request, 'pages/admin/admin_device_history.html', {'device': device})

@admin_required
def admin_categories(request):
    """Gestion des catégories"""
    categories = Category.objects.filter(is_deleted=False)
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie ajoutée.")
            return redirect('admin_categories')
    else:
        form = CategoryForm()
    return render(request, 'pages/admin/admin_categories.html', {'categories': categories, 'form': form})

@admin_required
def admin_edit_category(request, pk):
    """Modifier une catégorie"""
    category = get_object_or_404(Category, pk=pk, is_deleted=False)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie modifiée.")
            return redirect('admin_categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'pages/admin/admin_categories_edit.html', {'form': form, 'category': category})

@admin_required
def admin_delete_category(request, pk):
    """Suppression logique d'une catégorie"""
    category = get_object_or_404(Category, pk=pk)
    category.is_deleted = True
    category.save()
    messages.success(request, "Catégorie supprimée.")
    return redirect('admin_categories')

@admin_required
def admin_assign_list(request):
    """Portail regroupant toutes les assignations en cours ou à faire"""
    devices = Device.objects.filter(is_deleted=False).select_related('assigned_to').order_by('-created_at')
    return render(request, 'pages/admin/admin_assign_list.html', {'devices': devices})

@admin_required
def admin_delete_device(request, pk):
    device = get_object_or_404(Device, pk=pk)
    device.is_deleted = True
    device.status = 'BROKEN'
    device.assigned_to = None
    device.save()
    
    DeviceHistory.objects.create(
        device=device,
        action="Appareil supprimé (logique) et désaffecté",
        performer=request.user
    )
    
    messages.success(request, "Équipement supprimé logiciellement.")
    return redirect('admin_manage_devices')


# ==========================================
# 3. VUES TECHNICIEN
# ==========================================
@technician_required
def tech_dashboard(request):
    """Tableau de bord technicien"""
    context = {
        'open_tickets': Ticket.objects.filter(is_resolved=False).order_by('-priority', 'created_at'),
        'devices_maintenance': Device.objects.filter(status='MAINTENANCE'),
    }
    return render(request, 'pages/tech/dashboard_tech.html', context)

@technician_required
def tech_tickets(request):
    """Liste complète des tickets"""
    tickets = Ticket.objects.all().order_by('is_resolved', '-created_at')
    return render(request, 'pages/tech/tickets.html', {'tickets': tickets})

@technician_required
def tech_handle_ticket(request, pk):
    """Ajout d'un rapport de maintenance et fermeture d'un ticket"""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    # Si le rapport existe déjà, on l'édite
    report_instance = getattr(ticket, 'report', None)

    if request.method == 'POST':
        form = MaintenanceReportForm(request.POST, instance=report_instance)
        if form.is_valid():
            report = form.save(commit=False)
            report.ticket = ticket
            report.technician = request.user
            report.save()

            # Mettre à jour l'état du ticket et de la machine
            action_desc = f"Maintenance terminée : {report.action_taken[:50]}..." if ticket.is_resolved else f"Maintenance en cours : {report.action_taken[:50]}..."
            DeviceHistory.objects.create(
                device=ticket.device,
                action=action_desc,
                performer=request.user
            )

            ticket.is_resolved = "resolve_ticket" in request.POST
            ticket.save()

            new_status = request.POST.get('device_status')
            if new_status:
                ticket.device.status = new_status
                ticket.device.save()

            messages.success(request, "Rapport de maintenance enregistré.")
            return redirect('tech_tickets')
    else:
        form = MaintenanceReportForm(instance=report_instance)

    return render(request, 'pages/tech/maintenance.html', {
        'form': form, 
        'ticket': ticket, 
        'device_statuses': Device.STATUS_CHOICES
    })


# ==========================================
# 4. VUES UTILISATEUR
# ==========================================
@verified_required
def user_dashboard(request):
    """Zone utilisateur"""
    my_devices = Device.objects.filter(assigned_to=request.user)
    my_tickets = Ticket.objects.filter(reported_by=request.user).order_by('-created_at')
    
    base_template = "admin_base.html" if request.user.is_admin() or request.user.is_superuser else "base.html"

    context = {
        'devices': my_devices,
        'tickets': my_tickets,
        'base_template': base_template,
    }
    return render(request, 'pages/user/dashboard_user.html', context)

@verified_required
def user_report_issue(request):
    """Signaler une panne"""
    if request.method == 'POST':
        form = TicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.reported_by = request.user
            ticket.save()
            
            # Change status of device
            ticket.device.status = 'MAINTENANCE' # Ou on peut garder BROKEN, mais SIGNALER PANNE déclenche souvent maintenance
            ticket.device.save()

            DeviceHistory.objects.create(
                device=ticket.device,
                action=f"Panne signalée : {ticket.description[:50]}...",
                performer=request.user
            )

            messages.success(request, "Problème signalé avec succès. Un technicien va intervenir.")
            return redirect('user_dashboard')
    else:
        form = TicketForm(user=request.user)
    
    base_template = "admin_base.html" if request.user.is_admin() or request.user.is_superuser else "base.html"
    
    return render(request, 'pages/user/report_issue.html', {'form': form, 'base_template': base_template})