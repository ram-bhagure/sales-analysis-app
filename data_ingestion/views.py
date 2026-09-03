import pandas as pd
from django.shortcuts import render
from .forms import WorkbookUploadForm


def upload_workbook(request):
    preview = None
    error = None

    if request.method == 'POST':
        form = WorkbookUploadForm(request.POST, request.FILES)
        if form.is_valid():
            workbook_file = request.FILES['workbook']
            try:
                invoice_df = pd.read_excel(workbook_file, sheet_name='Invoice')
                mou_df = pd.read_excel(workbook_file, sheet_name='MOU')

                preview = {
                    'invoice_columns': list(invoice_df.columns),
                    'invoice_row_count': len(invoice_df),
                    'invoice_head': invoice_df.head(5).to_html(),
                    'mou_columns': list(mou_df.columns),
                    'mou_row_count': len(mou_df),
                    'mou_head': mou_df.head(5).to_html(),
                }
            except Exception as e:
                error = str(e)
    else:
        form = WorkbookUploadForm()

    return render(request, 'data_ingestion/upload.html', {
        'form': form,
        'preview': preview,
        'error': error,
    })