from django.contrib.auth.models import User
from django.db import models

class Package(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    data_limit = models.CharField(max_length=100)
    duration = models.CharField(max_length=50)
    minutes_limit = models.CharField(max_length=50, default=0)

    def __str__(self):
        return self.name

class UserPackage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, null=True, on_delete=models.SET_NULL)
    data_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # In MBs
    minutes_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # In minutes
    is_online = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Package"