from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse

evc_validator = RegexValidator(
    regex=r'^92\d{10}$',
    message="Enter digits only, starting with 92 (12 digits total)."
)


class MarketVisit(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    TYPE_CHOICES = [
        ('retailer', 'Retailer'),
        ('dso', 'DSO'),
        ('stall', 'Stall'),
        ('wic', 'WIC'),
    ]

    YES_NO_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    NEW_EXISTING_CHOICES = [
        ('new', 'New'),
        ('existing', 'Existing'),
    ]

    LOAD_STOCK_CHOICES = [
        ('0-99', '0-99'),
        ('100-500', '100-500'),
        ('501-1000', '501-1000'),
        ('1001-5000', '1001-5000'),
        ('above_5000', 'Above 5000'),
    ]

    AWARENESS_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    visited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='market_visits',
    )

    # --- Franchise selection (top box, fetched from uploaded hierarchy) ---
    franchise = models.ForeignKey(
        'hierarchy.FranchiseRecord',
        on_delete=models.SET_NULL,
        null=True,
        related_name='visits',
        verbose_name='Franchise (FR ID)',
    )
    new_or_existing = models.CharField(
        max_length=10, choices=NEW_EXISTING_CHOICES, verbose_name="New or Existing"
    )
    visit_date = models.DateField(db_index=True)

    # --- Information section ---
    name = models.CharField(max_length=150, verbose_name="Name")
    evc = models.CharField(
        max_length=12,
        validators=[evc_validator],
        verbose_name="EVC",
        help_text="Digits only, starting with 92",
    )
    visit_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    bvs = models.CharField(max_length=3, choices=YES_NO_CHOICES, verbose_name="BVS")
    bvs_imei = models.CharField(max_length=50, verbose_name="BVS IMEI")
    rso_visit = models.CharField(max_length=3, choices=YES_NO_CHOICES, verbose_name="RSO Visit")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # --- Stock Information section ---
    load_stock_range = models.CharField(max_length=15, choices=LOAD_STOCK_CHOICES, verbose_name="Load Stock")
    psim_stock = models.PositiveIntegerField(default=0, verbose_name="PSim Stock")
    npsim_stock = models.PositiveIntegerField(default=0, verbose_name="NP Sim Stock")
    mbb_stock = models.PositiveIntegerField(default=0, verbose_name="MBB Stock")

    # --- Competition section ---
    zong_avg_loading = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Zong - Average Loading")
    zong_avg_sim_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Zong - Average Sim Sales")
    jazz_avg_loading = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Jazz - Average Loading")
    jazz_avg_sim_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Jazz - Average Sim Sales")

    # --- Visibility section ---
    fascia_zong = models.BooleanField(default=False, verbose_name="Zong")
    fascia_ufone = models.BooleanField(default=False, verbose_name="Ufone")
    fascia_jazz = models.BooleanField(default=False, verbose_name="Jazz")
    avh_zong = models.BooleanField(default=False, verbose_name="Zong")
    avh_ufone = models.BooleanField(default=False, verbose_name="Ufone")
    avh_jazz = models.BooleanField(default=False, verbose_name="Jazz")
    pos_zong = models.BooleanField(default=False, verbose_name="Zong")
    pos_ufone = models.BooleanField(default=False, verbose_name="Ufone")
    pos_jazz = models.BooleanField(default=False, verbose_name="Jazz")

    # --- Awareness section ---
    promo_awareness = models.CharField(max_length=10, choices=AWARENESS_CHOICES, verbose_name="Promo Awareness")
    bundle_awareness = models.CharField(max_length=10, choices=AWARENESS_CHOICES, verbose_name="Bundle Awareness")

    # --- Commitment section (optional) ---
    fca_commitment = models.PositiveIntegerField(null=True, blank=True, verbose_name="FCA Commitment")
    mnp_commitment = models.PositiveIntegerField(null=True, blank=True, verbose_name="MNP Commitment")

    # --- Comments (optional) ---
    comments = models.TextField(blank=True, verbose_name="Comments")

    # --- Set by management on the Reports/Management side, not by the field agent ---
    management_comment = models.TextField(blank=True, verbose_name="Management Comment")

    # --- Photos ---
    photo = models.ImageField(upload_to='visit_photos/', verbose_name="Photo 1")
    photo2 = models.ImageField(upload_to='visit_photos/', blank=True, null=True, verbose_name="Photo 2")

    # --- Internal workflow tracking (not shown on the log-visit form) ---
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open', db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-visit_date', '-created_at']

    def __str__(self):
        label = self.franchise.fr_id if self.franchise_id else self.name
        return f"{label} — {self.visit_date}"

    def get_absolute_url(self):
        return reverse('visit_detail', kwargs={'pk': self.pk})