from django.test import TestCase
from .models import User, Role, Device

class GParcLogicTest(TestCase):
    def setUp(self):
        self.role_admin, _ = Role.objects.get_or_create(name=Role.ADMIN)
        self.role_user, _ = Role.objects.get_or_create(name=Role.USER)
        
        self.admin = User.objects.create_user(
            username='admin_test', 
            email='admin@test.com', 
            password='pass',
            role=self.role_admin
        )
        
        self.user = User.objects.create_user(
            username='user_test', 
            email='user@test.com', 
            password='pass',
            role=self.role_user
        )

    def test_role_verification(self):
        """Vérifie que les méthodes de rôle fonctionnent"""
        self.assertTrue(self.admin.is_admin())
        self.assertFalse(self.user.is_admin())

    def test_auto_history_signal(self):
        """Vérifie que le signal d'historique s'exécute lors d'une modification"""
        device = Device.objects.create(
            name="PC-001",
            serial_number="SN123",
            category_id=1, # Suppose qu'une catégorie existe ou est créée par ailleurs
            status='AVAILABLE'
        )
        # L'historique devrait avoir 1 entrée (création)
        from .models import DeviceHistory
        self.assertEqual(DeviceHistory.objects.filter(device=device).count(), 1)
        
        # Modification du statut
        device.status = 'MAINTENANCE'
        device.save()
        
        # Devrait avoir 2 entrées
        self.assertEqual(DeviceHistory.objects.filter(device=device).count(), 2)
