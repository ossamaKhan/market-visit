from django.contrib import admin
from .models import MarketVisit


@admin.register(MarketVisit)
class MarketVisitAdmin(admin.ModelAdmin):
    list_display = ('name', 'franchise', 'visit_date', 'visited_by', 'priority', 'status')
    list_filter = ('status', 'priority', 'visit_date', 'visit_type')
    search_fields = ('name', 'evc', 'franchise__fr_id', 'franchise__arm_name')
    date_hierarchy = 'visit_date'
