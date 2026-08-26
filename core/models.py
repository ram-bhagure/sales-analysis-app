from django.db import models


class Executive(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class Party(models.Model):
    """A dealer/distributor/channel partner. Party name is the natural key."""
    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    executive = models.ForeignKey(Executive, on_delete=models.PROTECT, related_name='parties')

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class Subproduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='subproducts')
    name = models.CharField(max_length=150)

    class Meta:
        unique_together = ('product', 'name')

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class Invoice(models.Model):
    """One row per invoice line item, as uploaded from the monthly workbook."""
    invoice_no = models.CharField(max_length=100)
    date = models.DateField()
    month = models.PositiveSmallIntegerField()   # derived from date, 1-12
    fiscal_year = models.CharField(max_length=9)  # e.g. "2026-2027"
    warehouse = models.CharField(max_length=150, blank=True)
    party = models.ForeignKey(Party, on_delete=models.PROTECT, related_name='invoices')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='invoices')
    subproduct = models.ForeignKey(Subproduct, on_delete=models.PROTECT, related_name='invoices', null=True, blank=True)
    units = models.DecimalField(max_digits=12, decimal_places=2)
    basic_amount = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['party', 'month', 'fiscal_year']),
        ]

    def __str__(self):
        return f"{self.invoice_no} - {self.party.name}"


class MOU(models.Model):
    """Annual target record per party, with monthly target/achievement columns."""
    party = models.OneToOneField(Party, on_delete=models.CASCADE, related_name='mou')
    fiscal_year = models.CharField(max_length=9)
    annual_target = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Monthly targets - stored as given in the workbook (Annual Target / 12 by business rule)
    target_apr = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_may = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_jun = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_jul = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_aug = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_sep = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_oct = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_nov = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_dec = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_jan = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_feb = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_mar = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Monthly achievement, as given directly in the MOU sheet (should reconcile against Invoice sums)
    achievement_apr = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achievement_may = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achievement_jun = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achievement_jul = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achievement_aug = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achievement_sep = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achievement_oct = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achievement_nov = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achievement_dec = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achievement_jan = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achievement_feb = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achievement_mar = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"MOU - {self.party.name} ({self.fiscal_year})"
    