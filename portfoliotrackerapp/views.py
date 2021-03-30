from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from .serializers import *


class TradeViewset(viewsets.ModelViewSet):
    """
        API for Trade list, create, update, delete and retrieve.
        POST to /trade/ - Add a trade.
        GET to /trade/ - List all trades.
        GET to /trade/1/ - Retrieve trade 1.
        POST to /trade/1/ to update trade 1
        DELETE to /trade/1/ to remove trade 1

        This API returns 400 for trade manipulations resulting negative positions
    """
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
    """
    API for Portfolio list, create, delete and retrieve.
    A list of all portfolios can be fetched as well as a single portfolio detail
    can be accessed by giving it's ID like /portfolio/1/

    The response includes the stock holding as well as Returns from the portfolio
    """
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer


class PositionViewset(viewsets.ModelViewSet):
    """Returns the position data"""
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
