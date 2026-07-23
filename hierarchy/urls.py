from django.urls import path
from . import views

urlpatterns = [
    path('hierarchy/upload/', views.hierarchy_upload, name='hierarchy_upload'),
    path('hierarchy/records/', views.hierarchy_list, name='hierarchy_list'),
    path('users/<int:user_id>/reset/', views.account_reset_password, name='account_reset_password'),
    path('users/<int:user_id>/set-password/', views.account_set_password, name='account_set_password'),
]
