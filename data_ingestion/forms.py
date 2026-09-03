from django import forms


class WorkbookUploadForm(forms.Form):
    workbook = forms.FileField(
        label='Monthly workbook (.xlsx)',
        help_text='Upload the single workbook containing both Invoice and MOU sheets.'
    )