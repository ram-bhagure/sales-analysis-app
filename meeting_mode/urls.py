from django.urls import path
from . import views

urlpatterns = [
    path('target/', views.all_india_target, name='meeting_all_india_target'),
    path('target/state/<str:state_name>/', views.state_target, name='meeting_state_target'),
    path('target/executive/<str:executive_name>/', views.executive_target, name='meeting_executive_target'),
    path('target/product/<str:product_name>/', views.product_target, name='meeting_product_target'),
]