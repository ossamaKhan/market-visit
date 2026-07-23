import json
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from hierarchy.models import FranchiseRecord
from .models import MarketVisit
from .forms import MarketVisitForm


def field_agent_required(view_func):
    """
    Any logged-in user may use these pages, EXCEPT accounts that only
    have report ViewerAccess (and aren't also staff) — they're sent to
    the Management dashboard instead, since that's the only area they're
    meant to use.
    """
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff and hasattr(request.user, 'viewer_access'):
            return redirect('management_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped


@field_agent_required
def dashboard(request):
    visits = MarketVisit.objects.filter(visited_by=request.user).select_related('franchise')
    total_visits = visits.count()

    paginator = Paginator(visits, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'visits/dashboard.html', {'total_visits': total_visits, 'page_obj': page_obj})


@login_required
def visit_detail(request, pk):
    visit = get_object_or_404(MarketVisit, pk=pk)
    is_management = request.user.is_staff or hasattr(request.user, 'viewer_access')
    return render(request, 'visits/visit_detail.html', {'visit': visit, 'is_management': is_management})


def _hierarchy_json(user):
    """
    Serializes only the franchise records whose hierarchy email matches
    the logged-in user, so the log-visit page's info box (and dropdown)
    only ever shows franchises that belong to them.
    """
    fields = ['id', 'fr_id', 'region', 'bu', 'fr_status', 'fr_city', 'fr_address', 'arm_name', 'arm_emp_no', 'email']
    queryset = FranchiseRecord.objects.filter(email__iexact=user.email) if user.email else FranchiseRecord.objects.none()
    data = {row['id']: row for row in queryset.values(*fields)}
    return json.dumps(data)


@field_agent_required
def visit_create(request):
    today = timezone.now().date()
    if request.method == 'POST':
        form = MarketVisitForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.visited_by = request.user
            visit.visit_date = today
            visit.save()
            messages.success(request, 'Market visit logged successfully.')
            return redirect('visit_detail', pk=visit.pk)
    else:
        form = MarketVisitForm(user=request.user)
    return render(request, 'visits/visit_form.html', {
        'form': form,
        'title': 'Log a Market Visit',
        'hierarchy_json': _hierarchy_json(request.user),
        'today': today,
    })
