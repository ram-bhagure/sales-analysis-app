from django.contrib import admin
from .models import UploadHistory


@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    list_display = ('filename', 'fiscal_year', 'status', 'uploaded_by', 'uploaded_at',
                     'invoice_rows_processed', 'mou_rows_processed', 'reconciliation_mismatches')
    list_filter = ('status', 'fiscal_year')
    readonly_fields = ('uploaded_at',)