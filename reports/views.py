import io
import json

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView, LogoutView
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from accounts.decorators import user_test_required
from accounts.forms import EmailAuthenticationForm
from hierarchy.models import FranchiseRecord
from visits.models import MarketVisit

report_access_required = user_test_required(
    lambda u: u.is_active and (u.is_staff or hasattr(u, 'viewer_access'))
)

FILTER_OPTIONS_CACHE_TIMEOUT = 300  # 5 minutes
FILTER_FIELDS = ['arm_name', 'fr_city', 'bu', 'fr_id']


class ManagementLoginView(LoginView):
    """
    The Management login (mounted at /management/login/). Only staff or
    accounts with report ViewerAccess may sign in here — a plain field
    agent account is rejected and pointed to the Field Agent login.
    """
    template_name = 'reports/login.html'
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if not (user.is_staff or hasattr(user, 'viewer_access')):
            form.add_error(None, "This is a field agent account — please use the Field Agent login instead.")
            return self.form_invalid(form)
        auth_login(self.request, user)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('management_dashboard')


class ManagementLogoutView(LogoutView):
    next_page = reverse_lazy('management_login')


@report_access_required
def management_dashboard(request):
    visits = MarketVisit.objects.all()
    total_visits = visits.count()

    six_months_ago = timezone.now().date().replace(day=1) - timezone.timedelta(days=150)
    by_month = (
        visits.filter(visit_date__gte=six_months_ago)
        .annotate(month=TruncMonth('visit_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    month_labels = [row['month'].strftime('%b %Y') for row in by_month]
    month_data = [row['count'] for row in by_month]

    def group_by(field, limit=None):
        qs = (
            visits.exclude(**{f'franchise__{field}': ''})
            .exclude(**{f'franchise__{field}': None})
            .values(f'franchise__{field}')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        if limit:
            qs = qs[:limit]
        labels = [row[f'franchise__{field}'] for row in qs]
        data = [row['count'] for row in qs]
        return labels, data

    bu_labels, bu_data = group_by('bu')
    region_labels, region_data = group_by('region')
    arm_labels, arm_data = group_by('arm_name', limit=5)

    status_counts = visits.values('status').annotate(count=Count('id'))
    status_display = dict(MarketVisit.STATUS_CHOICES)
    status_labels = [status_display.get(row['status'], row['status']) for row in status_counts]
    status_data = [row['count'] for row in status_counts]

    context = {
        'total_visits': total_visits,
        'month_labels': json.dumps(month_labels),
        'month_data': json.dumps(month_data),
        'bu_labels': json.dumps(bu_labels),
        'bu_data': json.dumps(bu_data),
        'region_labels': json.dumps(region_labels),
        'region_data': json.dumps(region_data),
        'arm_labels': json.dumps(arm_labels),
        'arm_data': json.dumps(arm_data),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
    }
    return render(request, 'reports/management_dashboard.html', context)


def get_cached_filter_options(field):
    """
    Distinct hierarchy values change only when someone re-uploads the
    hierarchy file, so it's safe to cache them briefly instead of
    re-scanning FranchiseRecord on every Reports page view. Invalidated
    explicitly by hierarchy.views.hierarchy_upload after a new upload.
    """
    cache_key = f'hierarchy_filter_options:{field}'
    values = cache.get(cache_key)
    if values is None:
        values = list(
            FranchiseRecord.objects.exclude(**{field: ''})
            .exclude(**{field: None})
            .values_list(field, flat=True)
            .distinct()
            .order_by(field)
        )
        cache.set(cache_key, values, FILTER_OPTIONS_CACHE_TIMEOUT)
    return values


def _filtered_visits(request):
    visits = MarketVisit.objects.select_related('franchise', 'visited_by')

    arm = request.GET.get('arm', '')
    city = request.GET.get('city', '')
    bu = request.GET.get('bu', '')
    fr_id = request.GET.get('fr_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if arm:
        visits = visits.filter(franchise__arm_name=arm)
    if city:
        visits = visits.filter(franchise__fr_city=city)
    if bu:
        visits = visits.filter(franchise__bu=bu)
    if fr_id:
        visits = visits.filter(franchise__fr_id=fr_id)
    if date_from:
        visits = visits.filter(visit_date__gte=date_from)
    if date_to:
        visits = visits.filter(visit_date__lte=date_to)

    return visits, {
        'arm': arm, 'city': city, 'bu': bu, 'fr_id': fr_id,
        'date_from': date_from, 'date_to': date_to,
    }


@report_access_required
def viewer_dashboard(request):
    visits, filters = _filtered_visits(request)

    paginator = Paginator(visits, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        **filters,
        'arm_options': get_cached_filter_options('arm_name'),
        'city_options': get_cached_filter_options('fr_city'),
        'bu_options': get_cached_filter_options('bu'),
        'fr_id_options': get_cached_filter_options('fr_id'),
        'query_string': request.GET.urlencode(),
    }
    return render(request, 'reports/viewer_dashboard.html', context)


@report_access_required
def viewer_dashboard_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (
        Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    visits, filters = _filtered_visits(request)
    visits = list(visits.order_by('-visit_date')[:300])  # sane cap for a single PDF

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=16 * mm, rightMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Market Visit Report", styles['Title']),
        Paragraph(f"Generated {timezone.now().strftime('%d %b %Y, %H:%M')}", styles['Normal']),
    ]

    active_filters = [f"{label}: {value}" for label, value in [
        ('ARM', filters['arm']), ('City', filters['city']), ('BU', filters['bu']),
        ('Franchise', filters['fr_id']), ('From', filters['date_from']), ('To', filters['date_to']),
    ] if value]
    if active_filters:
        story.append(Paragraph("Filters — " + " | ".join(active_filters), styles['Normal']))
    story.append(Spacer(1, 14))

    def scaled_image(field_file, max_w=170, max_h=130):
        try:
            reader = ImageReader(field_file.path)
            iw, ih = reader.getSize()
            scale = min(max_w / iw, max_h / ih, 1)
            return RLImage(field_file.path, width=iw * scale, height=ih * scale)
        except Exception:
            return None

    if not visits:
        story.append(Paragraph("No visits match these filters.", styles['Normal']))

    for visit in visits:
        franchise = visit.franchise
        story.append(Paragraph(
            f"{franchise.fr_id if franchise else '—'} — {visit.name}", styles['Heading3']
        ))

        def checkbox_summary(zong, ufone, jazz):
            flags = [label for label, on in [('Zong', zong), ('Ufone', ufone), ('Jazz', jazz)] if on]
            return ', '.join(flags) if flags else '—'

        fascia_summary = checkbox_summary(visit.fascia_zong, visit.fascia_ufone, visit.fascia_jazz)
        avh_summary = checkbox_summary(visit.avh_zong, visit.avh_ufone, visit.avh_jazz)
        pos_summary = checkbox_summary(visit.pos_zong, visit.pos_ufone, visit.pos_jazz)

        location = f"{visit.latitude}, {visit.longitude}" if visit.latitude and visit.longitude else '—'

        # Every field on the visit, as (label, value) pairs — two pairs per
        # table row. Keeping this as one flat list (rather than hand-built
        # rows) means a field can't quietly go missing again if the model
        # gains more fields later.
        pairs = [
            ('Date', str(visit.visit_date)),
            ('Logged By', visit.visited_by.email if visit.visited_by else '—'),
            ('ARM', franchise.arm_name if franchise else '—'),
            ('City', franchise.fr_city if franchise else '—'),
            ('Region', franchise.region if franchise else '—'),
            ('BU', franchise.bu if franchise else '—'),
            ('New/Existing', visit.get_new_or_existing_display()),
            ('Name', visit.name),
            ('EVC', visit.evc),
            ('Type', visit.get_visit_type_display()),
            ('BVS', visit.get_bvs_display()),
            ('BVS IMEI', visit.bvs_imei or '—'),
            ('RSO Visit', visit.get_rso_visit_display()),
            ('Location', location),
            ('Load Stock', visit.get_load_stock_range_display()),
            ('PSim Stock', str(visit.psim_stock)),
            ('NP Sim Stock', str(visit.npsim_stock)),
            ('MBB Stock', str(visit.mbb_stock)),
            ('Zong - Avg Loading', str(visit.zong_avg_loading)),
            ('Zong - Avg Sim Sales', str(visit.zong_avg_sim_sales)),
            ('Jazz - Avg Loading', str(visit.jazz_avg_loading)),
            ('Jazz - Avg Sim Sales', str(visit.jazz_avg_sim_sales)),
            ('Fascia', fascia_summary),
            ('AVH', avh_summary),
            ('POS', pos_summary),
            ('Promo Awareness', visit.get_promo_awareness_display()),
            ('Bundle Awareness', visit.get_bundle_awareness_display()),
            ('FCA Commitment', str(visit.fca_commitment) if visit.fca_commitment is not None else '—'),
            ('MNP Commitment', str(visit.mnp_commitment) if visit.mnp_commitment is not None else '—'),
        ]

        rows = []
        for i in range(0, len(pairs), 2):
            left = pairs[i]
            right = pairs[i + 1] if i + 1 < len(pairs) else ('', '')
            rows.append([left[0], left[1], right[0], right[1]])

        label_style = ParagraphStyle('label', parent=styles['Normal'], fontSize=8.5, fontName='Helvetica-Bold', textColor=colors.HexColor('#5C6E72'))
        value_style = ParagraphStyle('value', parent=styles['Normal'], fontSize=8.5)
        wrapped_rows = [
            [Paragraph(str(cell), label_style if col in (0, 2) else value_style) for col, cell in enumerate(row)]
            for row in rows
        ]

        table = Table(wrapped_rows, colWidths=[80, 145, 80, 145])
        table.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor('#DEE6E6')),
        ]))
        story.append(table)

        if visit.comments:
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<b>Comments:</b> {visit.comments}", styles['Normal']))

        if visit.management_comment:
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<b>Management Comment:</b> {visit.management_comment}", styles['Normal']))

        images = [img for img in (scaled_image(visit.photo), scaled_image(visit.photo2)) if img]
        if images:
            story.append(Spacer(1, 6))
            img_table = Table([images])
            story.append(img_table)

        story.append(Spacer(1, 16))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="market_visit_report.pdf"'
    return response


@report_access_required
def add_comment(request, pk):
    visit = get_object_or_404(MarketVisit, pk=pk)
    if request.method == 'POST':
        visit.management_comment = request.POST.get('management_comment', '').strip()
        visit.save(update_fields=['management_comment', 'updated_at'])
        messages.success(request, 'Comment saved.')
    return redirect('visit_detail', pk=visit.pk)