from django import forms
from .models import Device, Ticket, MaintenanceReport, User, Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4 placeholder-[var(--text-muted)]', 'placeholder': 'Nom de la catégorie (ex: Ordinateur Portable)'}),
        }

class TicketAssignmentForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['assigned_to']
        widgets = {
            'assigned_to': forms.Select(attrs={'class': 'form-select w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On ne peut assigner qu'à des techniciens ou au technicien principal
        from .models import Role
        self.fields['assigned_to'].queryset = User.objects.filter(role__name__in=[Role.TECHNICIAN, Role.HEAD_TECHNICIAN])

class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['name', 'serial_number', 'category', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4', 'placeholder': 'Marque et Modèle'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-input w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4', 'placeholder': 'Numéro de série unique'}),
            'category': forms.Select(attrs={'class': 'form-select w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4'}),
            'image': forms.FileInput(attrs={'class': 'form-input w-full text-[var(--text)] mb-4'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_deleted=False)


class DeviceAssignmentForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['assigned_to', 'status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4'}),
        }

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['device', 'description', 'priority']
        widgets = {
            'device': forms.Select(attrs={'class': 'form-select w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4 py-3 px-4'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4 py-3 px-4', 'rows': 4}),
            'priority': forms.Select(attrs={'class': 'form-select w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4 py-3 px-4'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # L'utilisateur ne peut signaler une panne que sur les équipements qui lui sont attribués
            self.fields['device'].queryset = Device.objects.filter(assigned_to=user)

class MaintenanceReportForm(forms.ModelForm):
    class Meta:
        model = MaintenanceReport
        fields = ['action_taken', 'cost']
        widgets = {
            'action_taken': forms.Textarea(attrs={'class': 'form-textarea w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4', 'required': 'required', 'placeholder': 'Décrivez précisément les actions effectuées...'}),
            'cost': forms.NumberInput(attrs={'class': 'form-input w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4', 'step': '0.01', 'placeholder': 'Coût éventuel (CFA)'}),
        }

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] text-sm py-1 px-2'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4'}),
            'phone': forms.TextInput(attrs={'class': 'form-input w-full bg-[var(--sidebar-bg)] border border-[var(--glass-border)] rounded-lg text-[var(--text)] mb-4'}),
        }

