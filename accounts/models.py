from django.db import models
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
        help_text="Required for the 'Executive' role - links this login to their party data."
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def sees_all_data(self):
        return self.role in ('admin', 'sales_head')
