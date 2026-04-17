from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Project

class MarketplaceLogicTest(TestCase):
    def setUp(self):
        # Create users
        self.client_user = User.objects.create_user(
            username='budi_test', 
            password='password123', 
            role='CLIENT', 
            balance=500000
        )
        self.freelancer_user = User.objects.create_user(
            username='eko_test', 
            password='password123', 
            role='FREELANCER', 
            balance=0
        )
        
        # Create a project
        self.project = Project.objects.create(
            title='Test Project',
            description='Test Description',
            budget=100000,
            client=self.client_user,
            status='OPEN'
        )
        
        self.client = Client()

    def test_payment_logic(self):
        """Uji logika pembayaran saat approve pekerjaan."""
        # Simulate login as client
        self.client.login(username='budi_test', password='password123')
        
        # Setup project to REVIEW status
        self.project.freelancer = self.freelancer_user
        self.project.status = 'REVIEW'
        self.project.work_submission = 'Tugas selesai pak!'
        self.project.save()
        
        # Call approve view (POST request)
        response = self.client.post(reverse('approve_work', args=[self.project.id]), {
            'rating': 5,
            'comment': 'Bagus sekali!'
        })
        
        # Refresh data from DB
        self.client_user.refresh_from_db()
        self.freelancer_user.refresh_from_db()
        self.project.refresh_from_db()
        
        # Verify payment
        self.assertEqual(self.client_user.balance, 400000) # 500k - 100k
        self.assertEqual(self.freelancer_user.balance, 100000) # 0 + 100k
        self.assertEqual(self.project.status, 'COMPLETED')
        self.assertEqual(response.status_code, 302) # Redirect to client_dashboard

    def test_insufficient_balance(self):
        """Uji jika saldo client tidak cukup."""
        self.client_user.balance = 50000
        self.client_user.save()
        
        self.client.login(username='budi_test', password='password123')
        
        self.project.freelancer = self.freelancer_user
        self.project.status = 'REVIEW'
        self.project.save()
        
        # Call approve view (POST request)
        self.client.post(reverse('approve_work', args=[self.project.id]), {
            'rating': 5,
            'comment': 'Saldo kurang...'
        })
        
        # Refresh data
        self.client_user.refresh_from_db()
        self.freelancer_user.refresh_from_db()
        self.project.refresh_from_db()
        
        # Verify NO payment occurred
        self.assertEqual(self.client_user.balance, 50000)
        self.assertEqual(self.freelancer_user.balance, 0)
        self.assertEqual(self.project.status, 'REVIEW')
