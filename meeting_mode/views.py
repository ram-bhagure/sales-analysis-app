from datetime import date
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.permissions import get_accessible_parties
from data_ingestion.services import get_fiscal_year
from core.models import MOU, Invoice


@login_required
def all_india_target(request):
    """Stream 1 (Target Review) - All-India opening screen.
    Only considers parties that have an MOU (target) record."""
    fiscal_year = get_fiscal_year(date.today())
    accessible_parties = get_accessible_parties(request.user)

    # Stream 1 scope: only targeted parties
    targeted_parties = accessible_parties.filter(mou__fiscal_year=fiscal_year)

    mous = MOU.objects.filter(party__in=targeted_parties, fiscal_year=fiscal_year)
    total_target = mous.aggregate(total=Sum('annual_target'))['total'] or 0
    total_achievement = Invoice.objects.filter(
        party__in=targeted_parties, fiscal_year=fiscal_year
    ).aggregate(total=Sum('basic_amount'))['total'] or 0
    percent_achieved = round((total_achievement / total_target) * 100, 1) if total_target else 0

    # State-wise tiles
    states = targeted_parties.values_list('state', flat=True).distinct()
    state_tiles = []
    for state_name in states:
        state_parties = targeted_parties.filter(state=state_name)
        state_target = MOU.objects.filter(
            party__in=state_parties, fiscal_year=fiscal_year
        ).aggregate(total=Sum('annual_target'))['total'] or 0
        state_achievement = Invoice.objects.filter(
            party__in=state_parties, fiscal_year=fiscal_year
        ).aggregate(total=Sum('basic_amount'))['total'] or 0
        state_percent = round((state_achievement / state_target) * 100, 1) if state_target else 0
        state_tiles.append({
            'name': state_name,
            'percent': state_percent,
        })

    context = {
        'fiscal_year': fiscal_year,
        'total_target': total_target,
        'total_achievement': total_achievement,
        'percent_achieved': percent_achieved,
        'state_tiles': state_tiles,
    }
    return render(request, 'meeting_mode/all_india_target.html', context)
