from django.db.models import Sum
from core.models import MOU, Invoice

MONTH_SUFFIXES = ['apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar']
MONTH_LABELS = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
MONTH_NUMBERS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]


def parse_selected_month(request):
    """Reads ?month=<1-12> from the request. Returns (month_number_or_None, label_or_None)."""
    raw = request.GET.get('month')
    if not raw:
        return None, None
    month_num = int(raw)
    label = MONTH_LABELS[MONTH_NUMBERS.index(month_num)]
    return month_num, label


def target_total(parties_qs, fiscal_year, selected_month=None):
    """Sums MOU target for the given parties - either the full annual_target,
    or a single month's target_<suffix> if selected_month is given."""
    if selected_month:
        suffix = MONTH_SUFFIXES[MONTH_NUMBERS.index(selected_month)]
        return MOU.objects.filter(
            party__in=parties_qs, fiscal_year=fiscal_year
        ).aggregate(total=Sum(f'target_{suffix}'))['total'] or 0
    return MOU.objects.filter(
        party__in=parties_qs, fiscal_year=fiscal_year
    ).aggregate(total=Sum('annual_target'))['total'] or 0


def achievement_total(parties_qs, fiscal_year, selected_month=None):
    """Sums Invoice.basic_amount for the given parties, optionally scoped to one month."""
    invoices = Invoice.objects.filter(party__in=parties_qs, fiscal_year=fiscal_year)
    if selected_month:
        invoices = invoices.filter(month=selected_month)
    return invoices.aggregate(total=Sum('basic_amount'))['total'] or 0


def units_total(parties_qs, fiscal_year, selected_month=None):
    """Sums Invoice.units for the given parties, optionally scoped to one month."""
    invoices = Invoice.objects.filter(party__in=parties_qs, fiscal_year=fiscal_year)
    if selected_month:
        invoices = invoices.filter(month=selected_month)
    return invoices.aggregate(total=Sum('units'))['total'] or 0


def monthly_units_trend(parties_qs, fiscal_year):
    """Returns a 12-value list of units sold per month (for tooltips alongside monthly_trend)."""
    units = []
    for month_num in MONTH_NUMBERS:
        total = Invoice.objects.filter(
            party__in=parties_qs, fiscal_year=fiscal_year, month=month_num
        ).aggregate(total=Sum('units'))['total'] or 0
        units.append(float(total))
    return units


def percent_achieved(target, achievement):
    return round((achievement / target) * 100, 1) if target else 0


def monthly_trend(parties_qs, fiscal_year):
    """Returns (monthly_target_list, monthly_achievement_list) across all 12 months,
    always full-year regardless of any month filter - used to draw the trend chart itself."""
    mous = MOU.objects.filter(party__in=parties_qs, fiscal_year=fiscal_year)
    targets, achievements = [], []
    for suffix, month_num in zip(MONTH_SUFFIXES, MONTH_NUMBERS):
        targets.append(float(mous.aggregate(total=Sum(f'target_{suffix}'))['total'] or 0))
        invoice_sum = Invoice.objects.filter(
            party__in=parties_qs, fiscal_year=fiscal_year, month=month_num
        ).aggregate(total=Sum('basic_amount'))['total'] or 0
        achievements.append(float(invoice_sum))
    return targets, achievements


def product_mix(parties_qs, fiscal_year, selected_month=None, limit=None):
    """Returns (labels, values, units) of Invoice data grouped by product name,
    sorted descending by value, optionally scoped to one month and/or capped to top N."""
    invoices = Invoice.objects.filter(party__in=parties_qs, fiscal_year=fiscal_year)
    if selected_month:
        invoices = invoices.filter(month=selected_month)
    rows = invoices.values('product__name').annotate(
        total=Sum('basic_amount'), total_units=Sum('units')
    ).order_by('-total')
    if limit:
        rows = rows[:limit]
    labels = [row['product__name'] for row in rows]
    values = [float(row['total']) for row in rows]
    units = [float(row['total_units'] or 0) for row in rows]
    return labels, values, units


PRODUCT_TREND_COLORS = ['#2a78d6', '#e8a05a', '#5aa36e', '#c65b5b', '#8a5ac6', '#5aa3e8']


def product_monthly_trend(parties_qs, fiscal_year, top_n=5):
    """Returns a list of {name, data, units, color} for the top_n products by total
    annual sales, each with a 12-month sales AND units trend - for a multi-line chart."""
    top_products = (
        Invoice.objects.filter(party__in=parties_qs, fiscal_year=fiscal_year)
        .values('product__name')
        .annotate(total=Sum('basic_amount'))
        .order_by('-total')[:top_n]
    )
    product_names = [row['product__name'] for row in top_products]

    series = []
    for i, name in enumerate(product_names):
        monthly_values, monthly_units = [], []
        for month_num in MONTH_NUMBERS:
            row = Invoice.objects.filter(
                party__in=parties_qs, fiscal_year=fiscal_year, product__name=name, month=month_num
            ).aggregate(total=Sum('basic_amount'), total_units=Sum('units'))
            monthly_values.append(float(row['total'] or 0))
            monthly_units.append(float(row['total_units'] or 0))
        series.append({
            'name': name,
            'data': monthly_values,
            'units': monthly_units,
            'color': PRODUCT_TREND_COLORS[i % len(PRODUCT_TREND_COLORS)],
        })
    return series