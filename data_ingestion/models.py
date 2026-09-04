from django.db import models
from django.contrib.auth.models import User


class UploadHistory(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial', 'Partial - completed with issues'),
        ('failed', 'Failed'),
    ]

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    fiscal_year = models.CharField(max_length=9)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    invoice_rows_processed = models.PositiveIntegerField(default=0)
    mou_rows_processed = models.PositiveIntegerField(default=0)
    reconciliation_mismatches = models.PositiveIntegerField(default=0)

    error_message = models.TextField(blank=True)
    notes = models.TextField(blank=True)  # e.g. list of mismatches, skipped rows

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.filename} - {self.uploaded_at:%Y-%m-%d %H:%M} ({self.status})"