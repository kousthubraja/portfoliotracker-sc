from django.db import models


class Portfolio(models.Model):
    name = models.CharField(max_length=50, null=True)

    def __str__(self):
        return f"{self.name}"


class PortfolioSecurityAllocation(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    security = models.CharField(max_length=10)
    count = models.PositiveIntegerField()
    time_of_addition = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.portfolio.name} : {self.security.name}"


class Trade(models.Model):
    BUY = 'B'
    SELL = 'S'
    TRADE_TYPE_CHOICES = ((BUY, 'Buy'), (SELL, 'Sell'))

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, db_index=True)
    security = models.CharField(max_length=10, db_index=True)
    count = models.PositiveIntegerField()
    trade_type = models.CharField(max_length=5, choices=TRADE_TYPE_CHOICES, default=BUY)
    trade_price = models.FloatField(default=100)
    trade_time = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.portfolio.name}: {self.security.name}: {self.trade_type}"


class Position(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, db_index=True)
    security = models.CharField(max_length=10, db_index=True)
    count = models.PositiveIntegerField()
    average_price = models.FloatField()

    def __str__(self):
        return f"{self.portfolio.name} : {self.security.name}"
