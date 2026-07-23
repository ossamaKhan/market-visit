from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import staff_required
from .forms import HierarchyUploadForm, SetPasswordForm
from .models import FranchiseRecord, UserCredential
from .utils import HierarchyFileError, generate_random_password, parse_hierarchy_file

# Must match reports.views.FILTER_FIELDS / cache key format exactly, so a
# fresh upload invalidates the same keys Reports reads from.
_HIERARCHY_FILTER_FIELDS = ['arm_name', 'fr_city', 'bu', 'fr_id']


@staff_required
def hierarchy_upload(request):
    if request.method == 'POST':
        form = HierarchyUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                records = parse_hierarchy_file(form.cleaned_data['file'])
            except HierarchyFileError as exc:
                messages.error(request, str(exc))
                return render(request, 'hierarchy/upload.html', {'form': form})

            accounts_created = 0
            records_created = 0
            records_updated = 0

            with transaction.atomic():
                # Step 1: make sure every unique email has a User + credential.
                unique_emails = {r['email'].lower() for r in records if r['email']}
                email_to_user = {}

                for email in unique_emails:
                    user = User.objects.filter(email__iexact=email).first()
                    if user is None:
                        password = generate_random_password()
                        user = User.objects.create_user(
                            username=email,
                            email=email,
                            password=password,
                        )
                        UserCredential.objects.create(
                            user=user,
                            plain_password=password,
                            must_change_password=True,
                        )
                        accounts_created += 1
                    email_to_user[email] = user

                # Step 2: upsert FranchiseRecord rows, linked to the right user.
                for row in records:
                    email = row['email'].lower()
                    user = email_to_user.get(email)
                    fr_id = row['fr_id']

                    fields = {
                        'region': row['region'],
                        'bu': row['bu'],
                        'fr_status': row['fr_status'],
                        'fr_city': row['fr_city'],
                        'fr_address': row['fr_address'],
                        'arm_name': row['arm_name'],
                        'arm_emp_no': row['arm_emp_no'],
                        'email': row['email'],
                        'user': user,
                    }
                    obj, created = FranchiseRecord.objects.update_or_create(
                        fr_id=fr_id, defaults=fields
                    )
                    if created:
                        records_created += 1
                    else:
                        records_updated += 1

            messages.success(
                request,
                f"Upload complete: {records_created} new record(s), "
                f"{records_updated} updated, {accounts_created} new account(s) created."
            )
            for field in _HIERARCHY_FILTER_FIELDS:
                cache.delete(f'hierarchy_filter_options:{field}')
            return redirect('hierarchy_list')
    else:
        form = HierarchyUploadForm()

    return render(request, 'hierarchy/upload.html', {'form': form})


@staff_required
def hierarchy_list(request):
    records = FranchiseRecord.objects.select_related('user')

    query = request.GET.get('q', '').strip()
    region_filter = request.GET.get('region', '')

    if query:
        records = records.filter(
            Q(fr_id__icontains=query) |
            Q(arm_name__icontains=query) |
            Q(email__icontains=query) |
            Q(fr_city__icontains=query)
        )
    if region_filter:
        records = records.filter(region=region_filter)

    regions = FranchiseRecord.objects.exclude(region='').values_list('region', flat=True).distinct().order_by('region')

    paginator = Paginator(records, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'query': query,
        'region_filter': region_filter,
        'regions': regions,
    }
    return render(request, 'hierarchy/list.html', context)


@staff_required
def account_reset_password(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        new_password = generate_random_password()
        user.set_password(new_password)
        user.save()
        credential, _ = UserCredential.objects.get_or_create(user=user)
        credential.plain_password = new_password
        credential.must_change_password = True
        credential.save()
        messages.success(request, f"Password reset for {user.email}.")
    return redirect('manage_users')


@staff_required
def account_set_password(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            credential, _ = UserCredential.objects.get_or_create(user=user)
            credential.plain_password = new_password
            credential.must_change_password = True
            credential.save()
            messages.success(request, f"Password updated for {user.email}.")
        else:
            messages.error(request, "Password must be at least 8 characters.")
    return redirect('manage_users')
