from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db import models
import random
import csv
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from django.core.cache import cache
from .models import User, Role, Device, Ticket, MaintenanceReport, Category, DeviceHistory, TicketChat
from .forms import DeviceForm, TicketForm, MaintenanceReportForm, UserRoleForm, CategoryForm, DeviceAssignmentForm, ProfileForm, TicketAssignmentForm
from .decorators import admin_required, technician_required, verified_required, head_technician_required

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

@csrf_exempt
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
    
    # Tout le monde utilise maintenant le layout avec sidebar
    base_template = "admin_base.html"
    block_name = "admin_content"

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
    """Tableau de bord de l'administrateur avec alertes de stock et cache"""
    # Récupérer les stats depuis le cache pour optimiser
    context = cache.get('admin_dashboard_stats')
    
    if not context:
        categories = Category.objects.annotate(
            device_count=Count('device', filter=models.Q(device__is_deleted=False)),
            available_count=Count('device', filter=models.Q(device__is_deleted=False, device__status='AVAILABLE'))
        )
        
        # Alertes : Moins de 2 disponibles dans une catégorie
        stock_alerts = [cat for cat in categories if cat.available_count < 2 and cat.device_count > 0]

        context = {
            'total_users': User.objects.count(),
            'total_devices': Device.objects.filter(is_deleted=False).count(),
            'available_devices': Device.objects.filter(status='AVAILABLE', is_deleted=False).count(),
            'assigned_devices': Device.objects.filter(status='ASSIGNED', is_deleted=False).count(),
            'maintenance_devices': Device.objects.filter(status='MAINTENANCE', is_deleted=False).count(),
            'broken_devices': Device.objects.filter(status='BROKEN', is_deleted=False).count(),
            'pending_tickets': Ticket.objects.filter(is_resolved=False, is_deleted=False).count(),
            'resolved_tickets': Ticket.objects.filter(is_resolved=True, is_deleted=False).count(),
            'high_priority_tickets': Ticket.objects.filter(priority='HIGH', is_deleted=False).count(),
            'normal_priority_tickets': Ticket.objects.filter(priority='NORMAL', is_deleted=False).count(),
            'recent_tickets': list(Ticket.objects.filter(is_deleted=False).order_by('-created_at')[:5]),
            'recent_devices': list(Device.objects.filter(is_deleted=False).order_by('-created_at')[:5]),
            'categories_stats': list(categories),
            'stock_alerts': stock_alerts,
        }
        # On garde les stats en mémoire pendant 5 minutes
        cache.set('admin_dashboard_stats', context, 300)

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

    roles = Role.objects.exclude(name='ADMIN')
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


@admin_required
def admin_tickets(request):
    """Vue globale pour l'admin : tous les tickets et rapports"""
    tickets = Ticket.objects.filter(is_deleted=False).order_by('-created_at')
    return render(request, 'pages/admin/admin_tickets.html', {
        'tickets': tickets,
        'base_template': "admin_base.html"
    })

@admin_required
def admin_device_history(request, pk):
    """Historique complet d'un équipement (pannes + réparations)"""
    device = get_object_or_404(Device, pk=pk)
    # On récupère tous les tickets (même supprimés/résolus) liés à cet appareil
    tickets = Ticket.objects.filter(device=device).order_by('-created_at')
    
    return render(request, 'pages/admin/admin_device_history.html', {
        'device': device,
        'tickets': tickets,
        'base_template': "admin_base.html"
    })

# ==========================================
# 3. VUES TECHNICIEN
# ==========================================
@technician_required
def tech_dashboard(request):
    """Tableau de bord technicien : filtré selon le rôle"""
    if request.user.is_head_technician():
        # Le technicien principal voit tout ce qui est ouvert
        open_tickets = Ticket.objects.filter(is_resolved=False).order_by('-priority', 'created_at')
        unassigned_tickets = Ticket.objects.filter(is_resolved=False, assigned_to=None).count()
    else:
        # Un technicien simple ne voit que ce qui lui est assigné
        open_tickets = Ticket.objects.filter(is_resolved=False, assigned_to=request.user).order_by('-priority', 'created_at')
        unassigned_tickets = 0

    devices_maintenance = Device.objects.filter(status='MAINTENANCE')
    assigned_devices = Device.objects.filter(assigned_to=request.user)
    
    context = {
        'open_tickets': open_tickets,
        'unassigned_count': unassigned_tickets,
        'devices_maintenance': devices_maintenance,
        'assigned_devices': assigned_devices,
        'base_template': "admin_base.html"
    }
    return render(request, 'pages/tech/dashboard_tech.html', context)

@head_technician_required
def tech_assign_ticket(request, pk):
    """Vue pour que le Technicien Principal assigne une panne à un tech"""
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = TicketAssignmentForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ticket assigné à {ticket.assigned_to.username}.")
            # Log de l'action
            DeviceHistory.objects.create(
                device=ticket.device,
                action=f"Ticket #{ticket.id} assigné à {ticket.assigned_to.username}",
                performer=request.user
            )
            return redirect('tech_dashboard')
    else:
        form = TicketAssignmentForm(instance=ticket)
    
    return render(request, 'pages/tech/assign_ticket.html', {
        'form': form,
        'ticket': ticket,
        'base_template': "admin_base.html"
    })

@technician_required
def tech_tickets(request):
    """Liste complète des tickets (non supprimés)"""
    tickets = Ticket.objects.filter(is_deleted=False).order_by('is_resolved', 'priority', '-created_at')
    return render(request, 'pages/tech/tickets.html', {
        'tickets': tickets,
        'base_template': "admin_base.html"
    })

@technician_required
def tech_handle_ticket(request, pk):
    """Ajout d'un rapport de maintenance et fermeture d'un ticket"""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    # Si le rapport existe déjà, on l’édite
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
        'device_statuses': Device.STATUS_CHOICES,
        'base_template': "admin_base.html"
    })

@login_required
def tech_edit_report(request, pk):
    """Modifier un rapport de maintenance (Admin ou Propriétaire)"""
    if request.user.is_admin() or request.user.is_superuser:
        report = get_object_or_404(MaintenanceReport, pk=pk)
    elif request.user.is_technician():
        report = get_object_or_404(MaintenanceReport, pk=pk, technician=request.user)
    else:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = MaintenanceReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, "Rapport d'intervention mis à jour.")
            return redirect('tech_tickets')
    else:
        form = MaintenanceReportForm(instance=report)
    
    return render(request, 'pages/tech/maintenance.html', {
        'form': form, 
        'ticket': report.ticket, 
        'is_edit': True,
        'base_template': "admin_base.html"
    })

@login_required
def tech_delete_report(request, pk):
    """Archiver (suppression logique) un rapport (Admin ou Propriétaire)"""
    if request.user.is_admin() or request.user.is_superuser:
        report = get_object_or_404(MaintenanceReport, pk=pk)
    elif request.user.is_technician():
        report = get_object_or_404(MaintenanceReport, pk=pk, technician=request.user)
    else:
        messages.error(request, "Action non autorisée.")
        return redirect('dashboard')

    report.is_deleted = True
    report.save()
    
    messages.warning(request, "Rapport archivé.")
    return redirect(request.META.get('HTTP_REFERER', 'tech_tickets'))

@login_required
def ticket_chat(request, pk):
    """Chat en temps réel entre utilisateurs, techniciens et admins sur un ticket"""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    # Vérification des permissions
    if not (request.user.is_admin() or request.user.is_superuser or request.user.is_technician() or request.user == ticket.reported_by):
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')
    
    # Pour le GET en AJAX (récupération des messages)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'GET':
        chats = ticket.chats.all()
        data = [{
            'sender': chat.sender.username,
            'role': chat.sender.role.get_name_display() if chat.sender.role else "Utilisateur",
            'is_me': chat.sender == request.user,
            'message': chat.message,
            'time': chat.created_at.strftime('%H:%M')
        } for chat in chats]
        return JsonResponse({'messages': data})

    # Pour le POST en AJAX (envoi de message)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            chat = TicketChat.objects.create(ticket=ticket, sender=request.user, message=message)
            return JsonResponse({'status': 'ok'})
        return JsonResponse({'status': 'error', 'message': 'Empty message'}, status=400)

    # Affichage normal de la page
    return render(request, 'pages/tech/ticket_chat.html', {
        'ticket': ticket,
        'base_template': "admin_base.html"
    })

@login_required
def user_edit_ticket(request, pk):
    """Modifier un signalement (Admin ou Propriétaire)"""
    if request.user.is_admin() or request.user.is_superuser:
        ticket = get_object_or_404(Ticket, pk=pk)
    else:
        ticket = get_object_or_404(Ticket, pk=pk, reported_by=request.user)
    if ticket.is_resolved:
        messages.error(request, "Impossible de modifier un ticket déjà résolu.")
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Signalement mis à jour.")
            return redirect('user_dashboard')
    else:
        form = TicketForm(instance=ticket, user=request.user)
    
    return render(request, 'pages/user/report_issue.html', {
        'form': form, 
        'ticket': ticket, 
        'is_edit': True,
        'base_template': "admin_base.html"
    })

@login_required
def user_delete_ticket(request, pk):
    """Suppression logique d'un ticket (Admin ou Propriétaire)"""
    if request.user.is_admin() or request.user.is_superuser:
        ticket = get_object_or_404(Ticket, pk=pk)
    else:
        ticket = get_object_or_404(Ticket, pk=pk, reported_by=request.user)
    if not ticket.is_resolved:
        # Si le ticket n'est pas résolu, on peut restaurer le statut de l'appareil
        ticket.device.status = 'ASSIGNED'
        ticket.device.save()
        
    ticket.is_deleted = True
    ticket.save()
    messages.warning(request, "Signalement supprimé.")
    return redirect('user_dashboard')


# ==========================================
# 4. VUES UTILISATEUR
# ==========================================
@verified_required
def user_dashboard(request):
    """Zone utilisateur"""
    my_devices = Device.objects.filter(assigned_to=request.user, is_deleted=False)
    my_tickets = Ticket.objects.filter(reported_by=request.user).order_by('-created_at')
    
    base_template = "admin_base.html"

    context = {
        'devices': my_devices,
        'tickets': my_tickets,
        'total_devices': my_devices.count(),
        'active_tickets': my_tickets.filter(is_resolved=False).count(),
        'base_template': base_template,
    }
    return render(request, 'pages/user/dashboard_user.html', context)

@verified_required
def user_report_issue(request):
    """Signaler une panne"""
    if request.method == 'POST':
        form = TicketForm(request.POST, user=request.user)
        if form.is_valid():
            device = form.cleaned_data.get('device')
            
            # Vérification : un seul signalement ouvert par équipement
            existing_ticket = Ticket.objects.filter(device=device, is_resolved=False, is_deleted=False).exists()
            if existing_ticket:
                messages.error(request, f"Un signalement est déjà en cours pour {device.name}. Veuillez patienter jusqu'à sa résolution.")
                return redirect('user_dashboard')

            ticket = form.save(commit=False)
            ticket.reported_by = request.user
            ticket.save()
            
            # Changement de statut automatique de l'appareil
            device.status = 'MAINTENANCE'
            device.save()

            DeviceHistory.objects.create(
                device=ticket.device,
                action=f"Panne signalée : {ticket.description[:50]}...",
                performer=request.user
            )

            messages.success(request, "Problème signalé avec succès. Un technicien va intervenir.")
            return redirect('user_dashboard')
    else:
        form = TicketForm(user=request.user)
    
    base_template = "admin_base.html"
    
    return render(request, 'pages/user/report_issue.html', {'form': form, 'base_template': base_template})

@login_required
def global_search(request):
    """Recherche globale dans tout le parc (Equipements, Utilisateurs, Tickets)"""
    query = request.GET.get('q', '').strip()
    results_devices = []
    results_users = []
    results_tickets = []

    if query:
        # 1. Recherche d'équipements
        results_devices = Device.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(serial_number__icontains=query),
            is_deleted=False
        )[:20]

        # 2. Recherche d'utilisateurs (Admin/Superuser uniquement)
        if request.user.is_admin() or request.user.is_superuser:
            results_users = User.objects.filter(
                models.Q(username__icontains=query) |
                models.Q(email__icontains=query) |
                models.Q(first_name__icontains=query) |
                models.Q(last_name__icontains=query)
            )[:20]

        # 3. Recherche de tickets (Admins et Techs voient tout, User voit les siens)
        if request.user.is_admin() or request.user.is_superuser or request.user.is_technician():
            results_tickets = Ticket.objects.filter(
                models.Q(description__icontains=query) |
                models.Q(device__name__icontains=query),
                is_deleted=False
            ).order_by('-created_at')[:20]
        else:
            results_tickets = Ticket.objects.filter(
                models.Q(description__icontains=query),
                reported_by=request.user,
                is_deleted=False
            ).order_by('-created_at')[:20]

    return render(request, 'pages/search_results.html', {
        'query': query,
        'devices': results_devices,
        'users': results_users,
        'tickets': results_tickets,
        'base_template': "admin_base.html"
    })

# ==========================================
# 5. FONCTIONNALITÉS AVANCÉES (EXPORT & BULK)
# ==========================================

@admin_required
def export_devices_csv(request):
    """Export de l'inventaire complet en CSV"""
    response = HttpResponse(content_type='text/csv')
    response.charset = 'utf-8-sig' # Pour Excel
    response['Content-Disposition'] = 'attachment; filename="inventaire_parc.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Nom', 'N° Serie', 'Categorie', 'Statut', 'Assigne a', 'Date Creation'])
    
    devices = Device.objects.filter(is_deleted=False).select_related('category', 'assigned_to')
    for d in devices:
        writer.writerow([
            d.id, d.name, d.serial_number, d.category.name, d.get_status_display(),
            d.assigned_to.username if d.assigned_to else 'Disponible',
            d.created_at.strftime('%d/%m/%Y')
        ])
    return response

@admin_required
def export_tickets_pdf(request):
    """Génération d'un rapport PDF des tickets ouverts"""
    from xhtml2pdf import pisa
    tickets = Ticket.objects.filter(is_deleted=False).order_by('-priority', '-created_at')
    html = render_to_string('pages/admin/export_tickets_pdf.html', {'tickets': tickets})
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_incidents.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Erreur PDF', status=500)
    return response

@admin_required
def admin_bulk_devices(request):
    """Actions groupées sur les équipements"""
    if request.method == 'POST':
        device_ids = request.POST.getlist('device_ids')
        action = request.POST.get('action')
        
        if not device_ids:
            messages.warning(request, "Aucun équipement sélectionné.")
            return redirect('admin_manage_devices')
            
        devices = Device.objects.filter(id__in=device_ids)
        count = devices.count()
        
        if action == 'delete':
            devices.update(is_deleted=True, status='BROKEN', assigned_to=None)
            for d in devices:
                DeviceHistory.objects.create(device=d, action="Suppression groupée", performer=request.user)
            messages.success(request, f"{count} équipements supprimés.")
        elif action == 'status_maintenance':
            devices.update(status='MAINTENANCE')
            messages.success(request, f"{count} équipements passés en maintenance.")
        elif action == 'status_stock':
            devices.update(status='AVAILABLE', assigned_to=None)
            messages.success(request, f"{count} équipements remis en stock.")
            
    return redirect('admin_manage_devices')

import google.generativeai as genai
from django.conf import settings
import json
import uuid

import os
from dotenv import load_dotenv
load_dotenv()

# Configuration API Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

@csrf_exempt
def ai_voice_agent(request):
    # Vérification stricte de l'accès admin
    is_admin = False
    if request.user.is_authenticated:
        if request.user.is_superuser or (hasattr(request.user, 'is_admin') and request.user.is_admin()):
            is_admin = True
    
    if not is_admin:
        return JsonResponse({'reply': 'Accès refusé. Cette fonctionnalité est réservée aux administrateurs.'}, status=403)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_text = data.get('text', '')
        except:
            return JsonResponse({'reply': 'Je n\'ai pas compris.'})
            
        system_instruction = """
        Tu es l'agent IA vocal du système G-Parc. Tu aides les administrateurs à gérer le parc informatique.
        Tu dois TOUJOURS répondre en format JSON strict.
        
        Exemple de JSON attendu:
        {
            "reply": "Le texte que tu dis à haute voix à l'utilisateur.",
            "action": "CREATE_DEVICE" | "ASSIGN_DEVICE" | "GET_STATS" | "DELETE_DEVICE" | "LIST_USERS" | "UPDATE_USER_ROLE" | "EXPORT_DATA" | "CHANGE_STATUS" | "SEARCH_DEVICE" | "NONE",
            "params": {
                "device_name": "Nom équipement",
                "category": "Catégorie",
                "target_username": "Nom utilisateur",
                "serial_number": "N° de série",
                "role": "ADMIN | TECHNICIAN | HEAD_TECHNICIAN | USER",
                "status": "AVAILABLE | ASSIGNED | MAINTENANCE | BROKEN"
            }
        }
        
        Règles d'actions:
        - Si on te demande d'ajouter ou créer un équipement: CREATE_DEVICE (device_name, category).
        - Si on te demande d'affecter un matériel à quelqu'un: ASSIGN_DEVICE (target_username, device_name).
        - Si on te demande un état des lieux ou statistiques: GET_STATS.
        - Si on te demande de supprimer un appareil: DELETE_DEVICE (serial_number ou device_name).
        - Si on te demande qui sont les utilisateurs ou membres: LIST_USERS.
        - Si on te demande de changer le rôle d'un utilisateur: UPDATE_USER_ROLE (target_username, role).
        - Si on te demande d'exporter les données ou le fichier CSV: EXPORT_DATA.
        - Si on te demande de changer l'état d'un appareil (maintenance, panne, etc): CHANGE_STATUS (serial_number, status).
        - Si on te demande de chercher un appareil: SEARCH_DEVICE (device_name ou serial_number).
        - Sinon: NONE.
        """
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
            response = model.generate_content(system_instruction + "\n\nDemande de l'admin: " + user_text)
            
            if not response or not response.text:
                return JsonResponse({'reply': "Désolé, je n'ai pas pu générer de réponse. Vérifiez votre connexion ou la validité de votre demande."})

            # Nettoyage de la réponse pour éviter les erreurs de parsing
            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()
            
            ai_data = json.loads(response_text)
            action = ai_data.get('action', 'NONE')
            params = ai_data.get('params', {})
            reply = ai_data.get('reply', 'Action effectuée.')
            
            # Exécution de l'action dans la DB
            if action == 'CREATE_DEVICE':
                cat_name = params.get('category', 'Ordinateur')
                dev_name = params.get('device_name', 'Nouvel Équipement')
                cat, _ = Category.objects.get_or_create(name=cat_name)
                sn = str(uuid.uuid4())[:8].upper()
                Device.objects.create(name=dev_name, category=cat, serial_number=sn, status='AVAILABLE')
                reply = f"C'est fait, j'ai créé l'équipement {dev_name} de catégorie {cat_name}. Le numéro de série généré est {sn}."
                
            elif action == 'ASSIGN_DEVICE':
                username = params.get('target_username', '').lower().strip()
                dev_name = params.get('device_name', '').lower().strip()
                
                target_user = User.objects.filter(models.Q(username__icontains=username) | models.Q(first_name__icontains=username)).first()
                        
                target_device = Device.objects.filter(status='AVAILABLE', name__icontains=dev_name).first()
                if not target_device:
                    target_device = Device.objects.filter(status='AVAILABLE').first()
                    
                if target_user and target_device:
                    target_device.assigned_to = target_user
                    target_device.status = 'ASSIGNED'
                    target_device.save()
                    
                    DeviceHistory.objects.create(
                        device=target_device,
                        action=f"Assigné à {target_user.username} via assistant vocal (v2.5)",
                        performer=request.user
                    )
                    reply = f"Parfait. L'équipement {target_device.name} a été assigné à {target_user.username}."
                else:
                    reply = "Je n'ai pas pu identifier précisément l'utilisateur ou aucun équipement de ce type n'est disponible."
                    
            elif action == 'GET_STATS':
                total = Device.objects.filter(is_deleted=False).count()
                hs = Device.objects.filter(status='BROKEN', is_deleted=False).count()
                maint = Device.objects.filter(status='MAINTENANCE', is_deleted=False).count()
                reply = f"Nous avons actuellement {total} équipements actifs. {hs} sont hors service et {maint} sont en cours de maintenance."

            elif action == 'DELETE_DEVICE':
                sn = params.get('serial_number', '')
                name = params.get('device_name', '')
                device = None
                if sn: device = Device.objects.filter(serial_number=sn).first()
                if not device and name: device = Device.objects.filter(name__icontains=name).first()
                
                if device:
                    device.is_deleted = True
                    device.save()
                    reply = f"L'équipement {device.name} a été retiré de l'inventaire avec succès."
                else:
                    reply = "Je n'ai pas trouvé l'équipement spécifié pour la suppression."

            elif action == 'LIST_USERS':
                users = User.objects.all()[:5]
                names = ", ".join([u.username for u in users])
                total = User.objects.count()
                reply = f"Il y a {total} utilisateurs au total. Les derniers inscrits sont : {names}."

            elif action == 'UPDATE_USER_ROLE':
                username = params.get('target_username', '').lower()
                role_name = params.get('role', '').upper()
                target_user = User.objects.filter(username__icontains=username).first()
                role_obj = Role.objects.filter(name=role_name).first()
                
                if target_user and role_obj:
                    target_user.role = role_obj
                    target_user.save()
                    reply = f"Le rôle de {target_user.username} a été mis à jour en {role_obj.get_name_display()}."
                else:
                    reply = "Je n'ai pas pu trouver l'utilisateur ou le rôle spécifié."

            elif action == 'EXPORT_DATA':
                reply = "Bien sûr. Vous pouvez télécharger l'export CSV en cliquant sur le bouton Export dans la gestion des équipements."

            elif action == 'CHANGE_STATUS':
                sn = params.get('serial_number', '')
                status = params.get('status', '').upper()
                device = Device.objects.filter(serial_number=sn).first()
                if device:
                    device.status = status
                    device.save()
                    reply = f"L'état de l'équipement {device.name} a été changé en {device.get_status_display()}."
                else:
                    reply = "Je n'ai pas pu identifier l'équipement par son numéro de série."

            elif action == 'SEARCH_DEVICE':
                name = params.get('device_name', '')
                device = Device.objects.filter(name__icontains=name).first()
                if device:
                    reply = f"J'ai trouvé l'équipement {device.name}. Son numéro de série est {device.serial_number} et son statut actuel est {device.get_status_display()}."
                else:
                    reply = "Je n'ai trouvé aucun équipement correspondant à votre recherche."

            return JsonResponse({'reply': reply})
            
        except Exception as e:
            print("Erreur IA:", str(e))
            return JsonResponse({'reply': f"Erreur technique (v2.5) : {str(e)}"})
            
    return JsonResponse({'error': 'Invalid request'}, status=400)
