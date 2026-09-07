from django.urls import path
from . import views

urlpatterns = [
    path('party/<str:party_name>/<str:fiscal_year>/', views.party_report, name='party_report'),
]