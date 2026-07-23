from django.contrib import admin
from .models import ViewerAccess


@admin.register(ViewerAccess)
class ViewerAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_by', 'created_at')
    search_fields = ('user__email',)
