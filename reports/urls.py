from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.ManagementLoginView.as_view(), name='management_login'),
    path('logout/', views.ManagementLogoutView.as_view(), name='management_logout'),
    path('dashboard/', views.management_dashboard, name='management_dashboard'),
    path('visits/', views.viewer_dashboard, name='viewer_dashboard'),
    path('pdf/', views.viewer_dashboard_pdf, name='viewer_dashboard_pdf'),
    path('comment/<int:pk>/', views.add_comment, name='visit_add_comment'),
]
