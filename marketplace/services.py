from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Project, Notification, WithdrawalRequest

class MarketplaceService:
    @staticmethod
    def approve_project_payment(project, client):
        """
        Logika bisnis terpusat untuk approval dan pembayaran.
        Memastikan integritas data dan pengiriman notifikasi.
        """
        if project.status != Project.Status.REVIEW:
            raise ValidationError("Proyek tidak dalam status review.")
        
        if client.balance < project.budget:
            raise ValidationError(f"Saldo tidak cukup. Butuh Rp {project.budget}, saldo Rp {client.balance}")

        with transaction.atomic():
            # 1. Potong Saldo Client
            client.balance -= project.budget
            client.save()

            # 2. Tambah Saldo Freelancer
            freelancer = project.freelancer
            freelancer.balance += project.budget
            freelancer.save()

            # 3. Update Status Proyek
            project.status = Project.Status.COMPLETED
            project.save()

            # 4. Notifikasi Otomatis (Sudah ditangani Signals, tapi bisa ditambahkan custom di sini)
            return True

    @staticmethod
    def create_withdrawal(user, amount):
        """Validasi dan pembuatan request penarikan."""
        if amount > user.balance:
            raise ValidationError("Saldo tidak mencukupi untuk penarikan ini.")
        
        if amount < 50000: # Batas minimal penarikan
            raise ValidationError("Minimal penarikan adalah Rp 50.000.")

        return WithdrawalRequest.objects.create(user=user, amount=amount)
