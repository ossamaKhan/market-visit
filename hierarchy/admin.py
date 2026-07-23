from django.contrib import admin
from .models import FranchiseRecord, UserCredential


@admin.register(FranchiseRecord)
class FranchiseRecordAdmin(admin.ModelAdmin):
    list_display = ('fr_id', 'region', 'bu', 'fr_city', 'arm_name', 'email', 'fr_status')
    list_filter = ('region', 'bu', 'fr_status')
    search_fields = ('fr_id', 'arm_name', 'email', 'fr_city')


@admin.register(UserCredential)
class UserCredentialAdmin(admin.ModelAdmin):
    list_display = ('user', 'must_change_password', 'updated_at')
    search_fields = ('user__email', 'user__username')
