from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from core.models import Executive


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('sales_head', 'Sales Head'),
        ('executive', 'Executive'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    executive = models.ForeignKey(
        Executive, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Only set this for the 'Executive' role - leave blank for Admin/Sales Head."
    )

    def clean(self):
        if self.role == 'executive' and not self.executive:
            raise ValidationError("Executive role requires an Executive to be selected.")
        if self.role in ('admin', 'sales_head') and self.executive:
            raise ValidationError("Admin/Sales Head accounts should not have an Executive selected.")

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def sees_all_data(self):
        return self.role in ('admin', 'sales_head')
    