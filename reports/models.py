from django.conf import settings
from django.db import models


class ViewerAccess(models.Model):
    """
    Marks a user as a report-only viewer: they can browse/filter visit
    records on the Reports dashboard, but (unless also is_staff) can't
    reach the field-agent pages (Log Visit, the main Dashboard, etc.) or
    the Hierarchy admin tools.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='viewer_access',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Viewer access for {self.user.email}"
