from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from .serializers import *


class TradeViewset(viewsets.ModelViewSet):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer

    def perform_destroy(self, trade):
        trades_on_security = Trade.objects.filter(portfolio=trade.portfolio,
                                                  security=trade.security) \
            .order_by('trade_time')

        count = 0
        average_price = 0
        for t in trades_on_security:
            if t == trade:
                continue

            if t.trade_type == Trade.BUY:
                count += t.count
                average_price += t.trade_price * t.count
            else:
                count -= t.count
                average_price -= t.trade_price * t.count
            if count < 0:
                raise ValidationError('Position becomes negative on deletion of this trade')

        if count != 0:
            average_price /= count
        else:
            average_price = 0

        positions_on_security = Position.objects.filter(portfolio=trade.portfolio, security=trade.security)
        # Todo - Make positions time series and snapshot position at each time there's a change so only trades post
        # trade to be deleted need to be checked
        if len(positions_on_security) > 0:
            position = positions_on_security[0]
            position.count = count
            position.average_price = average_price
            position.save()

        trade.delete()


class PortfolioViewset(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer


class PositionViewset(viewsets.ModelViewSet):
    """Returns the position data"""
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
