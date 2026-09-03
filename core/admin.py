from django.contrib import admin
from .models import Executive, Party, Product, Subproduct, Invoice, MOU


@admin.register(Executive)
class ExecutiveAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'executive')
    list_filter = ('state', 'executive')
    search_fields = ('name', 'city')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Subproduct)
class SubproductAdmin(admin.ModelAdmin):
    list_display = ('name', 'product')
    list_filter = ('product',)
    search_fields = ('name',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('voucher_no', 'date', 'party', 'product', 'subproduct', 'basic_amount', 'fiscal_year')
    list_filter = ('fiscal_year', 'month', 'product')
    search_fields = ('voucher_no', 'party__name')
    date_hierarchy = 'date'


@admin.register(MOU)
class MOUAdmin(admin.ModelAdmin):
    list_display = ('party', 'fiscal_year', 'annual_target')
    list_filter = ('fiscal_year',)
    search_fields = ('party__name',)
