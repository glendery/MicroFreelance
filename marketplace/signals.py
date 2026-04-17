from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Project, Notification, WithdrawalRequest

@receiver(post_save, sender=Project)
def project_notification(sender, instance, created, **kwargs):
    if created:
        # Notifikasi saat proyek baru dibuat (untuk freelancer mungkin?)
        # Tapi biasanya notifikasi lebih spesifik ke aksi
        pass
    else:
        # Notifikasi perubahan status
        if instance.status == Project.Status.IN_PROGRESS and instance.freelancer:
            Notification.objects.create(
                user=instance.client,
                title="Proyek Diambil",
                message=f"Freelancer {instance.freelancer.username} telah mengambil proyek '{instance.title}'."
            )
        elif instance.status == Project.Status.REVIEW:
            Notification.objects.create(
                user=instance.client,
                title="Pekerjaan Dikirim",
                message=f"Freelancer telah mengirimkan hasil kerja untuk proyek '{instance.title}'. Mohon ditinjau."
            )
        elif instance.status == Project.Status.COMPLETED:
            Notification.objects.create(
                user=instance.freelancer,
                title="Pembayaran Diterima",
                message=f"Selamat! Client telah menyetujui pekerjaan Anda untuk proyek '{instance.title}'. Saldo telah ditambahkan."
            )

@receiver(post_save, sender=WithdrawalRequest)
def withdrawal_notification(sender, instance, created, **kwargs):
    if not created:
        if instance.status == WithdrawalRequest.Status.APPROVED:
            Notification.objects.create(
                user=instance.user,
                title="Penarikan Disetujui",
                message=f"Permintaan penarikan saldo sebesar Rp {instance.amount} telah disetujui dan diproses."
            )
        elif instance.status == WithdrawalRequest.Status.REJECTED:
            Notification.objects.create(
                user=instance.user,
                title="Penarikan Ditolak",
                message=f"Mohon maaf, permintaan penarikan saldo sebesar Rp {instance.amount} ditolak."
            )
