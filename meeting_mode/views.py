from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.permissions import get_accessible_parties
from data_ingestion.services import get_fiscal_year
from core.models import MOU, Party
from .services import (
    MONTH_LABELS, MONTH_NUMBERS, parse_selected_month,
    target_total, achievement_total, units_total, percent_achieved,
    monthly_trend, monthly_units_trend, product_mix, product_monthly_trend,
    product_total, product_units_total, single_product_monthly_trend, subproduct_mix,
    product_breakdown_by_level, subproduct_monthly_trend
)


@login_required
def all_india_target(request):
    fiscal_year = get_fiscal_year(date.today())
    accessible_parties = get_accessible_parties(request.user)
    targeted_parties = accessible_parties.filter(mou__fiscal_year=fiscal_year)

    selected_month, selected_month_label = parse_selected_month(request)
    selected_product = request.GET.get('product') or None

    total_target = target_total(targeted_parties, fiscal_year, selected_month)
    total_achievement = achievement_total(targeted_parties, fiscal_year, selected_month, selected_product)
    total_units = units_total(targeted_parties, fiscal_year, selected_month, selected_product)
    monthly_target, monthly_achievement = monthly_trend(targeted_parties, fiscal_year)
    monthly_units = monthly_units_trend(targeted_parties, fiscal_year)
    product_labels, product_values, product_units = product_mix(targeted_parties, fiscal_year, selected_month)
    product_series = product_monthly_trend(targeted_parties, fiscal_year)

    states = targeted_parties.values_list('state', flat=True).distinct()
    state_tiles = []
    for state_name in states:
        state_parties = targeted_parties.filter(state=state_name)
        s_target = target_total(state_parties, fiscal_year, selected_month)
        s_achievement = achievement_total(state_parties, fiscal_year, selected_month, selected_product)
        s_units = units_total(state_parties, fiscal_year, selected_month, selected_product)
        state_tiles.append({
            'name': state_name,
            'percent': percent_achieved(s_target, s_achievement),
            'achievement': float(s_achievement),
            'units': float(s_units),
        })
    state_tiles.sort(key=lambda t: t['achievement'], reverse=True)

    total_for_contribution = sum (t['achievement'] for t in state_tiles)
    for t in state_tiles:
        t['contribution_pct'] = round((t['achievement'] / total_for_contribution)*100,) if total_for_contribution else 0

    context = {
        'fiscal_year': fiscal_year,
        'total_target': total_target,
        'total_achievement': total_achievement,
        'total_units': total_units,
        'percent_achieved': percent_achieved(total_target, total_achievement),
        'month_labels': MONTH_LABELS,
        'monthly_target': monthly_target,
        'monthly_achievement': monthly_achievement,
        'monthly_units': monthly_units,
        'month_numbers': MONTH_NUMBERS,
        'selected_month': selected_month,
        'selected_month_label': selected_month_label,
        'selected_product': selected_product,
        'state_tiles': state_tiles,
        'state_names': [t['name'] for t in state_tiles],
        'state_achievements': [t['achievement'] for t in state_tiles],
        'state_units': [t['units'] for t in state_tiles],
        'product_labels': product_labels,
        'product_values': product_values,
        'product_units': product_units,
        'product_series': product_series,
    }
    return render(request, 'meeting_mode/all_india_target.html', context)

@login_required
def state_target(request, state_name):
    """Stream 1 (Target Review) - State-level page."""
    fiscal_year = get_fiscal_year(date.today())
    accessible_parties = get_accessible_parties(request.user)
    targeted_parties = accessible_parties.filter(mou__fiscal_year=fiscal_year, state=state_name)

    selected_month, selected_month_label = parse_selected_month(request)

    total_target = target_total(targeted_parties, fiscal_year, selected_month)
    total_achievement = achievement_total(targeted_parties, fiscal_year, selected_month)
    total_units = units_total(targeted_parties, fiscal_year, selected_month)
    monthly_target, monthly_achievement = monthly_trend(targeted_parties, fiscal_year)
    monthly_units = monthly_units_trend(targeted_parties, fiscal_year)
    product_labels, product_values, product_units = product_mix(targeted_parties, fiscal_year, selected_month)
    product_series = product_monthly_trend(targeted_parties, fiscal_year)

    executives = targeted_parties.values_list('executive__name', flat=True).distinct()
    executive_tiles = []
    for exec_name in executives:
        exec_parties = targeted_parties.filter(executive__name=exec_name)
        e_target = target_total(exec_parties, fiscal_year, selected_month)
        e_achievement = achievement_total(exec_parties, fiscal_year, selected_month)
        e_units = units_total(exec_parties, fiscal_year, selected_month)
        executive_tiles.append({
            'name': exec_name,
            'percent': percent_achieved(e_target, e_achievement),
            'achievement': float(e_achievement),
            'units': float(e_units),
        })
    executive_tiles.sort(key=lambda t: t['achievement'], reverse=True)

    total_for_contribution = sum(t['achievement'] for t in executive_tiles)
    for t in executive_tiles:
        t['contribution_pct'] = round((t['achievement'] / total_for_contribution) * 100, 1) if total_for_contribution else 0

    context = {
        'state_name': state_name,
        'fiscal_year': fiscal_year,
        'total_target': total_target,
        'total_achievement': total_achievement,
        'total_units': total_units,
        'percent_achieved': percent_achieved(total_target, total_achievement),
        'month_labels': MONTH_LABELS,
        'monthly_target': monthly_target,
        'monthly_achievement': monthly_achievement,
        'monthly_units': monthly_units,
        'month_numbers': MONTH_NUMBERS,
        'selected_month': selected_month,
        'selected_month_label': selected_month_label,
        'executive_tiles': executive_tiles,
        'executive_names': [t['name'] for t in executive_tiles],
        'executive_achievements': [t['achievement'] for t in executive_tiles],
        'executive_units': [t['units'] for t in executive_tiles],
        'product_labels': product_labels,
        'product_values': product_values,
        'product_units': product_units,
        'product_series': product_series,
    }
    return render(request, 'meeting_mode/state_target.html', context)


@login_required
def executive_target(request, executive_name):
    """Stream 1 (Target Review) - Executive-level page."""
    fiscal_year = get_fiscal_year(date.today())
    accessible_parties = get_accessible_parties(request.user)
    targeted_parties = accessible_parties.filter(mou__fiscal_year=fiscal_year, executive__name=executive_name)

    selected_month, selected_month_label = parse_selected_month(request)

    total_target = target_total(targeted_parties, fiscal_year, selected_month)
    total_achievement = achievement_total(targeted_parties, fiscal_year, selected_month)
    total_units = units_total(targeted_parties, fiscal_year, selected_month)
    monthly_target, monthly_achievement = monthly_trend(targeted_parties, fiscal_year)
    monthly_units = monthly_units_trend(targeted_parties, fiscal_year)
    product_labels, product_values, product_units = product_mix(targeted_parties, fiscal_year, selected_month)
    product_series = product_monthly_trend(targeted_parties, fiscal_year)

    party_rows = []
    for party in targeted_parties:
        single_party = Party.objects.filter(pk=party.pk)
        p_target = target_total(single_party, fiscal_year, selected_month)
        p_achievement = achievement_total(single_party, fiscal_year, selected_month)
        p_units = units_total(single_party, fiscal_year, selected_month)
        party_rows.append({
            'name': party.name,
            'city': party.city,
            'target': float(p_target),
            'achievement': float(p_achievement),
            'units': float(p_units),
            'percent': percent_achieved(p_target, p_achievement),
        })
    party_rows.sort(key=lambda r: r['percent'], reverse=True)

    context = {
        'executive_name': executive_name,
        'fiscal_year': fiscal_year,
        'total_target': total_target,
        'total_achievement': total_achievement,
        'total_units': total_units,
        'percent_achieved': percent_achieved(total_target, total_achievement),
        'month_labels': MONTH_LABELS,
        'monthly_target': monthly_target,
        'monthly_achievement': monthly_achievement,
        'monthly_units': monthly_units,
        'month_numbers': MONTH_NUMBERS,
        'selected_month': selected_month,
        'selected_month_label': selected_month_label,
        'product_labels': product_labels,
        'product_values': product_values,
        'product_units': product_units,
        'product_series': product_series,
        'party_rows': party_rows,
        'party_names': [r['name'] for r in party_rows],
        'party_achievements': [r['achievement'] for r in party_rows],
        'party_targets': [r['target'] for r in party_rows],
        'party_units': [r['units'] for r in party_rows],
    }
    return render(request, 'meeting_mode/executive_target.html', context)


@login_required
def product_target(request, product_name):
    fiscal_year = get_fiscal_year(date.today())
    accessible_parties = get_accessible_parties(request.user)
    targeted_parties = accessible_parties.filter(mou__fiscal_year=fiscal_year)

    state_name = request.GET.get('state')
    executive_name = request.GET.get('executive')
    selected_month, selected_month_label = parse_selected_month(request)

    if state_name:
        targeted_parties = targeted_parties.filter(state=state_name)
        scope_label = state_name
        breakdown_field = 'party__executive__name'
        breakdown_level_label = 'Executives'
        breakdown_url_base = '/meeting/target/executive/'
    elif executive_name:
        targeted_parties = targeted_parties.filter(executive__name=executive_name)
        scope_label = executive_name
        breakdown_field = 'party__name'
        breakdown_level_label = 'Parties'
        breakdown_url_base = '/reports/party/'
    else:
        scope_label = "All India"
        breakdown_field = 'party__state'
        breakdown_level_label = 'States'
        breakdown_url_base = '/meeting/target/state/'

    total_achievement = product_total(targeted_parties, fiscal_year, product_name, selected_month)
    total_units = product_units_total(targeted_parties, fiscal_year, product_name, selected_month)
    monthly_sales, monthly_units = single_product_monthly_trend(targeted_parties, fiscal_year, product_name)
    subproduct_labels, subproduct_values, subproduct_units = subproduct_mix(
        targeted_parties, fiscal_year, product_name, selected_month
    )
    subproduct_series = subproduct_monthly_trend(targeted_parties, fiscal_year, product_name)

    subproduct_table = []
    for label, value, units_val in zip(subproduct_labels, subproduct_values, subproduct_units):
        pct = round((value / float(total_achievement)) * 100, 1) if total_achievement else 0
        subproduct_table.append({'name': label, 'value': value, 'units': units_val, 'pct': pct})

    breakdown_labels, breakdown_values, breakdown_units = product_breakdown_by_level(
        targeted_parties, fiscal_year, product_name, breakdown_field, selected_month
    )

    context = {
        'product_name': product_name,
        'scope_label': scope_label,
        'fiscal_year': fiscal_year,
        'total_achievement': total_achievement,
        'total_units': total_units,
        'month_labels': MONTH_LABELS,
        'month_numbers': MONTH_NUMBERS,
        'selected_month': selected_month,
        'selected_month_label': selected_month_label,
        'monthly_sales': monthly_sales,
        'monthly_units': monthly_units,
        'subproduct_labels': subproduct_labels,
        'subproduct_values': subproduct_values,
        'subproduct_units': subproduct_units,
        'subproduct_table': subproduct_table,
        'subproduct_series': subproduct_series,
        'breakdown_labels': breakdown_labels,
        'breakdown_values': breakdown_values,
        'breakdown_units': breakdown_units,
        'breakdown_level_label': breakdown_level_label,
        'breakdown_url_base': breakdown_url_base,
        'breakdown_is_party': executive_name is not None,
        'state_param': state_name or '',
        'executive_param': executive_name or '',
    }
    return render(request, 'meeting_mode/product_target.html', context)