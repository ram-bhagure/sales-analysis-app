from datetime import date
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.permissions import get_accessible_parties
from data_ingestion.services import get_fiscal_year
from core.models import MOU, Invoice, Party

MONTH_SUFFIXES = ['apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar']
MONTH_LABELS = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
MONTH_NUMBERS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]


@login_required
def all_india_target(request):
    """Stream 1 (Target Review) - All-India opening screen.
    Only considers parties that have an MOU (target) record.
    Optional ?month=<1-12> query param scopes tiles/state-tiles to that month only."""
    fiscal_year = get_fiscal_year(date.today())
    accessible_parties = get_accessible_parties(request.user)

    selected_month = request.GET.get('month')
    selected_month = int(selected_month) if selected_month else None
    selected_month_label = MONTH_LABELS[MONTH_NUMBERS.index(selected_month)] if selected_month else None

    # Stream 1 scope: only targeted parties
    targeted_parties = accessible_parties.filter(mou__fiscal_year=fiscal_year)
    mous = MOU.objects.filter(party__in=targeted_parties, fiscal_year=fiscal_year)

    def target_total(parties_qs):
        if selected_month:
            suffix = MONTH_SUFFIXES[MONTH_NUMBERS.index(selected_month)]
            return MOU.objects.filter(
                party__in=parties_qs, fiscal_year=fiscal_year
            ).aggregate(total=Sum(f'target_{suffix}'))['total'] or 0
        return MOU.objects.filter(
            party__in=parties_qs, fiscal_year=fiscal_year
        ).aggregate(total=Sum('annual_target'))['total'] or 0

    def achievement_total(parties_qs):
        invoices = Invoice.objects.filter(party__in=parties_qs, fiscal_year=fiscal_year)
        if selected_month:
            invoices = invoices.filter(month=selected_month)
        return invoices.aggregate(total=Sum('basic_amount'))['total'] or 0

    total_target = target_total(targeted_parties)
    total_achievement = achievement_total(targeted_parties)
    percent_achieved = round((total_achievement / total_target) * 100, 1) if total_target else 0

    # Monthly trend (always shows the full year, regardless of selected_month)
    monthly_target = []
    monthly_achievement = []
    for suffix, month_num in zip(MONTH_SUFFIXES, MONTH_NUMBERS):
        target_sum = mous.aggregate(total=Sum(f'target_{suffix}'))['total'] or 0
        monthly_target.append(float(target_sum))
        invoice_sum = Invoice.objects.filter(
            party__in=targeted_parties, fiscal_year=fiscal_year, month=month_num
        ).aggregate(total=Sum('basic_amount'))['total'] or 0
        monthly_achievement.append(float(invoice_sum))

    # State-wise tiles (respect selected_month if set)
    states = targeted_parties.values_list('state', flat=True).distinct()
    state_tiles = []
    for state_name in states:
        state_parties = targeted_parties.filter(state=state_name)
        state_target = target_total(state_parties)
        state_achievement = achievement_total(state_parties)
        state_percent = round((state_achievement / state_target) * 100, 1) if state_target else 0
        state_tiles.append({'name': state_name, 'percent': state_percent, 'achievement': float(state_achievement)})

    # Product mix (respects selected_month)
    product_invoices = Invoice.objects.filter(party__in=targeted_parties, fiscal_year=fiscal_year)
    if selected_month:
        product_invoices = product_invoices.filter(month=selected_month)
    product_totals = (
        product_invoices.values('product__name')
        .annotate(total=Sum('basic_amount'))
        .order_by('-total')
    )
    product_labels = [row['product__name'] for row in product_totals]
    product_values = [float(row['total']) for row in product_totals]

    context = {
        'fiscal_year': fiscal_year,
        'total_target': total_target,
        'total_achievement': total_achievement,
        'percent_achieved': percent_achieved,
        'month_labels': MONTH_LABELS,
        'monthly_target': monthly_target,
        'monthly_achievement': monthly_achievement,
        'state_tiles': state_tiles,
        'selected_month': selected_month,
        'selected_month_label': selected_month_label,
        'month_numbers': MONTH_NUMBERS,
        'product_labels': product_labels,
        'product_values': product_values,
    }
    return render(request, 'meeting_mode/all_india_target.html', context)


@login_required
def state_target(request, state_name):
    """Stream 1 (Target Review) - State-level page. Shows executive tiles
    for this state, plus the same header tiles / trend / product mix pattern."""
    fiscal_year = get_fiscal_year(date.today())
    accessible_parties = get_accessible_parties(request.user)

    targeted_parties = accessible_parties.filter(mou__fiscal_year=fiscal_year, state=state_name)
    mous = MOU.objects.filter(party__in=targeted_parties, fiscal_year=fiscal_year)

    selected_month = request.GET.get('month')
    selected_month = int(selected_month) if selected_month else None
    selected_month_label = MONTH_LABELS[MONTH_NUMBERS.index(selected_month)] if selected_month else None

    def target_total(parties_qs):
        if selected_month:
            suffix = MONTH_SUFFIXES[MONTH_NUMBERS.index(selected_month)]
            return MOU.objects.filter(
                party__in=parties_qs, fiscal_year=fiscal_year
            ).aggregate(total=Sum(f'target_{suffix}'))['total'] or 0
        return MOU.objects.filter(
            party__in=parties_qs, fiscal_year=fiscal_year
        ).aggregate(total=Sum('annual_target'))['total'] or 0

    def achievement_total(parties_qs):
        invoices = Invoice.objects.filter(party__in=parties_qs, fiscal_year=fiscal_year)
        if selected_month:
            invoices = invoices.filter(month=selected_month)
        return invoices.aggregate(total=Sum('basic_amount'))['total'] or 0

    total_target = target_total(targeted_parties)
    total_achievement = achievement_total(targeted_parties)
    percent_achieved = round((total_achievement / total_target) * 100, 1) if total_target else 0

    monthly_target = []
    monthly_achievement = []
    for suffix, month_num in zip(MONTH_SUFFIXES, MONTH_NUMBERS):
        target_sum = mous.aggregate(total=Sum(f'target_{suffix}'))['total'] or 0
        monthly_target.append(float(target_sum))
        invoice_sum = Invoice.objects.filter(
            party__in=targeted_parties, fiscal_year=fiscal_year, month=month_num
        ).aggregate(total=Sum('basic_amount'))['total'] or 0
        monthly_achievement.append(float(invoice_sum))

    # Executive tiles for this state
    executives = targeted_parties.values_list('executive__name', flat=True).distinct()
    executive_tiles = []
    for exec_name in executives:
        exec_parties = targeted_parties.filter(executive__name=exec_name)
        exec_target = target_total(exec_parties)
        exec_achievement = achievement_total(exec_parties)
        exec_percent = round((exec_achievement / exec_target) * 100, 1) if exec_target else 0
        executive_tiles.append({'name': exec_name, 'percent': exec_percent})

    # Product mix
    product_invoices = Invoice.objects.filter(party__in=targeted_parties, fiscal_year=fiscal_year)
    if selected_month:
        product_invoices = product_invoices.filter(month=selected_month)
    product_totals = (
        product_invoices.values('product__name').annotate(total=Sum('basic_amount')).order_by('-total')
    )
    product_labels = [row['product__name'] for row in product_totals]
    product_values = [float(row['total']) for row in product_totals]

    context = {
        'state_name': state_name,
        'fiscal_year': fiscal_year,
        'total_target': total_target,
        'total_achievement': total_achievement,
        'percent_achieved': percent_achieved,
        'month_labels': MONTH_LABELS,
        'monthly_target': monthly_target,
        'monthly_achievement': monthly_achievement,
        'month_numbers': MONTH_NUMBERS,
        'selected_month': selected_month,
        'selected_month_label': selected_month_label,
        'executive_tiles': executive_tiles,
        'product_labels': product_labels,
        'product_values': product_values,
    }
    return render(request, 'meeting_mode/state_target.html', context)


@login_required
def executive_target(request, executive_name):
    """Stream 1 (Target Review) - Executive-level page. Shows a parties bar
    chart sorted by % achieved, plus a detail table."""
    fiscal_year = get_fiscal_year(date.today())
    accessible_parties = get_accessible_parties(request.user)

    targeted_parties = accessible_parties.filter(
        mou__fiscal_year=fiscal_year, executive__name=executive_name
    )
    mous = MOU.objects.filter(party__in=targeted_parties, fiscal_year=fiscal_year)

    selected_month = request.GET.get('month')
    selected_month = int(selected_month) if selected_month else None
    selected_month_label = MONTH_LABELS[MONTH_NUMBERS.index(selected_month)] if selected_month else None

    def target_total(parties_qs):
        if selected_month:
            suffix = MONTH_SUFFIXES[MONTH_NUMBERS.index(selected_month)]
            return MOU.objects.filter(
                party__in=parties_qs, fiscal_year=fiscal_year
            ).aggregate(total=Sum(f'target_{suffix}'))['total'] or 0
        return MOU.objects.filter(
            party__in=parties_qs, fiscal_year=fiscal_year
        ).aggregate(total=Sum('annual_target'))['total'] or 0

    def achievement_total(parties_qs):
        invoices = Invoice.objects.filter(party__in=parties_qs, fiscal_year=fiscal_year)
        if selected_month:
            invoices = invoices.filter(month=selected_month)
        return invoices.aggregate(total=Sum('basic_amount'))['total'] or 0

    total_target = target_total(targeted_parties)
    total_achievement = achievement_total(targeted_parties)
    percent_achieved = round((total_achievement / total_target) * 100, 1) if total_target else 0

    monthly_target = []
    monthly_achievement = []
    for suffix, month_num in zip(MONTH_SUFFIXES, MONTH_NUMBERS):
        target_sum = mous.aggregate(total=Sum(f'target_{suffix}'))['total'] or 0
        monthly_target.append(float(target_sum))
        invoice_sum = Invoice.objects.filter(
            party__in=targeted_parties, fiscal_year=fiscal_year, month=month_num
        ).aggregate(total=Sum('basic_amount'))['total'] or 0
        monthly_achievement.append(float(invoice_sum))

    # Product mix
    product_invoices = Invoice.objects.filter(party__in=targeted_parties, fiscal_year=fiscal_year)
    if selected_month:
        product_invoices = product_invoices.filter(month=selected_month)
    product_totals = (
        product_invoices.values('product__name').annotate(total=Sum('basic_amount')).order_by('-total')
    )
    product_labels = [row['product__name'] for row in product_totals]
    product_values = [float(row['total']) for row in product_totals]

    # Parties: target, achievement, percent - sorted by percent descending
    party_rows = []
    for party in targeted_parties:
        p_target = target_total(Party.objects.filter(pk=party.pk))
        p_achievement = achievement_total(Party.objects.filter(pk=party.pk))
        p_percent = round((p_achievement / p_target) * 100, 1) if p_target else 0
        party_rows.append({
            'name': party.name,
            'city': party.city,
            'target': float(p_target),
            'achievement': float(p_achievement),
            'percent': p_percent,
        })
    party_rows.sort(key=lambda r: r['percent'], reverse=True)

    context = {
        'executive_name': executive_name,
        'fiscal_year': fiscal_year,
        'total_target': total_target,
        'total_achievement': total_achievement,
        'percent_achieved': percent_achieved,
        'month_labels': MONTH_LABELS,
        'monthly_target': monthly_target,
        'monthly_achievement': monthly_achievement,
        'month_numbers': MONTH_NUMBERS,
        'selected_month': selected_month,
        'selected_month_label': selected_month_label,
        'product_labels': product_labels,
        'product_values': product_values,
        'party_rows': party_rows,
        'party_names': [r['name'] for r in party_rows],
        'party_achievements': [r['achievement'] for r in party_rows],
        'party_targets': [r['target'] for r in party_rows],
    }
    return render(request, 'meeting_mode/executive_target.html', context)