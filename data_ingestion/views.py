import pandas as pd
from django.shortcuts import render
from .forms import WorkbookUploadForm
from .models import UploadHistory
from .services import get_fiscal_year, save_invoices, save_mou, reconcile


def upload_workbook(request):
    result = None
    error = None

    if request.method == 'POST':
        form = WorkbookUploadForm(request.POST, request.FILES)
        if form.is_valid():
            workbook_file = request.FILES['workbook']
            try:
                invoice_df = pd.read_excel(workbook_file, sheet_name='Invoice')
                mou_df = pd.read_excel(workbook_file, sheet_name='MOU')

                first_date = pd.to_datetime(invoice_df['Date'].iloc[0]).date()
                fiscal_year = get_fiscal_year(first_date)

                invoice_rows_saved = save_invoices(invoice_df, fiscal_year)
                mou_rows_saved, mismatch_notes = save_mou(mou_df, fiscal_year)
                reconciliation_notes = reconcile(fiscal_year)
                mismatch_notes = mismatch_notes + reconciliation_notes

                status = 'partial' if mismatch_notes else 'success'

                UploadHistory.objects.create(
                    uploaded_by=request.user if request.user.is_authenticated else None,
                    filename=workbook_file.name,
                    fiscal_year=fiscal_year,
                    status=status,
                    invoice_rows_processed=invoice_rows_saved,
                    mou_rows_processed=mou_rows_saved,
                    reconciliation_mismatches=len(mismatch_notes),
                    notes='\n'.join(mismatch_notes),
                )

                result = {
                    'fiscal_year': fiscal_year,
                    'invoice_rows_saved': invoice_rows_saved,
                    'mou_rows_saved': mou_rows_saved,
                    'mismatch_notes': mismatch_notes,
                }
            except Exception as e:
                error = str(e)
                UploadHistory.objects.create(
                    uploaded_by=request.user if request.user.is_authenticated else None,
                    filename=workbook_file.name,
                    fiscal_year='',
                    status='failed',
                    error_message=str(e),
                )
    else:
        form = WorkbookUploadForm()

    return render(request, 'data_ingestion/upload.html', {
        'form': form,
        'result': result,
        'error': error,
    })
