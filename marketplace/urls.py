from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from . import views

# DRF Router
router = DefaultRouter()
router.register(r'api/projects', views.ProjectViewSet)
router.register(r'api/categories', views.CategoryViewSet)

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Registration
    path('register/', views.register_select, name='register'),
    path('register/client/', views.register_client, name='register_client'),
    path('register/freelancer/', views.register_freelancer, name='register_freelancer'),
    
    # Auth
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboards
    path('dashboard/client/', views.client_dashboard, name='client_dashboard'),
    path('dashboard/freelancer/', views.freelancer_dashboard, name='freelancer_dashboard'),
    
    # Profiles
    path('profile/freelancer/<int:user_id>/', views.freelancer_profile, name='freelancer_profile'),
    
    # Project Actions
    path('projects/browse/', views.browse_projects, name='browse_projects'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('project/<int:project_id>/take/', views.take_project, name='take_project'),
    path('project/<int:project_id>/submit/', views.submit_work, name='submit_work'),
    path('project/<int:project_id>/approve/', views.approve_work, name='approve_work'),
    path('project/<int:project_id>/invoice/', views.download_invoice, name='download_invoice'),
    
    # Wallet & Withdrawal
    path('top-up/', views.top_up_balance, name='top_up'),
    path('withdraw/', views.withdrawal_request, name='withdraw'),
    
    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    
    # API
    path('', include(router.urls)),
]
