import pandas as pd
from django.shortcuts import render
from .forms import WorkbookUploadForm
from .models import UploadHistory
from .services import get_fiscal_year, save_invoices


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

                UploadHistory.objects.create(
                    uploaded_by=request.user if request.user.is_authenticated else None,
                    filename=workbook_file.name,
                    fiscal_year=fiscal_year,
                    status='success',
                    invoice_rows_processed=invoice_rows_saved,
                    mou_rows_processed=0,  # will fill in once MOU saving is built
                )

                result = {
                    'fiscal_year': fiscal_year,
                    'invoice_rows_saved': invoice_rows_saved,
                    'mou_rows_seen': len(mou_df),
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