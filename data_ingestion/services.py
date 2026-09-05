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


# Maps our model's month-suffix to the MOU sheet's actual month label
MONTH_COLUMN_MAP = {
    'apr': 'Apr', 'may': 'May', 'jun': 'June', 'jul': 'Jul',
    'aug': 'Aug', 'sep': 'Sep', 'oct': 'Oct', 'nov': 'Nov',
    'dec': 'Dec', 'jan': 'Jan', 'feb': 'Feb', 'mar': 'Mar',
}


def save_mou(mou_df, fiscal_year):
    """
    Deletes all existing MOU rows for the given fiscal_year, then inserts
    fresh rows parsed from mou_df. Returns (rows_saved, mismatch_notes list).

    Also validates that each month's Target column equals Annual Target / 12
    (within a small rounding tolerance), logging any exceptions found.

    Parties that have a target but no invoices this year won't already exist
    from save_invoices(), so they are created here using the MOU sheet's own
    Party Name, City, and Executive columns.
    """
    from core.models import MOU, Party, Executive

    mismatch_notes = []

    with transaction.atomic():
        MOU.objects.filter(fiscal_year=fiscal_year).delete()

        rows_saved = 0
        for _, row in mou_df.iterrows():
            party_name = str(row['Party Name']).strip()

            party, created = Party.objects.get_or_create(
                name=party_name,
                defaults={
                    'city': str(row.get('City', '')).strip(),
                    'state': str(row.get('State', '')).strip(),
                }
            )
            if created:
                # party had a target but no invoices - fill in executive from the MOU sheet itself
                exec_name = str(row.get('Executive', '')).strip()
                if exec_name:
                    executive, _ = Executive.objects.get_or_create(name=exec_name)
                    party.executive = executive
                party.save()
                mismatch_notes.append(
                    f"{party_name}: has a target but no invoices this year - party created from MOU sheet."
                )

            annual_target = row['Year Target']
            monthly_expected = round(annual_target / 12, 2) if annual_target else 0

            field_values = {'party': party, 'fiscal_year': fiscal_year, 'annual_target': annual_target}
            for suffix, label in MONTH_COLUMN_MAP.items():
                target_val = row.get(f'{label} Target', 0) or 0
                value_val = row.get(f'{label} Value', 0) or 0
                field_values[f'target_{suffix}'] = target_val
                field_values[f'achievement_{suffix}'] = value_val

                # validation: does this month's target match annual/12?
                if annual_target and abs(target_val - monthly_expected) > 1:
                    mismatch_notes.append(
                        f"{party_name}: {label} target ({target_val}) does not equal "
                        f"Annual Target/12 ({monthly_expected})."
                    )

            MOU.objects.create(**field_values)
            rows_saved += 1

        return rows_saved, mismatch_notes


def reconcile(fiscal_year, tolerance=1):
    """
    Compares Invoice.basic_amount summed by Party+Month against MOU's
    monthly achievement figure for that party, for the given fiscal_year.
    Returns a list of mismatch note strings (empty list = fully reconciled).
    """
    from django.db.models import Sum
    from core.models import MOU, Invoice

    notes = []
    month_num_to_suffix = {
        4: 'apr', 5: 'may', 6: 'jun', 7: 'jul', 8: 'aug', 9: 'sep',
        10: 'oct', 11: 'nov', 12: 'dec', 1: 'jan', 2: 'feb', 3: 'mar',
    }

    mous = MOU.objects.filter(fiscal_year=fiscal_year).select_related('party')

    for mou in mous:
        for month_num, suffix in month_num_to_suffix.items():
            invoice_sum = Invoice.objects.filter(
                party=mou.party, fiscal_year=fiscal_year, month=month_num
            ).aggregate(total=Sum('basic_amount'))['total'] or 0

            mou_achievement = getattr(mou, f'achievement_{suffix}') or 0

            if abs(invoice_sum - mou_achievement) > tolerance:
                notes.append(
                    f"{mou.party.name} - month {month_num}: Invoice sum ({invoice_sum}) "
                    f"vs MOU achievement ({mou_achievement}) - mismatch of {invoice_sum - mou_achievement}."
                )

    return notes
