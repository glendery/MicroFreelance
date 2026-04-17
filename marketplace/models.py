from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    """
    Kustom User model dengan role-based access control, saldo, dan avatar.
    """
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        CLIENT = 'CLIENT', 'Client'
        FREELANCER = 'FREELANCER', 'Freelancer'

    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.CLIENT
    )
    balance = models.BigIntegerField(default=0)
    avatar = models.FileField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_freelancer(self):
        return self.role == self.Role.FREELANCER

    @property
    def has_unread_notifications(self):
        return self.notifications.filter(is_read=False).exists()

    @property
    def freelancer_stats(self):
        """Menghitung statistik performa freelancer secara efisien."""
        completed_projects = self.projects_taken.filter(status='COMPLETED')
        total_earned = completed_projects.aggregate(models.Sum('budget'))['budget__sum'] or 0
        avg_rating = self.projects_taken.aggregate(models.Avg('review__rating'))['review__rating__avg'] or 0
        return {
            'count': completed_projects.count(),
            'earned': total_earned,
            'rating': avg_rating
        }

    @property
    def level_info(self):
        """Menentukan level berdasarkan pendapatan, rating, dan jam terbang."""
        if not self.is_freelancer:
            return None
            
        stats = self.freelancer_stats
        earned = stats['earned']
        rating = stats['rating']
        count = stats['count']

        if earned >= 5000000 and rating >= 4.5:
            return {'name': 'Elite Expert', 'badge': 'bg-danger', 'icon': 'fa-crown'}
        elif earned >= 1000000 and rating >= 4.0:
            return {'name': 'Rising Star', 'badge': 'bg-warning text-dark', 'icon': 'fa-star'}
        elif count >= 1:
            return {'name': 'Active Freelancer', 'badge': 'bg-primary', 'icon': 'fa-user-check'}
        else:
            return {'name': 'Newbie', 'badge': 'bg-secondary', 'icon': 'fa-seedling'}

class Category(models.Model):
    """Kategori proyek seperti Programming, Design, dll."""
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="Emoji atau FontAwesome class")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Project(models.Model):
    """
    Model Proyek yang mengelola siklus hidup tugas dan pembayaran.
    """
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        REVIEW = 'REVIEW', 'Review'
        COMPLETED = 'COMPLETED', 'Completed'

    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='projects')
    description = models.TextField()
    budget = models.BigIntegerField()
    client = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='projects_created'
    )
    freelancer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='projects_taken'
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    work_submission = models.TextField(blank=True, null=True)
    work_file = models.FileField(upload_to='submissions/', null=True, blank=True)

    def __str__(self):
        return self.title

    def clean(self):
        if self.budget < 0:
            raise ValidationError("Budget tidak boleh negatif.")

    def approve_and_pay(self):
        """Logika bisnis untuk menyetujui pekerjaan dan mentransfer dana."""
        if self.status != self.Status.REVIEW:
            raise ValidationError("Proyek harus dalam status REVIEW untuk disetujui.")
        
        if self.client.balance < self.budget:
            raise ValidationError("Saldo Client tidak mencukupi.")

        with transaction.atomic():
            self.client.balance -= self.budget
            self.freelancer.balance += self.budget
            self.client.save()
            self.freelancer.save()
            self.status = self.Status.COMPLETED
            self.save()

class ProjectReview(models.Model):
    """Review dan rating dari Client untuk Freelancer setelah proyek selesai."""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.project.title}"

class WithdrawalRequest(models.Model):
    """Permintaan penarikan saldo oleh Freelancer."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.BigIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount}"

class Notification(models.Model):
    """Notifikasi sistem untuk user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class ProjectMessage(models.Model):
    """Pesan sederhana (chat) antara Client dan Freelancer pada suatu proyek."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

class ActivityLog(models.Model):
    """Mencatat aktivitas user untuk keperluan audit/monitoring."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"
