from django.contrib.auth.models import User
from django.db import models


class MutualFund(models.Model):
  scheme_code = models.CharField(max_length=50, unique=True)
  scheme_name = models.CharField(max_length=255)
  fund_house = models.CharField(max_length=100)
  category = models.CharField(
      max_length=100, blank=True, null=True
  )  # e.g., Equity, Debt, Hybrid

  def __str__(self):
    return self.scheme_name


class NAVHistory(models.Model):
  mutual_fund = models.ForeignKey(
      MutualFund, on_delete=models.CASCADE, related_name='nav_history'
  )
  date = models.DateField()
  nav = models.DecimalField(max_digits=10, decimal_places=4)

  class Meta:
    unique_together = ('mutual_fund', 'date')
    ordering = ['-date']


class UserPortfolio(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  mutual_fund = models.ForeignKey(MutualFund, on_delete=models.CASCADE)
  units = models.DecimalField(max_digits=15, decimal_places=4)
  invested_amount = models.DecimalField(max_digits=12, decimal_places=2)
  purchase_date = models.DateField()

  def __str__(self):
    return f'{self.user.username} - {self.mutual_fund.scheme_name}'