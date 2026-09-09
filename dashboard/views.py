from datetime import date
from django.db.models import Sum
from django.shortcuts import render
from accounts.permissions import role_required, get_accessible_parties
from data_ingestion.services import get_fiscal_year
from core.models import MOU, Invoice

MONTH_SUFFIXES = ['apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar']
MONTH_LABELS = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
MONTH_NUMBERS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]


@role_required('admin', 'sales_head')
def management_dashboard(request):
    fiscal_year = get_fiscal_year(date.today())
    parties = get_accessible_parties(request.user)

    mous = MOU.objects.filter(party__in=parties, fiscal_year=fiscal_year)

    total_target = mous.aggregate(total=Sum('annual_target'))['total'] or 0

    total_achievement = Invoice.objects.filter(
        party__in=parties, fiscal_year=fiscal_year
    ).aggregate(total=Sum('basic_amount'))['total'] or 0

    total_units = Invoice.objects.filter(
        party__in=parties, fiscal_year=fiscal_year
    ).aggregate(total=Sum('units'))['total'] or 0

    percent_achieved = round((total_achievement / total_target) * 100, 1) if total_target else 0

    # Monthly trend: sum target_<month> across all MOUs, and actual invoice sum per month
    monthly_target = []
    monthly_achievement = []
    for suffix, month_num in zip(MONTH_SUFFIXES, MONTH_NUMBERS):
        target_sum = mous.aggregate(total=Sum(f'target_{suffix}'))['total'] or 0
        monthly_target.append(float(target_sum))

        invoice_sum = Invoice.objects.filter(
            party__in=parties, fiscal_year=fiscal_year, month=month_num
        ).aggregate(total=Sum('basic_amount'))['total'] or 0
        monthly_achievement.append(float(invoice_sum))

    # Monthly units (parallel to monthly_achievement, for tooltips)
    monthly_units = []
    for month_num in MONTH_NUMBERS:
        u = Invoice.objects.filter(
            party__in=parties, fiscal_year=fiscal_year, month=month_num
        ).aggregate(total=Sum('units'))['total'] or 0
        monthly_units.append(float(u))

    # Product mix: sum basic_amount grouped by product name
    product_totals = (
        Invoice.objects.filter(party__in=parties, fiscal_year=fiscal_year)
        .values('product__name')
        .annotate(total=Sum('basic_amount'), total_units=Sum('units'))
        .order_by('-total')
    )
    product_labels = [row['product__name'] for row in product_totals]
    product_values = [float(row['total']) for row in product_totals]
    product_units = [float(row['total_units'] or 0) for row in product_totals]

    context = {
        'fiscal_year': fiscal_year,
        'total_target': total_target,
        'total_achievement': total_achievement,
        'total_units': total_units,
        'percent_achieved': percent_achieved,
        'month_labels': MONTH_LABELS,
        'monthly_target': monthly_target,
        'monthly_achievement': monthly_achievement,
        'monthly_units': monthly_units,
        'product_labels': product_labels,
        'product_values': product_values,
        'product_units': product_units,
    }
    return render(request, 'dashboard/management.html', context)