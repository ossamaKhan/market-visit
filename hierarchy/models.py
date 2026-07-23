from django.conf import settings
from django.db import models


class FranchiseRecord(models.Model):
    """
    One row of the uploaded hierarchy Excel file.
    fr_id is treated as the unique key — re-uploading the sheet updates
    existing rows instead of duplicating them.
    """
    fr_id = models.CharField(max_length=50, unique=True, verbose_name="FR ID")
    region = models.CharField(max_length=100, blank=True, db_index=True)
    bu = models.CharField(max_length=100, blank=True, verbose_name="BU", db_index=True)
    fr_status = models.CharField(max_length=50, blank=True, verbose_name="FR Status")
    fr_city = models.CharField(max_length=100, blank=True, verbose_name="FR City", db_index=True)
    fr_address = models.CharField(max_length=255, blank=True, verbose_name="FR Address")
    arm_name = models.CharField(max_length=150, blank=True, verbose_name="ARM Name", db_index=True)
    arm_emp_no = models.CharField(max_length=50, blank=True, verbose_name="ARM Emp #")
    email = models.EmailField(db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='franchise_records',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['region', 'fr_id']

    def __str__(self):
        return f"{self.fr_id} — {self.arm_name}"


class UserCredential(models.Model):
    """
    Tracks the current plaintext password for accounts that were
    auto-provisioned from the hierarchy upload, so an admin can view or
    reset them. Django never stores passwords in plaintext on the User
    model itself (only a salted hash) — this table is a deliberate,
    separate record kept solely so admins can hand out / look up current
    login credentials for ARMs.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='credential',
    )
    plain_password = models.CharField(max_length=128)
    must_change_password = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Credential for {self.user.username}"
