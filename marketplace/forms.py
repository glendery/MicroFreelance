from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Project, ProjectReview, WithdrawalRequest, Category

class ProjectForm(forms.ModelForm):
    """Form untuk membuat atau mengedit proyek."""
    class Meta:
        model = Project
        fields = ['title', 'category', 'description', 'budget']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control rounded-pill px-4 py-2', 
                'placeholder': 'Apa yang perlu dikerjakan?'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select rounded-pill px-4'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control rounded-4 px-4 py-3', 
                'rows': 5, 
                'placeholder': 'Jelaskan detail tugas, tenggat waktu, dan hasil yang diharapkan...'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control rounded-pill px-4', 
                'placeholder': 'Berapa anggaran Anda? (Rp)'
            }),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ProjectReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} Bintang") for i in range(5, 0, -1)], attrs={'class': 'form-select rounded-pill'}),
            'comment': forms.Textarea(attrs={'class': 'form-control rounded-4', 'rows': 3, 'placeholder': 'Berikan feedback untuk freelancer...'}),
        }

class WithdrawalForm(forms.ModelForm):
    class Meta:
        model = WithdrawalRequest
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control rounded-pill', 'placeholder': 'Jumlah penarikan'}),
        }

class SignupForm(UserCreationForm):
    """Form pendaftaran user baru."""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)
