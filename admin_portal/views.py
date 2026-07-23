from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse

from accounts.decorators import admin_staff_required
from accounts.forms import EmailAuthenticationForm
from hierarchy.models import UserCredential
from reports.models import ViewerAccess
from visits.models import MarketVisit

from .forms import CreateUserForm


class AdminLoginView(LoginView):
    """
    A separate, staff-only login screen for the Admin Portal. Credentials
    are checked the same way as the regular login (email + password), but
    a valid non-staff account is rejected here — admins use this page,
    everyone else uses the Field Agent or Management login.
    """
    template_name = 'admin_portal/login.html'
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_staff:
            form.add_error(None, "This account doesn't have admin access.")
            return self.form_invalid(form)
        auth_login(self.request, user)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('hierarchy_upload')


class AdminLogoutView(LogoutView):
    next_page = reverse_lazy('admin_login')


@admin_staff_required
def manage_users(request):
    """
    "Add Users" — a single page combining the create-account form with
    the list of existing accounts (role, masked password, reset/set).
    """
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']

            user = User.objects.create_user(username=email, email=email, password=password)
            UserCredential.objects.create(user=user, plain_password=password, must_change_password=False)
            if role == 'viewer':
                ViewerAccess.objects.create(user=user, created_by=request.user)

            role_label = 'viewer' if role == 'viewer' else 'field agent'
            messages.success(request, f"Created {role_label} account for {email}.")
            return redirect('manage_users')
    else:
        form = CreateUserForm()

    credentials = UserCredential.objects.select_related('user').order_by('user__email')
    viewer_user_ids = set(ViewerAccess.objects.values_list('user_id', flat=True))

    query = request.GET.get('q', '').strip()
    if query:
        credentials = credentials.filter(user__email__icontains=query)

    users = []
    for cred in credentials:
        users.append({
            'credential': cred,
            'is_viewer': cred.user_id in viewer_user_ids,
        })

    return render(request, 'admin_portal/manage_users.html', {'form': form, 'users': users, 'query': query})


@admin_staff_required
def visit_log_list(request):
    visits = MarketVisit.objects.select_related('franchise', 'visited_by').order_by('-visit_date', '-created_at')

    query = request.GET.get('q', '').strip()
    if query:
        visits = visits.filter(
            Q(name__icontains=query) |
            Q(franchise__fr_id__icontains=query) |
            Q(franchise__arm_name__icontains=query) |
            Q(visited_by__email__icontains=query)
        )

    paginator = Paginator(visits, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_portal/visit_log_list.html', {'page_obj': page_obj, 'query': query})


@admin_staff_required
def visit_log_delete(request, pk):
    visit = get_object_or_404(MarketVisit, pk=pk)
    if request.method == 'POST':
        label = f"{visit.franchise.fr_id if visit.franchise else visit.name} — {visit.visit_date}"
        visit.delete()
        messages.success(request, f"Deleted visit log: {label}.")
        return redirect('visit_log_list')
    return render(request, 'admin_portal/visit_log_confirm_delete.html', {'visit': visit})
