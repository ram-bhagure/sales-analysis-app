from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from core.models import Party, MOU, Invoice

MONTH_SUFFIXES = ['apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar']
MONTH_LABELS = ['April', 'May', 'June', 'July', 'August', 'September',
                'October', 'November', 'December', 'January', 'February', 'March']
QUARTERS = [
    ('Q1', ['apr', 'may', 'jun']),
    ('Q2', ['jul', 'aug', 'sep']),
    ('Q3', ['oct', 'nov', 'dec']),
    ('Q4', ['jan', 'feb', 'mar']),
]


@login_required
def party_report(request, party_name, fiscal_year):
    party = get_object_or_404(Party, name=party_name)
    mou = get_object_or_404(MOU, party=party, fiscal_year=fiscal_year)

    monthly_data = []
    for suffix, label in zip(MONTH_SUFFIXES, MONTH_LABELS):
        target = getattr(mou, f'target_{suffix}') or 0
        sales = getattr(mou, f'achievement_{suffix}') or 0
        pct = round((sales / target) * 100, 1) if target else 0
        monthly_data.append({'suffix': suffix, 'label': label, 'target': target, 'sales': sales, 'pct': pct})

    quarterly_data = []
    for q_label, suffixes in QUARTERS:
        q_target = sum(m['target'] for m in monthly_data if m['suffix'] in suffixes)
        q_sales = sum(m['sales'] for m in monthly_data if m['suffix'] in suffixes)
        q_pct = round((q_sales / q_target) * 100, 1) if q_target else 0
        quarterly_data.append({'label': q_label, 'target': q_target, 'sales': q_sales, 'pct': q_pct})

    annual_target = mou.annual_target
    annual_sales = sum(m['sales'] for m in monthly_data)
    annual_pct = round((annual_sales / annual_target) * 100, 1) if annual_target else 0

    # Months with actual sales recorded so far
    active_months = [m for m in monthly_data if m['sales']]
    elapsed_count = len(active_months)

    performance_pct = (
        round(sum(m['pct'] for m in active_months) / elapsed_count, 2) if elapsed_count else 0
    )

    monthly_target_flat = float(monthly_target := (annual_target / 12 if annual_target else 0))
    prorated_target = monthly_target_flat * elapsed_count
    target_diff = float(annual_sales) - prorated_target
    target_status = f"Ahead by {abs(target_diff):,.0f}" if target_diff >= 0 else f"Behind by {abs(target_diff):,.0f}"

    avg_monthly_sale = round(float(annual_sales) / elapsed_count, 0) if elapsed_count else 0

    highest_month = max(active_months, key=lambda m: m['sales'])['label'] if active_months else '-'
    lowest_month = min(active_months, key=lambda m: m['sales'])['label'] if active_months else '-'

    # Page 2: product-wise breakdown, full-year totals for this party
    product_rows = (
        Invoice.objects.filter(party=party, fiscal_year=fiscal_year)
        .values('product__name', 'subproduct__name')
        .annotate(total_units=Sum('units'), total_value=Sum('basic_amount'))
        .order_by('-total_value')
    )
    product_table = []
    for row in product_rows:
        pct_of_total = round((float(row['total_value']) / float(annual_sales)) * 100, 1) if annual_sales else 0
        product_table.append({
            'product': row['product__name'],
            'subproduct': row['subproduct__name'] or '-',
            'units': row['total_units'],
            'value': row['total_value'],
            'pct': pct_of_total,
        })

    # Aggregate by product only, for the donut chart and top-contributor line
    product_summary = (
        Invoice.objects.filter(party=party, fiscal_year=fiscal_year)
        .values('product__name')
        .annotate(total=Sum('basic_amount'))
        .order_by('-total')
    )
    product_chart_labels = [row['product__name'] for row in product_summary]
    product_chart_values = [float(row['total']) for row in product_summary]
    # Bar chart: cap to top 10 products to keep it readable; donut/table keep full data
    product_bar_labels = product_chart_labels[:10]
    product_bar_values = product_chart_values[:10]
    top_product = product_summary[0]['product__name'] if product_summary else None
    top_product_value = float(product_summary[0]['total']) if product_summary else 0
    top_product_pct = round((top_product_value / float(annual_sales)) * 100, 1) if annual_sales else 0

    context = {
        'party': party,
        'fiscal_year': fiscal_year,
        'monthly_data': monthly_data,
        'quarterly_data': quarterly_data,
        'annual_target': annual_target,
        'annual_sales': annual_sales,
        'annual_pct': annual_pct,
        'performance_pct': performance_pct,
        'target_status': target_status,
        'avg_monthly_sale': avg_monthly_sale,
        'highest_month': highest_month,
        'lowest_month': lowest_month,
        'month_labels_short': [m['label'][:3] for m in monthly_data],
        'monthly_targets': [float(m['target']) for m in monthly_data],
        'monthly_sales': [float(m['sales']) for m in monthly_data],
        'quarter_labels': [q['label'] for q in quarterly_data],
        'quarter_targets': [float(q['target']) for q in quarterly_data],
        'quarter_sales': [float(q['sales']) for q in quarterly_data],
        'product_table': product_table,
        'product_chart_labels': product_chart_labels,
        'product_chart_values': product_chart_values,
        'product_bar_labels': product_bar_labels,
        'product_bar_values': product_bar_values,
        'top_product': top_product,
        'top_product_pct': top_product_pct,
    }
    return render(request, 'reports/party_report.html', context)
