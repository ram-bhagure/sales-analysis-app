from datetime import date
from django.db.models import Sum
from django.shortcuts import render
from accounts.permissions import role_required, get_accessible_parties
from data_ingestion.services import get_fiscal_year
from core.models import MOU, Invoice


@role_required('admin', 'sales_head')
def management_dashboard(request):
    fiscal_year = get_fiscal_year(date.today())
    parties = get_accessible_parties(request.user)

    total_target = MOU.objects.filter(
        party__in=parties, fiscal_year=fiscal_year
    ).aggregate(total=Sum('annual_target'))['total'] or 0

    total_achievement = Invoice.objects.filter(
        party__in=parties, fiscal_year=fiscal_year
    ).aggregate(total=Sum('basic_amount'))['total'] or 0

    percent_achieved = round((total_achievement / total_target) * 100, 1) if total_target else 0

    context = {
        'fiscal_year': fiscal_year,
        'total_target': total_target,
        'total_achievement': total_achievement,
        'percent_achieved': percent_achieved,
    }
    return render(request, 'dashboard/management.html', context)