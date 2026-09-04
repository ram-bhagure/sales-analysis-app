import pandas as pd
from django.db import transaction
from core.models import Party, Product, Subproduct, Executive, Invoice


def get_fiscal_year(d):
    """FY runs April to March. e.g. a date in Apr 2026 - Mar 2027 => '2026-2027'."""
    if d.month >= 4:
        return f"{d.year}-{d.year + 1}"
    return f"{d.year - 1}-{d.year}"


def save_invoices(invoice_df, fiscal_year):
    """
    Deletes all existing Invoice rows for the given fiscal_year, then inserts
    fresh rows parsed from invoice_df. Returns the number of rows saved.

    Expected invoice_df columns (already read from Excel, original headers):
    Date, Voucher No, Company, Party Name, Code, Product Code, Bundles,
    Basic, State, City, Executive
    """
    with transaction.atomic():
        Invoice.objects.filter(fiscal_year=fiscal_year).delete()

        rows_saved = 0
        for _, row in invoice_df.iterrows():
            date_val = pd.to_datetime(row['Date']).date()

            executive, _ = Executive.objects.get_or_create(name=str(row['Executive']).strip())

            party, _ = Party.objects.get_or_create(
                name=str(row['Party Name']).strip(),
                defaults={
                    'city': str(row['City']).strip(),
                    'state': str(row['State']).strip(),
                    'executive': executive,
                }
            )
            # keep party's executive/city/state in sync with latest upload
            party.city = str(row['City']).strip()
            party.state = str(row['State']).strip()
            party.executive = executive
            party.save()

            product, _ = Product.objects.get_or_create(name=str(row['Code']).strip())

            subproduct = None
            if pd.notna(row['Product Code']) and str(row['Product Code']).strip():
                subproduct, _ = Subproduct.objects.get_or_create(
                    product=product,
                    name=str(row['Product Code']).strip()
                )

            Invoice.objects.create(
                voucher_no=str(row['Voucher No']).strip(),
                date=date_val,
                month=date_val.month,
                fiscal_year=fiscal_year,
                warehouse=str(row['Company']).strip(),
                party=party,
                product=product,
                subproduct=subproduct,
                units=row['Bundles'],
                basic_amount=row['Basic'],
            )
            rows_saved += 1

        return rows_saved
    