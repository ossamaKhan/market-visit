from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('logout/', views.AdminLogoutView.as_view(), name='admin_logout'),
    path('users/', views.manage_users, name='manage_users'),
    path('visits/', views.visit_log_list, name='visit_log_list'),
    path('visits/<int:pk>/delete/', views.visit_log_delete, name='visit_log_delete'),
]
