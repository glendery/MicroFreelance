from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Sum, Avg
from django.core.cache import cache
from .services import MarketplaceService
from django.utils import timezone
from .models import User, Project, ProjectReview, WithdrawalRequest, Category, Notification, ProjectMessage
from .forms import ProjectForm, SignupForm, ReviewForm, WithdrawalForm

# PDF Imports
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

# DRF Imports
from rest_framework import viewsets, permissions
from .serializers import ProjectSerializer, CategorySerializer

# --- Web Views ---

def register_select(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'registration/register_select.html')

def _handle_registration(request, role, success_url):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = role
            user.save()
            login(request, user)
            messages.success(request, f"Selamat datang! Akun {user.get_role_display()} berhasil dibuat.")
            return redirect(success_url)
    else:
        form = SignupForm()
    return render(request, 'registration/register_form.html', {
        'form': form, 
        'role': role.title()
    })

def register_client(request):
    return _handle_registration(request, User.Role.CLIENT, 'client_dashboard')

def register_freelancer(request):
    return _handle_registration(request, User.Role.FREELANCER, 'freelancer_dashboard')

@login_required
def dashboard(request):
    if request.user.is_client:
        return redirect('client_dashboard')
    if request.user.is_freelancer:
        return redirect('freelancer_dashboard')
    if request.user.is_staff or request.user.role == User.Role.ADMIN:
        return redirect('admin:index')
    return render(request, 'marketplace/dashboard.html')

@login_required
def client_dashboard(request):
    if not request.user.is_client:
        return redirect('dashboard')
    
    projects = Project.objects.filter(client=request.user).order_by('-created_at')
    
    # Stats for Chart.js
    stats = {
        'total': projects.count(),
        'completed': projects.filter(status=Project.Status.COMPLETED).count(),
        'review': projects.filter(status=Project.Status.REVIEW).count(),
        'active': projects.filter(status=Project.Status.IN_PROGRESS).count(),
    }
    
    form = ProjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        project = form.save(commit=False)
        project.client = request.user
        project.status = Project.Status.OPEN
        project.save()
        messages.success(request, "Proyek baru berhasil dipublikasikan!")
        return redirect('client_dashboard')
    
    # Talent Scouting: Top Freelancers
    top_freelancers = User.objects.filter(role=User.Role.FREELANCER).annotate(
        avg_rating=Avg('projects_taken__review__rating'),
        completed_count=Count('projects_taken', filter=Q(projects_taken__status=Project.Status.COMPLETED))
    ).order_by('-avg_rating', '-completed_count')[:5]
    
    return render(request, 'marketplace/client_dashboard.html', {
        'projects': projects, 
        'form': form,
        'stats': stats,
        'top_freelancers': top_freelancers
    })

@login_required
def freelancer_dashboard(request):
    if not request.user.is_freelancer:
        return redirect('dashboard')
    
    my_projects = Project.objects.filter(freelancer=request.user).order_by('-created_at')
    open_projects = Project.objects.filter(status=Project.Status.OPEN).order_by('-created_at')[:5]
    
    # Stats for Chart.js
    stats = {
        'total': my_projects.count(),
        'completed': my_projects.filter(status=Project.Status.COMPLETED).count(),
        'active': my_projects.filter(status__in=[Project.Status.IN_PROGRESS, Project.Status.REVIEW]).count(),
        'total_earned': my_projects.filter(status=Project.Status.COMPLETED).aggregate(Sum('budget'))['budget__sum'] or 0
    }
    
    return render(request, 'marketplace/freelancer_dashboard.html', {
        'my_projects': my_projects,
        'open_projects': open_projects,
        'stats': stats
    })

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Keamanan: Hanya client pembuat atau freelancer pengambil yang bisa akses detail
    if request.user != project.client and request.user != project.freelancer:
        messages.error(request, "Akses dilarang.")
        return redirect('dashboard')

    messages_list = project.messages.all()
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            ProjectMessage.objects.create(
                project=project,
                sender=request.user,
                content=content
            )
            return redirect('project_detail', project_id=project.id)

    return render(request, 'marketplace/project_detail.html', {
        'project': project,
        'messages_list': messages_list
    })

@login_required
def freelancer_profile(request, user_id):
    freelancer = get_object_or_404(User, id=user_id, role=User.Role.FREELANCER)
    
    # Portfolio: Completed projects
    portfolio = Project.objects.filter(freelancer=freelancer, status=Project.Status.COMPLETED).order_by('-created_at')
    
    # Reviews
    reviews = ProjectReview.objects.filter(project__freelancer=freelancer).order_by('-created_at')
    
    # Stats
    stats = {
        'completed_count': portfolio.count(),
        'avg_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        'total_earned': portfolio.aggregate(Sum('budget'))['budget__sum'] or 0,
    }
    
    return render(request, 'marketplace/freelancer_profile.html', {
        'freelancer': freelancer,
        'portfolio': portfolio,
        'reviews': reviews,
        'stats': stats
    })

@login_required
def browse_projects(request):
    if not request.user.is_freelancer:
        messages.error(request, "Hanya Freelancer yang bisa menjelajahi proyek.")
        return redirect('dashboard')
    
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    min_budget = request.GET.get('min_budget')
    max_budget = request.GET.get('max_budget')
    
    projects = Project.objects.filter(status=Project.Status.OPEN).order_by('-created_at')
    
    # Advanced Filtering with Q objects
    if query:
        projects = projects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    if category_id:
        projects = projects.filter(category_id=category_id)
        
    if min_budget:
        projects = projects.filter(budget__gte=min_budget)
    
    if max_budget:
        projects = projects.filter(budget__lte=max_budget)
        
    # Caching categories for 1 hour
    categories = cache.get('marketplace_categories')
    if not categories:
        categories = Category.objects.all()
        cache.set('marketplace_categories', categories, 3600)

    return render(request, 'marketplace/browse_projects.html', {
        'projects': projects,
        'categories': categories,
        'selected_category': int(category_id) if category_id and category_id.isdigit() else None,
        'query': query
    })

@login_required
def take_project(request, project_id):
    if not request.user.is_freelancer:
        messages.error(request, "Hanya Freelancer yang bisa mengambil tugas.")
        return redirect('dashboard')
    
    project = get_object_or_404(Project, id=project_id)
    
    if project.status != Project.Status.OPEN:
        messages.error(request, "Maaf, tugas ini sudah diambil atau tidak tersedia lagi.")
        return redirect('browse_projects')

    if project.client == request.user:
        messages.error(request, "Anda tidak bisa mengambil tugas yang Anda buat sendiri.")
        return redirect('browse_projects')
        
    project.freelancer = request.user
    project.status = Project.Status.IN_PROGRESS
    project.save()
    messages.success(request, f"Tugas '{project.title}' berhasil diambil! Silakan mulai kerjakan.")
    return redirect('project_detail', project_id=project.id)

@login_required
def submit_work(request, project_id):
    if not request.user.is_freelancer:
        return redirect('dashboard')
    
    project = get_object_or_404(Project, id=project_id, freelancer=request.user, status=Project.Status.IN_PROGRESS)
    
    if request.method == 'POST':
        work_submission = request.POST.get('work_submission')
        work_file = request.FILES.get('work_file')
        
        if work_submission or work_file:
            project.work_submission = work_submission
            if work_file:
                project.work_file = work_file
            project.status = Project.Status.REVIEW
            project.save()
            messages.success(request, "Hasil kerja telah dikirim untuk ditinjau.")
            return redirect('project_detail', project_id=project.id)
    
    return render(request, 'marketplace/submit_work.html', {'project': project})

@login_required
def approve_work(request, project_id):
    if not request.user.is_client:
        return redirect('dashboard')
    
    project = get_object_or_404(Project, id=project_id, client=request.user, status=Project.Status.REVIEW)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                # Use Service Layer
                MarketplaceService.approve_project_payment(project, request.user)
                
                # Save Review
                review = form.save(commit=False)
                review.project = project
                review.save()
                
                messages.success(request, f"Tugas '{project.title}' disetujui dan dibayar!")
            except ValidationError as e:
                messages.error(request, e.message)
            return redirect('client_dashboard')
    else:
        form = ReviewForm()
        
    return render(request, 'marketplace/approve_confirm.html', {'project': project, 'form': form})

@login_required
def withdrawal_request(request):
    if not request.user.is_freelancer:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            try:
                MarketplaceService.create_withdrawal(request.user, amount)
                messages.success(request, "Permintaan penarikan saldo telah dikirim dan menunggu approval admin.")
            except ValidationError as e:
                messages.error(request, e.message)
            return redirect('dashboard')
    else:
        form = WithdrawalForm()
        
    return render(request, 'marketplace/withdrawal.html', {'form': form})

@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    # Mark as read
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'marketplace/notifications.html', {'notifications': notifications})

@login_required
def top_up_balance(request):
    if request.method == 'POST':
        try:
            amount = int(request.POST.get('amount', '0'))
            MAX_TOP_UP = 1_000_000_000_000 
            if 0 < amount <= MAX_TOP_UP:
                request.user.balance += amount
                request.user.save()
                messages.success(request, f"Top up berhasil! Saldo baru: Rp {request.user.balance}")
            else:
                messages.error(request, f"Jumlah tidak valid.")
        except ValueError:
            messages.error(request, "Masukkan angka yang valid.")
        return redirect('dashboard')
    return render(request, 'marketplace/top_up.html')

@login_required
def download_invoice(request, project_id):
    project = get_object_or_404(Project, id=project_id, status=Project.Status.COMPLETED)
    
    # Keamanan: Hanya client pembuat atau freelancer pengambil yang bisa akses
    if request.user != project.client and request.user != project.freelancer:
        messages.error(request, "Akses dilarang.")
        return redirect('dashboard')

    template_path = 'marketplace/invoice_pdf.html'
    context = {'project': project, 'today': timezone.now()}
    
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{project.id}.pdf"'
    
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('Kami mengalami masalah saat membuat PDF Anda <pre>' + html + '</pre>')
    return response

# --- API Viewsets ---

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
